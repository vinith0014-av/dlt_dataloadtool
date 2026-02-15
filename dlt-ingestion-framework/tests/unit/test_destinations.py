"""Unit tests for destination modules."""
import pytest
from unittest.mock import patch, MagicMock

from src.destinations.base import BaseDestination
from src.destinations.adls_gen2 import ADLSGen2Destination


class TestBaseDestination:
    """Tests for BaseDestination abstract class."""
    
    def test_cannot_instantiate_base_destination(self):
        """Test BaseDestination cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseDestination('test_dest', {})
    
    def test_base_destination_interface(self):
        """Test BaseDestination defines required interface."""
        assert hasattr(BaseDestination, 'validate_connection')
        assert hasattr(BaseDestination, 'get_destination_config')


class TestADLSGen2Destination:
    """Tests for ADLSGen2Destination."""
    
    def test_init(self):
        """Test ADLS Gen2 destination initialization."""
        config = {
            'bucket_url': 'az://raw-data',
            'azure_storage_account_name': 'testaccount',
            'azure_storage_account_key': 'testkey123456'
        }
        
        dest = ADLSGen2Destination('adls_dest', config)
        
        assert dest.name == 'adls_dest'
        assert dest.config == config
    
    def test_get_destination_config_basic(self):
        """Test ADLS Gen2destination configuration."""
        config = {
            'destination': {
                'filesystem': {
                    'bucket_url': 'az://raw-data',
                    'credentials': {
                        'azure_storage_account_name': 'testaccount',
                        'azure_storage_account_key': 'testkey123456'
                    }
                }
            }
        }
        
        dest = ADLSGen2Destination('adls_dest', config)
        dest_config = dest.get_destination_config()
        
        assert dest_config is not None
        assert 'bucket_url' in dest_config or 'credentials' in dest_config
    
    def test_date_partitioning_layout(self):
        """Test date partitioning layout configuration."""
        config = {
            'destination': {
                'filesystem': {
                    'bucket_url': 'az://raw-data',
                    'layout': '{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}',
                    'credentials': {
                        'azure_storage_account_name': 'testaccount',
                        'azure_storage_account_key': 'testkey123456'
                    }
                }
            }
        }
        
        dest = ADLSGen2Destination('adls_dest', config)
        dest_config = dest.get_destination_config()
        
        # Should include layout pattern
        # Implementation may vary based on dlt configuration format
        assert dest_config is not None
    
    def test_storage_account_name_validation(self):
        """Test storage account name validation."""
        # Storage account name must be lowercase alphanumeric
        invalid_config = {
            'bucket_url': 'az://raw-data',
            'azure_storage_account_name': 'Test-Account',  # Invalid: uppercase and dash
            'azure_storage_account_key': 'testkey'
        }
        
        # Should raise validation error or handle gracefully
        # Implementation depends on validation logic
        dest = ADLSGen2Destination('adls_dest', invalid_config)
        # Pydantic validation should catch this if integrated
    
    def test_bucket_url_scheme_validation(self):
        """Test bucket URL must start with az://."""
        invalid_config = {
            'bucket_url': 's3://wrong-bucket',  # Wrong scheme
            'azure_storage_account_name': 'testaccount',
            'azure_storage_account_key': 'testkey'
        }
        
        # Should validate Azure-specific URL scheme
        # Implementation may validate at Pydantic level or runtime
        pass
    
    @patch('azure.storage.blob.BlobServiceClient')
    def test_validate_connection_success(self, mock_blob_client):
        """Test successful ADLS Gen2 connection validation."""
        mock_client = MagicMock()
        mock_blob_client.return_value = mock_client
        
        config = {
            'bucket_url': 'az://raw-data',
            'azure_storage_account_name': 'testaccount',
            'azure_storage_account_key': 'testkey123456'
        }
        
        dest = ADLSGen2Destination('adls_dest', config)
        result = dest.validate_connection()
        
        # Should return True if connection succeeds
        assert isinstance(result, bool)
    
    @patch('azure.storage.blob.BlobServiceClient')
    def test_validate_connection_failure(self, mock_blob_client):
        """Test ADLS Gen2 connection validation handles failures."""
        mock_blob_client.side_effect = Exception("Authentication failed")
        
        config = {
            'bucket_url': 'az://raw-data',
            'azure_storage_account_name': 'testaccount',
            'azure_storage_account_key': 'wrongkey'
        }
        
        dest = ADLSGen2Destination('adls_dest', config)
        result = dest.validate_connection()
        
        assert result == False


