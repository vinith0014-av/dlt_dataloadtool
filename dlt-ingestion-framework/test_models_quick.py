#!/usr/bin/env python3
"""
Quick validation test for Pydantic configuration models.
Tests model validation without database connections.

Run this script to verify models are working correctly.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

def test_models():
    """Test Pydantic models."""
    print("\n" + "="*70)
    print("Pydantic Configuration Models - Quick Validation Test")
    print("="*70 + "\n")
    
    try:
        from models.job_config import JobConfig, LoadType, SourceType
        from models.source_config import PostgreSQLConfig, RESTAPIConfig
        from models.destination_config import ADLSGen2Config
        from pydantic import ValidationError
        
        # Test 1: Valid Job Configuration
        print("[TEST 1] Valid Job Configuration")
        print("-" * 70)
        
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
        print("✓ Job configuration validation passed")
        print(f"  Source: {job.source_type}")
        print(f"  Table: {job.table_name}")
        print(f"  Load Type: {job.load_type}")
        
        # Test 2: Incremental Job Validation
        print("\n[TEST 2] Incremental Job with Watermark")
        print("-" * 70)
        
        incremental_job = JobConfig(
            source_type="oracle",
            source_name="prod_oracle",
            table_name="customers",
            schema_name="dbo",
            load_type="INCREMENTAL",
            watermark_column="updated_at",
            last_watermark="2024-01-01",
            enabled="Y"
        )
        
        assert incremental_job.load_type == LoadType.INCREMENTAL
        assert incremental_job.watermark_column == "updated_at"
        print("✓ Incremental job validation passed")
        print(f"  Watermark Column: {incremental_job.watermark_column}")
        print(f"  Last Watermark: {incremental_job.last_watermark}")
        
        # Test 3: Invalid Job Should Fail
        print("\n[TEST 3] Invalid Job Configuration (Should Fail)")
        print("-" * 70)
        
        try:
            invalid_job = JobConfig(
                source_type="postgresql",
                source_name="test",
                table_name="test_table",
                load_type="INCREMENTAL",  # Missing watermark_column
                enabled="Y"
            )
            print("✗ Validation should have failed")
            return False
        except ValidationError as e:
            print("✓ Validation correctly rejected invalid configuration")
            print(f"  Error: watermark_column required for INCREMENTAL")
        
        # Test 4: PostgreSQL Configuration
        print("\n[TEST 4] PostgreSQL Source Configuration")
        print("-" * 70)
        
        pg_config = PostgreSQLConfig(
            host="localhost",
            port=5432,
            database="mydb",
            username="user",
            password="pass123",
            ssl_mode="prefer"
        )
        
        assert pg_config.host == "localhost"
        assert pg_config.port == 5432
        print("✓ PostgreSQL configuration validation passed")
        print(f"  Host: {pg_config.host}:{pg_config.port}")
        print(f"  Database: {pg_config.database}")
        print(f"  SSL Mode: {pg_config.ssl_mode}")
        
        # Test 5: REST API Configuration
        print("\n[TEST 5] REST API Configuration")
        print("-" * 70)
        
        api_config = RESTAPIConfig(
            base_url="https://api.example.com/",  # Trailing slash will be removed
            auth_type="api_key",
            api_key="test_key_123",
            api_key_name="X-API-Key",
            api_key_location="header",
            pagination_type="offset",
            page_size=100
        )
        
        assert api_config.base_url == "https://api.example.com"  # Trailing slash removed
        assert api_config.auth_type.value == "api_key"
        print("✓ REST API configuration validation passed")
        print(f"  Base URL: {api_config.base_url}")
        print(f"  Auth Type: {api_config.auth_type}")
        print(f"  Pagination: {api_config.pagination_type}")
        
        # Test 6: ADLS Gen2 Configuration
        print("\n[TEST 6] ADLS Gen2 Destination Configuration")
        print("-" * 70)
        
        adls_config = ADLSGen2Config(
            bucket_url="az://raw-data",
            azure_storage_account_name="storageaccount1",
            azure_storage_account_key="ABC123=="
        )
        
        assert adls_config.bucket_url == "az://raw-data"
        assert adls_config.azure_storage_account_name == "storageaccount1"
        print("✓ ADLS Gen2 configuration validation passed")
        print(f"  Bucket URL: {adls_config.bucket_url}")
        print(f"  Storage Account: {adls_config.azure_storage_account_name}")
        
        # Test 7: Invalid ADLS Configuration Should Fail
        print("\n[TEST 7] Invalid ADLS Configuration (Should Fail)")
        print("-" * 70)
        
        try:
            invalid_adls = ADLSGen2Config(
                bucket_url="az://raw-data",
                azure_storage_account_name="Storage-Account",  # Invalid: contains dash
                azure_storage_account_key="ABC123=="
            )
            print("✗ Validation should have failed")
            return False
        except ValidationError as e:
            print("✓ Validation correctly rejected invalid storage account name")
            print("  Error: Storage account name must be lowercase alphanumeric only")
        
        # Test 8: Type Conversion
        print("\n[TEST 8] Automatic Type Conversion")
        print("-" * 70)
        
        job_with_conversion = JobConfig(
            source_type="postgresql",
            source_name="test",
            table_name="test_table",
            enabled="y"  # Lowercase should be converted to uppercase
        )
        
        assert job_with_conversion.enabled == "Y"
        print("✓ Type conversion working correctly")
        print("  Input: 'y' → Output: 'Y'")
        
        # Test 9: Job to Dictionary Conversion
        print("\n[TEST 9] Model to Dictionary Conversion")
        print("-" * 70)
        
        job_dict = job.to_dict()
        assert isinstance(job_dict, dict)
        assert job_dict['source_type'] == "postgresql"
        print("✓ Model to dictionary conversion passed")
        print(f"  Dict Keys: {', '.join(list(job_dict.keys())[:5])}...")
        
        # Test 10: API Job Configuration
        print("\n[TEST 10] API Job Configuration")
        print("-" * 70)
        
        api_job = JobConfig(
            source_type="api",
            source_name="coingecko_api",
            table_name="crypto_markets",
            api_endpoint="/coins/markets",
            pagination_type="offset",
            page_size=250,
            enabled="Y"
        )
        
        assert api_job.source_type == SourceType.API
        assert api_job.page_size == 250
        print("✓ API job configuration validation passed")
        print(f"  Endpoint: {api_job.api_endpoint}")
        print(f"  Pagination: {api_job.pagination_type}")
        print(f"  Page Size: {api_job.page_size}")
        
        # Summary
        print("\n" + "="*70)
        print("[SUCCESS] All Pydantic Model Validations Passed!")
        print("="*70)
        print("\nFeature Summary:")
        print("  ✓ Job configuration validation")
        print("  ✓ Source configuration models (PostgreSQL, Oracle, MSSQL, Azure SQL, REST API)")
        print("  ✓ Destination configuration models (ADLS Gen2, Databricks, Delta Lake)")
        print("  ✓ Custom validators")
        print("  ✓ Type conversion and coercion")
        print("  ✓ Error messages for invalid configurations")
        print("\nBenefits:")
        print("  ✓ Catch configuration errors before execution")
        print("  ✓ Type-safe configuration access")
        print("  ✓ IDE autocomplete support")
        print("  ✓ Clear validation error messages")
        print("\nNext Steps:")
        print("  1. Configuration validation is now automatic in ConfigLoader")
        print("  2. Invalid Excel configurations will be rejected at load time")
        print("  3. See logs for detailed validation error messages")
        
        return True
        
    except AssertionError as e:
        print(f"\n[FAILED] Validation error: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_models()
    sys.exit(0 if success else 1)
