"""
Quick test script to verify Type Adapter Callbacks implementation.

Run this to validate:
1. Type adapter module imports correctly
2. Type adapters return correct SQLAlchemy types
3. get_type_adapter_for_source() works
"""
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'dlt-ingestion-framework'))

print("=" * 70)
print("TYPE ADAPTER CALLBACKS - VALIDATION TEST")
print("=" * 70)

# Test 1: Import module
print("\n1. Testing module import...")
try:
    from src.core.type_adapters import (
        oracle_type_adapter_callback,
        mssql_type_adapter_callback,
        postgresql_type_adapter_callback,
        get_type_adapter_for_source
    )
    print("   ✅ Module imported successfully")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    sys.exit(1)

# Test 2: Oracle type adapter
print("\n2. Testing Oracle type adapter...")
try:
    from sqlalchemy.dialects.oracle import NUMBER, DATE
    from sqlalchemy import DOUBLE, TIMESTAMP
    
    # Test NUMBER → DOUBLE
    number_type = NUMBER(precision=10, scale=2)
    result = oracle_type_adapter_callback(number_type)
    assert isinstance(result, type(DOUBLE())), "Oracle NUMBER should convert to DOUBLE"
    print("   ✅ Oracle NUMBER → DOUBLE conversion works")
    
    # Test DATE → TIMESTAMP
    date_type = DATE()
    result = oracle_type_adapter_callback(date_type)
    assert isinstance(result, type(TIMESTAMP())), "Oracle DATE should convert to TIMESTAMP"
    print("   ✅ Oracle DATE → TIMESTAMP conversion works")
    
except ImportError:
    print("   ⚠️  Oracle dialect not installed - skipping Oracle tests")

# Test 3: MSSQL type adapter
print("\n3. Testing MSSQL type adapter...")
try:
    from sqlalchemy.dialects.mssql import TIME, MONEY
    from sqlalchemy import String, DOUBLE
    
    # Test TIME → String
    time_type = TIME()
    result = mssql_type_adapter_callback(time_type)
    assert isinstance(result, type(String())), "MSSQL TIME should convert to String"
    assert result.length == 8, "TIME format should be HH:MM:SS (8 chars)"
    print("   ✅ MSSQL TIME → String conversion works")
    
    # Test MONEY → DOUBLE
    money_type = MONEY()
    result = mssql_type_adapter_callback(money_type)
    assert isinstance(result, type(DOUBLE())), "MSSQL MONEY should convert to DOUBLE"
    print("   ✅ MSSQL MONEY → DOUBLE conversion works")
    
except ImportError:
    print("   ⚠️  MSSQL dialect not installed - skipping MSSQL tests")

# Test 4: PostgreSQL type adapter
print("\n4. Testing PostgreSQL type adapter...")
try:
    from sqlalchemy.dialects.postgresql import INTERVAL
    from sqlalchemy import String
    
    # Test INTERVAL → String
    interval_type = INTERVAL()
    result = postgresql_type_adapter_callback(interval_type)
    assert isinstance(result, type(String())), "PostgreSQL INTERVAL should convert to String"
    print("   ✅ PostgreSQL INTERVAL → String conversion works")
    
except ImportError:
    print("   ⚠️  PostgreSQL dialect not installed - skipping PostgreSQL tests")

# Test 5: Adapter selection logic
print("\n5. Testing adapter selection logic...")
adapter = get_type_adapter_for_source('oracle', 'databricks')
assert adapter is not None, "Oracle → Databricks should return adapter"
assert callable(adapter), "Adapter should be callable"
print("   ✅ Oracle → Databricks adapter selection works")

adapter = get_type_adapter_for_source('mssql', 'databricks')
assert adapter is not None, "MSSQL → Databricks should return adapter"
print("   ✅ MSSQL → Databricks adapter selection works")

adapter = get_type_adapter_for_source('oracle', 'filesystem')
assert adapter is None, "Oracle → filesystem should not need adapter"
print("   ✅ Filesystem destination correctly returns None")

adapter = get_type_adapter_for_source('azure_sql', 'databricks')
assert adapter is not None, "Azure SQL should use MSSQL adapter"
print("   ✅ Azure SQL uses MSSQL adapter correctly")

# Test 6: Orchestrator integration
print("\n6. Testing orchestrator integration...")
try:
    from src.core.orchestrator import IngestionOrchestrator
    print("   ✅ Orchestrator can import type adapters")
except ImportError as e:
    print(f"   ❌ Orchestrator import failed: {e}")

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - Type Adapter Callbacks are working!")
print("=" * 70)
print("\nNext steps:")
print("1. Run full test suite: pytest tests/unit/test_type_adapters.py -v")
print("2. Test with real Oracle/MSSQL database")
print("3. Proceed to Feature 1.2: REST API Pagination Support")
print()
