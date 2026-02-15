"""
PostgreSQL source implementation.

Handles PostgreSQL-specific connection strings and table ingestion.
"""
import logging
from typing import Dict
from .base import BaseSource

logger = logging.getLogger(__name__)


class PostgreSQLSource(BaseSource):
    """PostgreSQL data source handler.
    
    Features:
    - Standard PostgreSQL connection strings
    - psycopg2 driver support
    - Schema support (defaults to 'public')
    - SSL connection options
    """
    
    def get_source_type(self) -> str:
        """Return PostgreSQL source type identifier."""
        return "postgresql"
    
    def build_connection_string(self, source_name: str) -> str:
        """Build PostgreSQL connection string.
        
        Args:
            source_name: Name of the PostgreSQL source in secrets
        
        Returns:
            PostgreSQL connection string in format:
            postgresql+psycopg2://user:pass@host:port/database
        
        Raises:
            KeyError: If source_name not found in secrets
        
        Example:
            postgresql+psycopg2://postgres:mypass@localhost:5432/sales_db
        """
        if 'sources' not in self.secrets or source_name not in self.secrets['sources']:
            raise KeyError(f"PostgreSQL source '{source_name}' not found in secrets")
        
        pg = self.secrets['sources'][source_name]
        
        # Required fields
        required = ['host', 'port', 'database', 'username', 'password']
        missing = [f for f in required if f not in pg]
        if missing:
            raise ValueError(f"Missing required PostgreSQL config: {missing}")
        
        # Build connection string
        conn_str = (
            f"postgresql+psycopg2://{pg['username']}:{pg['password']}"
            f"@{pg['host']}:{pg['port']}/{pg['database']}"
        )
        
        self.logger.debug(f"PostgreSQL connection: {pg['host']}:{pg['port']}/{pg['database']}")
        self.logger.info(f"[POSTGRESQL] Connected to {source_name}")
        
        return conn_str
    
    def supports_schema(self) -> bool:
        """PostgreSQL supports schema parameter."""
        return True
    
    def get_metadata(self, source_name: str) -> Dict:
        """Get PostgreSQL-specific metadata."""
        metadata = super().get_metadata(source_name)
        pg = self.secrets['sources'][source_name]
        
        metadata.update({
            'host': pg['host'],
            'port': pg['port'],
            'database': pg['database'],
            'driver': 'psycopg2',
            'default_schema': 'public'
        })
        
        return metadata
