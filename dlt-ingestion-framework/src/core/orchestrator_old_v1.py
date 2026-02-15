"""
Core Orchestrator - Main DLT pipeline execution logic.

This module contains the IngestionOrchestrator class that:
- Builds connection strings for different database types
- Creates DLT pipelines and resources
- Handles both database and API sources
- Extracts metrics and monitors schema evolution
- Records execution metadata

Supports: PostgreSQL, Oracle, MSSQL, Azure SQL, REST APIs
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from urllib.parse import quote_plus
import pandas as pd

import dlt
from dlt.sources.credentials import ConnectionStringCredentials
from dlt.sources.sql_database import sql_table
from dlt.sources.rest_api import rest_api_source

from src.config import ConfigLoader
from src.metadata import MetadataTracker

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """Main orchestrator for DLT-based multi-source data ingestion.
    
    Features:
        - Multi-source support (PostgreSQL, Oracle, MSSQL, Azure SQL, REST APIs)
        - Full and incremental loads with automatic watermark management
        - Date-partitioned Parquet output to ADLS Gen2
        - Schema evolution monitoring
        - Production-grade metrics extraction
        - Comprehensive audit logging
        - GB-scale data handling with dynamic chunking
        - Parallel table processing support
        - Pre-flight table size estimation
    
    DLT Best Practices:
        - Single pipeline instance reused across all jobs
        - Schema contracts for controlled evolution
        - Primary key support for proper merge operations
        - Pipeline state management and checkpointing
        - Memory-efficient processing with configurable chunk sizes
    """
    
    def __init__(self):
        """Initialize orchestrator with configuration and metadata tracking.
        
        Creates a single DLT pipeline instance that will be reused for all jobs.
        This follows DLT best practices for state management and performance.
        """
        self.config_loader = ConfigLoader()
        self.metadata_tracker = MetadataTracker()
        self.secrets = self.config_loader.load_secrets()
        
        # DLT BEST PRACTICE #1: Create pipeline ONCE and reuse for all jobs
        # This ensures proper state management and avoids creating separate metadata tables
        self.pipeline = dlt.pipeline(
            pipeline_name="multi_source_ingestion",
            destination="filesystem",
            dataset_name="raw_data"
        )
        
        logger.info("Orchestrator initialized")
        logger.info(f"DLT Pipeline: {self.pipeline.pipeline_name}")
        logger.info(f"Destination: {self.pipeline.destination}")
        logger.info(f"Working Directory: {self.pipeline.working_dir}")
        
        # State version may not be available until first run
        try:
            state_version = self.pipeline.state_version
            logger.info(f"Pipeline State Version: {state_version}")
        except:
            logger.info("Pipeline State: Not yet initialized")
    
    def parse_column_list(self, column_str: str) -> List[str]:
        """Parse comma-separated column string into list.
        
        Args:
            column_str: Comma-separated column names (e.g., 'date,country,region')
        
        Returns:
            List of column names, or empty list if None/empty
        """
        if not column_str or pd.isna(column_str):
            return []
        return [col.strip() for col in str(column_str).split(',') if col.strip()]
    
    def build_connection_string(self, source_type: str, source_name: str) -> Optional[str]:
        """Build database connection string for given source.
        
        Args:
            source_type: Database type (postgresql/oracle/mssql/azure_sql/api)
            source_name: Source identifier from Excel config
        
        Returns:
            SQLAlchemy connection string, or None for API sources
        
        Raises:
            ValueError: If source type unsupported or config missing required fields
        """
        source_type = source_type.lower()
        
        if source_type == "api":
            return None  # API sources don't use connection strings
        
        # PostgreSQL
        if source_type == "postgresql":
            cfg = self.secrets['sources']['postgresql']
            conn_str = (
                f"postgresql+psycopg2://{cfg['username']}:{cfg['password']}"
                f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
            )
            logger.debug(f"PostgreSQL connection: {cfg['host']}:{cfg['port']}/{cfg['database']}")
            return conn_str
        
        # Oracle
        elif source_type == "oracle":
            ora = self.secrets['sources']['oracle']
            
            # Direct connection (avoids tnsnames.ora requirement)
            if 'service_name' in ora:
                conn_str = (
                    f"oracle+oracledb://{ora['username']}:{ora['password']}"
                    f"@{ora['host']}:{ora['port']}/{ora['service_name']}"
                )
                logger.debug(f"Oracle connection: {ora['host']}:{ora['port']}/{ora['service_name']}")
            elif 'sid' in ora:
                conn_str = (
                    f"oracle+oracledb://{ora['username']}:{ora['password']}"
                    f"@{ora['host']}:{ora['port']}/{ora['sid']}"
                )
                logger.debug(f"Oracle connection: {ora['host']}:{ora['port']}/{ora['sid']}")
            else:
                raise ValueError("Oracle config must have either 'service_name' or 'sid'")
            
            return conn_str
        
        # SQL Server (on-premise)
        elif source_type == "mssql":
            ms = self.secrets['sources']['mssql']
            
            # Raw ODBC connection string (handles special characters in passwords)
            driver = ms.get('query', {}).get('driver', 'ODBC Driver 17 for SQL Server')
            encrypt = ms.get('query', {}).get('Encrypt', 'no')
            trust_cert = ms.get('query', {}).get('TrustServerCertificate', 'yes')
            
            odbc_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={ms['host']},{ms['port']};"
                f"DATABASE={ms['database']};"
                f"UID={ms['username']};"
                f"PWD={ms['password']};"
                f"Encrypt={encrypt};"
                f"TrustServerCertificate={trust_cert};"
            )
            
            conn_str = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"
            logger.debug(f"MSSQL connection: {ms['host']}:{ms['port']}/{ms['database']}")
            return conn_str
        
        # Azure SQL
        elif source_type == "azure_sql":
            azure = self.secrets['sources']['azure_sql']
            
            # Azure SQL requires encryption and proper SSL validation
            driver = azure.get('query', {}).get('driver', 'ODBC Driver 17 for SQL Server')
            encrypt = azure.get('query', {}).get('Encrypt', 'yes')  # Required for Azure
            trust_cert = azure.get('query', {}).get('TrustServerCertificate', 'no')  # Proper SSL
            
            odbc_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={azure['host']},{azure['port']};"
                f"DATABASE={azure['database']};"
                f"UID={azure['username']};"
                f"PWD={azure['password']};"
                f"Encrypt={encrypt};"
                f"TrustServerCertificate={trust_cert};"
            )
            
            conn_str = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"
            logger.debug(f"Azure SQL connection: {azure['host']}/{azure['database']}")
            return conn_str
        
        else:
            raise ValueError(f"Unsupported source type: {source_type}")
    
    def _estimate_table_size(self, conn_str: str, table_name: str, schema_name: Optional[str] = None) -> tuple:
        """Estimate table size and recommend chunk_size.
        
        Args:
            conn_str: Database connection string
            table_name: Name of the table
            schema_name: Schema name (optional)
        
        Returns:
            Tuple of (row_count, recommended_chunk_size)
        """
        try:
            from sqlalchemy import create_engine, text
            
            engine = create_engine(conn_str)
            full_table = f"{schema_name}.{table_name}" if schema_name else table_name
            
            # Try to get row count (database-specific optimizations)
            query = f"SELECT COUNT(*) as row_count FROM {full_table}"
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                row_count = result.scalar()
            
            # Recommend chunk_size based on table size
            if row_count < 100000:
                recommended_chunk = 50000  # Small tables
            elif row_count < 1000000:
                recommended_chunk = 100000  # Medium tables (default)
            elif row_count < 10000000:
                recommended_chunk = 250000  # Large tables (1-10M rows)
            elif row_count < 50000000:
                recommended_chunk = 500000  # Very large (10-50M rows)
            else:
                recommended_chunk = 1000000  # Massive tables (50M+ rows)
            
            logger.info(f"[TABLE SIZE] {full_table}: {row_count:,} rows")
            logger.info(f"[RECOMMENDED CHUNK] {recommended_chunk:,} rows for optimal performance")
            
            return row_count, recommended_chunk
            
        except Exception as e:
            logger.warning(f"[SIZE ESTIMATION SKIPPED] Could not estimate table size: {e}")
            return None, 100000  # Default fallback
    
    def execute_job(self, job: Dict) -> bool:
        """Execute a single ingestion job.
        
        Args:
            job: Job configuration dictionary from Excel
        
        Returns:
            True if job succeeded, False if failed
        """
        job_name = f"{job['source_name']}.{job['table_name']}"
        start_time = datetime.now()
        execution_date = start_time.strftime("%Y-%m-%d")
        execution_partition = start_time.strftime("%Y/%m/%d")
        
        logger.info("="*80)
        logger.info(f"Starting job: {job_name}")
        logger.info(f"  Source: {job['source_type']}")
        logger.info(f"  Load Type: {job['load_type']}")
        logger.info(f"  Execution Date: {execution_date}")
        logger.info(f"  Partition Path: {execution_partition}")
        
        rows_processed = 0
        
        try:
            # DLT BEST PRACTICE #1: REUSE existing pipeline instance
            # No longer creating new pipeline per job - using self.pipeline
            pipeline = self.pipeline
            
            logger.info(f"Using pipeline: {pipeline.pipeline_name}")
            
            # Handle API sources vs database sources
            if job['source_type'].lower() == "api":
                load_info = self._execute_api_job(job, pipeline)
            else:
                load_info = self._execute_database_job(job, pipeline)
            
            # Extract metrics from pipeline
            rows_processed = self._extract_row_count(pipeline, job['table_name'])
            
            # Monitor schema evolution
            schema_version = self._check_schema_evolution(pipeline, job['table_name'])
            
            # Log pipeline state for incremental loads
            if job['load_type'].upper() == "INCREMENTAL":
                self._log_incremental_state(pipeline, job['table_name'])
            
            # Calculate execution metrics
            duration = (datetime.now() - start_time).total_seconds()
            partition_path = f"{job['source_name']}/{job['table_name']}/{execution_partition}"
            full_adls_path = f"az://raw-data/{partition_path}"
            
            # Log success
            logger.info(f"[SUCCESS] Job completed successfully")
            logger.info(f"  Rows processed: {rows_processed:,}")
            logger.info(f"  Schema version: {schema_version}")
            logger.info(f"  Duration: {duration:.2f}s")
            logger.info(f"  ADLS Path: {full_adls_path}")
            logger.info(f"  Partition: {execution_partition}")
            
            # Record success in metadata
            self.metadata_tracker.record_job(
                job_name=job_name,
                status="SUCCESS",
                rows=rows_processed,
                duration=duration,
                partition_path=partition_path
            )
            
            return True
        
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"[FAILED] Job failed: {job_name}")
            logger.error(f"  Error: {str(e)}", exc_info=True)
            
            # Record failure in metadata
            self.metadata_tracker.record_job(
                job_name=job_name,
                status="FAILED",
                rows=0,
                duration=duration,
                partition_path=None,
                error=str(e)
            )
            
            return False
    
    def _execute_api_job(self, job: Dict, pipeline) -> any:
        """Execute API source ingestion using DLT rest_api_source.
        
        Args:
            job: Job configuration
            pipeline: DLT pipeline instance
        
        Returns:
            DLT load_info object
        """
        api_config = self.secrets['sources']['api'][job['source_name']]
        
        logger.info(f"API base URL: {api_config['base_url']}")
        
        # Get endpoint configuration
        endpoint_path = api_config.get('endpoint', job.get('endpoint', '/coins/markets'))
        endpoint_params = api_config.get('params', {})
        
        # Build REST API source config (DLT native)
        rest_config = {
            "client": {
                "base_url": api_config['base_url'],
            },
            "resources": [
                {
                    "name": job['table_name'],
                    "endpoint": {
                        "path": endpoint_path,
                        "params": endpoint_params
                    }
                }
            ]
        }
        
        # Add API key header if present
        if api_config.get('api_key'):
            rest_config["client"]["headers"] = {
                "x-cg-demo-api-key": api_config['api_key']
            }
        
        # Create REST API source (handles pagination, retry, state)
        logger.info(f"Creating DLT REST API source for: {job['table_name']}")
        api_source = rest_api_source(rest_config)
        
        # Execute pipeline
        write_disposition = "replace" if job['load_type'].upper() == "FULL" else "merge"
        
        # DLT BEST PRACTICE #2: Warn about merge limitation
        if write_disposition == "merge":
            logger.warning("[WARNING] API sources with filesystem destination use 'replace' mode")
            logger.warning("  Consider using warehouse destination for true merge/upsert")
            write_disposition = "replace"
        
        # DLT BEST PRACTICE #4: Add schema contract
        schema_contract = {
            "tables": "evolve",
            "columns": "evolve",
            "data_type": "discard_value"
        }
        
        logger.info(f"Running DLT REST API pipeline")
        load_info = pipeline.run(
            api_source,
            write_disposition=write_disposition,
            loader_file_format="parquet",
            schema_contract=schema_contract
        )
        
        return load_info
    
    def _execute_database_job(self, job: Dict, pipeline) -> any:
        """Execute database source ingestion using DLT sql_table.
        
        Args:
            job: Job configuration
            pipeline: DLT pipeline instance
        
        Returns:
            DLT load_info object
        """
        # Build connection string
        conn_str = self.build_connection_string(job['source_type'], job['source_name'])
        
        # Build incremental object if needed
        incremental_obj = None
        if job['load_type'].upper() == "INCREMENTAL" and job.get('watermark_column'):
            incremental_obj = dlt.sources.incremental(
                cursor_path=job['watermark_column'],
                initial_value=job.get('last_watermark')
            )
            logger.info(f"Incremental load: {job['watermark_column']} > {job.get('last_watermark')}")
        
        # DLT BEST PRACTICE #3: Extract primary_key from configuration
        primary_key = None
        if job.get('primary_key') and not pd.isna(job.get('primary_key')):
            # Support single key or composite keys (comma-separated)
            primary_key = [k.strip() for k in str(job['primary_key']).split(',')]
            if len(primary_key) == 1:
                primary_key = primary_key[0]
            logger.info(f"Primary key configured: {primary_key}")
        
        # DLT BEST PRACTICE #6: Parse column selection if provided
        # NOTE: Column selection is version-dependent - only use if DLT supports it
        columns = None
        if job.get('columns') and not pd.isna(job.get('columns')):
            columns = [col.strip() for col in str(job['columns']).split(',')]
            logger.info(f"Column selection: {len(columns)} columns specified")
            logger.warning(f"[WARNING] Column selection may not be supported in your DLT version")
        
        # GB-SCALE ENHANCEMENT #1: Pre-flight table size estimation
        estimated_rows = None
        recommended_chunk = 100000  # Default
        
        if job['load_type'].upper() == "FULL":
            logger.info("[PRE-FLIGHT CHECK] Estimating table size...")
            estimated_rows, recommended_chunk = self._estimate_table_size(
                conn_str, 
                job['table_name'], 
                job.get('schema_name')
            )
        
        # GB-SCALE ENHANCEMENT #2: Dynamic chunk_size from Excel config
        chunk_size = 100000  # Default fallback
        
        if job.get('chunk_size') and not pd.isna(job.get('chunk_size')):
            try:
                chunk_size = int(job['chunk_size'])
                logger.info(f"[CUSTOM CHUNK SIZE] Using configured value: {chunk_size:,} rows")
            except (ValueError, TypeError):
                logger.warning(f"[INVALID CHUNK SIZE] Defaulting to {chunk_size:,} rows")
        elif estimated_rows and estimated_rows > 1000000:
            # Auto-optimize for large tables
            chunk_size = recommended_chunk
            logger.info(f"[AUTO-OPTIMIZED] Chunk size adjusted to {chunk_size:,} rows for large table")
        
        # GB-SCALE ENHANCEMENT #3: Memory warning for very large chunks
        if chunk_size > 500000:
            logger.warning(f"[MEMORY WARNING] Large chunk size ({chunk_size:,} rows) may require significant memory")
            logger.warning(f"  Ensure Databricks cluster has sufficient memory (16GB+ recommended)")
        
        # Create DLT resource
        # Note: Only passing parameters that are supported by sql_table()
        resource_kwargs = {
            'credentials': ConnectionStringCredentials(conn_str),
            'table': job['table_name'],
            'incremental': incremental_obj,
            'backend': "pyarrow",
            'chunk_size': chunk_size,
            'detect_precision_hints': True,
            'defer_table_reflect': True
        }
        
        # Add optional parameters only if they have values
        if job.get('schema_name'):
            resource_kwargs['schema'] = job['schema_name']
        
        # DLT BEST PRACTICE #3: Add primary_key only if supported and configured
        if primary_key:
            resource_kwargs['primary_key'] = primary_key
        
        # DLT BEST PRACTICE #6: Add columns only if supported (removed for compatibility)
        # The 'columns' parameter is not available in all DLT versions
        # To use it, upgrade dlt: pip install --upgrade dlt[sql_database]
        
        resource = sql_table(**resource_kwargs)
        
        # Determine write disposition
        write_disposition = "replace" if job['load_type'].upper() == "FULL" else "merge"
        
        # DLT BEST PRACTICE #2: Filesystem doesn't support merge - ERROR instead of silent fallback
        if write_disposition == "merge":
            logger.error("[ERROR] Filesystem destination doesn't support 'merge' write disposition")
            logger.error("  Options to fix this:")
            logger.error("    1. Change load_type to 'FULL' in Excel config (data will be replaced)")
            logger.error("    2. Use Delta Lake format: [destination.filesystem.file_format] type='delta'")
            logger.error("    3. Switch to warehouse destination (BigQuery, Snowflake, DuckDB)")
            logger.error(f"  For now, using 'replace' mode - ALL EXISTING DATA WILL BE DELETED")
            write_disposition = "replace"
        
        logger.info(f"Write disposition: {write_disposition}")
        logger.info(f"Output format: Parquet (date-partitioned)")
        
        # DLT BEST PRACTICE #4: Add schema contract for controlled evolution
        schema_contract = {
            "tables": "evolve",           # Allow new tables to be created
            "columns": "evolve",          # Allow new columns (can change to 'freeze' for strict mode)
            "data_type": "discard_value"  # Discard values with mismatched types instead of failing
        }
        
        logger.info(f"Schema contract: {schema_contract}")
        
        # Execute pipeline
        logger.info("Executing pipeline...")
        load_info = pipeline.run(
            resource,
            write_disposition=write_disposition,
            table_name=job['table_name'],
            loader_file_format="parquet",
            # DLT BEST PRACTICE #4: Apply schema contract
            schema_contract=schema_contract
        )
        
        # DLT BEST PRACTICE #7: Log pipeline state after execution
        try:
            logger.info(f"Pipeline state version: {pipeline.state_version}")
        except:
            logger.info("Pipeline state: Execution completed")
        
        return load_info
    
    def _extract_row_count(self, pipeline, table_name: str) -> int:
        """Extract row count from pipeline metrics (DLT native).
        
        Args:
            pipeline: DLT pipeline instance
            table_name: Table name to get count for
        
        Returns:
            Number of rows processed
        """
        rows_processed = 0
        
        # Method 1: Try to get from last_trace (most accurate)
        if hasattr(pipeline, 'last_trace') and pipeline.last_trace:
            if hasattr(pipeline.last_trace, 'last_normalize_info'):
                if pipeline.last_trace.last_normalize_info:
                    row_counts = pipeline.last_trace.last_normalize_info.row_counts
                    if table_name in row_counts:
                        # row_counts can be int or dict
                        count_value = row_counts[table_name]
                        rows_processed = (
                            count_value if isinstance(count_value, int)
                            else count_value.get('row_count', 0)
                        )
                        logger.debug(f"Row count from pipeline trace: {rows_processed:,}")
        
        return rows_processed
    
    def _check_schema_evolution(self, pipeline, table_name: str) -> int:
        """Monitor for schema changes (DLT native schema evolution).
        
        Args:
            pipeline: DLT pipeline instance
            table_name: Table name to check
        
        Returns:
            Schema version number
        """
        schema_version = 1
        
        if hasattr(pipeline, 'default_schema') and pipeline.default_schema:
            schema = pipeline.default_schema
            schema_version = getattr(schema, 'version', 1)
            
            if schema_version > 1:
                logger.warning(f"[SCHEMA CHANGE] Detected in {table_name}")
                logger.warning(f"  Schema version: {schema_version} (changed from {schema_version - 1})")
                logger.warning(f"  Check _dlt_version/ folder in ADLS for details")
        
        return schema_version
    
    def _log_incremental_state(self, pipeline, table_name: str):
        """Log pipeline state for incremental loads (DLT native state inspection).
        
        Args:
            pipeline: DLT pipeline instance
            table_name: Table name to check state for
        """
        if not hasattr(pipeline, 'state') or not pipeline.state:
            return
        
        state = pipeline.state
        if 'sources' in state:
            for source_name, source_state in state['sources'].items():
                if 'resources' in source_state:
                    for resource_name, resource_state in source_state['resources'].items():
                        if resource_name == table_name and 'incremental' in resource_state:
                            cursor_info = resource_state['incremental']
                            logger.info(f"  Incremental State:")
                            logger.info(f"    Last cursor value: {cursor_info.get('last_value')}")
                            logger.info(f"    Cursor path: {cursor_info.get('cursor_path')}")
    
    def drop_pipeline_state(self):
        """Drop pipeline state and start fresh.
        
        DLT BEST PRACTICE #7: Provide state management capabilities.
        Use this to reset all incremental loads and start from scratch.
        """
        logger.warning("[STATE RESET] Dropping pipeline state...")
        self.pipeline.drop()
        logger.info("Pipeline state cleared. Next run will start fresh.")
    
    def checkpoint_pipeline(self):
        """Create a checkpoint of the current pipeline state.
        
        DLT BEST PRACTICE #7: Manual checkpointing for long-running jobs.
        """
        logger.info("[CHECKPOINT] Saving pipeline state...")
        self.pipeline.sync_destination()
        logger.info("Pipeline checkpoint saved.")
    
    def run_all(self, parallel: bool = False, max_workers: int = 3):
        """Execute all enabled jobs from configuration.
        
        Args:
            parallel: Enable parallel execution of jobs (default: False for safety)
            max_workers: Maximum concurrent jobs when parallel=True (default: 3)
        """
        execution_timestamp = datetime.now()
        execution_date = execution_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        partition_path = execution_timestamp.strftime("%Y/%m/%d")
        
        logger.info("="*80)
        logger.info("DLT Ingestion Framework - Production Grade (GB-Scale Optimized)")
        logger.info("="*80)
        logger.info(f"Execution Time: {execution_date}")
        logger.info(f"Partition Path: {partition_path}")
        logger.info(f"Pipeline: {self.pipeline.pipeline_name}")
        logger.info(f"Execution Mode: {'PARALLEL' if parallel else 'SEQUENTIAL'}")
        if parallel:
            logger.info(f"Max Concurrent Jobs: {max_workers}")
        
        # State version may not be available
        try:
            state_version = self.pipeline.state_version
            logger.info(f"Pipeline State Version: {state_version}")
        except:
            logger.info("Pipeline State: Ready")
            
        logger.info(f"Layout: {{table}}/{{YYYY}}/{{MM}}/{{DD}}/{{load_id}}.{{file_id}}.parquet")
        logger.info(f"Destination: az://raw-data (ADLS Gen2)")
        logger.info("="*80)
        
        try:
            # Load enabled jobs
            jobs = self.config_loader.load_jobs()
            
            if not jobs:
                logger.warning("No enabled jobs found. Exiting.")
                return
            
            logger.info(f"Executing {len(jobs)} ingestion jobs")
            logger.info("="*80)
            
            # Execute jobs (sequential or parallel)
            success_count = 0
            failed_count = 0
            
            if parallel:
                # GB-SCALE ENHANCEMENT #4: Parallel execution for multiple tables
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                logger.info(f"[PARALLEL MODE] Processing up to {max_workers} jobs concurrently")
                logger.warning("[WARNING] Ensure Databricks cluster has sufficient memory for parallel processing")
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {executor.submit(self.execute_job, job): job for job in jobs}
                    
                    for future in as_completed(futures):
                        job = futures[future]
                        try:
                            if future.result():
                                success_count += 1
                            else:
                                failed_count += 1
                        except Exception as e:
                            logger.error(f"Job {job['source_name']}.{job['table_name']} failed: {e}", exc_info=True)
                            failed_count += 1
            else:
                # Sequential execution (default - safer for large datasets)
                for job in jobs:
                    try:
                        if self.execute_job(job):
                            success_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"Unexpected error: {e}", exc_info=True)
                        failed_count += 1
            
            # Summary
            logger.info("="*80)
            logger.info("Ingestion Summary")
            logger.info("="*80)
            logger.info(f"Execution Date: {execution_date}")
            logger.info(f"Total Jobs: {len(jobs)}")
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {failed_count}")
            logger.info(f"Metadata: metadata/audit_{execution_timestamp.strftime('%Y%m%d')}.csv")
            logger.info("="*80)
        
        except Exception as e:
            logger.error(f"Fatal error in orchestrator: {e}", exc_info=True)
            raise
