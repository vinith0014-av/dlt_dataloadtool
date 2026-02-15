"""
Azure SQL source implementation.

Handles Azure SQL Database connections with enhanced security.
"""
import logging
from typing import Dict
from urllib.parse import quote_plus
from .base import BaseSource

logger = logging.getLogger(__name__)


class AzureSQLSource(BaseSource):
    """Azure SQL Database data source handler.
    
    Features:
    - Azure SQL-specific security settings (Encrypt=yes required)
    - Proper SSL certificate validation
    - ODBC Driver 17 for SQL Server
    - Azure Active Directory authentication support (future)
    
    Important:
        - Must add client IP to Azure SQL firewall before use
        - Go to Azure Portal → SQL Server → Networking → Add client IP
    """
    
    def get_source_type(self) -> str:
        """Return Azure SQL source type identifier."""
        return "azure_sql"
    
    def build_connection_string(self, source_name: str) -> str:
        """Build Azure SQL connection string with secure defaults.
        
        Args:
            source_name: Name of the Azure SQL source in secrets
        
        Returns:
            Azure SQL connection string with encryption enabled
        
        Raises:
            KeyError: If source_name not found in secrets
        
        Example:
            mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17...};Encrypt=yes
        
        Notes:
            - Encrypt=yes is REQUIRED for Azure SQL
            - TrustServerCertificate=no ensures proper SSL validation
            - Client IP must be whitelisted in Azure SQL firewall
        """
        if 'sources' not in self.secrets or source_name not in self.secrets['sources']:
            raise KeyError(f"Azure SQL source '{source_name}' not found in secrets")
        
        azure = self.secrets['sources'][source_name]
        
        # Required fields
        required = ['host', 'port', 'database', 'username', 'password']
        missing = [f for f in required if f not in azure]
        if missing:
            raise ValueError(f"Missing required Azure SQL config: {missing}")
        
        # Azure SQL requires encryption and proper SSL validation
        driver = azure.get('query', {}).get('driver', 'ODBC Driver 17 for SQL Server')
        encrypt = azure.get('query', {}).get('Encrypt', 'yes')  # REQUIRED for Azure
        trust_cert = azure.get('query', {}).get('TrustServerCertificate', 'no')  # Proper SSL
        
        # Build raw ODBC connection string
        odbc_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={azure['host']},{azure['port']};"
            f"DATABASE={azure['database']};"
            f"UID={azure['username']};"
            f"PWD={azure['password']};"
            f"Encrypt={encrypt};"
            f"TrustServerCertificate={trust_cert};"
        )
        
        # URL-encode the ODBC string
        conn_str = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"
        
        self.logger.debug(f"Azure SQL connection: {azure['host']}/{azure['database']}")
        self.logger.info(f"[AZURE SQL] Connected to {source_name}")
        self.logger.info(f"[AZURE SQL] Ensure client IP is whitelisted in Azure firewall")
        
        return conn_str
    
    def supports_schema(self) -> bool:
        """Azure SQL supports schema parameter (defaults to 'dbo')."""
        return True
    
    def validate_connection(self, source_name: str) -> bool:
        """Test Azure SQL connectivity with firewall check.
        
        Returns:
            True if connection successful
        
        Notes:
            If connection fails, check Azure SQL firewall rules
        """
        try:
            result = super().validate_connection(source_name)
            if not result:
                self.logger.error(
                    "[AZURE SQL] Connection failed. "
                    "Check Azure Portal → SQL Server → Networking → Add your client IP"
                )
            return result
        except Exception as e:
            self.logger.error(f"[AZURE SQL] Firewall may be blocking: {e}")
            return False
    
    def get_metadata(self, source_name: str) -> Dict:
        """Get Azure SQL-specific metadata."""
        metadata = super().get_metadata(source_name)
        azure = self.secrets['sources'][source_name]
        
        metadata.update({
            'host': azure['host'],
            'port': azure['port'],
            'database': azure['database'],
            'driver': azure.get('query', {}).get('driver', 'ODBC Driver 17 for SQL Server'),
            'encrypt': 'yes',  # Always yes for Azure
            'cloud_provider': 'azure',
            'default_schema': 'dbo',
            'requires_firewall_whitelist': True
        })
        
        return metadata
