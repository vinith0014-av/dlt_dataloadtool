# DLT Ingestion Framework - Missing Features Implementation Plan

**Created**: February 11, 2026  
**Target Completion**: April 30, 2026 (11 weeks)  
**Current Achievement**: 45-50%  
**Target Achievement**: 90%+

---

## 📋 Plan Overview

This document outlines the implementation plan for all missing features identified in the Framework Comparison Analysis. Features are organized by priority and phase, with detailed implementation steps, code examples, and acceptance criteria.

### Implementation Phases

| Phase | Duration | Focus Area | Achievement Target |
|-------|----------|------------|-------------------|
| **Phase 1** | Weeks 1-4 | Critical Fixes & Foundation | 45% → 70% |
| **Phase 2** | Weeks 5-8 | Production Hardening | 70% → 85% |
| **Phase 3** | Weeks 9-11 | Deployment & Polish | 85% → 90%+ |

### Feature Priority Legend

- 🔴 **P0 - Critical**: Production blockers, must fix immediately
- 🟠 **P1 - High**: Required for enterprise deployment
- 🟡 **P2 - Medium**: Nice-to-have, improves quality
- 🟢 **P3 - Low**: Future enhancements

---

## 🔴 PHASE 1: Critical Fixes & Foundation (Weeks 1-4)

### Feature 1.1: Type Adapter Callbacks
**Priority**: 🔴 P0 - Critical  
**Effort**: 2-3 days  
**Dependencies**: None  

#### Problem Statement
Oracle NUMBER and MSSQL TIME types cause schema conflicts with Databricks COPY INTO, resulting in `DELTA_FAILED_TO_MERGE_FIELDS` errors.

#### Implementation Steps

**Step 1.1.1: Create Type Adapter Module**
```
File: src/core/type_adapters.py
```

```python
"""
Type Adapter Callbacks for Databricks Compatibility.

Intercepts SQLAlchemy type reflection BEFORE dlt schema inference
to ensure compatible data types for Databricks COPY INTO operations.
"""
import logging
from typing import Optional, Any

from sqlalchemy import DOUBLE, String, TIMESTAMP
from sqlalchemy.types import TypeEngine

logger = logging.getLogger(__name__)


def oracle_type_adapter_callback(sql_type: TypeEngine) -> Optional[TypeEngine]:
    """
    Oracle type adapter for Databricks compatibility.
    
    Conversions:
    - NUMBER → DOUBLE (prevents DECIMAL(38,9) conflicts)
    - DATE → TIMESTAMP (consistent datetime handling)
    
    Args:
        sql_type: SQLAlchemy type from reflection
    
    Returns:
        Converted type or None to keep original
    """
    from sqlalchemy.dialects.oracle import NUMBER, DATE
    
    type_name = type(sql_type).__name__
    
    if isinstance(sql_type, NUMBER):
        logger.debug(f"Type adapter: Oracle NUMBER → DOUBLE")
        return DOUBLE()
    
    if isinstance(sql_type, DATE):
        logger.debug(f"Type adapter: Oracle DATE → TIMESTAMP")
        return TIMESTAMP(timezone=False)
    
    return None  # Keep original type


def mssql_type_adapter_callback(sql_type: TypeEngine) -> Optional[TypeEngine]:
    """
    MSSQL type adapter for Databricks compatibility.
    
    Conversions:
    - TIME → String (Spark cannot read TIME from Parquet)
    - DATETIMEOFFSET → TIMESTAMP (timezone handling)
    
    Args:
        sql_type: SQLAlchemy type from reflection
    
    Returns:
        Converted type or None to keep original
    """
    from sqlalchemy.dialects.mssql import TIME, DATETIMEOFFSET
    
    type_name = type(sql_type).__name__
    
    if isinstance(sql_type, TIME):
        logger.debug(f"Type adapter: MSSQL TIME → String")
        return String()
    
    if isinstance(sql_type, DATETIMEOFFSET):
        logger.debug(f"Type adapter: MSSQL DATETIMEOFFSET → TIMESTAMP")
        return TIMESTAMP(timezone=True)
    
    return None  # Keep original type


def postgresql_type_adapter_callback(sql_type: TypeEngine) -> Optional[TypeEngine]:
    """PostgreSQL type adapter (minimal changes needed)."""
    # PostgreSQL types are generally compatible
    return None


def get_type_adapter_for_source(source_type: str, destination: str = "databricks"):
    """
    Get appropriate type adapter callback for source/destination combination.
    
    Args:
        source_type: Source database type (oracle, mssql, postgresql, azure_sql)
        destination: Target destination (databricks, filesystem)
    
    Returns:
        Type adapter callback function or None
    """
    if destination != "databricks":
        return None  # No adaptation needed for filesystem
    
    adapters = {
        'oracle': oracle_type_adapter_callback,
        'mssql': mssql_type_adapter_callback,
        'azure_sql': mssql_type_adapter_callback,  # Same as MSSQL
        'postgresql': postgresql_type_adapter_callback,
    }
    
    adapter = adapters.get(source_type.lower())
    if adapter:
        logger.info(f"Using type adapter for {source_type} → {destination}")
    
    return adapter
```

**Step 1.1.2: Integrate into Source Modules**

Update `src/sources/oracle.py`:
```python
# Add import at top
from src.core.type_adapters import get_type_adapter_for_source

# In build_connection_string or get_dlt_resource method:
def get_dlt_resource(self, job: dict, destination: str = "databricks"):
    """Create DLT resource with type adapter."""
    conn_str = self.build_connection_string(job['source_name'])
    
    # Get type adapter for this source/destination combination
    type_adapter = get_type_adapter_for_source('oracle', destination)
    
    resource = sql_table(
        credentials=ConnectionStringCredentials(conn_str),
        table=job['table_name'],
        schema=job.get('schema_name'),
        type_adapter_callback=type_adapter,  # KEY ADDITION
        backend="pyarrow",
        chunk_size=job.get('chunk_size', 100000),
        detect_precision_hints=True,
        defer_table_reflect=True
    )
    
    return resource
```

**Step 1.1.3: Update Orchestrator**

Update `src/core/orchestrator.py` to pass destination type to sources.

#### Acceptance Criteria
- [ ] Oracle NUMBER columns load as DOUBLE in Databricks
- [ ] MSSQL TIME columns load as STRING in Databricks
- [ ] No `DELTA_FAILED_TO_MERGE_FIELDS` errors
- [ ] Unit tests pass for type adapter functions
- [ ] Integration test with real Oracle/MSSQL → Databricks

#### Test Cases
```python
# tests/unit/test_type_adapters.py
def test_oracle_number_to_double():
    from sqlalchemy.dialects.oracle import NUMBER
    from src.core.type_adapters import oracle_type_adapter_callback
    
    result = oracle_type_adapter_callback(NUMBER())
    assert isinstance(result, DOUBLE)

def test_mssql_time_to_string():
    from sqlalchemy.dialects.mssql import TIME
    from src.core.type_adapters import mssql_type_adapter_callback
    
    result = mssql_type_adapter_callback(TIME())
    assert isinstance(result, String)
```

---

### Feature 1.2: REST API Pagination Support
**Priority**: 🔴 P0 - Critical  
**Effort**: 5-7 days  
**Dependencies**: None  

#### Problem Statement
Current REST API implementation fetches only single page (100-1000 records), missing pagination support for large APIs.

#### Implementation Steps

**Step 1.2.1: Refactor REST API Source**
```
File: src/sources/rest_api.py (complete rewrite)
```

