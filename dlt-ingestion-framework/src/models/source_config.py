"""
Source configuration Pydantic models.

Validates source-specific configuration from secrets.
"""
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, HttpUrl


class PaginationType(str, Enum):
    """API pagination types."""
    SINGLE_PAGE = "single_page"
    OFFSET = "offset"
    CURSOR = "cursor"
    PAGE_NUMBER = "page_number"
    HEADER_LINK = "header_link"
    JSON_LINK = "json_link"


class AuthType(str, Enum):
    """API authentication types."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"


class BaseDatabaseConfig(BaseModel):
    """Base configuration for database sources."""
    
    host: str = Field(..., min_length=1, max_length=255)
    port: int = Field(..., ge=1, le=65535)
    database: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)
    
    @field_validator('host')
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host format."""
        if not v or v.isspace():
            raise ValueError("host cannot be empty")
        return v.strip()
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class PostgreSQLConfig(BaseDatabaseConfig):
    """PostgreSQL source configuration."""
    
    ssl_mode: Optional[str] = Field(
        default="prefer",
        description="SSL mode: disable, allow, prefer, require, verify-ca, verify-full"
    )
    
    connect_timeout: Optional[int] = Field(
        default=10,
        ge=1,
        le=300,
        description="Connection timeout in seconds"
    )
    
    @field_validator('ssl_mode')
    @classmethod
    def validate_ssl_mode(cls, v: Optional[str]) -> Optional[str]:
        """Validate SSL mode."""
        if v:
            valid_modes = ['disable', 'allow', 'prefer', 'require', 'verify-ca', 'verify-full']
            if v not in valid_modes:
                raise ValueError(f"ssl_mode must be one of: {', '.join(valid_modes)}")
        return v


class OracleConfig(BaseDatabaseConfig):
    """Oracle source configuration."""
    
    sid: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Oracle SID (mutually exclusive with service_name)"
    )
    
    service_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Oracle Service Name (mutually exclusive with SID)"
    )
    
    thick_mode: Optional[bool] = Field(
        default=False,
        description="Use Oracle thick mode (requires Oracle Client)"
    )
    
    @field_validator('sid', 'service_name')
    @classmethod
    def validate_oracle_identifier(cls, v: Optional[str]) -> Optional[str]:
        """Validate Oracle SID/service name."""
        if v and not v.replace('_', '').isalnum():
            raise ValueError("Invalid Oracle identifier (use alphanumeric and underscore only)")
        return v


class MSSQLConfig(BaseDatabaseConfig):
    """SQL Server source configuration."""
    
    driver: str = Field(
        default="ODBC Driver 17 for SQL Server",
        description="ODBC driver name"
    )
    
    encrypt: str = Field(
        default="no",
        description="Encrypt connection: yes or no"
    )
    
    trust_server_certificate: str = Field(
        default="yes",
        description="Trust server certificate: yes or no"
    )
    
    @field_validator('encrypt', 'trust_server_certificate')
    @classmethod
    def validate_yes_no(cls, v: str) -> str:
        """Validate yes/no fields."""
        v_lower = v.lower()
        if v_lower not in ['yes', 'no']:
            raise ValueError("Must be 'yes' or 'no'")
        return v_lower


class AzureSQLConfig(MSSQLConfig):
    """Azure SQL source configuration (extends MSSQL)."""
    
    encrypt: str = Field(
        default="yes",
        description="Encrypt connection (required for Azure)"
    )
    
    trust_server_certificate: str = Field(
        default="no",
        description="Trust server certificate (should be 'no' for Azure)"
    )
    
    authentication: Optional[str] = Field(
        default="SqlPassword",
        description="Authentication method: SqlPassword, ActiveDirectoryPassword, ActiveDirectoryIntegrated"
    )
    
    @field_validator('authentication')
    @classmethod
    def validate_authentication(cls, v: Optional[str]) -> Optional[str]:
        """Validate Azure SQL authentication method."""
        if v:
            valid_methods = ['SqlPassword', 'ActiveDirectoryPassword', 'ActiveDirectoryIntegrated']
            if v not in valid_methods:
                raise ValueError(f"authentication must be one of: {', '.join(valid_methods)}")
        return v


