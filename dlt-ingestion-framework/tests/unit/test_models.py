"""
Unit tests for Pydantic configuration models.

Tests validation logic for job, source, and destination configurations.
"""
import pytest
from pydantic import ValidationError

from src.models.job_config import JobConfig, LoadType, SourceType, JobConfigList
from src.models.source_config import (
    PostgreSQLConfig,
    OracleConfig,
    MSSQLConfig,
    AzureSQLConfig,
    RESTAPIConfig,
    PaginationType,
    AuthType
)
from src.models.destination_config import (
    ADLSGen2Config,
    FilesystemConfig,
    DatabricksConfig
)


class TestJobConfig:
    """Test job configuration model."""
    
    def test_valid_full_load_job(self):
        """Test valid FULL load job."""
        job = JobConfig(
            source_type="postgresql",
            source_name="prod_postgres",
            table_name="orders",
            load_type="FULL",
            enabled="Y"
        )
        
        assert job.source_type == SourceType.POSTGRESQL
        assert job.load_type == LoadType.FULL
        assert job.is_enabled() is True
    
    def test_valid_incremental_job(self):
        """Test valid INCREMENTAL load job."""
        job = JobConfig(
            source_type="oracle",
            source_name="prod_oracle",
            table_name="customers",
            schema_name="dbo",
            load_type="INCREMENTAL",
            watermark_column="updated_at",
            last_watermark="2024-01-01",
            enabled="Y"
        )
        
        assert job.load_type == LoadType.INCREMENTAL
        assert job.watermark_column == "updated_at"
    
    def test_incremental_without_watermark_fails(self):
        """Test INCREMENTAL without watermark_column fails."""
        with pytest.raises(ValidationError) as exc_info:
            JobConfig(
                source_type="postgresql",
                source_name="test",
                table_name="test_table",
                load_type="INCREMENTAL",
                enabled="Y"
            )
        
        assert "watermark_column" in str(exc_info.value)
    
    def test_oracle_without_schema_fails(self):
        """Test Oracle without schema_name fails."""
        with pytest.raises(ValidationError) as exc_info:
            JobConfig(
                source_type="oracle",
                source_name="test",
                table_name="test_table",
                enabled="Y"
            )
        
        assert "schema_name" in str(exc_info.value)
    
    def test_invalid_source_type_fails(self):
        """Test invalid source_type fails."""
        with pytest.raises(ValidationError):
            JobConfig(
                source_type="invalid_type",
                source_name="test",
                table_name="test_table",
                enabled="Y"
            )
    
    def test_enabled_flag_conversion(self):
        """Test enabled flag is converted to uppercase."""
        job = JobConfig(
            source_type="postgresql",
            source_name="test",
            table_name="test_table",
            enabled="y"
        )
        
        assert job.enabled == "Y"
        assert job.is_enabled() is True
    
    def test_page_size_validation(self):
        """Test page_size validation."""
        # Valid page size
        job1 = JobConfig(
            source_type="api",
            source_name="test_api",
            table_name="data",
            page_size=100,
            enabled="Y"
        )
        assert job1.page_size == 100
        
        # Too small fails
        with pytest.raises(ValidationError):
            JobConfig(
                source_type="api",
                source_name="test_api",
                table_name="data",
                page_size=0,
                enabled="Y"
            )
        
        # Too large fails
        with pytest.raises(ValidationError):
            JobConfig(
                source_type="api",
                source_name="test_api",
                table_name="data",
                page_size=20000,
                enabled="Y"
            )
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        job = JobConfig(
            source_type="postgresql",
            source_name="test",
            table_name="test_table",
            enabled="Y"
        )
        
        job_dict = job.to_dict()
        assert isinstance(job_dict, dict)
        assert job_dict['source_type'] == "postgresql"
        assert job_dict['source_name'] == "test"


class TestJobConfigList:
    """Test job configuration list operations."""
    
    def test_get_enabled_jobs(self):
        """Test filtering enabled jobs."""
        jobs = JobConfigList(jobs=[
            JobConfig(source_type="postgresql", source_name="db1", table_name="t1", enabled="Y"),
            JobConfig(source_type="postgresql", source_name="db2", table_name="t2", enabled="N"),
            JobConfig(source_type="postgresql", source_name="db3", table_name="t3", enabled="Y")
        ])
        
        enabled = jobs.get_enabled_jobs()
        assert len(enabled) == 2
        assert all(job.is_enabled() for job in enabled)
    
    def test_get_jobs_by_source_type(self):
        """Test filtering by source type."""
        jobs = JobConfigList(jobs=[
            JobConfig(source_type="postgresql", source_name="db1", table_name="t1", enabled="Y"),
            JobConfig(source_type="oracle", source_name="db2", table_name="t2", schema_name="dbo", enabled="Y"),
            JobConfig(source_type="postgresql", source_name="db3", table_name="t3", enabled="Y")
        ])
        
        postgres_jobs = jobs.get_jobs_by_source_type(SourceType.POSTGRESQL)
        assert len(postgres_jobs) == 2
        assert all(job.source_type == SourceType.POSTGRESQL for job in postgres_jobs)