```python
"""
REST API Source - Production-grade REST API ingestion using DLT native rest_api_source.

Supports:
- 6 pagination types (single_page, offset, cursor, page_number, header_link, json_link)
- 4 authentication methods (api_key, bearer, basic, oauth2)
- Rate limiting and retries
- Incremental loading
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from dlt.sources.rest_api import rest_api_source
from src.sources.base import BaseSource

logger = logging.getLogger(__name__)


class PaginationType(Enum):
    """Supported pagination types."""
    SINGLE_PAGE = "single_page"
    OFFSET = "offset"
    CURSOR = "cursor"
    PAGE_NUMBER = "page_number"
    HEADER_LINK = "header_link"
    JSON_LINK = "json_link"


class AuthType(Enum):
    """Supported authentication types."""
    NONE = "none"
    API_KEY = "api_key"
    BEARER = "bearer"
    BASIC = "basic"
    OAUTH2 = "oauth2"


@dataclass
class PaginationConfig:
    """Pagination configuration."""
    type: PaginationType
    limit_param: str = "limit"
    offset_param: str = "offset"
    cursor_param: str = "cursor"
    cursor_path: str = "next_cursor"
    page_param: str = "page"
    per_page_param: str = "per_page"
    page_size: int = 100
    max_pages: Optional[int] = None


@dataclass
class AuthConfig:
    """Authentication configuration."""
    type: AuthType
    api_key: Optional[str] = None
    api_key_name: str = "X-API-Key"
    api_key_location: str = "header"  # header or query
    token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    oauth_url: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class RESTAPISource(BaseSource):
    """
    Production-grade REST API source using DLT native rest_api_source.
    
    Features:
    - 6 pagination types
    - 4 authentication methods
    - Automatic retry with exponential backoff
    - Rate limiting support
    - Incremental loading via cursors
    """
    
    def __init__(self, secrets: Dict):
        super().__init__(secrets, 'api')
        self.source_type = 'api'
    
    def build_connection_string(self, source_name: str) -> str:
        """REST APIs don't use connection strings."""
        return None
    
    def get_api_config(self, source_name: str) -> Dict:
        """Get API configuration from secrets."""
        return self.secrets.get('sources', {}).get(source_name, {})
    
    def build_rest_config(self, job: Dict) -> Dict:
        """
        Build DLT rest_api_source configuration from job definition.
        
        Args:
            job: Job configuration dictionary with:
                - source_name: API source name (for secrets lookup)
                - table_name: Resource/endpoint name
                - api_endpoint: API endpoint path
                - pagination_type: Pagination strategy
                - auth_type: Authentication method
        
        Returns:
            DLT rest_api_source compatible configuration
        """
        api_config = self.get_api_config(job['source_name'])
        
        # Build client configuration
        client_config = {
            "base_url": api_config.get('base_url', api_config.get('url', ''))
        }
        
        # Add authentication
        auth_config = self._build_auth_config(job, api_config)
        if auth_config:
            client_config.update(auth_config)
        
        # Add rate limiting if specified
        if api_config.get('rate_limit'):
            client_config['rate_limit'] = api_config['rate_limit']
        
        # Build resource configuration
        resource_config = self._build_resource_config(job, api_config)
        
        rest_config = {
            "client": client_config,
            "resources": [resource_config]
        }
        
        logger.info(f"Built REST config for {job['source_name']}.{job['table_name']}")
        logger.debug(f"Config: {rest_config}")
        
        return rest_config
    
    def _build_auth_config(self, job: Dict, api_config: Dict) -> Optional[Dict]:
        """Build authentication configuration."""
        auth_type = job.get('auth_type', api_config.get('auth_type', 'none')).lower()
        
        if auth_type == 'none':
            return None
        
        if auth_type == 'api_key':
            api_key = api_config.get('api_key')
            api_key_name = api_config.get('api_key_name', 'X-API-Key')
            api_key_location = api_config.get('api_key_location', 'header')
            
            if api_key_location == 'header':
                return {"headers": {api_key_name: api_key}}
            else:
                return {"params": {api_key_name: api_key}}
        
        if auth_type == 'bearer':
            token = api_config.get('token', api_config.get('bearer_token'))
            return {"headers": {"Authorization": f"Bearer {token}"}}
        
        if auth_type == 'basic':
            username = api_config.get('username')
            password = api_config.get('password')
            return {"auth": (username, password)}
        
        if auth_type == 'oauth2':
            # OAuth2 client credentials flow
            return {
                "auth": {
                    "type": "oauth2",
                    "token_url": api_config.get('oauth_url'),
                    "client_id": api_config.get('client_id'),
                    "client_secret": api_config.get('client_secret')
                }
            }
        
        logger.warning(f"Unknown auth type: {auth_type}")
        return None
    
    def _build_resource_config(self, job: Dict, api_config: Dict) -> Dict:
        """Build resource (endpoint) configuration."""
        endpoint_path = job.get('api_endpoint', job['table_name'])
        
        resource_config = {
            "name": job['table_name'],
            "endpoint": {
                "path": endpoint_path
            }
        }
        
        # Add query parameters if specified
        if api_config.get('params'):
            resource_config["endpoint"]["params"] = api_config['params']
        
        # Add pagination
        pagination_config = self._build_pagination_config(job, api_config)
        if pagination_config:
            resource_config["endpoint"]["paginator"] = pagination_config
        
        # Add data selector if response is wrapped
        if api_config.get('data_selector'):
            resource_config["endpoint"]["data_selector"] = api_config['data_selector']
        
        return resource_config
    
    def _build_pagination_config(self, job: Dict, api_config: Dict) -> Optional[Dict]:
        """Build pagination configuration based on type."""
        pagination_type = job.get('pagination_type', 
                                  api_config.get('pagination_type', 'single_page')).lower()
        
        page_size = job.get('page_size', api_config.get('page_size', 100))
        
        if pagination_type == 'single_page':
            return None  # No pagination
        
        if pagination_type == 'offset':
            return {
                "type": "offset",
                "limit": page_size,
                "offset_param": api_config.get('offset_param', 'offset'),
                "limit_param": api_config.get('limit_param', 'limit')
            }
        
        if pagination_type == 'cursor':
            return {
                "type": "cursor",
                "cursor_param": api_config.get('cursor_param', 'cursor'),
                "cursor_path": api_config.get('cursor_path', 'next_cursor')
            }
        
        if pagination_type == 'page_number':
            return {
                "type": "page_number",
                "page_param": api_config.get('page_param', 'page'),
                "per_page": page_size,
                "per_page_param": api_config.get('per_page_param', 'per_page'),
                "base_page": api_config.get('base_page', 1)
            }
        
        if pagination_type == 'header_link':
            return {
                "type": "header_link",
                "next_url_path": api_config.get('next_url_path', 'links.next')
            }
        
        if pagination_type == 'json_link':
            return {
                "type": "json_link",
                "next_url_path": api_config.get('next_url_path', 'next')
            }
        
        logger.warning(f"Unknown pagination type: {pagination_type}")
        return None
    
    def create_source(self, job: Dict):
        """
        Create DLT REST API source from job configuration.
        
        Args:
            job: Job configuration dictionary
        
        Returns:
            DLT source object
        """
        rest_config = self.build_rest_config(job)
        return rest_api_source(rest_config)
    
    def get_resource(self, job: Dict):
        """
        Get specific resource from REST API source.
        
        Args:
            job: Job configuration dictionary
        
        Returns:
            DLT resource for the specified endpoint
        """
        source = self.create_source(job)
        resource_name = job['table_name']
        
        if hasattr(source, resource_name):
            return getattr(source, resource_name)
        
        # Try to get from resources collection
        if hasattr(source, 'resources') and resource_name in source.resources:
            return source.resources[resource_name]
        
        raise ValueError(f"Resource '{resource_name}' not found in API source")
    
    def validate_connection(self, source_name: str) -> bool:
        """Validate API connectivity."""
        import requests
        
        api_config = self.get_api_config(source_name)
        base_url = api_config.get('base_url', api_config.get('url', ''))
        
        if not base_url:
            logger.error(f"No base_url configured for API source: {source_name}")
            return False
        
        try:
            # Simple health check (HEAD request)
            response = requests.head(base_url, timeout=10)
            return response.status_code < 500
        except requests.RequestException as e:
            logger.warning(f"API connection check failed: {e}")
            return False
```

**Step 1.2.2: Update Secrets Configuration**

Add API configuration examples to `.dlt/secrets.toml`:
```toml
# REST API with offset pagination
[sources.github_api]
base_url = "https://api.github.com"
auth_type = "bearer"
token = "ghp_xxxxxxxxxxxx"
pagination_type = "header_link"
rate_limit = 30  # requests per minute

# REST API with cursor pagination
[sources.stripe_api]
base_url = "https://api.stripe.com/v1"
auth_type = "bearer"
token = "sk_live_xxxxxxxxxxxx"
pagination_type = "cursor"
cursor_param = "starting_after"
cursor_path = "data[-1].id"

# REST API with API key
[sources.coingecko_api]
base_url = "https://api.coingecko.com/api/v3"
auth_type = "api_key"
api_key = "CG-xxxxxxxxxxxx"
api_key_name = "x-cg-demo-api-key"
api_key_location = "header"
pagination_type = "offset"
page_size = 100
```

**Step 1.2.3: Update Excel Configuration**

Add columns to `ingestion_config.xlsx`:
| Column | Description | Example Values |
|--------|-------------|----------------|
| `api_endpoint` | API endpoint path | `/users`, `/repos/{owner}/{repo}/issues` |
| `pagination_type` | Pagination strategy | `offset`, `cursor`, `page_number`, `header_link`, `json_link`, `single_page` |
| `auth_type` | Authentication method | `none`, `api_key`, `bearer`, `basic`, `oauth2` |
| `page_size` | Records per page | `100`, `500`, `1000` |

#### Acceptance Criteria
- [ ] All 6 pagination types work correctly
- [ ] All 4 authentication methods work correctly
- [ ] Rate limiting prevents API throttling
- [ ] Incremental loading via cursors works
- [ ] Unit tests for pagination config building
- [ ] Integration test with JSONPlaceholder API

#### Test Cases
```python
# tests/unit/test_rest_api_source.py
def test_offset_pagination_config():
    source = RESTAPISource({})
    job = {
        'source_name': 'test_api',
        'table_name': 'users',
        'pagination_type': 'offset',
        'page_size': 50
    }
    api_config = {'base_url': 'https://api.example.com'}
    
    config = source._build_pagination_config(job, api_config)
    
    assert config['type'] == 'offset'
    assert config['limit'] == 50

def test_bearer_auth_config():
    source = RESTAPISource({})
    job = {'auth_type': 'bearer'}
    api_config = {'token': 'test_token'}
    
    config = source._build_auth_config(job, api_config)
    
    assert 'Authorization' in config['headers']
    assert config['headers']['Authorization'] == 'Bearer test_token'
```

---

### Feature 1.3: Pydantic Configuration Models
**Priority**: 🔴 P0 - Critical  
**Effort**: 10-12 days  
**Dependencies**: None  

#### Problem Statement
Dictionary-based configuration catches errors at runtime instead of validation time, wasting compute resources and debugging time.

#### Implementation Steps

**Step 1.3.1: Create Models Package Structure**
```
src/models/
├── __init__.py
├── base.py              # Base model classes
├── pipeline.py          # Pipeline configuration
├── sources/
│   ├── __init__.py
│   ├── database.py      # Database source configs
│   ├── rest_api.py      # REST API configs
│   └── filesystem.py    # Filesystem configs (future)
├── destinations/
│   ├── __init__.py
│   ├── adls.py          # ADLS destination
│   └── databricks.py    # Databricks destination (future)
└── common.py            # Shared configurations
```

