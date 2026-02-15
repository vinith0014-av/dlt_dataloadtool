"""Update Excel config to match actual database tables."""
import pandas as pd
from pathlib import Path

def create_matching_config():
    """Create config matching actual database tables."""
    
    # Define jobs matching actual tables found
    jobs = [
        # PostgreSQL - orders table (10,003 rows)
        {
            'source_type': 'postgresql',
            'source_name': 'postgres_source',
            'table_name': 'orders',
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
        # MSSQL - users table (3 rows)
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
        # API - CoinGecko (if you want to test API ingestion)
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
    print("✅ CONFIGURATION UPDATED TO MATCH ACTUAL TABLES")
    print("=" * 80)
    print(f"\nFile: {output_path}")
    print(f"\nEnabled Jobs ({len(jobs)}):\n")
    
    for idx, job in enumerate(jobs, 1):
        print(f"{idx}. {job['source_name']}.{job['table_name']}")
        print(f"   Source: {job['source_type']}")
        print(f"   Load: {job['load_type']}")
        if job['api_endpoint']:
            print(f"   API: {job['api_endpoint']}")
        print()
    
    print("=" * 80)
    print("EXPECTED RESULTS:")
    print("=" * 80)
    print("  ✅ postgres_source.orders → ~10,003 rows")
    print("  ✅ Source1.users → ~3 rows")
    print("  ✅ coingecko.crypto_prices → ~250 rows (if API key valid)")
    print("\n  📊 Total expected: ~10,256 rows")
    print("=" * 80)

if __name__ == "__main__":
    create_matching_config()
