"""Create a clean Excel configuration template."""
import pandas as pd
from pathlib import Path

def create_clean_config():
    """Create a clean ingestion_config.xlsx with only valid columns."""
    
    # Define valid columns based on JobConfig model
    valid_columns = [
        'source_type',      # REQUIRED: postgresql, oracle, mssql, azure_sql, api
        'source_name',      # REQUIRED: Name in secrets.toml
        'table_name',       # REQUIRED: Table or API resource name
        'load_type',        # REQUIRED: FULL or INCREMENTAL
        'enabled',          # REQUIRED: Y or N
        # Optional - Database
        'schema_name',      # Oracle schema (optional)
        'watermark_column', # For INCREMENTAL (optional)
        'last_watermark',   # Last value for INCREMENTAL (optional)
        # Optional - API
        'api_endpoint',     # API path like /coins/markets (optional)
        'pagination_type',  # offset, cursor, page_number, etc. (optional)
        'auth_type',        # none, api_key, bearer, basic, oauth2 (optional)
        'page_size',        # Records per page (optional, default 100)
        'data_selector',    # Path to data in response like 'data.items' (optional)
        'primary_key',      # Primary key for merge (optional)
        # Optional - Performance
        'chunk_size',       # Override chunk size for large tables (optional)
        'params',           # Additional params as JSON (optional)
    ]
    
    # Create sample data for 5 common job types
    sample_data = [
        # PostgreSQL FULL load
        {
            'source_type': 'postgresql',
            'source_name': 'postgres_source',
            'table_name': 'customers',
            'load_type': 'FULL',
            'enabled': 'Y',
            'schema_name': None,
            'watermark_column': None,
            'last_watermark': None,
            'api_endpoint': None,
            'pagination_type': None,
            'auth_type': None,
            'page_size': None,
            'data_selector': None,
            'primary_key': None,
            'chunk_size': None,
            'params': None,
        },
        # PostgreSQL INCREMENTAL load
        {
            'source_type': 'postgresql',
            'source_name': 'postgres_source',
            'table_name': 'orders',
            'load_type': 'INCREMENTAL',
            'enabled': 'Y',
            'schema_name': None,
            'watermark_column': 'updated_at',
            'last_watermark': '2024-01-01',
            'api_endpoint': None,
            'pagination_type': None,
            'auth_type': None,
            'page_size': None,
            'data_selector': None,
            'primary_key': 'order_id',
            'chunk_size': None,
            'params': None,
        },
        # Oracle FULL load
        {
            'source_type': 'oracle',
            'source_name': 'oracle_db',
            'table_name': 'EMPLOYEES',
            'load_type': 'FULL',
            'enabled': 'Y',
            'schema_name': 'HR',
            'watermark_column': None,
            'last_watermark': None,
            'api_endpoint': None,
            'pagination_type': None,
            'auth_type': None,
            'page_size': None,
            'data_selector': None,
            'primary_key': None,
            'chunk_size': None,
            'params': None,
        },
        # MSSQL FULL load
        {
            'source_type': 'mssql',
            'source_name': 'Source1',
            'table_name': 'products',
            'load_type': 'FULL',
            'enabled': 'Y',
            'schema_name': None,
            'watermark_column': None,
            'last_watermark': None,
            'api_endpoint': None,
            'pagination_type': None,
            'auth_type': None,
            'page_size': None,
            'data_selector': None,
            'primary_key': None,
            'chunk_size': None,
            'params': None,
        },
        # API load
        {
            'source_type': 'api',
            'source_name': 'coingecko',
            'table_name': 'crypto_prices',
            'load_type': 'FULL',
            'enabled': 'Y',
            'schema_name': None,
            'watermark_column': None,
            'last_watermark': None,
            'api_endpoint': '/coins/markets',
            'pagination_type': 'offset',
            'auth_type': 'api_key',
            'page_size': 250,
            'data_selector': None,
            'primary_key': None,
            'chunk_size': None,
            'params': '{"vs_currency": "usd"}',
        },
    ]
    
    # Create DataFrame
    df = pd.DataFrame(sample_data, columns=valid_columns)
    
    # Save to Excel
    output_path = Path('config/ingestion_config_clean.xlsx')
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='SourceConfig', index=False)
    
    print("=" * 80)
    print("✅ CLEAN CONFIGURATION TEMPLATE CREATED")
    print("=" * 80)
    print(f"\nFile: {output_path}")
    print(f"\nSample Jobs Created: {len(sample_data)}")
    print("\nValid Columns:")
    for col in valid_columns:
        print(f"  - {col}")
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Review the clean template: config/ingestion_config_clean.xlsx")
    print("2. Backup your current file: config/ingestion_config.xlsx")
    print("3. Replace with clean version:")
    print("   - Delete: config/ingestion_config.xlsx")
    print("   - Rename: ingestion_config_clean.xlsx -> ingestion_config.xlsx")
    print("4. Edit job details to match your needs")
    print("5. Run again: python run.py")
    print("=" * 80)
    
    print("\n📋 Sample Jobs in Template:")
    for idx, job in enumerate(sample_data, 1):
        status = "✅ ENABLED" if job['enabled'] == 'Y' else "❌ DISABLED"
        print(f"\n{idx}. {job['source_name']}.{job['table_name']}")
        print(f"   Type: {job['source_type']} | Load: {job['load_type']} | {status}")
        if job['watermark_column']:
            print(f"   Watermark: {job['watermark_column']}")
        if job['api_endpoint']:
            print(f"   API: {job['api_endpoint']}")

if __name__ == "__main__":
    create_clean_config()