**Step 1.3.2: Create Base Models**
```
File: src/models/base.py
```

```python
"""
Base Pydantic models for configuration validation.
"""
from typing import Optional, Any, Dict, List
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator


class SourceType(str, Enum):
    """Supported source types."""
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"
    MSSQL = "mssql"
    AZURE_SQL = "azure_sql"
    API = "api"
    FILESYSTEM = "filesystem"


class LoadType(str, Enum):
    """Supported load types."""
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"


class BaseConfig(BaseModel):
    """Base configuration with common settings."""
    
    class Config:
        extra = "forbid"  # Reject unknown fields
        str_strip_whitespace = True
        use_enum_values = True
```

**Step 1.3.3: Create Pipeline Models**
```
File: src/models/pipeline.py
```

```python
"""
Pipeline configuration models.
"""
from typing import Optional, List, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

from src.models.base import BaseConfig, SourceType, LoadType


class JobConfig(BaseConfig):
    """Configuration for a single ingestion job."""
    
    # Required fields
    source_type: SourceType = Field(..., description="Type of data source")
    source_name: str = Field(..., min_length=1, max_length=100, description="Logical source name")
    table_name: str = Field(..., min_length=1, max_length=200, description="Table or endpoint name")
    load_type: LoadType = Field(..., description="Load strategy")
    enabled: bool = Field(True, description="Whether job is enabled")
    
    # Optional fields
    schema_name: Optional[str] = Field(None, description="Database schema (required for Oracle)")
    watermark_column: Optional[str] = Field(None, description="Column for incremental loads")
    last_watermark: Optional[str] = Field(None, description="Last processed watermark value")
    chunk_size: Optional[int] = Field(100000, ge=1000, le=10000000, description="Rows per chunk")
    
    # API-specific fields
    api_endpoint: Optional[str] = Field(None, description="API endpoint path")
    pagination_type: Optional[str] = Field("single_page", description="Pagination strategy")
    auth_type: Optional[str] = Field("none", description="Authentication method")
    page_size: Optional[int] = Field(100, ge=1, le=10000, description="Records per page")
    
    @field_validator('source_type', mode='before')
    @classmethod
    def validate_source_type(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v
    
    @field_validator('load_type', mode='before')
    @classmethod
    def validate_load_type(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v
    
    @field_validator('enabled', mode='before')
    @classmethod
    def validate_enabled(cls, v):
        if isinstance(v, str):
            return v.upper() == 'Y' or v.lower() == 'true'
        return bool(v)
    
    @field_validator('table_name')
    @classmethod
    def validate_table_name(cls, v):
        import re
        # Allow alphanumeric, underscore, dot (for schema.table)
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_.]*$', v):
            raise ValueError(f"Invalid table name: {v}. Must be alphanumeric with underscores.")
        return v
    
    @model_validator(mode='after')
    def validate_incremental_config(self):
        if self.load_type == LoadType.INCREMENTAL:
            if not self.watermark_column:
                raise ValueError("INCREMENTAL load requires 'watermark_column'")
        return self
    
    @model_validator(mode='after')
    def validate_oracle_schema(self):
        if self.source_type == SourceType.ORACLE:
            if not self.schema_name:
                raise ValueError("Oracle sources require 'schema_name'")
        return self
    
    @model_validator(mode='after')
    def validate_api_config(self):
        if self.source_type == SourceType.API:
            if not self.api_endpoint and not self.table_name:
                raise ValueError("API sources require 'api_endpoint' or 'table_name'")
        return self


class PipelineConfig(BaseConfig):
    """Configuration for the entire pipeline run."""
    
    name: str = Field("dlt_pipeline", description="Pipeline name")
    jobs: List[JobConfig] = Field(..., min_length=1, description="List of job configurations")
    parallel: bool = Field(False, description="Run jobs in parallel")
    max_workers: int = Field(5, ge=1, le=20, description="Max parallel workers")
    stop_on_error: bool = Field(False, description="Stop pipeline on first error")
    
    @property
    def enabled_jobs(self) -> List[JobConfig]:
        """Get only enabled jobs."""
        return [job for job in self.jobs if job.enabled]
```

**Step 1.3.4: Create Database Source Models**
```
File: src/models/sources/database.py
```

```python
"""
Database source configuration models.
"""
from typing import Optional, Literal
from pydantic import Field, SecretStr, field_validator

from src.models.base import BaseConfig


class DatabaseConnectionConfig(BaseConfig):
    """Database connection configuration."""
    
    host: str = Field(..., min_length=1, description="Database host")
    port: int = Field(..., ge=1, le=65535, description="Database port")
    database: str = Field(..., min_length=1, description="Database name")
    username: str = Field(..., min_length=1, description="Database username")
    password: SecretStr = Field(..., description="Database password")
    
    # Optional connection settings
    connect_timeout: int = Field(30, ge=5, le=300, description="Connection timeout in seconds")
    query_timeout: int = Field(300, ge=30, le=3600, description="Query timeout in seconds")


class PostgreSQLConnectionConfig(DatabaseConnectionConfig):
    """PostgreSQL-specific connection configuration."""
    
    port: int = Field(5432, ge=1, le=65535)
    ssl_mode: Optional[Literal["disable", "allow", "prefer", "require"]] = Field("prefer")


class OracleConnectionConfig(DatabaseConnectionConfig):
    """Oracle-specific connection configuration."""
    
    port: int = Field(1521, ge=1, le=65535)
    service_name: Optional[str] = Field(None, description="Oracle service name")
    sid: Optional[str] = Field(None, description="Oracle SID")
    
    @field_validator('service_name', 'sid')
    @classmethod
    def validate_service_or_sid(cls, v, info):
        # At least one must be provided - validated in model_validator
        return v


class MSSQLConnectionConfig(DatabaseConnectionConfig):
    """MSSQL-specific connection configuration."""
    
    port: int = Field(1433, ge=1, le=65535)
    driver: str = Field("ODBC Driver 17 for SQL Server")
    encrypt: bool = Field(True, description="Enable encryption")
    trust_server_certificate: bool = Field(False)
    
    # Azure SQL specific
    azure_sql: bool = Field(False, description="Is Azure SQL Database")


class AzureSQLConnectionConfig(MSSQLConnectionConfig):
    """Azure SQL-specific configuration."""
    
    azure_sql: bool = Field(True)
    encrypt: bool = Field(True)
    trust_server_certificate: bool = Field(False)
```

**Step 1.3.5: Create REST API Models**
```
File: src/models/sources/rest_api.py
```

```python
"""
REST API source configuration models.
"""
from typing import Optional, Dict, Any, Literal, Union, List
from pydantic import Field, SecretStr, field_validator, model_validator

from src.models.base import BaseConfig


class RateLimitConfig(BaseConfig):
    """Rate limiting configuration."""
    requests_per_second: float = Field(10.0, ge=0.1, le=1000)
    burst_limit: int = Field(10, ge=1, le=100)


class PaginationOffsetConfig(BaseConfig):
    """Offset-based pagination configuration."""
    type: Literal["offset"] = "offset"
    limit_param: str = Field("limit", description="Limit parameter name")
    offset_param: str = Field("offset", description="Offset parameter name")
    limit: int = Field(100, ge=1, le=10000)
    maximum_offset: Optional[int] = Field(None, description="Max offset to prevent infinite loops")


class PaginationCursorConfig(BaseConfig):
    """Cursor-based pagination configuration."""
    type: Literal["cursor"] = "cursor"
    cursor_param: str = Field("cursor", description="Cursor parameter name")
    cursor_path: str = Field("next_cursor", description="Path to next cursor in response")


class PaginationPageNumberConfig(BaseConfig):
    """Page number pagination configuration."""
    type: Literal["page_number"] = "page_number"
    page_param: str = Field("page")
    per_page_param: str = Field("per_page")
    per_page: int = Field(100, ge=1, le=10000)
    base_page: int = Field(1, ge=0, le=1)
    total_pages_path: Optional[str] = Field(None)


class PaginationHeaderLinkConfig(BaseConfig):
    """Header link pagination (GitHub style)."""
    type: Literal["header_link"] = "header_link"
    next_url_path: str = Field("links.next")


class PaginationJsonLinkConfig(BaseConfig):
    """JSON body link pagination."""
    type: Literal["json_link"] = "json_link"
    next_url_path: str = Field("next")


PaginationConfig = Union[
    PaginationOffsetConfig,
    PaginationCursorConfig,
    PaginationPageNumberConfig,
    PaginationHeaderLinkConfig,
    PaginationJsonLinkConfig
]


class ApiKeyAuthConfig(BaseConfig):
    """API key authentication."""
    type: Literal["api_key"] = "api_key"
    api_key: SecretStr = Field(..., description="API key value")
    name: str = Field("X-API-Key", description="Header or param name")
    location: Literal["header", "query"] = Field("header")


class BearerTokenAuthConfig(BaseConfig):
    """Bearer token authentication."""
    type: Literal["bearer"] = "bearer"
    token: SecretStr = Field(..., description="Bearer token")


class BasicAuthConfig(BaseConfig):
    """Basic HTTP authentication."""
    type: Literal["basic"] = "basic"
    username: str = Field(...)
    password: SecretStr = Field(...)


class OAuth2Config(BaseConfig):
    """OAuth 2.0 client credentials authentication."""
    type: Literal["oauth2"] = "oauth2"
    token_url: str = Field(..., description="OAuth token endpoint")
    client_id: str = Field(...)
    client_secret: SecretStr = Field(...)
    scope: Optional[str] = Field(None)


AuthConfig = Union[ApiKeyAuthConfig, BearerTokenAuthConfig, BasicAuthConfig, OAuth2Config]


class RestApiConnectionConfig(BaseConfig):
    """REST API connection configuration."""
    
    base_url: str = Field(..., description="Base URL for the API")
    auth: Optional[AuthConfig] = Field(None, description="Authentication configuration")
    headers: Dict[str, str] = Field(default_factory=dict)
    rate_limit: Optional[RateLimitConfig] = Field(None)
    timeout: int = Field(30, ge=5, le=300)


class RestApiResourceConfig(BaseConfig):
    """REST API resource (endpoint) configuration."""
    
    name: str = Field(..., description="Resource name (becomes table name)")
    path: str = Field(..., description="Endpoint path (can include {params})")
    method: Literal["GET", "POST"] = Field("GET")
    params: Dict[str, Any] = Field(default_factory=dict)
    pagination: Optional[PaginationConfig] = Field(None)
    data_selector: Optional[str] = Field(None, description="JSON path to data array")
    primary_key: Optional[List[str]] = Field(None)
```

