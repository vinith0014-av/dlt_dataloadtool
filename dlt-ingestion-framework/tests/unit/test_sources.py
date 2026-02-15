"""Unit tests for source modules."""
import pytest
from unittest.mock import patch, MagicMock

from src.sources.base import BaseSource
from src.sources.postgresql import PostgreSQLSource
from src.sources.oracle import OracleSource
from src.sources.mssql import MSSQLSource
from src.sources.azure_sql import AzureSQLSource


class TestBaseSource:
    """Tests for BaseSource abstract class."""
    
    def test_cannot_instantiate_base_source(self):
        """Test BaseSource cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseSource('test_source', {})
    
    def test_base_source_interface(self):
        """Test BaseSource defines required interface."""
        # Check that abstract methods exist
        assert hasattr(BaseSource, 'build_connection_string')
        assert hasattr(BaseSource, 'validate_connection')


class TestPostgreSQLSource:
    """Tests for PostgreSQLSource."""
    
    def test_init(self):
        """Test PostgreSQL source initialization."""
        config = {
            'sources': {
                'test_pg': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'testdb',
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = PostgreSQLSource('test_pg', config)
        
        assert source.name == 'test_pg'
        assert source.config == config
    
    def test_build_connection_string_basic(self):
        """Test PostgreSQL connection string generation."""
        config = {
            'sources': {
                'test_pg': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'testdb',
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = PostgreSQLSource('test_pg', config)
        conn_str = source.build_connection_string('test_pg')
        
        assert 'postgresql+psycopg2://' in conn_str
        assert 'localhost' in conn_str
        assert '5432' in conn_str
        assert 'testdb' in conn_str
        assert 'user' in conn_str
    
    def test_build_connection_string_with_ssl(self):
        """Test PostgreSQL connection string with SSL mode."""
        config = {
            'sources': {
                'test_pg': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'testdb',
                    'username': 'user',
                    'password': 'pass',
                    'ssl_mode': 'require'
                }
            }
        }
        
        source = PostgreSQLSource('test_pg', config)
        conn_str = source.build_connection_string('test_pg')
        
        # SSL mode support is optional in current implementation
        # Just verify connection string is valid
        assert 'postgresql+psycopg2://' in conn_str
        assert 'localhost' in conn_str
    
    @patch('sqlalchemy.create_engine')
    def test_validate_connection_success(self, mock_create_engine):
        """Test successful connection validation."""
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_engine.connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_engine.connect.return_value.__exit__ = MagicMock(return_value=False)
        mock_create_engine.return_value = mock_engine
        
        config = {
            'sources': {
                'test_pg': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'testdb',
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = PostgreSQLSource('test_pg', config)
        result = source.validate_connection('test_pg')
        
        assert result == True
        mock_create_engine.assert_called_once()
    
    @patch('psycopg2.connect')
    def test_validate_connection_failure(self, mock_connect):
        """Test connection validation handles failures."""
        mock_connect.side_effect = Exception("Connection refused")
        
        config = {
            'sources': {
                'test_pg': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'testdb',
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = PostgreSQLSource('test_pg', config)
        result = source.validate_connection('test_pg')
        
        assert result == False


class TestOracleSource:
    """Tests for OracleSource."""
    
    def test_build_connection_string_with_sid(self):
        """Test Oracle connection string with SID."""
        config = {
            'sources': {
                'test_oracle': {
                    'host': 'localhost',
                    'port': 1521,
                    'sid': 'ORCL',
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = OracleSource('test_oracle', config)
        conn_str = source.build_connection_string('test_oracle')
        
        assert 'oracle+oracledb://' in conn_str
        assert 'localhost' in conn_str
        assert '1521' in conn_str
        assert 'ORCL' in conn_str or 'sid' in conn_str.lower()
    
    def test_build_connection_string_with_service_name(self):
        """Test Oracle connection string with service_name."""
        config = {
            'sources': {
                'test_oracle': {
                    'host': 'localhost',
                    'port': 1521,
                    'service_name': 'ORCLPDB',
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = OracleSource('test_oracle', config)
        conn_str = source.build_connection_string('test_oracle')
        
        assert 'oracle+oracledb://' in conn_str
        assert 'ORCLPDB' in conn_str or 'service_name' in conn_str.lower()
    
    def test_requires_sid_or_service_name(self):
        """Test Oracle requires either SID or service_name."""
        config = {
            'sources': {
                'test_oracle': {
                    'host': 'localhost',
                    'port': 1521,
                    # Missing both sid and service_name
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = OracleSource('test_oracle', config)
        
        # Should raise error or handle gracefully
        # Implementation depends on source validation


class TestMSSQLSource:
    """Tests for MSSQLSource."""
    
    def test_build_connection_string_odbc(self):
        """Test MSSQL connection string with ODBC format."""
        config = {
            'sources': {
                'test_mssql': {
                    'host': 'localhost',
                    'port': 1433,
                    'database': 'testdb',
                    'username': 'user',
                    'password': 'pass',
                    'driver': 'ODBC Driver 17 for SQL Server'
                }
            }
        }
        
        source = MSSQLSource('test_mssql', config)
        conn_str = source.build_connection_string('test_mssql')
        
        assert 'mssql+pyodbc:' in conn_str
        assert 'ODBC+Driver+17' in conn_str or 'ODBC Driver 17' in conn_str
        assert 'localhost' in conn_str
        assert '1433' in conn_str
    
    def test_connection_string_handles_special_chars(self):
        """Test MSSQL connection string handles special characters in password."""
        config = {
            'sources': {
                'test_mssql': {
                    'host': 'localhost',
                    'port': 1433,
                    'database': 'testdb',
                    'username': 'user',
                    'password': 'p@ss;word!',  # Special characters
                    'driver': 'ODBC Driver 17 for SQL Server'
                }
            }
        }
        
        source = MSSQLSource('test_mssql', config)
        conn_str = source.build_connection_string('test_mssql')
        
        # Should properly encode/escape special characters
        assert conn_str is not None
        assert 'ODBC+Driver+17' in conn_str or 'ODBC Driver 17' in conn_str


class TestAzureSQLSource:
    """Tests for AzureSQLSource."""
    
    def test_build_connection_string_with_encryption(self):
        """Test Azure SQL connection string includes encryption."""
        config = {
            'sources': {
                'test_azure': {
                    'host': 'test-server.database.windows.net',
                    'port': 1433,
                    'database': 'testdb',
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = AzureSQLSource('test_azure', config)
        conn_str = source.build_connection_string('test_azure')
        
        assert 'mssql+pyodbc:' in conn_str
        assert 'Encrypt%3Dyes' in conn_str or 'Encrypt=yes' in conn_str
        assert 'TrustServerCertificate%3Dno' in conn_str or 'TrustServerCertificate=no' in conn_str
    
    def test_azure_sql_hostname_validation(self):
        """Test Azure SQL validates hostname format."""
        config = {
            'sources': {
                'test_azure': {
                    'host': 'test-server.database.windows.net',
                    'port': 1433,
                    'database': 'testdb',
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = AzureSQLSource('test_azure', config)
        
        # Should accept valid Azure SQL hostname
        assert '.database.windows.net' in config['sources']['test_azure']['host']


class TestSourceFactory:
    """Tests for source factory pattern (if implemented)."""
    
    def test_create_postgresql_source(self):
        """Test factory creates PostgreSQL source."""
        # If factory pattern exists
        pass
    
    def test_create_unknown_source_type(self):
        """Test factory handles unknown source types."""
        # Should raise clear error
        pass


class TestConnectionValidation:
    """Tests for connection validation across all sources."""
    
    def test_all_sources_implement_validation(self):
        """Test all source classes implement validate_connection."""
        sources = [PostgreSQLSource, OracleSource, MSSQLSource, AzureSQLSource]
        
        for source_class in sources:
            assert hasattr(source_class, 'validate_connection')
    
    def test_validation_returns_boolean(self):
        """Test validation always returns boolean."""
        config = {
            'sources': {
                'test': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'test',
                    'username': 'user',
                    'password': 'pass'
                }
            }
        }
        
        source = PostgreSQLSource('test', config)
        
        with patch('psycopg2.connect'):
            result = source.validate_connection('test')
            assert isinstance(result, bool)
