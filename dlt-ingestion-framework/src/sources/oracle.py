"""
Oracle source implementation.

Handles Oracle-specific connection strings with SID/service_name support.
"""
import logging
from typing import Dict
from .base import BaseSource

logger = logging.getLogger(__name__)


class OracleSource(BaseSource):
    """Oracle data source handler.
    
    Features:
    - Thin client connection (no Oracle client install needed)
    - SID or service_name support
    - Schema support (required for Oracle)
    - oracledb driver (python-oracledb)
    """
    
    def get_source_type(self) -> str:
        """Return Oracle source type identifier."""
        return "oracle"
    
    def build_connection_string(self, source_name: str) -> str:
        """Build Oracle connection string.
        
        Args:
            source_name: Name of the Oracle source in secrets
        
        Returns:
            Oracle connection string in format:
            oracle+oracledb://user:pass@host:port/sid_or_service
        
        Raises:
            KeyError: If source_name not found in secrets
            ValueError: If neither SID nor service_name provided
        
        Example:
            oracle+oracledb://hr_user:pass@oracledb:1521/ORCL
        """
        if 'sources' not in self.secrets or source_name not in self.secrets['sources']:
            raise KeyError(f"Oracle source '{source_name}' not found in secrets")
        
        ora = self.secrets['sources'][source_name]
        
        # Required fields
        required = ['host', 'port', 'username', 'password']
        missing = [f for f in required if f not in ora]
        if missing:
            raise ValueError(f"Missing required Oracle config: {missing}")
        
        # Must have either SID or service_name
        if 'sid' not in ora and 'service_name' not in ora:
            raise ValueError("Oracle config must have either 'sid' or 'service_name'")
        
        # Use SID or service_name
        db_identifier = ora.get('sid') or ora.get('service_name')
        
        # Build connection string (thin client - no tnsnames.ora needed)
        conn_str = (
            f"oracle+oracledb://{ora['username']}:{ora['password']}"
            f"@{ora['host']}:{ora['port']}/{db_identifier}"
        )
        
        self.logger.debug(f"Oracle connection: {ora['host']}:{ora['port']}/{db_identifier}")
        self.logger.info(f"[ORACLE] Connected to {source_name}")
        
        return conn_str
    
    def supports_schema(self) -> bool:
        """Oracle requires schema parameter (owner schema)."""
        return True
    
    def get_metadata(self, source_name: str) -> Dict:
        """Get Oracle-specific metadata."""
        metadata = super().get_metadata(source_name)
        ora = self.secrets['sources'][source_name]
        
        metadata.update({
            'host': ora['host'],
            'port': ora['port'],
            'sid': ora.get('sid'),
            'service_name': ora.get('service_name'),
            'driver': 'oracledb',
            'requires_schema': True
        })
        
        return metadata