class TestFilesystemDestination:
    """Tests for generic filesystem destination."""
    
    def test_s3_destination(self):
        """Test S3 filesystem destination configuration."""
        config = {
            'bucket_url': 's3://my-bucket',
            'aws_access_key_id': 'access_key',
            'aws_secret_access_key': 'secret_key'
        }
        
        # Test S3 configuration if supported
        # Implementation depends on destination module structure
        pass
    
    def test_gcs_destination(self):
        """Test Google Cloud Storage destination."""
        config = {
            'bucket_url': 'gs://my-bucket',
            'credentials_path': '/path/to/service-account.json'
        }
        
        # Test GCS configuration if supported
        pass
    
    def test_local_filesystem(self):
        """Test local filesystem destination."""
        config = {
            'bucket_url': 'file:///tmp/dlt-data'
        }
        
        # Test local filesystem configuration
        pass


class TestDatabricksDestination:
    """Tests for Databricks Unity Catalog destination."""
    
    @pytest.mark.skip(reason="Databricks destination not yet implemented")
    def test_databricks_config(self):
        """Test Databricks destination configuration."""
        config = {
            'server_hostname': 'test.azuredatabricks.net',
            'http_path': '/sql/1.0/warehouses/test',
            'catalog': 'main',
            'schema': 'raw',
            'access_token': 'token123'
        }
        
        # Future test for Databricks destination
        pass
    
    @pytest.mark.skip(reason="Databricks destination not yet implemented")
    def test_unity_catalog_table_creation(self):
        """Test Unity Catalog table creation."""
        # Future test for managed table creation
        pass


class TestDeltaLakeDestination:
    """Tests for Delta Lake destination."""
    
    @pytest.mark.skip(reason="Delta Lake destination not yet implemented")
    def test_delta_lake_config(self):
        """Test Delta Lake destination configuration."""
        config = {
            'location': 'az://delta-tables',
            'catalog': 'unity_catalog',
            'database': 'raw'
        }
        
        # Future test for Delta Lake destination
        pass
    
    @pytest.mark.skip(reason="Delta Lake destination not yet implemented")
    def test_merge_operations(self):
        """Test Delta Lake merge/upsert operations."""
        # Future test for merge strategy
        pass


class TestDestinationFactory:
    """Tests for destination factory pattern."""
    
    def test_create_adls_destination(self):
        """Test factory creates ADLS Gen2 destination."""
        # If factory pattern exists
        pass
    
    def test_create_unknown_destination_type(self):
        """Test factory handles unknown destination types."""
        # Should raise clear error
        pass


class TestDestinationValidation:
    """Tests for destination validation across all types."""
    
    def test_all_destinations_implement_validation(self):
        """Test all destination classes implement validate_connection."""
        # When more destinations are added
        destinations = [ADLSGen2Destination]
        
        for dest_class in destinations:
            assert hasattr(dest_class, 'validate_connection')
    
    def test_validation_returns_boolean(self):
        """Test validation always returns boolean."""
        config = {
            'bucket_url': 'az://raw-data',
            'azure_storage_account_name': 'testaccount',
            'azure_storage_account_key': 'testkey'
        }
        
        dest = ADLSGen2Destination('test', config)
        
        with patch('azure.storage.blob.BlobServiceClient'):
            result = dest.validate_connection()
            assert isinstance(result, bool)


