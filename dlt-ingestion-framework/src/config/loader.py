"""
Configuration Loader - Loads Excel job definitions and secrets (TOML or Key Vault).
Includes Pydantic model validation for type-safe configuration.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
import toml
from pydantic import ValidationError

from src.auth.keyvault_manager import KeyVaultManager
from src.models.job_config import JobConfig, JobConfigList

logger = logging.getLogger(__name__)

# Check if Key Vault libraries are available
try:
    from azure.identity import DefaultAzureCredential
    KEYVAULT_AVAILABLE = True
except ImportError:
    KEYVAULT_AVAILABLE = False


class ConfigLoader:
    """Loads job configuration from Excel and credentials from secrets.toml or Azure Key Vault.
    
    Supports two credential sources:
        1. Local development: .dlt/secrets.toml (DLT native location)
        2. Production: Azure Key Vault (auto-detected via AZURE_KEY_VAULT_URL env var)
    
    The framework automatically falls back to secrets.toml if Key Vault is unavailable.
    """
    
    def __init__(self, config_dir: Path = None, use_keyvault: bool = None):
        """Initialize configuration loader.
        
        Args:
            config_dir: Directory containing ingestion_config.xlsx (default: ./config)
            use_keyvault: Force Key Vault usage. If None, auto-detects from env var.
        """
        # Set paths
        root_dir = Path(__file__).parent.parent.parent
        self.config_dir = config_dir or root_dir / "config"
        self.excel_path = self.config_dir / "ingestion_config.xlsx"
        self.secrets_path = root_dir / ".dlt" / "secrets.toml"
        
        # Auto-detect Key Vault if AZURE_KEY_VAULT_URL environment variable is set
        if use_keyvault is None:
            use_keyvault = bool(os.getenv('AZURE_KEY_VAULT_URL'))
        
        self.use_keyvault = use_keyvault and KEYVAULT_AVAILABLE
        self.keyvault = None
        
        # Initialize Key Vault if requested
        if self.use_keyvault:
            try:
                self.keyvault = KeyVaultManager()
                logger.info("[KEY VAULT] Credential Source: Azure Key Vault")
            except Exception as e:
                logger.warning(f"[WARNING] Key Vault init failed: {e}")
                logger.warning("  Falling back to secrets.toml")
                self.use_keyvault = False
        
        if not self.use_keyvault:
            # Check if running in Databricks or using environment variables
            if self._is_databricks():
                logger.info("[DATABRICKS] Credential Source: Databricks Secrets")
            elif os.getenv('DLT_POSTGRESQL_HOST') or os.getenv('DLT_ORACLE_HOST'):
                logger.info("[ENV] Credential Source: Environment Variables")
            else:
                logger.info("[LOCAL] Credential Source: .dlt/secrets.toml")
    
    def load_jobs(self, validate: bool = True) -> List[Dict]:
        """Load enabled jobs from Excel configuration with optional Pydantic validation.
        
        Args:
            validate: If True, validate jobs using Pydantic models (default: True)
        
        Returns:
            List of job dictionaries with configuration details
        
        Raises:
            FileNotFoundError: If ingestion_config.xlsx not found
            ValueError: If Excel sheet structure is invalid or validation fails
        """
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.excel_path}")
        
        logger.info(f"Loading configuration from: {self.excel_path}")
        
        try:
            df = pd.read_excel(self.excel_path, sheet_name="SourceConfig")
        except Exception as e:
            raise ValueError(f"Failed to load Excel config: {e}")
        
        # Replace NaN values with None for proper Pydantic validation
        df = df.where(pd.notnull(df), None)
        
        # Convert to records
        all_jobs = df.to_dict('records')
        
        # Post-process: Ensure all nan/NaN values are truly None
        import math
        import json
        for job in all_jobs:
            for key, value in list(job.items()):
                # Handle pandas NaN, numpy nan, and float nan
                if value is None:
                    continue
                try:
                    if isinstance(value, float) and math.isnan(value):
                        job[key] = None
                except (TypeError, ValueError):
                    pass  # Not a float or can't check for nan
                
                # Handle params field - convert JSON string to dict
                if key == 'params' and isinstance(value, str):
                    try:
                        job[key] = json.loads(value)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in params field for job {job.get('table_name', 'unknown')}: {value}")
                        job[key] = None
        
        # Validate using Pydantic if requested
        if validate:
            validated_jobs, validation_errors = self._validate_jobs(all_jobs)
            
            if validation_errors:
                logger.error(f"[VALIDATION] Found {len(validation_errors)} invalid jobs:")
                for row, error in validation_errors:
                    logger.error(f"  Row {row}: {error}")
                raise ValueError(f"Configuration validation failed: {len(validation_errors)} invalid jobs")
            
            # Filter enabled jobs from validated jobs
            enabled_jobs = [job.to_dict() for job in validated_jobs if job.is_enabled()]
            logger.info(f"[VALIDATION] ✓ All jobs validated successfully")
            logger.info(f"Found {len(enabled_jobs)} enabled jobs out of {len(df)} total")
            return enabled_jobs
        else:
            # Original behavior: no validation
            enabled = df[df['enabled'].str.upper() == 'Y']
            logger.info(f"Found {len(enabled)} enabled jobs out of {len(df)} total (validation skipped)")
            return enabled.to_dict('records')
    
    def load_secrets(self) -> Dict:
        """Load secrets from TOML file.
        
        Returns:
            Dictionary with all secrets from .dlt/secrets.toml
        """
        if not self.secrets_path.exists():
            logger.warning(f"[SECRETS] File not found: {self.secrets_path} - returning empty dict")
            return {}
        
        logger.debug(f"Loading secrets from: {self.secrets_path}")
        return toml.load(self.secrets_path)
    
    def get_source_config(self, source_name: str) -> Optional[Dict]:
        """Get source configuration from multiple sources with priority fallback.
        
        Priority:
            1. Databricks Secrets (if running in Databricks)
            2. Azure Key Vault (if enabled and available)
            3. Environment variables (DLT_<SOURCE>_<KEY> format)
            4. Fallback to .dlt/secrets.toml
        
        Args:
            source_name: Source identifier (e.g., 'postgresql', 'oracle', 'api.coingecko')
        
        Returns:
            Dictionary with source configuration, or None if not found
        """
        # Try Databricks Secrets first (if in Databricks environment)
        db_config = self._load_from_databricks(source_name)
        if db_config:
            logger.debug(f"Retrieved config from Databricks Secrets: {source_name}")
            return db_config
        
        # Try Key Vault if enabled
        if self.use_keyvault and self.keyvault:
            try:
                config = self.keyvault.get_source_config(source_name)
                if config:
                    logger.debug(f"Retrieved config from Key Vault: {source_name}")
                    return config
            except Exception as e:
                logger.warning(f"Key Vault lookup failed for {source_name}: {e}")
                logger.warning("Falling back to environment variables or secrets.toml")
        
        # Try environment variables (format: DLT_<SOURCE>_<KEY>)
        env_config = self._load_from_env(source_name)
        if env_config:
            logger.debug(f"Retrieved config from environment variables: {source_name}")
            return env_config
        
        # Fallback to secrets.toml
        try:
            secrets = self.load_secrets()
            if 'sources' in secrets and source_name in secrets['sources']:
                logger.debug(f"Retrieved config from secrets.toml: {source_name}")
                return secrets['sources'][source_name]
        except Exception as e:
            logger.error(f"Failed to load secrets from TOML: {e}")
        
        raise KeyError(f"Source configuration '{source_name}' not found in any secret source")
    
    def _is_databricks(self) -> bool:
        """Check if running in Databricks environment."""
        try:
            from pyspark.dbutils import DBUtils
            from pyspark.sql import SparkSession
            spark = SparkSession.builder.getOrCreate()
            dbutils = DBUtils(spark)
            return True
        except:
            return False
    
    def get_destination_config(self, dest_name: str) -> Dict:
        """Get destination configuration from secrets.
        
        Args:
            dest_name: Destination type name (e.g., 'filesystem', 'databricks')
        
        Returns:
            Dictionary with destination configuration
        
        Raises:
            KeyError: If destination not found in secrets
        """
        secrets = self.load_secrets()
        
        if 'destination' not in secrets:
            raise KeyError(f"No destination configuration found in secrets")
        
        if dest_name not in secrets['destination']:
            raise KeyError(f"Destination '{dest_name}' not found in secrets")
        
        dest_config = secrets['destination'][dest_name].copy()
        
        # Flatten credentials if present
        if 'credentials' in dest_config:
            for key, value in dest_config['credentials'].items():
                if key not in dest_config:
                    dest_config[key] = value
        
        return dest_config
    
    def _load_from_databricks(self, source_name: str) -> Optional[Dict]:
        """Load source configuration from Databricks Secrets.
        
        Format: {source-name}-{key} in scope 'dlt-framework'
        Example: postgresql-host, postgresql-password
        
        Args:
            source_name: Source identifier (e.g., 'postgresql', 'oracle')
        
        Returns:
            Dictionary with configuration, or None if not in Databricks
        """
        try:
            # Check if running in Databricks
            from pyspark.dbutils import DBUtils
            from pyspark.sql import SparkSession
            
            spark = SparkSession.builder.getOrCreate()
            dbutils = DBUtils(spark)
            
            config = {}
            scope = "dlt-framework"
            
            # Common keys to try
            keys = ['host', 'port', 'database', 'username', 'password', 
                    'sid', 'schema', 'base-url', 'api-key', 'bucket-url',
                    'storage-account', 'storage-key']
            
            for key in keys:
                secret_name = f"{source_name}-{key}"
                try:
                    value = dbutils.secrets.get(scope=scope, key=secret_name)
                    if value:
                        # Convert hyphenated keys to underscored for compatibility
                        config[key.replace('-', '_')] = value
                except:
                    continue
            
            return config if config else None
        except:
            # Not running in Databricks
            return None
    
    def get_destination_config(self, dest_name: str) -> Optional[Dict]:
        """Get destination configuration from secrets.
        
        Args:
            dest_name: Destination type name (e.g., 'filesystem', 'databricks')
        
        Returns:
            Dictionary with destination configuration
        
        Raises:
            KeyError: If destination not found in secrets
        """
        secrets = self.load_secrets()
        
        if 'destination' not in secrets:
            raise KeyError(f"No destination configuration found in secrets")
        
        if dest_name not in secrets['destination']:
            raise KeyError(f"Destination '{dest_name}' not found in secrets")
        
        dest_config = secrets['destination'][dest_name]
        
        # Flatten credentials if present
        if 'credentials' in dest_config:
            # Keep both nested and flattened format
            for key, value in dest_config['credentials'].items():
                if key not in dest_config:
                    dest_config[key] = value
        
        return dest_config
    
    def _load_from_env(self, source_name: str) -> Optional[Dict]:
        """Load source configuration from environment variables.
        
        Environment variable format: DLT_<SOURCE>_<KEY>
        Example: DLT_POSTGRESQL_HOST, DLT_POSTGRESQL_PASSWORD
        
        Args:
            source_name: Source identifier (e.g., 'postgresql', 'oracle')
        
        Returns:
            Dictionary with configuration, or None if not found
        """
        # Normalize source name to uppercase for env vars
        source_prefix = f"DLT_{source_name.upper().replace('-', '_')}_"
        
        # Check if any env vars exist for this source
        config = {}
        
        # Common database keys
        keys = ['HOST', 'PORT', 'DATABASE', 'USERNAME', 'PASSWORD', 'SID', 
                'SCHEMA', 'BASE_URL', 'API_KEY', 'BUCKET_URL', 'STORAGE_ACCOUNT', 
                'STORAGE_KEY']
        
        for key in keys:
            env_var = f"{source_prefix}{key}"
            value = os.getenv(env_var)
            if value:
                config[key.lower()] = value
        
        return config if config else None
    
    def _validate_jobs(self, jobs: List[Dict]) -> tuple[List[JobConfig], List[tuple[int, str]]]:
        """Validate jobs using Pydantic models.
        
        Args:
            jobs: List of job dictionaries from Excel
        
        Returns:
            Tuple of (validated_jobs, errors) where errors is list of (row_index, error_message)
        """
        validated_jobs = []
        errors = []
        
        for idx, job_dict in enumerate(jobs):
            try:
                # Create Pydantic model (validates automatically)
                job = JobConfig(**job_dict)
                validated_jobs.append(job)
            except ValidationError as e:
                # Extract validation error messages
                error_messages = []
                for error in e.errors():
                    field = '.'.join(str(loc) for loc in error['loc'])
                    message = error['msg']
                    error_messages.append(f"{field}: {message}")
                errors.append((idx + 2, '; '.join(error_messages)))  # +2 for Excel row (header + 0-index)
            except Exception as e:
                errors.append((idx + 2, str(e)))
        
        return validated_jobs, errors