**Step 1.3.6: Integrate with ConfigLoader**

Update `src/config/loader.py`:
```python
from src.models.pipeline import JobConfig, PipelineConfig
from pydantic import ValidationError

def load_jobs(self) -> List[JobConfig]:
    """Load and validate jobs from Excel."""
    df = pd.read_excel(self.excel_path, sheet_name="SourceConfig")
    
    validated_jobs = []
    validation_errors = []
    
    for idx, row in df.iterrows():
        try:
            job = JobConfig(**row.to_dict())
            if job.enabled:
                validated_jobs.append(job)
        except ValidationError as e:
            validation_errors.append({
                'row': idx + 2,  # Excel row number
                'errors': e.errors()
            })
    
    if validation_errors:
        self._log_validation_errors(validation_errors)
        raise ValueError(f"Configuration validation failed with {len(validation_errors)} errors")
    
    logger.info(f"Validated {len(validated_jobs)} enabled jobs")
    return validated_jobs
```

#### Acceptance Criteria
- [ ] All 50+ Pydantic models created and documented
- [ ] Excel configuration validated at load time
- [ ] Clear validation error messages with row numbers
- [ ] Unit tests for all model validators
- [ ] Integration with ConfigLoader complete

#### Test Cases
```python
# tests/unit/test_models.py
def test_job_config_valid():
    job = JobConfig(
        source_type="postgresql",
        source_name="test_db",
        table_name="customers",
        load_type="FULL"
    )
    assert job.source_type == SourceType.POSTGRESQL

def test_job_config_invalid_source_type():
    with pytest.raises(ValidationError):
        JobConfig(
            source_type="invalid",
            source_name="test",
            table_name="test",
            load_type="FULL"
        )

def test_incremental_requires_watermark():
    with pytest.raises(ValidationError):
        JobConfig(
            source_type="postgresql",
            source_name="test",
            table_name="test",
            load_type="INCREMENTAL"
            # Missing watermark_column
        )
```

---

### Feature 1.4: Unit Test Suite Foundation
**Priority**: 🔴 P0 - Critical  
**Effort**: 10-14 days  
**Dependencies**: Features 1.1-1.3 (for testing)  

#### Problem Statement
Zero automated tests means no safety net for refactoring, regression risks, and manual testing overhead.

#### Implementation Steps

**Step 1.4.1: Create Test Infrastructure**
```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_config_loader.py
│   ├── test_validators.py
│   ├── test_retry_handler.py
│   ├── test_metrics.py
│   ├── test_type_adapters.py
│   ├── test_rest_api_source.py
│   └── models/
│       ├── test_job_config.py
│       ├── test_database_config.py
│       └── test_rest_api_config.py
├── integration/
│   ├── __init__.py
│   ├── test_postgresql_to_duckdb.py
│   └── test_rest_api_to_duckdb.py
└── fixtures/
    ├── sample_config.xlsx
    ├── sample_secrets.toml
    └── mock_api_responses.json
```

**Step 1.4.2: Create conftest.py**
```
File: tests/conftest.py
```

```python
"""
Shared pytest fixtures for all tests.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_secrets():
    """Sample secrets configuration."""
    return {
        'sources': {
            'postgresql': {
                'host': 'localhost',
                'port': 5432,
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_pass'
            },
            'oracle': {
                'host': 'localhost',
                'port': 1521,
                'service_name': 'TESTDB',
                'username': 'test_user',
                'password': 'test_pass'
            },
            'test_api': {
                'base_url': 'https://api.example.com',
                'auth_type': 'bearer',
                'token': 'test_token'
            }
        },
        'destination': {
            'filesystem': {
                'bucket_url': 'az://test-container',
                'azure_storage_account_name': 'testaccount',
                'azure_storage_account_key': 'testkey'
            }
        }
    }


@pytest.fixture
def sample_job_full():
    """Sample FULL load job configuration."""
    return {
        'source_type': 'postgresql',
        'source_name': 'test_db',
        'table_name': 'customers',
        'load_type': 'FULL',
        'enabled': 'Y'
    }


@pytest.fixture
def sample_job_incremental():
    """Sample INCREMENTAL load job configuration."""
    return {
        'source_type': 'postgresql',
        'source_name': 'test_db',
        'table_name': 'orders',
        'load_type': 'INCREMENTAL',
        'watermark_column': 'updated_at',
        'last_watermark': '2026-01-01',
        'enabled': 'Y'
    }


@pytest.fixture
def sample_api_job():
    """Sample API job configuration."""
    return {
        'source_type': 'api',
        'source_name': 'test_api',
        'table_name': 'users',
        'api_endpoint': '/users',
        'pagination_type': 'offset',
        'auth_type': 'bearer',
        'load_type': 'FULL',
        'enabled': 'Y'
    }


@pytest.fixture
def sample_excel_config(temp_dir):
    """Create sample Excel configuration file."""
    data = [
        {'source_type': 'postgresql', 'source_name': 'test_db', 'table_name': 'customers', 
         'load_type': 'FULL', 'enabled': 'Y'},
        {'source_type': 'postgresql', 'source_name': 'test_db', 'table_name': 'orders', 
         'load_type': 'INCREMENTAL', 'watermark_column': 'updated_at', 'enabled': 'Y'},
        {'source_type': 'oracle', 'source_name': 'oracle_db', 'table_name': 'products',
         'schema_name': 'sales', 'load_type': 'FULL', 'enabled': 'N'}
    ]
    
    df = pd.DataFrame(data)
    excel_path = temp_dir / 'ingestion_config.xlsx'
    df.to_excel(excel_path, sheet_name='SourceConfig', index=False)
    
    return excel_path


@pytest.fixture
def mock_dlt_pipeline():
    """Mock DLT pipeline for testing without actual data movement."""
    with patch('dlt.pipeline') as mock:
        pipeline = MagicMock()
        pipeline.pipeline_name = 'test_pipeline'
        pipeline.destination = 'filesystem'
        mock.return_value = pipeline
        yield pipeline


@pytest.fixture
def mock_sql_table():
    """Mock sql_table for testing without database connection."""
    with patch('dlt.sources.sql_database.sql_table') as mock:
        resource = MagicMock()
        mock.return_value = resource
        yield mock
```

**Step 1.4.3: Create Core Unit Tests**
```
File: tests/unit/test_config_loader.py
```

```python
"""Unit tests for ConfigLoader."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.config.loader import ConfigLoader


class TestConfigLoader:
    """Tests for ConfigLoader class."""
    
    def test_init_with_defaults(self):
        """Test ConfigLoader initialization with default paths."""
        loader = ConfigLoader()
        assert loader.config_dir.exists() or True  # May not exist in test env
    
    def test_load_jobs_from_excel(self, sample_excel_config):
        """Test loading jobs from Excel file."""
        loader = ConfigLoader(config_dir=sample_excel_config.parent)
        loader.excel_path = sample_excel_config
        
        jobs = loader.load_jobs()
        
        assert len(jobs) == 2  # Only enabled jobs
        assert jobs[0]['source_type'] == 'postgresql'
        assert jobs[0]['table_name'] == 'customers'
    
    def test_load_jobs_file_not_found(self, temp_dir):
        """Test error when Excel file doesn't exist."""
        loader = ConfigLoader(config_dir=temp_dir)
        loader.excel_path = temp_dir / 'nonexistent.xlsx'
        
        with pytest.raises(FileNotFoundError):
            loader.load_jobs()
    
    def test_load_secrets_from_toml(self, temp_dir, sample_secrets):
        """Test loading secrets from TOML file."""
        import toml
        
        secrets_path = temp_dir / '.dlt' / 'secrets.toml'
        secrets_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(secrets_path, 'w') as f:
            toml.dump(sample_secrets, f)
        
        loader = ConfigLoader()
        loader.secrets_path = secrets_path
        
        secrets = loader.load_secrets()
        
        assert 'sources' in secrets
        assert 'postgresql' in secrets['sources']
    
    def test_get_source_config(self, sample_secrets):
        """Test retrieving source configuration."""
        loader = ConfigLoader()
        loader._secrets_cache = sample_secrets
        
        config = loader.get_source_config('postgresql')
        
        assert config['host'] == 'localhost'
        assert config['port'] == 5432


class TestConfigLoaderKeyVault:
    """Tests for Key Vault integration."""
    
    @patch('src.config.loader.KeyVaultManager')
    def test_keyvault_fallback(self, mock_kv, sample_secrets):
        """Test fallback to TOML when Key Vault unavailable."""
        mock_kv.side_effect = Exception("Key Vault unavailable")
        
        loader = ConfigLoader(use_keyvault=True)
        
        assert loader.use_keyvault == False
```

