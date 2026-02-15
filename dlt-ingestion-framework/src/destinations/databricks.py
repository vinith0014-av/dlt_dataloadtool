"""
Databricks Unity Catalog Destination.

Supports:
- Unity Catalog (catalog.schema.table)
- External ADLS staging for cross-tenant deployment
- Delta Lake format with ACID transactions
- Automatic schema evolution
- Managed and external tables

Architecture:
    Source → dlt → ADLS (staging) → COPY INTO → Databricks Delta Tables
"""
import logging
from typing import Dict, Any, Optional
from .base import BaseDestination

logger = logging.getLogger(__name__)


class DatabricksDestination(BaseDestination):
    """
    Databricks Unity Catalog destination using filesystem staging.
    
    This destination uses a two-stage approach:
    1. Stage data to ADLS Gen2 in Parquet format
    2. Use Databricks COPY INTO to load into Delta Lake tables
    
    Benefits:
    - Cross-tenant deployment support (ADLS in different tenant)
    - Efficient bulk loading with COPY INTO
    - Automatic schema evolution
    - Delta Lake features (ACID, time travel, Z-ordering)
    """
    
    def get_destination_type(self) -> str:
        """Return Databricks destination type identifier."""
        return "databricks"
    
    def get_dlt_destination_config(self) -> Dict[str, Any]:
        """
        Get DLT destination configuration for Databricks with filesystem staging.
        
        Returns:
            Dictionary with 'destination' and 'staging' configuration
        
        Raises:
            KeyError: If Databricks or staging credentials not found
            ValueError: If required configuration fields are missing
        
        Example config in secrets.toml:
            [destination.databricks]
            server_hostname = "adb-xxxx.azuredatabricks.net"
            http_path = "/sql/1.0/warehouses/xxxx"
            catalog = "main"
            schema = "raw"
            
            [destination.databricks.credentials]
            server_hostname = "adb-xxxx.azuredatabricks.net"
            http_path = "/sql/1.0/warehouses/xxxx"
            access_token = "dapi..."
            
            # Staging configuration
            [destination.filesystem]
            bucket_url = "az://staging@dltstagingaccount.dfs.core.windows.net"
            
            [destination.filesystem.credentials]
            azure_storage_account_name = "dltstagingaccount"
            azure_storage_sas_token = "?sv=2024-11-04&ss=..."
        """
        if 'destination' not in self.secrets:
            raise KeyError("Destination configuration not found in secrets")
        
        if 'databricks' not in self.secrets['destination']:
            raise KeyError("Databricks destination not found in secrets")
        
        databricks_config = self.secrets['destination']['databricks']
        
        # Validate Databricks configuration
        if 'credentials' not in databricks_config:
            raise ValueError("Databricks credentials missing in secrets")
        
        creds = databricks_config['credentials']
        required_fields = ['server_hostname', 'http_path', 'access_token']
        missing_fields = [f for f in required_fields if f not in creds]
        if missing_fields:
            raise ValueError(f"Missing required Databricks credentials: {', '.join(missing_fields)}")
        
        # Validate staging configuration
        if 'filesystem' not in self.secrets['destination']:
            raise KeyError("Filesystem staging configuration not found in secrets")
        
        staging_config = self.secrets['destination']['filesystem']
        if 'credentials' not in staging_config:
            raise ValueError("Staging credentials missing in secrets")
        
        staging_creds = staging_config['credentials']
        if 'azure_storage_account_name' not in staging_creds:
            raise ValueError("Staging requires 'azure_storage_account_name'")
        
        # Check for either SAS token or storage key
        has_sas = 'azure_storage_sas_token' in staging_creds
        has_key = 'azure_storage_account_key' in staging_creds
        if not (has_sas or has_key):
            raise ValueError("Staging requires either 'azure_storage_sas_token' or 'azure_storage_account_key'")
        
        # Build DLT destination config
        config = {
            'destination': 'databricks',
            'staging': 'filesystem',
            'credentials': {
                'server_hostname': creds['server_hostname'],
                'http_path': creds['http_path'],
                'catalog': databricks_config.get('catalog', 'main'),
                'access_token': creds['access_token']
            },
            'staging_config': {
                'bucket_url': staging_config.get('bucket_url', 'az://staging'),
                'credentials': {
                    'azure_storage_account_name': staging_creds['azure_storage_account_name']
                }
            }
        }
        
        # Add SAS token or storage key to staging credentials
        if has_sas:
            config['staging_config']['credentials']['azure_storage_sas_token'] = staging_creds['azure_storage_sas_token']
        if has_key:
            config['staging_config']['credentials']['azure_storage_account_key'] = staging_creds['azure_storage_account_key']
        
        # Log configuration (without sensitive data)
        self.logger.info(f"[DATABRICKS] Configured Unity Catalog destination")
        self.logger.info(f"  Server: {creds['server_hostname']}")
        self.logger.info(f"  HTTP Path: {creds['http_path']}")
        self.logger.info(f"  Catalog: {config['credentials']['catalog']}")
        self.logger.info(f"  Schema: {databricks_config.get('schema', 'raw')}")
        self.logger.info(f"  Staging: {config['staging_config']['bucket_url']}")
        self.logger.info(f"  Staging Account: {staging_creds['azure_storage_account_name']}")
        
        return config
    
    def get_schema_name(self, job: Optional[Dict] = None) -> str:
        """Get target schema name for job.
        
        Args:
            job: Optional job configuration with 'target_schema' field
        
        Returns:
            Schema name (defaults to 'raw')
        
        Priority:
        1. Job-specific 'target_schema' field
        2. Destination-level 'schema' configuration
        3. Default: 'raw'
        """
        if job and 'target_schema' in job:
            return job['target_schema']
        
        databricks_config = self.secrets['destination']['databricks']
        return databricks_config.get('schema', 'raw')
    
    def get_catalog_name(self) -> str:
        """Get Unity Catalog name.
        
        Returns:
            Catalog name (defaults to 'main')
        """
        databricks_config = self.secrets['destination']['databricks']
        return databricks_config.get('catalog', 'main')
    
    def get_full_table_name(self, table_name: str, job: Optional[Dict] = None) -> str:
        """Build fully qualified table name in Unity Catalog.
        
        Args:
            table_name: Table name
            job: Optional job configuration
        
        Returns:
            Fully qualified table name: catalog.schema.table
        
        Example:
            main.raw.customers
        """
        catalog = self.get_catalog_name()
        schema = self.get_schema_name(job)
        return f"{catalog}.{schema}.{table_name}"
    
    def validate_connection(self) -> bool:
        """Validate Databricks connectivity.
        
        Tests:
        1. databricks-sql-connector package is installed
        2. Can connect to Databricks SQL warehouse
        3. Can execute simple query
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Check if databricks-sql-connector is installed
            try:
                from databricks import sql as databricks_sql
            except ImportError:
                self.logger.warning("[DATABRICKS] databricks-sql-connector not installed")
                self.logger.warning("  Install with: pip install databricks-sql-connector")
                return False
            
            # Get credentials
            databricks_config = self.secrets['destination']['databricks']
            creds = databricks_config['credentials']
            
            # Attempt connection
            self.logger.info("[DATABRICKS] Testing connection...")
            conn = databricks_sql.connect(
                server_hostname=creds['server_hostname'],
                http_path=creds['http_path'],
                access_token=creds['access_token']
            )
            
            # Execute test query
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            self.logger.info("[DATABRICKS] Connection validated successfully")
            self.logger.info(f"  Server: {creds['server_hostname']}")
            self.logger.info(f"  Catalog: {self.get_catalog_name()}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"[DATABRICKS] Connection failed: {e}")
            self.logger.error("  Verify server_hostname, http_path, and access_token in secrets")
            return False
    
    def validate_staging(self) -> bool:
        """Validate ADLS staging connectivity.
        
        Tests:
        1. azure-storage-blob package is installed
        2. Can authenticate to ADLS storage account
        3. Can access staging container
        
        Returns:
            True if staging accessible, False otherwise
        """
        try:
            from azure.storage.blob import BlobServiceClient
            
            staging_config = self.secrets['destination']['filesystem']
            staging_creds = staging_config['credentials']
            
            # Build connection string or use SAS token
            if 'azure_storage_sas_token' in staging_creds:
                # Use SAS token
                account_name = staging_creds['azure_storage_account_name']
                sas_token = staging_creds['azure_storage_sas_token']
                account_url = f"https://{account_name}.blob.core.windows.net"
                
                # Remove leading '?' from SAS token if present
                if sas_token.startswith('?'):
                    sas_token = sas_token[1:]
                
                blob_service_client = BlobServiceClient(account_url=account_url, credential=sas_token)
                
            elif 'azure_storage_account_key' in staging_creds:
                # Use account key
                conn_str = (
                    f"DefaultEndpointsProtocol=https;"
                    f"AccountName={staging_creds['azure_storage_account_name']};"
                    f"AccountKey={staging_creds['azure_storage_account_key']};"
                    f"EndpointSuffix=core.windows.net"
                )
                blob_service_client = BlobServiceClient.from_connection_string(conn_str)
            else:
                self.logger.error("[DATABRICKS] No staging credentials found (SAS token or account key)")
                return False
            
            # Test access
            containers = list(blob_service_client.list_containers(max_results=1))
            
            self.logger.info("[DATABRICKS] Staging validation successful")
            self.logger.info(f"  Storage Account: {staging_creds['azure_storage_account_name']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"[DATABRICKS] Staging validation failed: {e}")
            self.logger.error("  Verify staging credentials in secrets")
            return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get Databricks-specific metadata.
        
        Returns:
            Dictionary with destination metadata
        """
        metadata = super().get_metadata()
        
        databricks_config = self.secrets['destination']['databricks']
        creds = databricks_config['credentials']
        staging_config = self.secrets['destination']['filesystem']
        staging_creds = staging_config['credentials']
        
        metadata.update({
            'server_hostname': creds['server_hostname'],
            'http_path': creds['http_path'],
            'catalog': self.get_catalog_name(),
            'schema': self.get_schema_name(),
            'staging_bucket': staging_config.get('bucket_url', 'az://staging'),
            'staging_account': staging_creds['azure_storage_account_name'],
            'file_format': 'delta',
            'table_type': 'managed',
            'cloud_provider': 'azure',
            'supports_acid': True,
            'supports_time_travel': True,
            'supports_schema_evolution': True
        })
        
        return metadata