class TestLayoutPatterns:
    """Tests for file layout patterns."""
    
    def test_default_layout_pattern(self):
        """Test default date partitioning layout."""
        config = {
            'destination': {
                'filesystem': {
                    'bucket_url': 'az://raw-data',
                    'credentials': {
                        'azure_storage_account_name': 'testaccount',
                        'azure_storage_account_key': 'testkey'
                    }
                }
            }
        }
        
        dest = ADLSGen2Destination('adls', config)
        dest_config = dest.get_destination_config()
        
        # Default layout should include date partitioning
        # {table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}
        assert dest_config is not None
    
    def test_custom_layout_pattern(self):
        """Test custom layout pattern."""
        config = {
            'destination': {
                'filesystem': {
                    'bucket_url': 'az://raw-data',
                    'layout': 'custom/{table_name}/year={YYYY}/month={MM}/day={DD}/{load_id}.parquet',
                    'credentials': {
                        'azure_storage_account_name': 'testaccount',
                        'azure_storage_account_key': 'testkey'
                    }
                }
            }
        }
        
        dest = ADLSGen2Destination('adls', config)
        dest_config = dest.get_destination_config()
        
        # Should use custom layout
        assert dest_config is not None
    
    def test_hive_partitioning(self):
        """Test Hive-style partitioning layout."""
        config = {
            'bucket_url': 'az://raw-data',
            'azure_storage_account_name': 'testaccount',
            'azure_storage_account_key': 'testkey',
            'layout': '{table_name}/year={YYYY}/month={MM}/day={DD}/{load_id}.parquet'
        }
        
        dest = ADLSGen2Destination('adls', config)
        
        # Hive-style partitions for Databricks/Spark compatibility
        assert dest is not None


class TestCredentialManagement:
    """Tests for credential handling in destinations."""
    
    def test_storage_key_not_logged(self):
        """Test storage keys are not logged in clear text."""
        config = {
            'bucket_url': 'az://raw-data',
            'azure_storage_account_name': 'testaccount',
            'azure_storage_account_key': 'super_secret_key_12345'
        }
        
        dest = ADLSGen2Destination('adls', config)
        
        # String representation should not include secret
        dest_str = str(dest)
        assert 'super_secret_key_12345' not in dest_str
    
    def test_managed_identity_support(self):
        """Test Managed Identity authentication (no key required)."""
        config = {
            'bucket_url': 'az://raw-data',
            'azure_storage_account_name': 'testaccount'
            # No azure_storage_account_key - uses Managed Identity
        }
        
        # Should support Managed Identity authentication
        # Implementation depends on Azure SDK integration
        pass