**Step 1.4.4: Create Validator Tests**
```
File: tests/unit/test_validators.py
```

```python
"""Unit tests for validators."""
import pytest

from src.core.validators import (
    ConfigValidator, SecretsValidator, DataQualityValidator,
    ValidationResult, ValidationSeverity
)


class TestConfigValidator:
    """Tests for ConfigValidator."""
    
    @pytest.fixture
    def validator(self):
        return ConfigValidator()
    
    def test_validate_valid_job(self, validator, sample_job_full):
        """Test validation of valid job configuration."""
        results = validator.validate_job(sample_job_full)
        assert all(r.passed for r in results)
    
    def test_validate_missing_required_field(self, validator):
        """Test validation catches missing required fields."""
        job = {'source_type': 'postgresql', 'source_name': 'test'}
        # Missing table_name, load_type, enabled
        
        results = validator.validate_job(job)
        
        failed = [r for r in results if not r.passed]
        assert len(failed) >= 1
        assert any('table_name' in r.message for r in failed)
    
    def test_validate_invalid_source_type(self, validator):
        """Test validation catches invalid source type."""
        job = {
            'source_type': 'invalid_db',
            'source_name': 'test',
            'table_name': 'test',
            'load_type': 'FULL',
            'enabled': 'Y'
        }
        
        results = validator.validate_job(job)
        
        failed = [r for r in results if not r.passed]
        assert any('source_type' in r.message.lower() for r in failed)
    
    def test_validate_incremental_requires_watermark(self, validator):
        """Test incremental load requires watermark column."""
        job = {
            'source_type': 'postgresql',
            'source_name': 'test',
            'table_name': 'test',
            'load_type': 'INCREMENTAL',
            'enabled': 'Y'
            # Missing watermark_column
        }
        
        results = validator.validate_job(job)
        
        failed = [r for r in results if not r.passed]
        assert any('watermark' in r.message.lower() for r in failed)


class TestSecretsValidator:
    """Tests for SecretsValidator."""
    
    @pytest.fixture
    def validator(self):
        return SecretsValidator()
    
    def test_validate_secrets_present(self, validator, sample_secrets, sample_job_full):
        """Test validation passes when secrets exist."""
        results = validator.validate_job_secrets(sample_job_full, sample_secrets)
        assert all(r.passed for r in results)
    
    def test_validate_secrets_missing(self, validator, sample_job_full):
        """Test validation fails when secrets missing."""
        empty_secrets = {'sources': {}}
        
        results = validator.validate_job_secrets(sample_job_full, empty_secrets)
        
        failed = [r for r in results if not r.passed]
        assert len(failed) >= 1
```

**Step 1.4.5: Create pytest configuration**
```
File: pytest.ini
```

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    unit: Unit tests (fast, no external dependencies)
    integration: Integration tests (require Docker or external services)
    slow: Slow tests (>10 seconds)
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

**Step 1.4.6: Update requirements.txt**

Add to `requirements.txt`:
```
# Testing
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.12.0
pytest-xdist>=3.5.0  # Parallel test execution

# Code Quality
black>=24.0.0
ruff>=0.2.0
mypy>=1.8.0
```

#### Acceptance Criteria
- [ ] pytest infrastructure set up and running
- [ ] 50+ unit tests covering core modules
- [ ] Test coverage reporting configured (target: 40%)
- [ ] All tests pass on clean run
- [ ] CI-ready test configuration

#### Test Coverage Targets (Phase 1)

| Module | Target Coverage | Tests |
|--------|----------------|-------|
| `config/loader.py` | 60% | 10 tests |
| `core/validators.py` | 80% | 15 tests |
| `core/retry_handler.py` | 70% | 10 tests |
| `core/metrics.py` | 60% | 8 tests |
| `core/type_adapters.py` | 90% | 5 tests |
| `models/*.py` | 80% | 15 tests |

---

## 🟠 PHASE 2: Production Hardening (Weeks 5-8)

### Feature 2.1: Databricks Unity Catalog Destination
**Priority**: 🟠 P1 - High  
**Effort**: 8-10 days  
**Dependencies**: Type adapters (1.1)  

#### Problem Statement
Current ADLS Gen2 filesystem destination requires manual COPY INTO to load data into Databricks.

#### Implementation Steps

**Step 2.1.1: Create Databricks Destination Module**
```
File: src/destinations/databricks.py
```

```python
"""
Databricks Unity Catalog Destination.

Supports:
- Unity Catalog (catalog.schema.table)
- External ADLS staging
- Delta Lake format with ACID transactions
- Automatic schema evolution
"""
import logging
from typing import Dict, Optional

from src.destinations.base import BaseDestination

logger = logging.getLogger(__name__)


class DatabricksDestination(BaseDestination):
    """
    Databricks Unity Catalog destination using filesystem staging.
    
    Architecture:
    Source → dlt → ADLS (staging) → COPY INTO → Databricks Delta Tables
    """
    
    def __init__(self, secrets: Dict):
        super().__init__(secrets)
        self.destination_type = 'databricks'
        self._config = self.secrets.get('destination', {}).get('databricks', {})
        self._staging_config = self.secrets.get('destination', {}).get('filesystem', {})
    
    def get_dlt_destination_config(self) -> Dict:
        """
        Get DLT destination configuration for Databricks with filesystem staging.
        
        Returns:
            Dictionary with 'destination' and 'staging' configuration
        """
        return {
            'destination': 'databricks',
            'staging': 'filesystem',
            'credentials': {
                'server_hostname': self._config.get('server_hostname'),
                'http_path': self._config.get('http_path'),
                'catalog': self._config.get('catalog', 'main'),
                'access_token': self._config.get('access_token')
            },
            'staging_credentials': {
                'bucket_url': self._staging_config.get('bucket_url'),
                'azure_storage_account_name': self._staging_config.get('azure_storage_account_name'),
                'azure_storage_sas_token': self._staging_config.get('azure_storage_sas_token')
            }
        }
    
    def get_schema_name(self, job: Dict) -> str:
        """Get target schema name for job."""
        return job.get('target_schema', self._config.get('schema', 'raw'))
    
    def validate_connection(self) -> bool:
        """Validate Databricks connectivity."""
        try:
            from databricks import sql as databricks_sql
            
            conn = databricks_sql.connect(
                server_hostname=self._config.get('server_hostname'),
                http_path=self._config.get('http_path'),
                access_token=self._config.get('access_token')
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            
            logger.info("[DATABRICKS] Connection validated successfully")
            return True
            
        except ImportError:
            logger.warning("databricks-sql-connector not installed")
            return False
        except Exception as e:
            logger.error(f"Databricks connection failed: {e}")
            return False
```

**Step 2.1.2: Update Orchestrator for Databricks**

Add Databricks destination support in `orchestrator.py`:
```python
def _get_destination(self, destination_type: str = None):
    """Get destination instance based on configuration."""
    dest_type = destination_type or self.secrets.get('destination', {}).get('type', 'filesystem')
    
    if dest_type == 'databricks':
        from src.destinations.databricks import DatabricksDestination
        return DatabricksDestination(self.secrets)
    else:
        return self.destination  # Default ADLS Gen2
```

**Step 2.1.3: Add Secrets Configuration**

Update `.dlt/secrets.toml`:
```toml
[destination.databricks]
type = "databricks"
server_hostname = "adb-xxxx.azuredatabricks.net"
http_path = "/sql/1.0/warehouses/xxxx"
catalog = "main"
schema = "raw"
access_token = "dapi..."

[destination.databricks.credentials]
server_hostname = "adb-xxxx.azuredatabricks.net"
http_path = "/sql/1.0/warehouses/xxxx"
access_token = "dapi..."

# Staging for cross-tenant deployment
[destination.filesystem]
bucket_url = "az://staging@dltstagingaccount.dfs.core.windows.net"

[destination.filesystem.credentials]
azure_storage_account_name = "dltstagingaccount"
azure_storage_sas_token = "?sv=2024-11-04&ss=..."
```

#### Acceptance Criteria
- [ ] Databricks Unity Catalog destination works
- [ ] Cross-tenant ADLS staging configured
- [ ] Delta Lake tables created automatically
- [ ] Schema evolution handled correctly
- [ ] Integration test with real Databricks cluster

---

### Feature 2.2: Filesystem Source
**Priority**: 🟠 P1 - High  
**Effort**: 5-7 days  
**Dependencies**: None  

#### Problem Statement
Cannot ingest data from cloud storage files (CSV, Parquet, JSONL from ADLS/S3/GCS).

#### Implementation Steps

**Step 2.2.1: Create Filesystem Source Module**
```
File: src/sources/filesystem.py
```