class TestPostgreSQLConfig:
    """Test PostgreSQL configuration model."""
    
    def test_valid_config(self):
        """Test valid PostgreSQL configuration."""
        config = PostgreSQLConfig(
            host="localhost",
            port=5432,
            database="mydb",
            username="user",
            password="pass123"
        )
        
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.ssl_mode == "prefer"  # default
    
    def test_invalid_ssl_mode_fails(self):
        """Test invalid SSL mode fails."""
        with pytest.raises(ValidationError):
            PostgreSQLConfig(
                host="localhost",
                port=5432,
                database="mydb",
                username="user",
                password="pass",
                ssl_mode="invalid"
            )
    
    def test_invalid_port_fails(self):
        """Test invalid port fails."""
        with pytest.raises(ValidationError):
            PostgreSQLConfig(
                host="localhost",
                port=70000,  # exceeds max
                database="mydb",
                username="user",
                password="pass"
            )


class TestRESTAPIConfig:
    """Test REST API configuration model."""
    
    def test_api_key_header_auth(self):
        """Test API key in header authentication."""
        config = RESTAPIConfig(
            base_url="https://api.example.com",
            auth_type="api_key",
            api_key="test_key",
            api_key_name="X-API-Key",
            api_key_location="header"
        )
        
        assert config.auth_type == AuthType.API_KEY
        assert config.api_key_location == "header"
    
    def test_bearer_token_auth(self):
        """Test bearer token authentication."""
        config = RESTAPIConfig(
            base_url="https://api.example.com",
            auth_type="bearer",
            token="bearer_token_123"
        )
        
        assert config.auth_type == AuthType.BEARER
        assert config.token == "bearer_token_123"
    
    def test_offset_pagination(self):
        """Test offset pagination configuration."""
        config = RESTAPIConfig(
            base_url="https://api.example.com",
            pagination_type="offset",
            page_size=100,
            offset_param="offset",
            limit_param="limit"
        )
        
        assert config.pagination_type == PaginationType.OFFSET
        assert config.page_size == 100
    
    def test_invalid_base_url_fails(self):
        """Test invalid base URL fails."""
        with pytest.raises(ValidationError):
            RESTAPIConfig(base_url="invalid_url")
    
    def test_base_url_trailing_slash_removed(self):
        """Test trailing slash is removed from base_url."""
        config = RESTAPIConfig(base_url="https://api.example.com/")
        assert config.base_url == "https://api.example.com"


class TestADLSGen2Config:
    """Test ADLS Gen2 configuration model."""
    
    def test_valid_config(self):
        """Test valid ADLS Gen2 configuration."""
        config = ADLSGen2Config(
            bucket_url="az://raw-data",
            azure_storage_account_name="storageaccount1",
            azure_storage_account_key="ABC123=="
        )
        
        assert config.bucket_url == "az://raw-data"
        assert config.azure_storage_account_name == "storageaccount1"
    
    def test_invalid_storage_account_name_fails(self):
        """Test invalid storage account name fails."""
        # Contains uppercase
        with pytest.raises(ValidationError):
            ADLSGen2Config(
                bucket_url="az://raw-data",
                azure_storage_account_name="StorageAccount",
                azure_storage_account_key="ABC123=="
            )
        
        # Contains special characters
        with pytest.raises(ValidationError):
            ADLSGen2Config(
                bucket_url="az://raw-data",
                azure_storage_account_name="storage-account",
                azure_storage_account_key="ABC123=="
            )
    
    def test_invalid_bucket_url_scheme_fails(self):
        """Test invalid bucket URL scheme fails."""
        with pytest.raises(ValidationError):
            ADLSGen2Config(
                bucket_url="s3://raw-data",  # Wrong scheme for ADLS
                azure_storage_account_name="storageaccount",
                azure_storage_account_key="ABC123=="
            )


class TestDatabricksConfig:
    """Test Databricks configuration model."""
    
    def test_valid_config(self):
        """Test valid Databricks configuration."""
        config = DatabricksConfig(
            server_hostname="adb-1234567890.12.azuredatabricks.net",
            http_path="/sql/1.0/warehouses/abcd1234",
            access_token="dapi1234567890",
            catalog="main",
            schema="default"
        )
        
        assert "azuredatabricks.net" in config.server_hostname
        assert config.http_path.startswith("/sql/")
    
    def test_hostname_with_protocol_fails(self):
        """Test hostname with protocol fails."""
        with pytest.raises(ValidationError):
            DatabricksConfig(
                server_hostname="https://adb-123.azuredatabricks.net",
                http_path="/sql/1.0/warehouses/abc"
            )
    
    def test_invalid_http_path_fails(self):
        """Test invalid HTTP path fails."""
        with pytest.raises(ValidationError):
            DatabricksConfig(
                server_hostname="adb-123.azuredatabricks.net",
                http_path="/invalid/path"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
