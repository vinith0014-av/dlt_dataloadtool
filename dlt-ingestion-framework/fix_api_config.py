"""Fix CoinGecko API configuration with correct parameters."""
import pandas as pd
from pathlib import Path

def fix_api_config():
    """Update CoinGecko API with correct pagination parameters."""
    
    jobs = [
        # PostgreSQL - orders table with INCREMENTAL load
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
        # MSSQL - users table
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
        # API - CoinGecko with FIXED pagination (page_number instead of offset)
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
            'pagination_type': 'page_number',  # Changed from 'offset' to 'page_number'
            'auth_type': 'none',  # Changed from 'api_key' to 'none' (free tier)
            'page_size': 100,  # Reduced from 250 to 100 (safer for free tier)
            'data_selector': None,
            'primary_key': None,
            'chunk_size': None,
            'params': '{"vs_currency": "usd", "order": "market_cap_desc"}',  # Added order param
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
    print("✅ API CONFIGURATION FIXED")
    print("=" * 80)
    print(f"\nFile: {output_path}")
    print("\n🔧 Changes Made to CoinGecko API:\n")
    print("  1. Pagination: offset → page_number ✓")
    print("  2. Auth Type: api_key → none (free tier) ✓")
    print("  3. Page Size: 250 → 100 (safer for rate limits) ✓")
    print("  4. Added 'order' parameter for consistent results ✓")
    
    print("\n" + "=" * 80)
    print("ALL 3 JOBS NOW CONFIGURED:")
    print("=" * 80)
    
    for idx, job in enumerate(jobs, 1):
        enabled = "✅ ENABLED" if job['enabled'] == 'Y' else "❌ DISABLED"
        print(f"\n{idx}. {job['source_name']}.{job['table_name']} - {enabled}")
        print(f"   Type: {job['source_type']} | Load: {job['load_type']}")
        
        if job['watermark_column']:
            print(f"   🔄 Incremental: {job['watermark_column']} (from {job['last_watermark']})")
        
        if job['api_endpoint']:
            print(f"   🌐 API: {job['api_endpoint']}")
            print(f"   📄 Pagination: {job['pagination_type']}")
            print(f"   📊 Page Size: {job['page_size']}")
    
    print("\n" + "=" * 80)
    print("READY TO RUN!")
    print("=" * 80)
    print("\nRun: .venv\\Scripts\\python.exe run.py")
    print("\nExpected Results:")
    print("  ✅ postgres_source.orders → 10,003 rows (incremental)")
    print("  ✅ Source1.users → 3 rows (full)")
    print("  ✅ coingecko.crypto_prices → ~100 rows (API)")
    print("=" * 80)

if __name__ == "__main__":
    fix_api_config()
