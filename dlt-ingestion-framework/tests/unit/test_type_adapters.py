"""
Unit tests for Type Adapter Callbacks.

Tests Oracle NUMBER, MSSQL TIME conversions for Databricks compatibility.
"""
import pytest
from unittest.mock import Mock

from src.core.type_adapters import (
    oracle_type_adapter_callback,
    mssql_type_adapter_callback,
    postgresql_type_adapter_callback,
    get_type_adapter_for_source
)


class TestOracleTypeAdapter:
    """Test Oracle type adapter conversions."""
    
    def test_oracle_number_to_double(self):
        """Test Oracle NUMBER → DOUBLE conversion."""
        try:
            from sqlalchemy.dialects.oracle import NUMBER
            from sqlalchemy import DOUBLE
            
            # Test decimal NUMBER
            number_type = NUMBER(precision=10, scale=2)
            result = oracle_type_adapter_callback(number_type)
            
            assert result is not None
            assert isinstance(result, type(DOUBLE()))
            
        except ImportError:
            pytest.skip("Oracle dialect not installed")
    
    def test_oracle_number_integer_to_bigint(self):
        """Test Oracle NUMBER(precision, scale=0) → BIGINT conversion."""
        try:
            from sqlalchemy.dialects.oracle import NUMBER
            from sqlalchemy import BIGINT
            
            # Test integer NUMBER (scale=0)
            number_type = NUMBER(precision=10, scale=0)
            result = oracle_type_adapter_callback(number_type)
            
            assert result is not None
            assert isinstance(result, type(BIGINT()))
            
        except ImportError:
            pytest.skip("Oracle dialect not installed")
    
    def test_oracle_date_to_timestamp(self):
        """Test Oracle DATE → TIMESTAMP conversion."""
        try:
            from sqlalchemy.dialects.oracle import DATE
            from sqlalchemy import TIMESTAMP
            
            date_type = DATE()
            result = oracle_type_adapter_callback(date_type)
            
            assert result is not None
            assert isinstance(result, type(TIMESTAMP()))
            
        except ImportError:
            pytest.skip("Oracle dialect not installed")
    
    def test_oracle_varchar_unchanged(self):
        """Test non-converted types return None."""
        try:
            from sqlalchemy.dialects.oracle import VARCHAR2
            
            varchar_type = VARCHAR2(100)
            result = oracle_type_adapter_callback(varchar_type)
            
            assert result is None  # No conversion needed
            
        except ImportError:
            pytest.skip("Oracle dialect not installed")


class TestMSSQLTypeAdapter:
    """Test MSSQL type adapter conversions."""
    
    def test_mssql_time_to_string(self):
        """Test MSSQL TIME → String conversion."""
        try:
            from sqlalchemy.dialects.mssql import TIME
            from sqlalchemy import String
            
            time_type = TIME()
            result = mssql_type_adapter_callback(time_type)
            
            assert result is not None
            assert isinstance(result, type(String()))
            assert result.length == 8  # HH:MM:SS format
            
        except ImportError:
            pytest.skip("MSSQL dialect not installed")
    
    def test_mssql_datetimeoffset_to_timestamp(self):
        """Test MSSQL DATETIMEOFFSET → TIMESTAMP conversion."""
        try:
            from sqlalchemy.dialects.mssql import DATETIMEOFFSET
            from sqlalchemy import TIMESTAMP
            
            dt_type = DATETIMEOFFSET()
            result = mssql_type_adapter_callback(dt_type)
            
            assert result is not None
            assert isinstance(result, type(TIMESTAMP()))
            
        except ImportError:
            pytest.skip("MSSQL dialect not installed")
    
    def test_mssql_money_to_double(self):
        """Test MSSQL MONEY → DOUBLE conversion."""
        try:
            from sqlalchemy.dialects.mssql import MONEY
            from sqlalchemy import DOUBLE
            
            money_type = MONEY()
            result = mssql_type_adapter_callback(money_type)
            
            assert result is not None
            assert isinstance(result, type(DOUBLE()))
            
        except ImportError:
            pytest.skip("MSSQL dialect not installed")


class TestPostgreSQLTypeAdapter:
    """Test PostgreSQL type adapter (minimal conversions)."""
    
    def test_postgresql_interval_to_string(self):
        """Test PostgreSQL INTERVAL → String conversion."""
        try:
            from sqlalchemy.dialects.postgresql import INTERVAL
            from sqlalchemy import String
            
            interval_type = INTERVAL()
            result = postgresql_type_adapter_callback(interval_type)
            
            assert result is not None
            assert isinstance(result, type(String()))
            
        except ImportError:
            pytest.skip("PostgreSQL dialect not installed")
    
    def test_postgresql_varchar_unchanged(self):
        """Test PostgreSQL types generally unchanged."""
        from sqlalchemy import VARCHAR
        
        varchar_type = VARCHAR(100)
        result = postgresql_type_adapter_callback(varchar_type)
        
        assert result is None  # No conversion needed


class TestGetTypeAdapterForSource:
    """Test type adapter selection logic."""
    
    def test_oracle_databricks_returns_adapter(self):
        """Test Oracle → Databricks returns type adapter."""
        adapter = get_type_adapter_for_source('oracle', 'databricks')
        assert adapter is not None
        assert callable(adapter)
        assert adapter == oracle_type_adapter_callback
    
    def test_mssql_databricks_returns_adapter(self):
        """Test MSSQL → Databricks returns type adapter."""
        adapter = get_type_adapter_for_source('mssql', 'databricks')
        assert adapter is not None
        assert callable(adapter)
        assert adapter == mssql_type_adapter_callback
    
    def test_azure_sql_uses_mssql_adapter(self):
        """Test Azure SQL uses MSSQL adapter."""
        adapter = get_type_adapter_for_source('azure_sql', 'databricks')
        assert adapter is not None
        assert adapter == mssql_type_adapter_callback
    
    def test_postgresql_databricks_returns_adapter(self):
        """Test PostgreSQL → Databricks returns adapter."""
        adapter = get_type_adapter_for_source('postgresql', 'databricks')
        assert adapter is not None
        assert callable(adapter)
    
    def test_filesystem_destination_returns_none(self):
        """Test filesystem destination doesn't need type adapter."""
        adapter = get_type_adapter_for_source('oracle', 'filesystem')
        assert adapter is None
    
    def test_unknown_source_returns_none(self):
        """Test unknown source type returns None."""
        adapter = get_type_adapter_for_source('unknown_db', 'databricks')
        assert adapter is None
    
    def test_unity_catalog_destination_returns_adapter(self):
        """Test Unity Catalog destination uses type adapter."""
        adapter = get_type_adapter_for_source('oracle', 'unity_catalog')
        assert adapter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
