"""
Destination configuration Pydantic models.

Validates destination-specific configuration from secrets.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class BaseDestinationConfig(BaseModel):
    """Base configuration for destinations."""
    
    type: str = Field(..., description="Destination type")
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True


class FilesystemConfig(BaseDestinationConfig):
    """Filesystem destination configuration (includes ADLS Gen2)."""
    
    type: str = Field(default="filesystem", description="Destination type")
    
    bucket_url: str = Field(
        ...,
        min_length=1,
        description="Storage URL (az://, s3://, gs://, file://)"
    )
    
    layout: Optional[str] = Field(
        default="{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}",
        description="File layout pattern with date partitioning"
    )
    
    @field_validator('bucket_url')
    @classmethod
    def validate_bucket_url(cls, v: str) -> str:
        """Validate bucket URL format."""
        v = v.strip()
        valid_schemes = ['az://', 's3://', 'gs://', 'file://']
        if not any(v.startswith(scheme) for scheme in valid_schemes):
            raise ValueError(
                f"bucket_url must start with: {', '.join(valid_schemes)}"
            )
        return v
    
    @field_validator('layout')
    @classmethod
    def validate_layout(cls, v: Optional[str]) -> Optional[str]:
        """Validate layout contains required placeholders."""
        if v:
            required_placeholders = ['{table_name}', '{load_id}', '{file_id}', '{ext}']
            for placeholder in required_placeholders:
                if placeholder not in v:
                    raise ValueError(
                        f"layout must contain {placeholder}"
                    )
        return v


class ADLSGen2Config(FilesystemConfig):
    """ADLS Gen2 destination configuration (extends Filesystem)."""
    
    azure_storage_account_name: str = Field(
        ...,
        min_length=3,
        max_length=24,
        description="Azure storage account name"
    )
    
    azure_storage_account_key: str = Field(
        ...,
        min_length=1,
        description="Azure storage account key"
    )
    
    @field_validator('azure_storage_account_name')
    @classmethod
    def validate_storage_account_name(cls, v: str) -> str:
        """Validate Azure storage account name format."""
        if not v.isalnum():
            raise ValueError(
                "azure_storage_account_name must contain only lowercase letters and numbers"
            )
        if not v.islower():
            raise ValueError(
                "azure_storage_account_name must be lowercase"
            )
        return v
    
    @field_validator('bucket_url')
    @classmethod
    def validate_adls_bucket_url(cls, v: str) -> str:
        """Validate ADLS bucket URL."""
        if not v.startswith('az://'):
            raise ValueError("ADLS Gen2 bucket_url must start with az://")
        return v


class DatabricksConfig(BaseDestinationConfig):
    """Databricks destination configuration."""
    
    type: str = Field(default="databricks", description="Destination type")
    
    server_hostname: str = Field(
        ...,
        min_length=1,
        description="Databricks workspace hostname"
    )
    
    http_path: str = Field(
        ...,
        min_length=1,
        description="SQL warehouse HTTP path"
    )
    
    access_token: Optional[str] = Field(
        default=None,
        description="Databricks personal access token"
    )
    
    catalog: Optional[str] = Field(
        default="main",
        description="Unity Catalog name"
    )
    
    schema: str = Field(
        default="default",
        description="Database/schema name"
    )
    
    @field_validator('server_hostname')
    @classmethod
    def validate_hostname(cls, v: str) -> str:
        """Validate Databricks hostname format."""
        v = v.strip()
        if v.startswith('http://') or v.startswith('https://'):
            raise ValueError("server_hostname should not include http:// or https://")
        if not ('.azuredatabricks.net' in v or '.cloud.databricks.com' in v or '.gcp.databricks.com' in v):
            raise ValueError("Invalid Databricks hostname format")
        return v
    
    @field_validator('http_path')
    @classmethod
    def validate_http_path(cls, v: str) -> str:
        """Validate HTTP path format."""
        if not v.startswith('/sql/'):
            raise ValueError("http_path must start with /sql/")
        return v


class DeltaLakeConfig(BaseDestinationConfig):
    """Delta Lake destination configuration."""
    
    type: str = Field(default="delta", description="Destination type")
    
    location: str = Field(
        ...,
        min_length=1,
        description="Delta table location (ADLS, S3, GCS, local)"
    )
    
    catalog: Optional[str] = Field(
        default=None,
        description="Unity Catalog name"
    )
    
    database: str = Field(
        default="default",
        description="Database/schema name"
    )
    
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Validate Delta location format."""
        valid_prefixes = ['abfss://', 'az://', 's3://', 'gs://', 'file://']
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            raise ValueError(
                f"location must start with: {', '.join(valid_prefixes)}"
            )
        return v


# Union type for all destination configurations
DestinationConfig = FilesystemConfig | ADLSGen2Config | DatabricksConfig | DeltaLakeConfig