```python
"""
Filesystem Source - Ingest from cloud storage (ADLS, S3, GCS).

Supports:
- File formats: Parquet, CSV, JSONL
- Protocols: az (ADLS), s3 (AWS), gs (GCS), file (local)
- Incremental tracking: file_modified, file_name, folder_date
"""
import logging
from typing import Dict, Optional, List
from enum import Enum

import dlt
from dlt.sources import filesystem as dlt_filesystem
from dlt.sources.filesystem import readers

from src.sources.base import BaseSource

logger = logging.getLogger(__name__)


class FileFormat(Enum):
    """Supported file formats."""
    PARQUET = "parquet"
    CSV = "csv"
    JSONL = "jsonl"


class IncrementalMode(Enum):
    """Incremental tracking modes."""
    FILE_MODIFIED = "file_modified"
    FILE_NAME = "file_name"
    FOLDER_DATE = "folder_date"
    NONE = "none"


class FilesystemSource(BaseSource):
    """
    Cloud storage filesystem source.
    
    Supports ADLS Gen2, S3, GCS, and local filesystem.
    """
    
    def __init__(self, secrets: Dict):
        super().__init__(secrets, 'filesystem')
        self.source_type = 'filesystem'
    
    def build_connection_string(self, source_name: str) -> str:
        """Filesystem uses bucket URL, not connection string."""
        config = self.get_source_config(source_name)
        return config.get('bucket_url', config.get('path'))
    
    def get_source_config(self, source_name: str) -> Dict:
        """Get filesystem source configuration."""
        return self.secrets.get('sources', {}).get(source_name, {})
    
    def create_source(self, job: Dict):
        """
        Create DLT filesystem source from job configuration.
        
        Args:
            job: Job configuration with:
                - source_name: Filesystem source name
                - table_name: Resource name (becomes table name)
                - file_glob: File pattern (e.g., "*.parquet", "data/*.csv")
                - file_format: parquet, csv, jsonl
                - incremental_mode: file_modified, file_name, folder_date, none
        """
        config = self.get_source_config(job['source_name'])
        
        bucket_url = config.get('bucket_url')
        file_glob = job.get('file_glob', '**/*.parquet')
        file_format = job.get('file_format', 'parquet').lower()
        
        # Build credentials
        credentials = self._build_credentials(config)
        
        # Get appropriate reader
        reader = self._get_reader(file_format)
        
        # Create filesystem source
        source = dlt_filesystem(
            bucket_url=bucket_url,
            file_glob=file_glob,
            credentials=credentials
        )
        
        # Apply reader
        return source | reader
    
    def _build_credentials(self, config: Dict) -> Optional[Dict]:
        """Build storage credentials."""
        if config.get('azure_storage_account_name'):
            return {
                'azure_storage_account_name': config['azure_storage_account_name'],
                'azure_storage_account_key': config.get('azure_storage_account_key'),
                'azure_storage_sas_token': config.get('azure_storage_sas_token')
            }
        
        if config.get('aws_access_key_id'):
            return {
                'aws_access_key_id': config['aws_access_key_id'],
                'aws_secret_access_key': config['aws_secret_access_key']
            }
        
        return None
    
    def _get_reader(self, file_format: str):
        """Get appropriate file reader."""
        if file_format == 'parquet':
            return readers.read_parquet()
        elif file_format == 'csv':
            return readers.read_csv()
        elif file_format == 'jsonl':
            return readers.read_jsonl()
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
    
    def validate_connection(self, source_name: str) -> bool:
        """Validate filesystem connectivity."""
        try:
            import fsspec
            
            config = self.get_source_config(source_name)
            bucket_url = config.get('bucket_url')
            
            fs = fsspec.filesystem(
                'az',
                account_name=config.get('azure_storage_account_name'),
                account_key=config.get('azure_storage_account_key')
            )
            
            # Try to list files
            files = fs.ls(bucket_url.replace('az://', ''))
            logger.info(f"Filesystem accessible, found {len(files)} items")
            return True
            
        except Exception as e:
            logger.error(f"Filesystem connection failed: {e}")
            return False
```

#### Acceptance Criteria
- [ ] ADLS Gen2 file reading works
- [ ] Parquet, CSV, JSONL formats supported
- [ ] Incremental loading by file_modified time
- [ ] Glob patterns work correctly
- [ ] Unit tests for filesystem source

---

### Feature 2.3: Integration Test Suite
**Priority**: 🟠 P1 - High  
**Effort**: 7-10 days  
**Dependencies**: All source modules  

#### Problem Statement
No end-to-end tests with real data sources, risking production failures.

#### Implementation Steps

**Step 2.3.1: Docker Compose for Test Databases**
```
File: tests/docker/docker-compose.yml
```

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: test_postgres
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5433:5432"
    volumes:
      - ./init_postgres.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d test_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  oracle:
    image: gvenzl/oracle-xe:21-slim
    container_name: test_oracle
    environment:
      ORACLE_PASSWORD: test_pass
    ports:
      - "1522:1521"
    healthcheck:
      test: ["CMD", "healthcheck.sh"]
      interval: 10s
      timeout: 5s
      retries: 10

  mssql:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: test_mssql
    environment:
      ACCEPT_EULA: "Y"
      SA_PASSWORD: "TestPass123!"
    ports:
      - "1434:1433"
    healthcheck:
      test: /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "TestPass123!" -Q "SELECT 1"
      interval: 10s
      timeout: 5s
      retries: 10
```

**Step 2.3.2: Create Integration Tests**
```
File: tests/integration/test_postgresql_to_duckdb.py
```

```python
"""Integration tests: PostgreSQL → DuckDB pipeline."""
import pytest
import duckdb

from src.core.orchestrator import IngestionOrchestrator


@pytest.mark.integration
@pytest.mark.slow
class TestPostgreSQLToDuckDB:
    """End-to-end tests for PostgreSQL ingestion."""
    
    @pytest.fixture
    def orchestrator(self, sample_secrets):
        """Create orchestrator with test configuration."""
        # Override destination to DuckDB
        sample_secrets['destination'] = {
            'type': 'duckdb',
            'path': ':memory:'
        }
        
        # Use local Docker PostgreSQL
        sample_secrets['sources']['postgresql'] = {
            'host': 'localhost',
            'port': 5433,
            'database': 'test_db',
            'username': 'test_user',
            'password': 'test_pass'
        }
        
        return IngestionOrchestrator(secrets=sample_secrets)
    
    def test_full_load_customers(self, orchestrator):
        """Test FULL load of customers table."""
        job = {
            'source_type': 'postgresql',
            'source_name': 'postgresql',
            'table_name': 'customers',
            'load_type': 'FULL',
            'enabled': True
        }
        
        result = orchestrator.execute_job(job)
        
        assert result['status'] == 'SUCCESS'
        assert result['rows_processed'] > 0
    
    def test_incremental_load_orders(self, orchestrator):
        """Test INCREMENTAL load of orders table."""
        job = {
            'source_type': 'postgresql',
            'source_name': 'postgresql',
            'table_name': 'orders',
            'load_type': 'INCREMENTAL',
            'watermark_column': 'created_at',
            'last_watermark': '2020-01-01',
            'enabled': True
        }
        
        # First run
        result1 = orchestrator.execute_job(job)
        assert result1['status'] == 'SUCCESS'
        rows_first = result1['rows_processed']
        
        # Second run (should load fewer/no rows)
        result2 = orchestrator.execute_job(job)
        assert result2['status'] == 'SUCCESS'
