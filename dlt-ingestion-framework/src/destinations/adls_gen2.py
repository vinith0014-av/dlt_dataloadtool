"""
Azure Data Lake Storage Gen2 destination implementation.

Handles ADLS Gen2-specific configuration and date partitioning.
"""
import logging
from typing import Dict, Any
from .base import BaseDestination

logger = logging.getLogger(__name__)


class ADLSGen2Destination(BaseDestination):
    """Azure Data Lake Storage Gen2 destination handler.
    
    Features:
    - Date-partitioned Parquet output: {table}/{YYYY}/{MM}/{DD}/{file}.parquet
    - Azure Storage Account authentication
    - Filesystem destination with az:// protocol
    - Automatic directory creation
    - Support for multiple containers
    """
    
    def get_destination_type(self) -> str:
        """Return ADLS Gen2 destination type identifier."""
        return "adls_gen2"
    
    def get_dlt_destination_config(self) -> Dict[str, Any]:
        """Get DLT filesystem destination configuration for ADLS Gen2.
        
        Returns:
            Dictionary with DLT destination configuration
        
        Raises:
            KeyError: If ADLS credentials not found in secrets
        
        Example config in secrets.toml:
            [destination.filesystem]
            bucket_url = "az://raw-data"
            layout = "{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}"
            
            [destination.filesystem.credentials]
            azure_storage_account_name = "dltpoctest"
            azure_storage_account_key = "your_key"
        """
        if 'destination' not in self.secrets or 'filesystem' not in self.secrets['destination']:
            raise KeyError("ADLS Gen2 destination not found in secrets")
        
        dest = self.secrets['destination']['filesystem']
        
        # Validate required fields
        if 'credentials' not in dest:
            raise ValueError("ADLS Gen2 credentials missing in secrets")
        
        creds = dest['credentials']
        if 'azure_storage_account_name' not in creds or 'azure_storage_account_key' not in creds:
            raise ValueError("ADLS Gen2 requires 'azure_storage_account_name' and 'azure_storage_account_key'")
        
        # Build DLT destination config
        config = {
            'destination': 'filesystem',
            'bucket_url': dest.get('bucket_url', 'az://raw-data'),
            'layout': dest.get('layout', '{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}'),
            'credentials': {
                'azure_storage_account_name': creds['azure_storage_account_name'],
                'azure_storage_account_key': creds['azure_storage_account_key']
            }
        }
        
        self.logger.info(f"[ADLS GEN2] Configured destination")
        self.logger.info(f"  Bucket: {config['bucket_url']}")
        self.logger.info(f"  Layout: {config['layout']}")
        self.logger.info(f"  Storage Account: {creds['azure_storage_account_name']}")
        
        return config
    
    def validate_connection(self) -> bool:
        """Test ADLS Gen2 connectivity.
        
        Returns:
            True if storage account is accessible, False otherwise
        """
        try:
            from azure.storage.blob import BlobServiceClient
            
            dest = self.secrets['destination']['filesystem']
            creds = dest['credentials']
            
            # Build connection string
            conn_str = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={creds['azure_storage_account_name']};"
                f"AccountKey={creds['azure_storage_account_key']};"
                f"EndpointSuffix=core.windows.net"
            )
            
            # Test connection
            blob_service_client = BlobServiceClient.from_connection_string(conn_str)
            
            # List containers to verify access
            containers = list(blob_service_client.list_containers(max_results=1))
            
            self.logger.info(f"[ADLS GEN2] Connection successful")
            self.logger.info(f"  Storage Account: {creds['azure_storage_account_name']}")
            self.logger.info(f"  Accessible containers: {len(list(blob_service_client.list_containers()))}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"[ADLS GEN2] Connection failed: {e}")
            self.logger.error("  Verify storage account name and key in secrets")
            return False
    
    def get_partition_path(self, table_name: str, year: str, month: str, day: str) -> str:
        """Build partition path for a specific date.
        
        Args:
            table_name: Name of the table
            year: Year (YYYY)
            month: Month (MM)
            day: Day (DD)
        
        Returns:
            Full partition path
        
        Example:
            orders/2026/02/09
        """
        return f"{table_name}/{year}/{month}/{day}"
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get ADLS Gen2-specific metadata."""
        metadata = super().get_metadata()
        
        dest = self.secrets['destination']['filesystem']
        creds = dest['credentials']
        
        metadata.update({
            'bucket_url': dest.get('bucket_url', 'az://raw-data'),
            'layout': dest.get('layout', '{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}'),
            'storage_account': creds['azure_storage_account_name'],
            'file_format': 'parquet',
            'partition_strategy': 'date_based',
            'cloud_provider': 'azure'
        })
        
        return metadata
