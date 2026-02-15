"""
Base class for all data sources.

Defines the interface that all source implementations must follow.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseSource(ABC):
    """Abstract base class for all data sources.
    
    Each source type (PostgreSQL, Oracle, MSSQL, etc.) must implement:
    - build_connection_string(): Database connection string generation
    - get_source_type(): Return source type identifier
    - supports_schema(): Whether source supports schema parameter
    
    Optional overrides:
    - estimate_table_size(): Table row count estimation
    - validate_connection(): Test connectivity before ingestion
    - get_metadata(): Additional source-specific metadata
    """
    
    def __init__(self, name: str, config: Dict):
        """Initialize source with name and configuration.
        
        Args:
            name: Source instance name
            config: Dictionary containing source credentials
        """
        self.name = name
        self.config = config
        # Keep backward compatibility with secrets attribute
        self.secrets = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up source-specific logger.
        
        Returns:
            Logger instance configured for this source type
        """
        source_logger = logging.getLogger(f"{__name__}.{self.get_source_type()}")
        return source_logger
    
    @abstractmethod
    def build_connection_string(self, source_name: str) -> str:
        """Build database connection string.
        
        Args:
            source_name: Name of the source configuration
        
        Returns:
            SQLAlchemy-compatible connection string
        
        Raises:
            ValueError: If source configuration is invalid
            KeyError: If required credentials are missing
        """
        pass
    
    @abstractmethod
    def get_source_type(self) -> str:
        """Return source type identifier.
        
        Returns:
            Source type string (e.g., 'postgresql', 'oracle')
        """
        pass
    
    def supports_schema(self) -> bool:
        """Whether this source supports schema parameter.
        
        Returns:
            True if source supports schema (e.g., Oracle), False otherwise
        """
        return False
    
    def estimate_table_size(self, conn_str: str, table_name: str, 
                           schema_name: Optional[str] = None) -> Tuple[Optional[int], int]:
        """Estimate table size and recommend chunk size.
        
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
            
            # Try to get row count
            query = f"SELECT COUNT(*) as row_count FROM {full_table}"
            
            with engine.connect() as conn:
                result = conn.execute(text(query))
                row_count = result.scalar()
            
            # Recommend chunk_size based on table size
            if row_count < 100000:
                recommended_chunk = 50000
            elif row_count < 1000000:
                recommended_chunk = 100000
            elif row_count < 10000000:
                recommended_chunk = 250000
            elif row_count < 50000000:
                recommended_chunk = 500000
            else:
                recommended_chunk = 1000000
            
            self.logger.info(f"[TABLE SIZE] {full_table}: {row_count:,} rows")
            self.logger.info(f"[RECOMMENDED CHUNK] {recommended_chunk:,} rows")
            
            return row_count, recommended_chunk
            
        except Exception as e:
            self.logger.warning(f"[SIZE ESTIMATION FAILED] {e}")
            return None, 100000  # Default fallback
    
    def validate_connection(self, source_name: str) -> bool:
        """Test database connectivity.
        
        Args:
            source_name: Name of the source configuration
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            from sqlalchemy import create_engine
            conn_str = self.build_connection_string(source_name)
            engine = create_engine(conn_str)
            with engine.connect():
                pass
            self.logger.info(f"[CONNECTION OK] {source_name}")
            return True
        except Exception as e:
            self.logger.error(f"[CONNECTION FAILED] {source_name}: {e}")
            return False
    
    def get_metadata(self, source_name: str) -> Dict[str, Any]:
        """Get source-specific metadata.
        
        Args:
            source_name: Name of the source configuration
        
        Returns:
            Dictionary with source metadata
        """
        return {
            'source_type': self.get_source_type(),
            'source_name': source_name,
            'supports_schema': self.supports_schema()
        }