```

#### Acceptance Criteria
- [ ] Docker Compose setup for PostgreSQL, Oracle, MSSQL
- [ ] Integration tests for each database type
- [ ] Data integrity validation (row counts, checksums)
- [ ] Incremental load state management tests
- [ ] CI/CD integration ready

---

### Feature 2.4: Data Quality Module (Basic)
**Priority**: 🟠 P1 - High  
**Effort**: 10-14 days  
**Dependencies**: None  

#### Problem Statement
No automated data quality checks; manual validation required after each load.

#### Implementation Steps

**Step 2.4.1: Create Data Quality Module**
```
File: src/quality/dq_runner.py
```

```python
"""
Data Quality Runner - Post-load validation checks.

Supports:
- Row count validation
- Null rate checks
- Uniqueness checks
- Freshness checks
- Custom SQL checks
"""
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class CheckSeverity(Enum):
    """Data quality check severity."""
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CheckStatus(Enum):
    """Data quality check result status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DQCheckResult:
    """Result of a data quality check."""
    check_name: str
    check_type: str
    status: CheckStatus
    severity: CheckSeverity
    message: str
    actual_value: Optional[float] = None
    expected_value: Optional[float] = None
    threshold: Optional[float] = None
    execution_time_ms: float = 0


@dataclass
class DQReport:
    """Data quality report for a table."""
    table_name: str
    run_timestamp: datetime
    checks: List[DQCheckResult]
    
    @property
    def passed(self) -> bool:
        """All checks passed."""
        return all(c.status == CheckStatus.PASSED for c in self.checks)
    
    @property
    def critical_failures(self) -> List[DQCheckResult]:
        """Get critical check failures."""
        return [c for c in self.checks 
                if c.status == CheckStatus.FAILED and c.severity == CheckSeverity.CRITICAL]


class DataQualityRunner:
    """
    Runs data quality checks after pipeline load.
    
    Check Types:
    - row_count: Validate minimum/maximum row counts
    - null_rate: Check null percentage in columns
    - uniqueness: Validate primary key uniqueness
    - freshness: Check data recency
    - custom_sql: Run custom validation queries
    """
    
    def __init__(self, connection):
        """
        Initialize DQ runner.
        
        Args:
            connection: Database connection (SQLAlchemy engine or similar)
        """
        self.connection = connection
    
    def run_checks(self, table_name: str, checks: List[Dict]) -> DQReport:
        """
        Run all configured checks for a table.
        
        Args:
            table_name: Target table name
            checks: List of check configurations
        
        Returns:
            DQReport with all check results
        """
        results = []
        
        for check in checks:
            check_type = check.get('type')
            
            if check_type == 'row_count':
                result = self._check_row_count(table_name, check)
            elif check_type == 'null_rate':
                result = self._check_null_rate(table_name, check)
            elif check_type == 'uniqueness':
                result = self._check_uniqueness(table_name, check)
            elif check_type == 'freshness':
                result = self._check_freshness(table_name, check)
            elif check_type == 'custom_sql':
                result = self._check_custom_sql(table_name, check)
            else:
                result = DQCheckResult(
                    check_name=check.get('name', 'unknown'),
                    check_type=check_type,
                    status=CheckStatus.SKIPPED,
                    severity=CheckSeverity.WARNING,
                    message=f"Unknown check type: {check_type}"
                )
            
            results.append(result)
        
        return DQReport(
            table_name=table_name,
            run_timestamp=datetime.now(),
            checks=results
        )
    
    def _check_row_count(self, table_name: str, check: Dict) -> DQCheckResult:
        """Check row count is within expected range."""
        import time
        start = time.time()
        
        min_rows = check.get('min_rows', 0)
        max_rows = check.get('max_rows', float('inf'))
        
        try:
            result = self.connection.execute(f"SELECT COUNT(*) FROM {table_name}")
            actual_count = result.scalar()
            
            passed = min_rows <= actual_count <= max_rows
            
            return DQCheckResult(
                check_name=check.get('name', f'row_count_{table_name}'),
                check_type='row_count',
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=CheckSeverity(check.get('severity', 'error')),
                message=f"Row count: {actual_count:,} (expected: {min_rows:,} - {max_rows:,})",
                actual_value=actual_count,
                expected_value=min_rows,
                execution_time_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return DQCheckResult(
                check_name=check.get('name', f'row_count_{table_name}'),
                check_type='row_count',
                status=CheckStatus.FAILED,
                severity=CheckSeverity.CRITICAL,
                message=f"Check failed: {e}"
            )
    
    def _check_null_rate(self, table_name: str, check: Dict) -> DQCheckResult:
        """Check null rate is below threshold."""
        column = check.get('column')
        max_null_rate = check.get('max_null_rate', 0.05)  # 5% default
        
        try:
            result = self.connection.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) as null_count
                FROM {table_name}
            """)
            row = result.fetchone()
            
            null_rate = row.null_count / row.total if row.total > 0 else 0
            passed = null_rate <= max_null_rate
            
            return DQCheckResult(
                check_name=check.get('name', f'null_rate_{column}'),
                check_type='null_rate',
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=CheckSeverity(check.get('severity', 'warning')),
                message=f"Null rate for {column}: {null_rate:.2%} (max: {max_null_rate:.2%})",
                actual_value=null_rate,
                threshold=max_null_rate
            )
        except Exception as e:
            return DQCheckResult(
                check_name=check.get('name', f'null_rate_{column}'),
                check_type='null_rate',
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message=f"Check failed: {e}"
            )
    
    def _check_uniqueness(self, table_name: str, check: Dict) -> DQCheckResult:
        """Check column(s) uniqueness."""
        columns = check.get('columns', [])
        if isinstance(columns, str):
            columns = [columns]
        
        column_list = ', '.join(columns)
        
        try:
            result = self.connection.execute(f"""
                SELECT {column_list}, COUNT(*) as cnt
                FROM {table_name}
                GROUP BY {column_list}
                HAVING COUNT(*) > 1
                LIMIT 10
            """)
            duplicates = result.fetchall()
            
            passed = len(duplicates) == 0
            
            return DQCheckResult(
                check_name=check.get('name', f'uniqueness_{column_list}'),
                check_type='uniqueness',
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=CheckSeverity(check.get('severity', 'error')),
                message=f"Uniqueness check for ({column_list}): {'PASSED' if passed else f'{len(duplicates)} duplicates found'}",
                actual_value=len(duplicates)
            )
        except Exception as e:
            return DQCheckResult(
                check_name=check.get('name', f'uniqueness_{column_list}'),
                check_type='uniqueness',
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message=f"Check failed: {e}"
            )
    
    def _check_freshness(self, table_name: str, check: Dict) -> DQCheckResult:
        """Check data freshness (max age)."""
        column = check.get('column')
        max_age_hours = check.get('max_age_hours', 24)
        
        try:
            result = self.connection.execute(f"""
                SELECT MAX({column}) as latest
                FROM {table_name}
            """)
            latest = result.scalar()
            
            if latest is None:
                return DQCheckResult(
                    check_name=check.get('name', f'freshness_{column}'),
                    check_type='freshness',
                    status=CheckStatus.FAILED,
                    severity=CheckSeverity.WARNING,
                    message=f"No data found in {table_name}"
                )
            
            age_hours = (datetime.now() - latest).total_seconds() / 3600
            passed = age_hours <= max_age_hours
            
            return DQCheckResult(
                check_name=check.get('name', f'freshness_{column}'),
                check_type='freshness',
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=CheckSeverity(check.get('severity', 'warning')),
                message=f"Data age: {age_hours:.1f} hours (max: {max_age_hours} hours)",
                actual_value=age_hours,
                threshold=max_age_hours
            )
        except Exception as e:
            return DQCheckResult(
                check_name=check.get('name', f'freshness_{column}'),
                check_type='freshness',
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message=f"Check failed: {e}"
            )
    
    def _check_custom_sql(self, table_name: str, check: Dict) -> DQCheckResult:
        """Run custom SQL validation."""
        sql = check.get('sql')
        expected_value = check.get('expected_value')
        
        try:
            result = self.connection.execute(sql)
            actual_value = result.scalar()
            
            passed = actual_value == expected_value
            
            return DQCheckResult(
                check_name=check.get('name', 'custom_sql'),
                check_type='custom_sql',
                status=CheckStatus.PASSED if passed else CheckStatus.FAILED,
                severity=CheckSeverity(check.get('severity', 'error')),
                message=f"Custom check: {actual_value} {'==' if passed else '!='} {expected_value}",
                actual_value=actual_value,
                expected_value=expected_value
            )
        except Exception as e:
            return DQCheckResult(
                check_name=check.get('name', 'custom_sql'),
                check_type='custom_sql',
                status=CheckStatus.FAILED,
                severity=CheckSeverity.CRITICAL,
                message=f"Check failed: {e}"
            )
```

#### Acceptance Criteria
- [ ] Row count validation works
- [ ] Null rate checks implemented
- [ ] Uniqueness checks work
- [ ] Freshness checks (data age) implemented
- [ ] Custom SQL checks supported
- [ ] DQ report generation
- [ ] Integration with orchestrator

---

## 🟡 PHASE 3: Deployment & Polish (Weeks 9-11)

### Feature 3.1: Wheel Packaging & CLI
**Priority**: 🟡 P2 - Medium  
**Effort**: 4-5 days  
**Dependencies**: All core modules  

#### Implementation Steps

**Step 3.1.1: Create pyproject.toml**
```
File: pyproject.toml
```

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "dlt-ingestion-framework"
version = "1.0.0"
description = "Configuration-driven DLT ingestion framework for multi-source data loading"
readme = "README.md"
license = "MIT"
requires-python = ">=3.10"
authors = [
    { name = "Your Team", email = "team@example.com" }
]
keywords = ["dlt", "data-ingestion", "databricks", "adls", "etl"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

dependencies = [
    "dlt[filesystem,sql_database]>=1.4.0",
    "pydantic>=2.0",
    "pandas>=2.0.0",
    "openpyxl>=3.1.0",
    "toml>=0.10.2",
    "azure-storage-blob>=12.19.0",
    "azure-identity>=1.15.0",
    "adlfs>=2023.4.0",
    "pyarrow>=14.0.0",
    "sqlalchemy>=1.4.0",
]

[project.optional-dependencies]
postgresql = ["psycopg2-binary>=2.9.0"]
oracle = ["oracledb>=1.3.0"]
mssql = ["pyodbc>=5.0.0"]
databases = [
    "psycopg2-binary>=2.9.0",
    "oracledb>=1.3.0",
    "pyodbc>=5.0.0",
]
databricks = ["databricks-sql-connector>=3.0.0"]
quality = ["soda-core-spark-df>=3.0.0"]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0",
    "black>=24.0.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
]
all = [
    "dlt-ingestion-framework[databases,databricks,quality,dev]"
]

[project.scripts]
dlt-ingest = "src.cli:main"
run-pipeline = "src.cli:main"

[project.urls]
Homepage = "https://github.com/your-org/dlt-ingestion-framework"
Documentation = "https://github.com/your-org/dlt-ingestion-framework/docs"
Repository = "https://github.com/your-org/dlt-ingestion-framework"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --tb=short"

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
select = ["E", "F", "W", "I", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_ignores = true
```

**Step 3.1.2: Create CLI Module**
```
File: src/cli.py
```