class RESTAPIConfig(BaseModel):
    """REST API source configuration."""
    
    base_url: str = Field(
        ...,
        min_length=1,
        description="API base URL"
    )
    
    auth_type: AuthType = Field(
        default=AuthType.NONE,
        description="Authentication type"
    )
    
    # API Key Authentication
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    
    api_key_name: Optional[str] = Field(
        default="X-API-Key",
        description="API key header/query parameter name"
    )
    
    api_key_location: Optional[str] = Field(
        default="header",
        description="Location: header or query"
    )
    
    # Bearer Token Authentication
    token: Optional[str] = Field(
        default=None,
        description="Bearer token"
    )
    
    # Basic Authentication
    username: Optional[str] = Field(
        default=None,
        description="Username for basic auth"
    )
    
    password: Optional[str] = Field(
        default=None,
        description="Password for basic auth"
    )
    
    # OAuth 2.0
    oauth_url: Optional[str] = Field(
        default=None,
        description="OAuth token endpoint"
    )
    
    client_id: Optional[str] = Field(
        default=None,
        description="OAuth client ID"
    )
    
    client_secret: Optional[str] = Field(
        default=None,
        description="OAuth client secret"
    )
    
    scope: Optional[str] = Field(
        default=None,
        description="OAuth scope"
    )
    
    # Pagination
    pagination_type: PaginationType = Field(
        default=PaginationType.SINGLE_PAGE,
        description="Pagination strategy"
    )
    
    page_size: Optional[int] = Field(
        default=100,
        ge=1,
        le=10000,
        description="Records per page"
    )
    
    # Offset Pagination
    offset_param: Optional[str] = Field(
        default="offset",
        description="Offset parameter name"
    )
    
    limit_param: Optional[str] = Field(
        default="limit",
        description="Limit parameter name"
    )
    
    maximum_offset: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum offset (safety limit)"
    )
    
    # Cursor Pagination
    cursor_param: Optional[str] = Field(
        default=None,
        description="Cursor parameter name"
    )
    
    cursor_path: Optional[str] = Field(
        default=None,
        description="Path to cursor in response"
    )
    
    # Page Number Pagination
    page_param: Optional[str] = Field(
        default="page",
        description="Page parameter name"
    )
    
    per_page_param: Optional[str] = Field(
        default="per_page",
        description="Per-page parameter name"
    )
    
    base_page: Optional[int] = Field(
        default=1,
        ge=0,
        le=1,
        description="Starting page: 0 or 1"
    )
    
    # JSON Link Pagination
    next_url_path: Optional[str] = Field(
        default=None,
        description="Path to next URL in JSON response"
    )
    
    # Advanced
    rate_limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=10000,
        description="Requests per minute"
    )
    
    timeout: Optional[int] = Field(
        default=30,
        ge=1,
        le=300,
        description="Request timeout in seconds"
    )
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate base URL format."""
        v = v.strip()
        if not v.startswith(('http://', 'https://')):
            raise ValueError("base_url must start with http:// or https://")
        if v.endswith('/'):
            v = v.rstrip('/')  # Remove trailing slash
        return v
    
    @field_validator('api_key_location')
    @classmethod
    def validate_api_key_location(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key location."""
        if v:
            v_lower = v.lower()
            if v_lower not in ['header', 'query']:
                raise ValueError("api_key_location must be 'header' or 'query'")
            return v_lower
        return v
    
    @field_validator('auth_type')
    @classmethod
    def validate_auth_type_enum(cls, v: AuthType) -> AuthType:
        """Ensure auth_type is valid enum."""
        if not isinstance(v, AuthType):
            try:
                return AuthType(v)
            except ValueError:
                valid_types = [t.value for t in AuthType]
                raise ValueError(f"auth_type must be one of: {', '.join(valid_types)}")
        return v
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True


# Union type for all source configurations
SourceConfig = PostgreSQLConfig | OracleConfig | MSSQLConfig | AzureSQLConfig | RESTAPIConfig
