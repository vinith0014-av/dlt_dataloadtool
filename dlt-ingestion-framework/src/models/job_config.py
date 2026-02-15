"""
Job configuration Pydantic models.

Validates ingestion job configuration from Excel.
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator


class LoadType(str, Enum):
    """Supported load types."""
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"


class SourceType(str, Enum):
    """Supported source types."""
    POSTGRESQL = "postgresql"
    ORACLE = "oracle"
    MSSQL = "mssql"
    AZURE_SQL = "azure_sql"
    API = "api"


class JobConfig(BaseModel):
    """
    Ingestion job configuration model.
    
    Validates a single job from ingestion_config.xlsx.
    
    Example:
        ```python
        job = JobConfig(
            source_type="postgresql",
            source_name="prod_postgres",
            table_name="orders",
            load_type="INCREMENTAL",
            watermark_column="updated_at",
            enabled="Y"
        )
        ```
    """
    
    # Required Fields
    source_type: SourceType = Field(
        ...,
        description="Type of data source"
    )
    
    source_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Name of source in secrets configuration"
    )
    
    table_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Table or API endpoint name"
    )
    
    load_type: LoadType = Field(
        default=LoadType.FULL,
        description="FULL (replace) or INCREMENTAL (merge)"
    )
    
    enabled: str = Field(
        default="Y",
        description="Y to enable, N to disable"
    )
    
    # Optional Fields - Database
    schema_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Schema name (Oracle only)"
    )
    
    watermark_column: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Column for incremental loads"
    )
    
    last_watermark: Optional[str] = Field(
        default=None,
        description="Last watermark value (datetime, int, etc.)"
    )
    
    # Optional Fields - API
    api_endpoint: Optional[str] = Field(
        default=None,
        max_length=500,
        description="API endpoint path (e.g., /api/users)"
    )
    
    pagination_type: Optional[str] = Field(
        default=None,
        description="Pagination type: offset, cursor, page_number, header_link, json_link, single_page"
    )
    
    auth_type: Optional[str] = Field(
        default=None,
        description="Authentication type: none, api_key, bearer, basic, oauth2"
    )
    
    page_size: Optional[int] = Field(
        default=100,
        ge=1,
        le=10000,
        description="Records per page for APIs"
    )
    
    data_selector: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Path to data array in API response (e.g., data.items)"
    )
    
    primary_key: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Primary key column(s) for merge operations"
    )
    
    # Optional Fields - Advanced
    chunk_size: Optional[int] = Field(
        default=None,
        ge=1000,
        le=5000000,
        description="Override default chunk size for large tables"
    )
    
    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional query parameters for APIs"
    )
    
    # Validators
    @field_validator('enabled')
    @classmethod
    def validate_enabled(cls, v: str) -> str:
        """Validate enabled flag is Y or N."""
        v_upper = v.upper()
        if v_upper not in ['Y', 'N']:
            raise ValueError("enabled must be 'Y' or 'N'")
        return v_upper
    
    @field_validator('source_name', 'table_name')
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        """Validate identifier names (no special characters)."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError(f"Invalid identifier: {v}. Use only alphanumeric, dash, underscore")
        return v
    
    @field_validator('watermark_column')
    @classmethod
    def validate_watermark_column(cls, v: Optional[str]) -> Optional[str]:
        """Validate watermark column name."""
        if v and not v.replace('_', '').isalnum():
            raise ValueError(f"Invalid watermark column: {v}")
        return v
    
    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v: Optional[int]) -> Optional[int]:
        """Validate page size is reasonable."""
        if v is not None:
            if v < 1:
                raise ValueError("page_size must be at least 1")
            if v > 10000:
                raise ValueError("page_size should not exceed 10,000 for optimal performance")
        return v
    
    @field_validator('chunk_size')
    @classmethod
    def validate_chunk_size(cls, v: Optional[int]) -> Optional[int]:
        """Validate chunk size is reasonable."""
        if v is not None:
            if v < 1000:
                raise ValueError("chunk_size should be at least 1,000")
            if v > 5000000:
                raise ValueError("chunk_size should not exceed 5,000,000 to avoid memory issues")
        return v
    
    @model_validator(mode='after')
    def validate_incremental_config(self) -> 'JobConfig':
        """Validate incremental load configuration."""
        if self.load_type == LoadType.INCREMENTAL:
            if not self.watermark_column:
                raise ValueError(
                    "watermark_column is required for INCREMENTAL load type"
                )
        return self
    
    @model_validator(mode='after')
    def validate_api_config(self) -> 'JobConfig':
        """Validate API-specific configuration."""
        if self.source_type == SourceType.API:
            if not self.api_endpoint and not self.table_name:
                raise ValueError(
                    "api_endpoint or table_name is required for API sources"
                )
        return self
    
    @model_validator(mode='after')
    def validate_oracle_config(self) -> 'JobConfig':
        """Validate Oracle-specific configuration."""
        if self.source_type == SourceType.ORACLE:
            if not self.schema_name:
                raise ValueError(
                    "schema_name is required for Oracle sources"
                )
        return self
    
    def is_enabled(self) -> bool:
        """Check if job is enabled."""
        return self.enabled.upper() == 'Y'
    
    def get_api_endpoint(self) -> str:
        """Get API endpoint path (fallback to table_name)."""
        return self.api_endpoint or f"/{self.table_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (compatible with existing code)."""
        return self.model_dump(exclude_none=True)
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = 'forbid'  # Reject unknown fields


class JobConfigList(BaseModel):
    """Collection of job configurations."""
    
    jobs: list[JobConfig] = Field(
        default_factory=list,
        description="List of ingestion jobs"
    )
    
    def get_enabled_jobs(self) -> list[JobConfig]:
        """Get only enabled jobs."""
        return [job for job in self.jobs if job.is_enabled()]
    
    def get_jobs_by_source_type(self, source_type: SourceType) -> list[JobConfig]:
        """Get jobs filtered by source type."""
        return [job for job in self.jobs if job.source_type == source_type]
    
    def get_job_by_name(self, source_name: str, table_name: str) -> Optional[JobConfig]:
        """Get specific job by source and table name."""
        for job in self.jobs:
            if job.source_name == source_name and job.table_name == table_name:
                return job
        return None
    
    def validate_all(self) -> tuple[list[JobConfig], list[tuple[int, str]]]:
        """
        Validate all jobs and return valid jobs + errors.
        
        Returns:
            Tuple of (valid_jobs, errors) where errors is list of (row_index, error_message)
        """
        valid_jobs = []
        errors = []
        
        for idx, job in enumerate(self.jobs):
            try:
                # Pydantic already validated during model creation
                valid_jobs.append(job)
            except Exception as e:
                errors.append((idx + 2, str(e)))  # +2 for Excel row (header + 0-index)
        
        return valid_jobs, errors