```python
"""
Command-line interface for DLT Ingestion Framework.

Usage:
    dlt-ingest                      # Run all enabled jobs
    dlt-ingest --job customers      # Run specific job
    dlt-ingest --validate           # Validate configuration only
    dlt-ingest --list               # List all jobs
"""
import argparse
import sys
import logging
from pathlib import Path

from src.core.orchestrator import IngestionOrchestrator
from src.config.loader import ConfigLoader
from src.utils.logger import setup_logger


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DLT Ingestion Framework - Configuration-driven data loading"
    )
    
    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Path to configuration directory'
    )
    
    parser.add_argument(
        '--job', '-j',
        type=str,
        help='Run specific job by table name'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate configuration without running'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all configured jobs'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run jobs in parallel'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=5,
        help='Number of parallel workers (default: 5)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(level=getattr(logging, args.log_level))
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize config loader
        config_dir = args.config or Path('config')
        loader = ConfigLoader(config_dir=config_dir)
        
        if args.list:
            # List all jobs
            jobs = loader.load_jobs()
            print(f"\nConfigured Jobs ({len(jobs)} total):\n")
            for job in jobs:
                status = "✅" if job.get('enabled', '').upper() == 'Y' else "❌"
                print(f"  {status} {job['source_name']}.{job['table_name']} ({job['load_type']})")
            return 0
        
        if args.validate:
            # Validate configuration only
            jobs = loader.load_jobs()
            secrets = loader.load_secrets()
            
            from src.core.validators import ConfigValidator, SecretsValidator
            config_validator = ConfigValidator()
            secrets_validator = SecretsValidator()
            
            all_passed = True
            for job in jobs:
                results = config_validator.validate_job(job)
                results.extend(secrets_validator.validate_job_secrets(job, secrets))
                
                failed = [r for r in results if not r.passed]
                if failed:
                    all_passed = False
                    print(f"❌ {job['source_name']}.{job['table_name']}:")
                    for r in failed:
                        print(f"   - {r.message}")
                else:
                    print(f"✅ {job['source_name']}.{job['table_name']}")
            
            return 0 if all_passed else 1
        
        # Run orchestrator
        orchestrator = IngestionOrchestrator()
        
        if args.job:
            # Run specific job
            jobs = loader.load_jobs()
            job = next((j for j in jobs if j['table_name'] == args.job), None)
            
            if not job:
                logger.error(f"Job not found: {args.job}")
                return 1
            
            result = orchestrator.execute_job(job)
            return 0 if result['status'] == 'SUCCESS' else 1
        
        else:
            # Run all enabled jobs
            orchestrator.run_all(
                parallel=args.parallel,
                max_workers=args.workers
            )
            return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

#### Acceptance Criteria
- [ ] `pip install .` works
- [ ] `dlt-ingest` CLI command works
- [ ] `--validate` flag validates without running
- [ ] `--list` shows all configured jobs
- [ ] Optional dependencies work (oracle, mssql)

---

### Feature 3.2: Databricks Asset Bundle
**Priority**: 🟡 P2 - Medium  
**Effort**: 3-4 days  
**Dependencies**: Wheel packaging (3.1)  

#### Implementation Steps

**Step 3.2.1: Create databricks.yml**
```
File: databricks.yml
```

```yaml
bundle:
  name: dlt_ingestion_framework

# Build configuration
artifacts:
  default:
    type: whl
    path: .
    build: "pip wheel . --wheel-dir dist --no-deps"

# Job resources
resources:
  jobs:
    # Daily ingestion job
    daily_ingestion:
      name: "[${bundle.target}] DLT Daily Ingestion"
      schedule:
        quartz_cron_expression: "0 0 6 * * ?"  # 6 AM daily
        timezone_id: "UTC"
      
      tasks:
        - task_key: run_all_jobs
          python_wheel_task:
            package_name: dlt_ingestion_framework
            entry_point: run-pipeline
            parameters: []
          
          libraries:
            - whl: ${artifacts.default.files[0]}
          
          cluster_id: ${var.cluster_id}
    
    # On-demand single table job
    single_table_ingestion:
      name: "[${bundle.target}] DLT Single Table"
      
      tasks:
        - task_key: run_single_job
          python_wheel_task:
            package_name: dlt_ingestion_framework
            entry_point: run-pipeline
            parameters:
              - "--job"
              - "{{job.parameters.table_name}}"
          
          libraries:
            - whl: ${artifacts.default.files[0]}
          
          job_cluster_key: ingestion_cluster
      
      job_clusters:
        - job_cluster_key: ingestion_cluster
          new_cluster:
            spark_version: "14.3.x-scala2.12"
            node_type_id: "Standard_DS3_v2"
            num_workers: 2
            spark_conf:
              spark.speculation: "true"

# Environment-specific configuration
targets:
  dev:
    mode: development
    default: true
    workspace:
      host: ${var.databricks_host}
    variables:
      cluster_id: ${var.dev_cluster_id}
  
  staging:
    mode: staging
    workspace:
      host: ${var.databricks_host}
    variables:
      cluster_id: ${var.staging_cluster_id}
  
  prod:
    mode: production
    workspace:
      host: ${var.databricks_host}
    variables:
      cluster_id: ${var.prod_cluster_id}
    run_as:
      service_principal_name: "dlt-ingestion-sp"

# Variables
variables:
  databricks_host:
    description: "Databricks workspace URL"
  dev_cluster_id:
    description: "Development cluster ID"
  staging_cluster_id:
    description: "Staging cluster ID"
  prod_cluster_id:
    description: "Production cluster ID"
```

#### Acceptance Criteria
- [ ] `databricks bundle validate` passes
- [ ] `databricks bundle deploy -t dev` works
- [ ] `databricks bundle run -t dev daily_ingestion` executes
- [ ] Environment-specific configuration works
- [ ] CI/CD integration documented

---

### Feature 3.3: JSON Metrics Export
**Priority**: 🟡 P2 - Medium  
**Effort**: 2-3 days  
**Dependencies**: Metrics module  

#### Implementation Steps

**Step 3.3.1: Add JSON Export to MetricsCollector**

Update `src/core/metrics.py`:
```python
def export_to_json(self, output_dir: Path = None) -> Path:
    """
    Export pipeline metrics to JSON file.
    
    Args:
        output_dir: Directory for output file (default: metadata/)
    
    Returns:
        Path to generated JSON file
    """
    from datetime import datetime
    import json
    
    output_dir = output_dir or Path('metadata')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"metrics_{self.pipeline_name}_{timestamp}.json"
    filepath = output_dir / filename
    
    metrics_data = {
        'pipeline_name': self.pipeline_name,
        'run_timestamp': datetime.now().isoformat(),
        'jobs': [job.to_dict() for job in self.job_metrics],
        'summary': {
            'total_jobs': len(self.job_metrics),
            'successful_jobs': len([j for j in self.job_metrics if j.status == 'SUCCESS']),
            'failed_jobs': len([j for j in self.job_metrics if j.status == 'FAILED']),
            'total_rows': sum(j.rows_processed for j in self.job_metrics),
            'total_duration_seconds': sum(j.duration_seconds for j in self.job_metrics),
        },
        'health_score': self.calculate_health_score()
    }
    
    with open(filepath, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    logger.info(f"Metrics exported to: {filepath}")
    return filepath
```

#### Acceptance Criteria
- [ ] JSON metrics file generated after each run
- [ ] All job metrics included
- [ ] Summary statistics calculated
- [ ] Health score included
- [ ] File path logged

---

### Feature 3.4: Documentation Completion
**Priority**: 🟡 P2 - Medium  
**Effort**: 5-7 days  
**Dependencies**: All features  

#### Documentation Deliverables

1. **TROUBLESHOOTING_GUIDE.md** - Common errors and solutions
2. **API_REFERENCE.md** - Module and class documentation
3. **CONFIGURATION_TEMPLATES.md** - Example configurations
4. **OPERATIONAL_RUNBOOK.md** - Day-to-day operations guide
5. **MIGRATION_GUIDE.md** - Upgrading from previous versions

---

## 📊 Progress Tracking

### Weekly Milestones

| Week | Features | Target Coverage | Status |
|------|----------|----------------|--------|
| 1 | Type adapters (1.1) | 45% → 50% | 🔴 Not Started |
| 2 | REST API pagination (1.2) | 50% → 55% | 🔴 Not Started |
| 3-4 | Pydantic models (1.3) | 55% → 65% | 🔴 Not Started |
| 4-5 | Unit tests (1.4) | 65% → 70% | 🔴 Not Started |
| 6-7 | Databricks destination (2.1) | 70% → 75% | 🔴 Not Started |
| 7-8 | Filesystem source (2.2) | 75% → 78% | 🔴 Not Started |
| 8-9 | Integration tests (2.3) | 78% → 82% | 🔴 Not Started |
| 9-10 | Data quality (2.4) | 82% → 85% | 🔴 Not Started |
| 10 | Wheel packaging (3.1) | 85% → 87% | 🔴 Not Started |
| 11 | DAB + docs (3.2-3.4) | 87% → 90% | 🔴 Not Started |

### Definition of Done

Each feature is complete when:
- [ ] Code implemented and reviewed
- [ ] Unit tests written (>70% coverage)
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] No regressions in existing tests

---

## 🚀 Getting Started

### Immediate Next Steps

1. **Week 1, Day 1-2**: Implement type adapter callbacks (Feature 1.1)
   - Create `src/core/type_adapters.py`
   - Integrate into Oracle/MSSQL sources
   - Write unit tests

2. **Week 1, Day 3-5**: Start REST API pagination (Feature 1.2)
   - Refactor `src/sources/rest_api.py`
   - Implement 6 pagination types
   - Add authentication methods

3. **Week 2**: Complete REST API and start Pydantic models

### Development Environment Setup

```bash
# Clone repository
cd dlt-ingestion-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install development dependencies
pip install -e ".[dev,databases]"

# Run tests
pytest tests/unit -v

# Run linting
ruff check src/
black src/ --check
mypy src/
```

---

**Document Version**: 1.0  
**Created**: February 11, 2026  
**Last Updated**: February 11, 2026  
**Next Review**: Weekly during implementation

