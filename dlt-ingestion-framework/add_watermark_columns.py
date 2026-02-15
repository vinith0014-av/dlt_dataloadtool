"""Update config to add watermark columns for incremental loads."""
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def update_with_watermarks():
    """Add watermark columns to enable incremental loads."""
    
    # Define jobs with watermark columns
    jobs = [
        # PostgreSQL - orders table with INCREMENTAL load
        {
            'source_type': 'postgresql',
            'source_name': 'postgres_source',
            'table_name': 'orders',
            'load_type': 'INCREMENTAL',  # Changed to INCREMENTAL
            'enabled': 'Y',
            'schema_name': None,
            'watermark_column': 'updated_at',  # Add watermark column
            'last_watermark': '2024-01-01',    # Starting point
            'api_endpoint': None,
            'pagination_type': None,
            'auth_type': None,
            'page_size': None,
            'data_selector': None,
            'primary_key': 'order_id',  # Add primary key for merge
            'chunk_size': None,
            'params': None,
        },
        # MSSQL - users table (FULL load - no watermark needed)
        {
            'source_type': 'mssql',
            'source_name': 'Source1',
            'table_name': 'users',
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
        # API - CoinGecko (FULL load - APIs typically don't support incremental)
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
            'params': '{"vs_currency": "usd", "per_page": 250}',
        },
    ]
    
    # Valid columns
    columns = [
        'source_type', 'source_name', 'table_name', 'load_type', 'enabled',
        'schema_name', 'watermark_column', 'last_watermark',
        'api_endpoint', 'pagination_type', 'auth_type', 'page_size',
        'data_selector', 'primary_key', 'chunk_size', 'params'
    ]
    
    # Create DataFrame
    df = pd.DataFrame(jobs, columns=columns)
    
    # Save
    output_path = Path('config/ingestion_config.xlsx')
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='SourceConfig', index=False)
    
    print("=" * 80)
    print("✅ CONFIGURATION UPDATED WITH WATERMARK COLUMNS")
    print("=" * 80)
    print(f"\nFile: {output_path}")
    print(f"\nEnabled Jobs ({len(jobs)}):\n")
    
    for idx, job in enumerate(jobs, 1):
        print(f"{idx}. {job['source_name']}.{job['table_name']}")
        print(f"   Source: {job['source_type']}")
        print(f"   Load Type: {job['load_type']}")
        
        if job['load_type'] == 'INCREMENTAL':
            print(f"   🔄 Watermark Column: {job['watermark_column']}")
            print(f"   📅 Last Watermark: {job['last_watermark']}")
            print(f"   🔑 Primary Key: {job['primary_key']}")
        
        if job['api_endpoint']:
            print(f"   🌐 API: {job['api_endpoint']}")
        print()
    
    print("=" * 80)
    print("HOW INCREMENTAL LOADS WORK:")
    print("=" * 80)
    print("\n1️⃣  First Run:")
    print("   - Loads all rows where updated_at >= '2024-01-01'")
    print("   - Framework tracks the maximum updated_at value")
    print("\n2️⃣  Subsequent Runs:")
    print("   - Only loads rows with updated_at > last maximum value")
    print("   - Automatically updates last_watermark in pipeline state")
    print("\n3️⃣  Merge Strategy:")
    print("   - Uses primary_key to identify existing records")
    print("   - Updates existing rows, inserts new rows")
    print("=" * 80)
    print("\n💡 TIP: To test incremental load:")
    print("   1. Run ingestion once")
    print("   2. Update some rows in the orders table (change updated_at)")
    print("   3. Run ingestion again - only updated rows will be loaded")
    print("=" * 80)

if __name__ == "__main__":
    update_with_watermarks()
