"""
Core Orchestrator - Production-grade DLT pipeline execution (v2.1).

PRODUCTION FEATURES:
- Pre-flight validation of configuration and secrets
- Retry logic with exponential backoff and circuit breakers
- Metrics collection for monitoring and alerting
- Per-source log files for easy debugging
- Error-only logs for quick issue identification
- Health scoring and pipeline status reporting

This module coordinates between:
- Source modules (PostgreSQL, Oracle, MSSQL, Azure SQL, REST APIs)
- Destination modules (ADLS Gen2)
- Validation (config, secrets, data quality)
- Retry handling (exponential backoff, circuit breakers)
- Metrics collection (performance, health scoring)
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd

import dlt
from dlt.sources.credentials import ConnectionStringCredentials
from dlt.sources.sql_database import sql_table
from dlt.sources.rest_api import rest_api_source

from src.config import ConfigLoader
from src.metadata import MetadataTracker
from src.utils.log_manager import LogManager

# Import modular sources and destinations
from src.sources import (
    PostgreSQLSource, OracleSource, MSSQLSource, 
    AzureSQLSource, RESTAPISource
)
from src.destinations import ADLSGen2Destination, DatabricksDestination

# Import production modules
from src.core.validators import ConfigValidator, SecretsValidator, DataQualityValidator
from src.core.retry_handler import RetryHandler, RetryConfig, CircuitBreaker, CircuitBreakerConfig
from src.core.metrics import MetricsCollector, get_metrics_collector
from src.core.type_adapters import get_type_adapter_for_source

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """Production-grade orchestrator for DLT-based multi-source data ingestion.
    
    PRODUCTION FEATURES (v2.1):
        - Pre-flight validation (config + secrets)
        - Retry logic with exponential backoff
        - Circuit breakers for failing sources
        - Metrics collection and health scoring
        - Per-source log files for debugging
        - Error-only logs for quick issue identification
    
    Features:
        - Multi-source support (PostgreSQL, Oracle, MSSQL, Azure SQL, REST APIs)
        - Full and incremental loads with automatic watermark management
        - Date-partitioned Parquet output to ADLS Gen2
        - Schema evolution monitoring
        - Production-grade metrics extraction
        - GB-scale data handling with dynamic chunking
        - Parallel table processing support
    
    DLT Best Practices:
        - Single pipeline instance reused across all jobs
        - Schema contracts for controlled evolution
        - Primary key support for proper merge operations
        - Pipeline state management and checkpointing
        - Memory-efficient processing with configurable chunk sizes
    """
    
    def __init__(self, config_dir: Optional[Path] = None, validate_on_init: bool = True):
        """Initialize orchestrator with modular sources and destinations.
        
        Args:
            config_dir: Optional custom config directory path
            validate_on_init: Run pre-flight validation (default: True)
        
        Creates:
        - Single DLT pipeline (reused for all jobs)
        - Source instances for each database type
        - Destination instance for ADLS Gen2
        - Log manager for per-source logging
        - Validators for config and secrets
        - Metrics collector for monitoring
        - Retry handlers with circuit breakers
        """
        self.config_loader = ConfigLoader(config_dir=config_dir) if config_dir else ConfigLoader()
        self.metadata_tracker = MetadataTracker()
        self.secrets = self.config_loader.load_secrets()
        
        # Initialize log manager (per-source logging)
        self.log_manager = LogManager()
        
        # Initialize validators
        self.config_validator = ConfigValidator()
        self.secrets_validator = SecretsValidator()
        self.data_quality_validator = DataQualityValidator()
        
        # Initialize metrics collector
        self.metrics = get_metrics_collector("dlt_ingestion")
        
        # Initialize circuit breakers per source type
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Initialize source modules
        self.sources = {
            'postgresql': PostgreSQLSource('postgresql', self.secrets),
            'oracle': OracleSource('oracle', self.secrets),
            'mssql': MSSQLSource('mssql', self.secrets),
            'azure_sql': AzureSQLSource('azure_sql', self.secrets),
            'api': RESTAPISource('api', self.secrets)
        }
        
        # Initialize destination module (dynamically based on config)
        self.destination = self._initialize_destination()
        
        # Validate secrets for destination
        if validate_on_init:
            self._validate_destination_secrets()
        
        # Get DLT destination config from destination module
        dest_config = self.destination.get_dlt_destination_config()
        
        # DLT BEST PRACTICE #1: Create pipeline ONCE and reuse for all jobs
        self.pipeline = dlt.pipeline(
            pipeline_name="multi_source_ingestion",
            destination=dest_config['destination'],
            dataset_name="raw_data"
        )
        
        logger.info("[ORCHESTRATOR v2.1] Production-grade initialization")
        logger.info(f"  DLT Pipeline: {self.pipeline.pipeline_name}")
        logger.info(f"  Destination: {self.destination.get_destination_type()}")
        logger.info(f"  DLT Destination Type: {self.pipeline.destination}")
        logger.info(f"  Sources: {list(self.sources.keys())}")
        logger.info(f"  Validators: config, secrets, data_quality")
        logger.info(f"  Retry Logic: exponential backoff with circuit breakers")
        logger.info(f"  Log Directory: {self.log_manager.base_log_dir}")
        
        # Note: Destination connectivity already validated in _initialize_destination()
        logger.info("[INITIALIZATION] Complete - orchestrator ready")
    
    def _initialize_destination(self):
        """Initialize destination module based on configuration.
        
        Checks secrets for destination type and creates appropriate destination instance.
        Defaults to ADLS Gen2 for backward compatibility.
        
        Returns:
            Destination instance (ADLSGen2Destination or DatabricksDestination)
        
        Example secrets.toml:
            [destination]
            type = "databricks"  # or "filesystem" for ADLS Gen2
        """
        # Get destination type from secrets (default to filesystem/ADLS Gen2)
        dest_type = self.secrets.get('destination', {}).get('type', 'filesystem')
        
        if dest_type == 'databricks':
            logger.info("[ORCHESTRATOR] Initializing Databricks Unity Catalog destination")
            destination = DatabricksDestination('databricks', self.secrets)
            
            # Validate both Databricks and staging connectivity
            if destination.validate_connection():
                logger.info("[DATABRICKS] Connection validated")
            else:
                logger.warning("[DATABRICKS] Connection validation failed")
            
            if destination.validate_staging():
                logger.info("[DATABRICKS] Staging validated")
            else:
                logger.warning("[DATABRICKS] Staging validation failed")
                
            return destination
            
        else:
            logger.info("[ORCHESTRATOR] Initializing ADLS Gen2 filesystem destination")
            return ADLSGen2Destination('adls_gen2', self.secrets)
    
    def _validate_destination_secrets(self):
        """Validate destination secrets before pipeline creation."""
        results = self.secrets_validator.validate_destination_secrets(self.secrets)
        for result in results:
            if not result.passed:
                logger.error(f"[VALIDATION] {result.message}")
                raise ValueError(f"Destination validation failed: {result.message}")
    
    def _get_circuit_breaker(self, source_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a source."""
        if source_name not in self._circuit_breakers:
            self._circuit_breakers[source_name] = CircuitBreaker(
                name=source_name,
                config=CircuitBreakerConfig(
                    failure_threshold=3,
                    success_threshold=1,
                    timeout=60.0
                )
            )
        return self._circuit_breakers[source_name]
    
    def _get_retry_handler(self, source_name: str, source_type: str) -> RetryHandler:
        """Get retry handler configured for source type."""
        circuit_breaker = self._get_circuit_breaker(source_name)
        
        if source_type == 'api':
            config = RetryConfig(
                max_retries=5,
                initial_delay=1.0,
                max_delay=60.0,
                exponential_base=2.0
            )
        else:
            config = RetryConfig(
                max_retries=3,
                initial_delay=2.0,
                max_delay=30.0,
                exponential_base=2.0
            )
        
        return RetryHandler(config, circuit_breaker)
    
    def execute_job(self, job: Dict) -> bool:
        """Execute a single ingestion job with validation, retry, and metrics.
        
        Args:
            job: Job configuration dictionary from Excel
        
        Returns:
            True if job succeeded, False if failed
        """
        job_name = f"{job['source_name']}.{job['table_name']}"
        source_type = job['source_type'].lower()
        source_name = job['source_name']
        
        # Set up per-source logger
        source_logger = self.log_manager.setup_source_logger(source_name, source_type)
        
        source_logger.info("="*80)
        source_logger.info(f"Starting job: {job_name}")
        source_logger.info(f"  Source Type: {source_type}")
        source_logger.info(f"  Load Type: {job['load_type']}")
        source_logger.info("="*80)
        
        # Pre-flight validation
        validation_results = self.config_validator.validate_job(job)
        for result in validation_results:
            if not result.passed:
                source_logger.error(f"[VALIDATION FAILED] {result.message}")
                if result.severity.value in ['error', 'critical']:
                    self.metadata_tracker.record_job(
                        job_name=job_name,
                        status="VALIDATION_FAILED",
                        rows=0,
                        duration=0,
                        error_message=result.message
                    )
                    return False
        
        # Validate secrets for this source
        secret_results = self.secrets_validator.validate_source_secrets(
            self.secrets, source_name, source_type
        )
        for result in secret_results:
            if not result.passed:
                source_logger.error(f"[SECRETS VALIDATION FAILED] {result.message}")
                self.metadata_tracker.record_job(
                    job_name=job_name,
                    status="SECRETS_INVALID",
                    rows=0,
                    duration=0,
                    error_message=result.message
                )
                return False
        
        # Start metrics tracking
        self.metrics.start_job(job_name, source_type, "adls_gen2")
        
        start_time = datetime.now()
        retry_handler = self._get_retry_handler(source_name, source_type)
        
        try:
            # Get appropriate source module
            if source_type not in self.sources:
                raise ValueError(f"Unsupported source type: {source_type}")
            
            source = self.sources[source_type]
            
            # Execute with retry logic
            if source_type == 'api':
                success, rows_processed = retry_handler.execute_with_retry(
                    self._execute_api_job, job, source, source_logger
                )
            else:
                success, rows_processed = retry_handler.execute_with_retry(
                    self._execute_database_job, job, source, source_logger
                )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            if success:
                source_logger.info(f"[SUCCESS] Job completed in {duration:.2f}s")
                source_logger.info(f"  Rows processed: {rows_processed:,}")
                
                # Data quality validation
                dq_result = self.data_quality_validator.validate_not_empty(
                    rows_processed, job['table_name']
                )
                if not dq_result.passed:
                    source_logger.warning(f"[DATA QUALITY] {dq_result.message}")
                
                # Record success
                self.metadata_tracker.record_job(
                    job_name=job_name,
                    status="SUCCESS",
                    rows=rows_processed,
                    duration=duration
                )
                
                # Update metrics
                self.metrics.complete_job(job_name, "SUCCESS", rows_processed)
                
                return True
            else:
                source_logger.error(f"[FAILED] Job failed after {duration:.2f}s")
                
                self.metadata_tracker.record_job(
                    job_name=job_name,
                    status="FAILED",
                    rows=0,
                    duration=duration,
                    error_message="Job execution failed"
                )
                
                self.metrics.complete_job(job_name, "FAILED", 0, "Job execution failed")
                
                return False
                
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = f"{type(e).__name__}: {str(e)}"
            source_logger.error(f"[ERROR] Job failed with exception: {e}", exc_info=True)
            
            self.metadata_tracker.record_job(
                job_name=job_name,
                status="ERROR",
                rows=0,
                duration=duration,
                error_message=error_msg
            )
            
            self.metrics.complete_job(job_name, "ERROR", 0, error_msg)
            
            return False
    
    def _execute_database_job(self, job: Dict, source, source_logger) -> tuple:
        """Execute database ingestion job.
        
        Args:
            job: Job configuration
            source: Source module instance
            source_logger: Per-source logger
        
        Returns:
            Tuple of (success: bool, rows_processed: int)
        """
        source_name = job['source_name']
        table_name = job['table_name']
        
        try:
            # Build connection string using source module
            conn_str = source.build_connection_string(source_name)
            source_logger.info(f"[CONNECTION] Built connection string for {source_name}")
            
            # Pre-flight table size estimation (for FULL loads)
            estimated_rows = None
            recommended_chunk = 100000
            
            if job['load_type'].upper() == "FULL":
                source_logger.info("[PRE-FLIGHT] Estimating table size...")
                estimated_rows, recommended_chunk = source.estimate_table_size(
                    conn_str, 
                    table_name, 
                    job.get('schema_name')
                )
            
            # Dynamic chunk_size (Excel config or auto-optimized)
            chunk_size = self._determine_chunk_size(
                job, estimated_rows, recommended_chunk, source_logger
            )
            
            # Build incremental object if needed
            incremental_obj = self._build_incremental(job, source_logger)
            
            # Build primary key if specified
            primary_key = self._build_primary_key(job, source_logger)
            
            # Get destination type (for type adapter selection)
            destination_type = self.secrets.get('destination', {}).get('type', 'filesystem')
            
            # Get type adapter callback for source → destination compatibility
            type_adapter = get_type_adapter_for_source(
                source_type=job['source_type'],
                destination=destination_type
            )
            
            if type_adapter:
                source_logger.info(f"[TYPE ADAPTER] Enabled for {job['source_type']} → {destination_type}")
            
            # Create DLT resource
            resource_kwargs = {
                'credentials': ConnectionStringCredentials(conn_str),
                'table': table_name,
                'incremental': incremental_obj,
                'backend': "pyarrow",
                'chunk_size': chunk_size,
                'detect_precision_hints': True,
                'defer_table_reflect': True,
                'type_adapter_callback': type_adapter  # KEY ADDITION: Type compatibility
            }
            
            # Add schema if source supports it
            if source.supports_schema() and job.get('schema_name'):
                resource_kwargs['schema'] = job['schema_name']
                source_logger.info(f"[SCHEMA] Using schema: {job['schema_name']}")
            
            # Add primary key if specified
            if primary_key:
                resource_kwargs['primary_key'] = primary_key
            
            resource = sql_table(**resource_kwargs)
            
            # Determine write disposition
            write_disposition = "replace" if job['load_type'].upper() == "FULL" else "merge"
            
            # Filesystem doesn't support merge - fallback to replace
            if write_disposition == "merge":
                source_logger.warning("[WARNING] Filesystem doesn't support merge - using replace")
                write_disposition = "replace"
            
            # Execute DLT pipeline
            source_logger.info(f"[DLT] Running pipeline with {write_disposition} disposition...")
            load_info = self.pipeline.run(
                resource, 
                write_disposition=write_disposition, 
                loader_file_format="parquet"
            )
            
            # Extract row count
            rows_processed = self._extract_row_count(load_info, table_name, source_logger)
            
            # Check for schema evolution
            self._check_schema_evolution(table_name, source_logger)
            
            return True, rows_processed
            
        except Exception as e:
            source_logger.error(f"[DATABASE JOB FAILED] {e}", exc_info=True)
            return False, 0
    
    def _execute_api_job(self, job: Dict, source: RESTAPISource, source_logger) -> tuple:
        """Execute REST API ingestion job.
        
        Args:
            job: Job configuration
            source: REST API source module
            source_logger: Per-source logger
        
        Returns:
            Tuple of (success: bool, rows_processed: int)
        """
        source_name = job['source_name']
        table_name = job['table_name']
        endpoint_path = job.get('api_endpoint', table_name)
        
        try:
            # Build REST API configuration using source module (v2.0 with pagination)
            source_logger.info(f"[REST API] Configuring endpoint: {endpoint_path}")
            
            # Get API configuration
            api_config = source.get_api_config(source_name)
            
            # Log configuration details
            source_logger.info(f"[REST API] Base URL: {api_config.get('base_url')}")
            pagination_type = job.get('pagination_type', api_config.get('pagination_type', 'single_page'))
            source_logger.info(f"[REST API] Pagination: {pagination_type}")
            
            # Build DLT REST config
            rest_config = source.build_rest_config(job)
            
            # Create REST API source (DLT native - handles pagination, retry, state)
            from dlt.sources.rest_api import rest_api_source
            api_source = rest_api_source(rest_config)
            resource = api_source.resources[table_name]
            
            # Execute DLT pipeline
            source_logger.info("[DLT] Running API pipeline...")
            load_info = self.pipeline.run(
                resource, 
                write_disposition="replace",  # APIs typically use full refresh
                loader_file_format="parquet"
            )
            
            # Extract row count
            rows_processed = self._extract_row_count(load_info, table_name, source_logger)
            
            return True, rows_processed
            
        except Exception as e:
            source_logger.error(f"[API JOB FAILED] {e}", exc_info=True)
            return False, 0
    
    def _determine_chunk_size(self, job: Dict, estimated_rows: Optional[int], 
                             recommended_chunk: int, source_logger) -> int:
        """Determine optimal chunk size (Excel config or auto-optimized).
        
        Args:
            job: Job configuration
            estimated_rows: Estimated table rows (if available)
            recommended_chunk: Auto-recommended chunk size
            source_logger: Logger instance
        
        Returns:
            Final chunk_size to use
        """
        chunk_size = 100000  # Default
        
        # Check Excel config first
        if job.get('chunk_size') and not pd.isna(job.get('chunk_size')):
            try:
                chunk_size = int(job['chunk_size'])
                source_logger.info(f"[CHUNK SIZE] Using configured value: {chunk_size:,} rows")
            except (ValueError, TypeError):
                source_logger.warning(f"[INVALID CHUNK SIZE] Defaulting to {chunk_size:,}")
        
        # Auto-optimize for large tables
        elif estimated_rows and estimated_rows > 1000000:
            chunk_size = recommended_chunk
            source_logger.info(f"[AUTO-OPTIMIZED] Chunk size: {chunk_size:,} rows")
        
        # Memory warning for large chunks
        if chunk_size > 500000:
            source_logger.warning(f"[MEMORY WARNING] Large chunk ({chunk_size:,} rows)")
            source_logger.warning("  Ensure Databricks cluster has 16GB+ memory")
        
        return chunk_size
    
    def _build_incremental(self, job: Dict, source_logger) -> Optional:
        """Build DLT incremental object if needed.
        
        Args:
            job: Job configuration
            source_logger: Logger instance
        
        Returns:
            DLT incremental object or None
        """
        if job['load_type'].upper() == "INCREMENTAL" and job.get('watermark_column'):
            incremental_obj = dlt.sources.incremental(
                cursor_path=job['watermark_column'],
                initial_value=job.get('last_watermark')
            )
            source_logger.info(f"[INCREMENTAL] Watermark column: {job['watermark_column']}")
            source_logger.info(f"[INCREMENTAL] Initial value: {job.get('last_watermark')}")
            return incremental_obj
        
        return None
    
    def _build_primary_key(self, job: Dict, source_logger) -> Optional:
        """Build primary key configuration.
        
        Args:
            job: Job configuration
            source_logger: Logger instance
        
        Returns:
            Primary key(s) or None
        """
        if job.get('primary_key') and not pd.isna(job.get('primary_key')):
            keys = [k.strip() for k in str(job['primary_key']).split(',')]
            primary_key = keys[0] if len(keys) == 1 else keys
            source_logger.info(f"[PRIMARY KEY] {primary_key}")
            return primary_key
        
        return None
    
    def _extract_row_count(self, load_info, table_name: str, source_logger) -> int:
        """Extract row count from DLT pipeline trace.
        
        Args:
            load_info: DLT load info object
            table_name: Name of the table
            source_logger: Logger instance
        
        Returns:
            Number of rows processed
        """
        rows_processed = 0
        
        try:
            if hasattr(self.pipeline, 'last_trace') and self.pipeline.last_trace:
                if hasattr(self.pipeline.last_trace, 'last_normalize_info'):
                    row_counts = self.pipeline.last_trace.last_normalize_info.row_counts
                    if table_name in row_counts:
                        count_value = row_counts[table_name]
                        rows_processed = count_value if isinstance(count_value, int) else count_value.get('row_count', 0)
                        source_logger.info(f"[METRICS] Rows processed: {rows_processed:,}")
        except Exception as e:
            source_logger.warning(f"[METRICS] Could not extract row count: {e}")
        
        return rows_processed
    
    def _check_schema_evolution(self, table_name: str, source_logger):
        """Check for schema evolution.
        
        Args:
            table_name: Name of the table
            source_logger: Logger instance
        """
        try:
            if hasattr(self.pipeline, 'default_schema'):
                schema = self.pipeline.default_schema
                schema_version = schema.version if hasattr(schema, 'version') else 1
                if schema_version > 1:
                    source_logger.warning(f"[SCHEMA CHANGE] Version {schema_version} detected")
                    source_logger.warning("  Check _dlt_version/ folder in ADLS")
        except Exception as e:
            source_logger.debug(f"[SCHEMA CHECK] Could not check evolution: {e}")
    
    def run_all(self, parallel: bool = False, max_workers: int = 3,
                skip_validation: bool = False):
        """Execute all enabled jobs with full production features.
        
        Args:
            parallel: Enable parallel execution (default: False for safety)
            max_workers: Maximum concurrent jobs when parallel=True
            skip_validation: Skip pre-flight validation (not recommended)
        """
        execution_timestamp = datetime.now()
        execution_date = execution_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info("="*80)
        logger.info("DLT Ingestion Framework v2.1 - Production Grade")
        logger.info("="*80)
        logger.info(f"Execution Time: {execution_date}")
        logger.info(f"Pipeline: {self.pipeline.pipeline_name}")
        logger.info(f"Execution Mode: {'PARALLEL' if parallel else 'SEQUENTIAL'}")
        logger.info(f"Pre-flight Validation: {'DISABLED' if skip_validation else 'ENABLED'}")
        logger.info(f"Retry Logic: exponential backoff with circuit breakers")
        logger.info(f"Log Directory: {self.log_manager.base_log_dir}")
        if parallel:
            logger.info(f"Max Concurrent Jobs: {max_workers}")
        logger.info("="*80)
        
        try:
            # Load enabled jobs (skip validation for backup config compatibility)
            jobs = self.config_loader.load_jobs(validate=False)
            
            if not jobs:
                logger.warning("No enabled jobs found. Exiting.")
                return
            
            logger.info(f"Loaded {len(jobs)} enabled jobs")
            
            # Pre-flight validation of all jobs
            if not skip_validation:
                logger.info("[PRE-FLIGHT] Validating all job configurations...")
                all_valid, validation_results = self.config_validator.validate_all_jobs(jobs)
                
                error_count = sum(1 for r in validation_results if not r.passed)
                if error_count > 0:
                    logger.warning(f"[PRE-FLIGHT] {error_count} validation issues found")
                    for result in validation_results:
                        if not result.passed:
                            logger.warning(f"  - {result.message}")
                
                if not all_valid:
                    logger.error("[PRE-FLIGHT] Critical validation errors - aborting")
                    return
                
                logger.info("[PRE-FLIGHT] All validations passed")
            
            logger.info("="*80)
            logger.info(f"Executing {len(jobs)} ingestion jobs")
            logger.info("="*80)
            
            # Execute jobs
            success_count = 0
            failed_count = 0
            
            if parallel:
                # Parallel execution
                from concurrent.futures import ThreadPoolExecutor, as_completed
                
                logger.info(f"[PARALLEL MODE] Processing up to {max_workers} jobs concurrently")
                logger.warning("[WARNING] Ensure Databricks cluster has sufficient memory")
                
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
                            logger.error(f"Job {job['source_name']}.{job['table_name']} failed: {e}")
                            failed_count += 1
            else:
                # Sequential execution (default)
                for job in jobs:
                    try:
                        if self.execute_job(job):
                            success_count += 1
                        else:
                            failed_count += 1
                    except Exception as e:
                        logger.error(f"Unexpected error: {e}", exc_info=True)
                        failed_count += 1
            
            # Get metrics summary
            metrics_summary = self.metrics.get_summary()
            health_score = self.metrics.get_health_score()
            
            # Summary with health score
            logger.info("="*80)
            logger.info("Ingestion Summary")
            logger.info("="*80)
            logger.info(f"Execution Date: {execution_date}")
            logger.info(f"Total Jobs: {len(jobs)}")
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {failed_count}")
            logger.info(f"Success Rate: {success_count/len(jobs)*100:.1f}%")
            logger.info(f"Health Score: {health_score:.1f}/100")
            logger.info(f"Total Rows: {metrics_summary.get('total_rows_processed', 0):,}")
            logger.info(f"Total Duration: {metrics_summary.get('total_duration_seconds', 0):.2f}s")
            logger.info(f"Avg Throughput: {metrics_summary.get('average_rows_per_second', 0):.0f} rows/sec")
            logger.info(f"Metadata: metadata/audit_{execution_timestamp.strftime('%Y%m%d')}.csv")
            logger.info(f"Logs: {self.log_manager.base_log_dir}")
            logger.info(f"Errors: {self.log_manager.error_log_dir}")
            logger.info("="*80)
            
            # Export metrics to JSON
            metrics_file = Path("metadata") / f"metrics_{execution_timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            self.metrics.export_json(str(metrics_file))
        
        except Exception as e:
            logger.error(f"Fatal error in orchestrator: {e}", exc_info=True)
            raise
        finally:
            # Cleanup log handlers
            self.log_manager.close_all_handlers()
    
    def build_connection_string(self, source_type: str, source_name: str) -> str:
        """Build database connection string for given source.
        
        Public method exposed for testing and utilities.
        
        Args:
            source_type: Type of source (postgresql, oracle, mssql, azure_sql)
            source_name: Name of source in secrets configuration
        
        Returns:
            Connection string for the source
        
        Raises:
            ValueError: If source type is not supported or not a database
        """
        if source_type not in self.sources:
            raise ValueError(f"Unsupported source type: {source_type}")
        
        if source_type == 'api':
            raise ValueError("API sources do not have connection strings")
        
        source = self.sources[source_type]
        return source.build_connection_string(source_name)