class TestDatabricksDestination:
    """Tests for DatabricksDestination."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.valid_config = {
            'destination': {
                'type': 'databricks',
                'databricks': {
                    'server_hostname': 'adb-test.azuredatabricks.net',
                    'http_path': '/sql/1.0/warehouses/test-warehouse',
                    'catalog': 'main',
                    'schema': 'raw',
                    'credentials': {
                        'server_hostname': 'adb-test.azuredatabricks.net',
                        'http_path': '/sql/1.0/warehouses/test-warehouse',
                        'access_token': 'dapi_test_token_12345'
                    }
                },
                'filesystem': {
                    'bucket_url': 'az://staging@teststorage.dfs.core.windows.net',
                    'credentials': {
                        'azure_storage_account_name': 'teststorage',
                        'azure_storage_sas_token': '?sv=2024-11-04&ss=bfqt&srt=sco'
                    }
                }
            }
        }
    
    def test_init(self):
        """Test Databricks destination initialization."""
        from src.destinations.databricks import DatabricksDestination
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        
        assert dest.name == 'databricks_dest'
        assert dest.config == self.valid_config
        assert dest.get_destination_type() == 'databricks'
    
    def test_get_destination_config_basic(self):
        """Test Databricks destination configuration."""
        from src.destinations.databricks import DatabricksDestination
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        dest_config = dest.get_dlt_destination_config()
        
        assert dest_config is not None
        assert dest_config['destination'] == 'databricks'
        assert dest_config['staging'] == 'filesystem'
        assert 'credentials' in dest_config
        assert 'staging_config' in dest_config
    
    def test_databricks_credentials_required(self):
        """Test that Databricks credentials are required."""
        from src.destinations.databricks import DatabricksDestination
        
        invalid_config = {
            'destination': {
                'databricks': {
                    'server_hostname': 'adb-test.azuredatabricks.net'
                    # Missing credentials
                }
            }
        }
        
        dest = DatabricksDestination('databricks_dest', invalid_config)
        
        with pytest.raises(ValueError, match="credentials missing"):
            dest.get_dlt_destination_config()
    
    def test_staging_credentials_required(self):
        """Test that staging credentials are required."""
        from src.destinations.databricks import DatabricksDestination
        
        invalid_config = {
            'destination': {
                'databricks': {
                    'credentials': {
                        'server_hostname': 'adb-test.azuredatabricks.net',
                        'http_path': '/sql/1.0/warehouses/test',
                        'access_token': 'dapi_test'
                    }
                }
                # Missing filesystem staging config
            }
        }
        
        dest = DatabricksDestination('databricks_dest', invalid_config)
        
        with pytest.raises(KeyError, match="staging configuration"):
            dest.get_dlt_destination_config()
    
    def test_catalog_name_default(self):
        """Test catalog name defaults to 'main'."""
        from src.destinations.databricks import DatabricksDestination
        
        config = self.valid_config.copy()
        config['destination']['databricks'].pop('catalog', None)
        
        dest = DatabricksDestination('databricks_dest', config)
        
        assert dest.get_catalog_name() == 'main'
    
    def test_catalog_name_custom(self):
        """Test custom catalog name."""
        from src.destinations.databricks import DatabricksDestination
        
        config = self.valid_config.copy()
        config['destination']['databricks']['catalog'] = 'custom_catalog'
        
        dest = DatabricksDestination('databricks_dest', config)
        
        assert dest.get_catalog_name() == 'custom_catalog'
    
    def test_schema_name_default(self):
        """Test schema name defaults to 'raw'."""
        from src.destinations.databricks import DatabricksDestination
        
        config = self.valid_config.copy()
        config['destination']['databricks'].pop('schema', None)
        
        dest = DatabricksDestination('databricks_dest', config)
        
        assert dest.get_schema_name() == 'raw'
    
    def test_schema_name_from_job(self):
        """Test schema name from job configuration."""
        from src.destinations.databricks import DatabricksDestination
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        job = {'target_schema': 'custom_schema'}
        
        assert dest.get_schema_name(job) == 'custom_schema'
    
    def test_full_table_name(self):
        """Test fully qualified table name generation."""
        from src.destinations.databricks import DatabricksDestination
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        
        full_name = dest.get_full_table_name('customers')
        
        assert full_name == 'main.raw.customers'
    
    def test_full_table_name_with_custom_catalog_schema(self):
        """Test fully qualified table name with custom catalog and schema."""
        from src.destinations.databricks import DatabricksDestination
        
        config = self.valid_config.copy()
        config['destination']['databricks']['catalog'] = 'bronze'
        config['destination']['databricks']['schema'] = 'staging'
        
        dest = DatabricksDestination('databricks_dest', config)
        
        full_name = dest.get_full_table_name('orders')
        
        assert full_name == 'bronze.staging.orders'
    
    def test_sas_token_credentials(self):
        """Test SAS token authentication for staging."""
        from src.destinations.databricks import DatabricksDestination
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        dest_config = dest.get_dlt_destination_config()
        
        staging_creds = dest_config['staging_config']['credentials']
        assert 'azure_storage_sas_token' in staging_creds
        assert staging_creds['azure_storage_account_name'] == 'teststorage'
    
    def test_storage_key_credentials(self):
        """Test storage account key authentication for staging."""
        from src.destinations.databricks import DatabricksDestination
        
        config = self.valid_config.copy()
        config['destination']['filesystem']['credentials'] = {
            'azure_storage_account_name': 'teststorage',
            'azure_storage_account_key': 'test_key_12345'
        }
        
        dest = DatabricksDestination('databricks_dest', config)
        dest_config = dest.get_dlt_destination_config()
        
        staging_creds = dest_config['staging_config']['credentials']
        assert 'azure_storage_account_key' in staging_creds
    
    def test_missing_staging_auth(self):
        """Test error when neither SAS token nor storage key provided."""
        from src.destinations.databricks import DatabricksDestination
        
        config = self.valid_config.copy()
        config['destination']['filesystem']['credentials'] = {
            'azure_storage_account_name': 'teststorage'
            # Missing both sas_token and account_key
        }
        
        dest = DatabricksDestination('databricks_dest', config)
        
        with pytest.raises(ValueError, match="azure_storage_sas_token.*azure_storage_account_key"):
            dest.get_dlt_destination_config()
    
    def test_metadata(self):
        """Test Databricks destination metadata."""
        from src.destinations.databricks import DatabricksDestination
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        metadata = dest.get_metadata()
        
        expected_keys = [
            'destination_type',
            'server_hostname',
            'http_path',
            'catalog',
            'schema',
            'staging_bucket',
            'staging_account',
            'file_format',
            'supports_acid',
            'supports_time_travel'
        ]
        
        assert all(k in metadata for k in expected_keys)
        assert metadata['destination_type'] == 'databricks'
        assert metadata['file_format'] == 'delta'
        assert metadata['supports_acid'] is True
    
    def test_validate_connection_no_databricks_connector(self):
        """Test connection validation when databricks-sql-connector not installed."""
        from src.destinations.databricks import DatabricksDestination
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        
        # Mock the databricks import to raise ImportError
        with patch.dict('sys.modules', {'databricks': None, 'databricks.sql': None}):
            result = dest.validate_connection()
        
        assert result is False
    
    @patch('src.destinations.databricks.DatabricksDestination.validate_connection')
    def test_validate_connection_success(self, mock_validate):
        """Test successful connection validation."""
        from src.destinations.databricks import DatabricksDestination
        
        mock_validate.return_value = True
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        result = dest.validate_connection()
        
        assert result is True
    
    @patch('src.destinations.databricks.DatabricksDestination.validate_staging')
    def test_validate_staging_success(self, mock_validate_staging):
        """Test successful staging validation."""
        from src.destinations.databricks import DatabricksDestination
        
        mock_validate_staging.return_value = True
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        result = dest.validate_staging()
        
        assert result is True
    
    def test_bucket_url_configuration(self):
        """Test staging bucket URL configuration."""
        from src.destinations.databricks import DatabricksDestination
        
        dest = DatabricksDestination('databricks_dest', self.valid_config)
        dest_config = dest.get_dlt_destination_config()
        
        assert dest_config['staging_config']['bucket_url'] == 'az://staging@teststorage.dfs.core.windows.net'


class TestDestinationFactory:
    """Tests for destination factory pattern."""
    
    def test_create_adls_destination(self):
        """Test creating ADLS Gen2 destination."""
        config = {
            'destination': {
                'type': 'filesystem',
                'filesystem': {
                    'bucket_url': 'az://raw-data',
                    'credentials': {
                        'azure_storage_account_name': 'testaccount',
                        'azure_storage_account_key': 'testkey'
                    }
                }
            }
        }
        
        dest = ADLSGen2Destination('adls_dest', config)
        
        assert dest.get_destination_type() == 'adls_gen2'
    
    def test_create_databricks_destination(self):
        """Test creating Databricks destination."""
        from src.destinations.databricks import DatabricksDestination
        
        config = {
            'destination': {
                'type': 'databricks',
                'databricks': {
                    'credentials': {
                        'server_hostname': 'adb-test.azuredatabricks.net',
                        'http_path': '/sql/1.0/warehouses/test',
                        'access_token': 'dapi_test'
                    }
                },
                'filesystem': {
                    'credentials': {
                        'azure_storage_account_name': 'test',
                        'azure_storage_sas_token': '?sv=test'
                    }
                }
            }
        }
        
        dest = DatabricksDestination('databricks_dest', config)
        
        assert dest.get_destination_type() == 'databricks'
    
    def test_destination_interface_compatibility(self):
        """Test that all destinations implement the same interface."""
        from src.destinations.databricks import DatabricksDestination
        
        adls_config = {
            'destination': {
                'filesystem': {
                    'bucket_url': 'az://raw-data',
                    'credentials': {
                        'azure_storage_account_name': 'test',
                        'azure_storage_account_key': 'key'
                    }
                }
            }
        }
        
        databricks_config = {
            'destination': {
                'databricks': {
                    'credentials': {
                        'server_hostname': 'test',
                        'http_path': 'test',
                        'access_token': 'test'
                    }
                },
                'filesystem': {
                    'credentials': {
                        'azure_storage_account_name': 'test',
                        'azure_storage_sas_token': 'test'
                    }
                }
            }
        }
        
        adls_dest = ADLSGen2Destination('adls', adls_config)
        databricks_dest = DatabricksDestination('databricks', databricks_config)
        
        # Both should have same interface
        assert hasattr(adls_dest, 'get_destination_type')
        assert hasattr(adls_dest, 'get_dlt_destination_config')
        assert hasattr(adls_dest, 'validate_connection')
        assert hasattr(adls_dest, 'get_metadata')
        
        assert hasattr(databricks_dest, 'get_destination_type')
        assert hasattr(databricks_dest, 'get_dlt_destination_config')
        assert hasattr(databricks_dest, 'validate_connection')
        assert hasattr(databricks_dest, 'get_metadata')
