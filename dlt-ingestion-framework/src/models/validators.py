"""
Custom validators for configuration models.

Provides reusable validation logic.
"""
import re
from typing import Any, Optional
from urllib.parse import urlparse


def validate_connection_string(conn_str: str) -> bool:
    """
    Validate database connection string format.
    
    Args:
        conn_str: Connection string to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If connection string is invalid
    """
    if not conn_str or not conn_str.strip():
        raise ValueError("Connection string cannot be empty")
    
    # Check for common patterns
    if '://' not in conn_str:
        raise ValueError("Connection string must contain protocol (e.g., postgresql://)")
    
    # Check for credentials
    if '@' not in conn_str:
        raise ValueError("Connection string must contain credentials (user:pass@host)")
    
    return True


def validate_url(url: str, require_https: bool = False) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        require_https: If True, only allow HTTPS URLs
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If URL is invalid
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")
    
    parsed = urlparse(url)
    
    if not parsed.scheme:
        raise ValueError("URL must include scheme (http:// or https://)")
    
    if parsed.scheme not in ['http', 'https']:
        raise ValueError("URL scheme must be http or https")
    
    if require_https and parsed.scheme != 'https':
        raise ValueError("URL must use HTTPS")
    
    if not parsed.netloc:
        raise ValueError("URL must include hostname")
    
    return True


def validate_table_name(table_name: str) -> bool:
    """
    Validate table/view name.
    
    Args:
        table_name: Table name to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If table name is invalid
    """
    if not table_name or not table_name.strip():
        raise ValueError("Table name cannot be empty")
    
    # Allow alphanumeric, underscore, dash
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, table_name):
        raise ValueError(
            "Table name must contain only alphanumeric characters, underscores, and dashes"
        )
    
    # Should not start with number
    if table_name[0].isdigit():
        raise ValueError("Table name cannot start with a number")
    
    # Length check
    if len(table_name) > 255:
        raise ValueError("Table name exceeds maximum length (255)")
    
    return True


def validate_pagination_config(
    pagination_type: str,
    config: dict
) -> bool:
    """
    Validate pagination configuration based on type.
    
    Args:
        pagination_type: Type of pagination
        config: Pagination configuration dict
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If pagination config is invalid
    """
    if pagination_type == 'offset':
        if 'page_size' not in config or config['page_size'] < 1:
            raise ValueError("offset pagination requires valid page_size")
        if 'maximum_offset' in config and config['maximum_offset'] < 0:
            raise ValueError("maximum_offset must be non-negative")
    
    elif pagination_type == 'cursor':
        if not config.get('cursor_param'):
            raise ValueError("cursor pagination requires cursor_param")
        if not config.get('cursor_path'):
            raise ValueError("cursor pagination requires cursor_path")
    
    elif pagination_type == 'page_number':
        if 'page_size' not in config or config['page_size'] < 1:
            raise ValueError("page_number pagination requires valid page_size")
        if config.get('base_page') not in [0, 1, None]:
            raise ValueError("base_page must be 0 or 1")
    
    elif pagination_type == 'json_link':
        if not config.get('next_url_path'):
            raise ValueError("json_link pagination requires next_url_path")
    
    return True


def validate_auth_config(
    auth_type: str,
    config: dict
) -> bool:
    """
    Validate authentication configuration based on type.
    
    Args:
        auth_type: Type of authentication
        config: Authentication configuration dict
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If auth config is invalid
    """
    if auth_type == 'api_key':
        if not config.get('api_key'):
            raise ValueError("api_key authentication requires api_key")
        if config.get('api_key_location') not in ['header', 'query', None]:
            raise ValueError("api_key_location must be 'header' or 'query'")
    
    elif auth_type == 'bearer':
        if not config.get('token'):
            raise ValueError("bearer authentication requires token")
    
    elif auth_type == 'basic':
        if not config.get('username') or not config.get('password'):
            raise ValueError("basic authentication requires username and password")
    
    elif auth_type == 'oauth2':
        if not config.get('oauth_url'):
            raise ValueError("oauth2 requires oauth_url")
        if not config.get('client_id') or not config.get('client_secret'):
            raise ValueError("oauth2 requires client_id and client_secret")
    
    return True


def validate_incremental_config(
    load_type: str,
    watermark_column: Optional[str],
    last_watermark: Optional[Any]
) -> bool:
    """
    Validate incremental load configuration.
    
    Args:
        load_type: Load type (FULL or INCREMENTAL)
        watermark_column: Watermark column name
        last_watermark: Last watermark value
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If incremental config is invalid
    """
    if load_type.upper() == 'INCREMENTAL':
        if not watermark_column:
            raise ValueError("INCREMENTAL load requires watermark_column")
        
        # Validate column name
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', watermark_column):
            raise ValueError(
                "watermark_column must be valid identifier (alphanumeric and underscore)"
            )
    
    return True


def validate_chunk_size(chunk_size: int, table_rows: Optional[int] = None) -> bool:
    """
    Validate chunk size is reasonable.
    
    Args:
        chunk_size: Chunk size to validate
        table_rows: Optional table size for context
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If chunk size is invalid
    """
    if chunk_size < 1000:
        raise ValueError("chunk_size should be at least 1,000 for efficiency")
    
    if chunk_size > 5000000:
        raise ValueError("chunk_size should not exceed 5,000,000 to avoid memory issues")
    
    if table_rows and chunk_size > table_rows:
        raise ValueError(
            f"chunk_size ({chunk_size}) should not exceed table size ({table_rows})"
        )
    
    return True


def validate_port(port: int) -> bool:
    """
    Validate TCP port number.
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If port is invalid
    """
    if not (1 <= port <= 65535):
        raise ValueError("Port must be between 1 and 65535")
    
    # Warn about non-standard ports for common databases
    standard_ports = {
        5432: "PostgreSQL",
        1521: "Oracle",
        1433: "SQL Server",
        3306: "MySQL",
        27017: "MongoDB"
    }
    
    return True
