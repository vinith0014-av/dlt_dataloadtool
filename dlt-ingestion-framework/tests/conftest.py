"""
Shared pytest fixtures for all tests.

This module provides reusable fixtures for testing the DLT ingestion framework.
All tests can access these fixtures via pytest's dependency injection.
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
    """Sample secrets configuration for all source types."""
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
            'mssql': {
                'host': 'localhost',
                'port': 1433,
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_pass',
                'driver': 'ODBC Driver 17 for SQL Server'
            },
            'azure_sql': {
                'host': 'test-server.database.windows.net',
                'port': 1433,
                'database': 'test_db',
                'username': 'test_user',
                'password': 'test_pass'
            },
            'test_api': {
                'base_url': 'https://api.example.com',
                'auth_type': 'bearer',
                'token': 'test_token_12345'
            }
        },
        'destination': {
            'filesystem': {
                'bucket_url': 'az://test-container',
                'azure_storage_account_name': 'testaccount',
                'azure_storage_account_key': 'testkey123456'
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
def sample_oracle_job():
    """Sample Oracle job configuration (requires schema_name)."""
    return {
        'source_type': 'oracle',
        'source_name': 'oracle_db',
        'table_name': 'products',
        'schema_name': 'SALES',
        'load_type': 'FULL',
        'enabled': 'Y'
    }


@pytest.fixture
def sample_api_job():
    """Sample API job configuration with pagination."""
    return {
        'source_type': 'api',
        'source_name': 'test_api',
        'table_name': 'users',
        'api_endpoint': '/users',
        'pagination_type': 'offset',
        'auth_type': 'bearer',
        'page_size': 100,
        'load_type': 'FULL',
        'enabled': 'Y'
    }


@pytest.fixture
def sample_excel_config(temp_dir):
    """Create sample Excel configuration file for testing."""
    data = [
        {
            'source_type': 'postgresql', 
            'source_name': 'test_db', 
            'table_name': 'customers', 
            'load_type': 'FULL', 
            'enabled': 'Y'
        },
        {
            'source_type': 'postgresql', 
            'source_name': 'test_db', 
            'table_name': 'orders', 
            'load_type': 'INCREMENTAL', 
            'watermark_column': 'updated_at',
            'last_watermark': '2026-01-01',
            'enabled': 'Y'
        },
        {
            'source_type': 'oracle', 
            'source_name': 'oracle_db', 
            'table_name': 'products',
            'schema_name': 'SALES',
            'load_type': 'FULL', 
            'enabled': 'N'  # Disabled
        },
        {
            'source_type': 'api',
            'source_name': 'test_api',
            'table_name': 'users',
            'api_endpoint': '/users',
            'pagination_type': 'offset',
            'auth_type': 'bearer',
            'load_type': 'FULL',
            'enabled': 'Y'
        }
    ]
    
    df = pd.DataFrame(data)
    excel_path = temp_dir / 'ingestion_config.xlsx'
    df.to_excel(excel_path, sheet_name='SourceConfig', index=False)
    
    return excel_path


@pytest.fixture
def sample_secrets_toml(temp_dir, sample_secrets):
    """Create sample secrets.toml file for testing."""
    import toml
    
    secrets_dir = temp_dir / '.dlt'
    secrets_dir.mkdir(parents=True, exist_ok=True)
    secrets_path = secrets_dir / 'secrets.toml'
    
    with open(secrets_path, 'w') as f:
        toml.dump(sample_secrets, f)
    
    return secrets_path


@pytest.fixture
def mock_dlt_pipeline():
    """Mock DLT pipeline for testing without actual data movement."""
    with patch('dlt.pipeline') as mock:
        pipeline = MagicMock()
        pipeline.pipeline_name = 'test_pipeline'
        pipeline.destination = 'filesystem'
        pipeline.dataset_name = 'test_dataset'
        
        # Mock last_trace for metrics extraction
        pipeline.last_trace = MagicMock()
        pipeline.last_trace.last_normalize_info = MagicMock()
        pipeline.last_trace.last_normalize_info.row_counts = {'test_table': 100}
        
        # Mock run method
        load_info = MagicMock()
        load_info.has_failed_jobs = False
        pipeline.run = MagicMock(return_value=load_info)
        
        mock.return_value = pipeline
        yield pipeline


@pytest.fixture
def mock_sql_table():
    """Mock sql_table for testing without database connection."""
    with patch('dlt.sources.sql_database.sql_table') as mock:
        resource = MagicMock()
        resource.__name__ = 'test_table'
        mock.return_value = resource
        yield mock


@pytest.fixture
def mock_rest_api_source():
    """Mock REST API source for testing without API calls."""
    with patch('dlt.sources.rest_api.rest_api_source') as mock:
        api_source = MagicMock()
        resource = MagicMock()
        resource.__name__ = 'test_resource'
        api_source.resources = {'test_resource': resource}
        mock.return_value = api_source
        yield mock


@pytest.fixture
def mock_keyvault_manager():
    """Mock KeyVaultManager for testing without Azure connection."""
    with patch('src.auth.keyvault_manager.KeyVaultManager') as mock:
        manager = MagicMock()
        
        # Mock get_secret method
        def get_secret_side_effect(secret_name):
            secrets_map = {
                'postgresql-host': 'localhost',
                'postgresql-port': '5432',
                'postgresql-database': 'test_db',
                'postgresql-username': 'test_user',
                'postgresql-password': 'test_pass'
            }
            return secrets_map.get(secret_name)
        
        manager.get_secret = MagicMock(side_effect=get_secret_side_effect)
        mock.return_value = manager
        yield manager


@pytest.fixture
def mock_metadata_tracker():
    """Mock MetadataTracker for testing without file I/O."""
    with patch('src.metadata.tracker.MetadataTracker') as mock:
        tracker = MagicMock()
        tracker.record_job = MagicMock()
        tracker.get_last_watermark = MagicMock(return_value=None)
        mock.return_value = tracker
        yield tracker


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration between tests."""
    import logging
    # Remove all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    yield
    # Cleanup after test
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


@pytest.fixture
def sample_connection_strings():
    """Sample connection strings for different database types."""
    return {
        'postgresql': 'postgresql+psycopg2://user:pass@localhost:5432/testdb',
        'oracle': 'oracle+oracledb://user:pass@localhost:1521/TESTDB',
        'mssql': 'mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost,1433;DATABASE=testdb;UID=user;PWD=pass',
        'azure_sql': 'mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=test.database.windows.net,1433;DATABASE=testdb;UID=user;PWD=pass;Encrypt=yes'
    }
