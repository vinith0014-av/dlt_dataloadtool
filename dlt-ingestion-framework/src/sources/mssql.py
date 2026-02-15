"""
MSSQL source implementation.

Handles Microsoft SQL Server connections with ODBC driver support.
"""
import logging
from typing import Dict
from urllib.parse import quote_plus
from .base import BaseSource

logger = logging.getLogger(__name__)


class MSSQLSource(BaseSource):
    """Microsoft SQL Server data source handler.
    
    Features:
    - ODBC Driver 17 for SQL Server
    - Raw ODBC connection string (handles special characters in passwords)
    - Encryption and certificate trust options
    - Windows or SQL Server authentication
    """
    
    def get_source_type(self) -> str:
        """Return MSSQL source type identifier."""
        return "mssql"
    
    def build_connection_string(self, source_name: str) -> str:
        """Build MSSQL connection string using ODBC.
        
        Args:
            source_name: Name of the MSSQL source in secrets
        
        Returns:
            MSSQL connection string with properly encoded ODBC parameters
        
        Raises:
            KeyError: If source_name not found in secrets
        
        Example:
            mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17...}
        
        Notes:
            - Uses raw ODBC format to handle special characters in passwords
            - Requires ODBC Driver 17 for SQL Server to be installed
            - URL-encodes the entire ODBC string for safety
        """
        if 'sources' not in self.secrets or source_name not in self.secrets['sources']:
            raise KeyError(f"MSSQL source '{source_name}' not found in secrets")
        
        ms = self.secrets['sources'][source_name]
        
        # Required fields
        required = ['host', 'port', 'database', 'username', 'password']
        missing = [f for f in required if f not in ms]
        if missing:
            raise ValueError(f"Missing required MSSQL config: {missing}")
        
        # Optional query parameters with defaults
        driver = ms.get('query', {}).get('driver', 'ODBC Driver 17 for SQL Server')
        encrypt = ms.get('query', {}).get('Encrypt', 'no')
        trust_cert = ms.get('query', {}).get('TrustServerCertificate', 'yes')
        
        # Build raw ODBC connection string
        odbc_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={ms['host']},{ms['port']};"
            f"DATABASE={ms['database']};"
            f"UID={ms['username']};"
            f"PWD={ms['password']};"
            f"Encrypt={encrypt};"
            f"TrustServerCertificate={trust_cert};"
        )
        
        # URL-encode the ODBC string
        conn_str = f"mssql+pyodbc:///?odbc_connect={quote_plus(odbc_str)}"
        
        self.logger.debug(f"MSSQL connection: {ms['host']}:{ms['port']}/{ms['database']}")
        self.logger.info(f"[MSSQL] Connected to {source_name}")
        
        return conn_str
    
    def supports_schema(self) -> bool:
        """MSSQL supports schema parameter (defaults to 'dbo')."""
        return True
    
    def get_metadata(self, source_name: str) -> Dict:
        """Get MSSQL-specific metadata."""
        metadata = super().get_metadata(source_name)
        ms = self.secrets['sources'][source_name]
        
        metadata.update({
            'host': ms['host'],
            'port': ms['port'],
            'database': ms['database'],
            'driver': ms.get('query', {}).get('driver', 'ODBC Driver 17 for SQL Server'),
            'encrypt': ms.get('query', {}).get('Encrypt', 'no'),
            'default_schema': 'dbo'
        })
        
        return metadata
