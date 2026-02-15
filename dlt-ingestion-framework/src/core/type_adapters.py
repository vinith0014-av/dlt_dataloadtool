"""
Type Adapter Callbacks for Databricks Compatibility.

Intercepts SQLAlchemy type reflection BEFORE dlt schema inference
to ensure compatible data types for Databricks COPY INTO operations.

This module prevents schema conflicts like:
- Oracle NUMBER → DECIMAL(38,9) conflicts → Convert to DOUBLE
- MSSQL TIME → Spark cannot read TIME from Parquet → Convert to String
"""
import logging
from typing import Optional, Callable

from sqlalchemy import DOUBLE, String, TIMESTAMP, Integer, BIGINT
from sqlalchemy.types import TypeEngine

logger = logging.getLogger(__name__)


def oracle_type_adapter_callback(sql_type: TypeEngine) -> Optional[TypeEngine]:
    """
    Oracle type adapter for Databricks compatibility.
    
    Conversions:
    - NUMBER → DOUBLE (prevents DECIMAL(38,9) conflicts in Delta Lake)
    - DATE → TIMESTAMP (consistent datetime handling)
    - NUMBER with precision=0 → BIGINT (integer values)
    
    Args:
        sql_type: SQLAlchemy type from reflection
    
    Returns:
        Converted type or None to keep original
    """
    try:
        from sqlalchemy.dialects.oracle import NUMBER, DATE
        
        type_name = type(sql_type).__name__
        
        if isinstance(sql_type, NUMBER):
            # Check if it's an integer (precision with scale=0)
            if hasattr(sql_type, 'scale') and sql_type.scale == 0:
                if hasattr(sql_type, 'precision') and sql_type.precision and sql_type.precision <= 18:
                    logger.debug(f"Type adapter: Oracle NUMBER(precision={sql_type.precision}, scale=0) → BIGINT")
                    return BIGINT()
            
            # Default: Convert to DOUBLE for decimal numbers
            logger.debug(f"Type adapter: Oracle NUMBER → DOUBLE")
            return DOUBLE()
        
        if isinstance(sql_type, DATE):
            logger.debug(f"Type adapter: Oracle DATE → TIMESTAMP")
            return TIMESTAMP(timezone=False)
        
    except ImportError:
        logger.warning("Oracle dialect not available - skipping Oracle type adaptations")
    
    return None  # Keep original type


def mssql_type_adapter_callback(sql_type: TypeEngine) -> Optional[TypeEngine]:
    """
    MSSQL type adapter for Databricks compatibility.
    
    Conversions:
    - TIME → String (Spark cannot read TIME from Parquet)
    - DATETIMEOFFSET → TIMESTAMP (timezone handling)
    - SMALLMONEY, MONEY → DOUBLE (currency types)
    
    Args:
        sql_type: SQLAlchemy type from reflection
    
    Returns:
        Converted type or None to keep original
    """
    try:
        from sqlalchemy.dialects.mssql import TIME, DATETIMEOFFSET, MONEY, SMALLMONEY
        
        type_name = type(sql_type).__name__
        
        if isinstance(sql_type, TIME):
            logger.debug(f"Type adapter: MSSQL TIME → String (format: 'HH:MM:SS')")
            return String(length=8)  # HH:MM:SS format
        
        if isinstance(sql_type, DATETIMEOFFSET):
            logger.debug(f"Type adapter: MSSQL DATETIMEOFFSET → TIMESTAMP")
            return TIMESTAMP(timezone=True)
        
        if isinstance(sql_type, (MONEY, SMALLMONEY)):
            logger.debug(f"Type adapter: MSSQL {type_name} → DOUBLE")
            return DOUBLE()
        
    except ImportError:
        logger.warning("MSSQL dialect not available - skipping MSSQL type adaptations")
    
    return None  # Keep original type


def postgresql_type_adapter_callback(sql_type: TypeEngine) -> Optional[TypeEngine]:
    """
    PostgreSQL type adapter (minimal changes needed).
    
    PostgreSQL types are generally compatible with Databricks.
    Only edge cases need conversion:
    - INTERVAL → String (duration representation)
    
    Args:
        sql_type: SQLAlchemy type from reflection
    
    Returns:
        Converted type or None to keep original
    """
    try:
        from sqlalchemy.dialects.postgresql import INTERVAL
        
        if isinstance(sql_type, INTERVAL):
            logger.debug(f"Type adapter: PostgreSQL INTERVAL → String")
            return String()
        
    except ImportError:
        logger.warning("PostgreSQL dialect not available - skipping PostgreSQL type adaptations")
    
    return None  # PostgreSQL types are generally compatible


def get_type_adapter_for_source(source_type: str, destination: str = "databricks") -> Optional[Callable]:
    """
    Get appropriate type adapter callback for source/destination combination.
    
    Args:
        source_type: Source database type (oracle, mssql, postgresql, azure_sql)
        destination: Target destination (databricks, filesystem)
    
    Returns:
        Type adapter callback function or None
    """
    # Type adapters only needed for Databricks destination
    # Filesystem destination (Parquet) can handle most types
    if destination not in ["databricks", "unity_catalog"]:
        logger.debug(f"No type adapter needed for destination: {destination}")
        return None
    
    adapters = {
        'oracle': oracle_type_adapter_callback,
        'mssql': mssql_type_adapter_callback,
        'azure_sql': mssql_type_adapter_callback,  # Azure SQL uses MSSQL engine
        'postgresql': postgresql_type_adapter_callback,
    }
    
    adapter = adapters.get(source_type.lower())
    
    if adapter:
        logger.info(f"[TYPE ADAPTER] Using type adapter for {source_type} → {destination}")
    else:
        logger.debug(f"No type adapter configured for source: {source_type}")
    
    return adapter


def log_type_conversion(original_type: TypeEngine, converted_type: Optional[TypeEngine], 
                        column_name: str = None):
    """
    Log type conversion for debugging.
    
    Args:
        original_type: Original SQLAlchemy type
        converted_type: Converted type (or None if no conversion)
        column_name: Optional column name for context
    """
    if converted_type:
        col_info = f" (column: {column_name})" if column_name else ""
        logger.info(
            f"[TYPE CONVERSION]{col_info} {type(original_type).__name__} → "
            f"{type(converted_type).__name__}"
        )
