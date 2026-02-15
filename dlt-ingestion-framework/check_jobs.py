"""Quick script to check enabled jobs in config."""
import pandas as pd
import sys
from pathlib import Path

def check_jobs():
    """Check which jobs are enabled in the configuration."""
    config_file = Path("config/ingestion_config.xlsx")
    
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return
    
    try:
        # Read the Excel configuration
        df = pd.read_excel(config_file, sheet_name="SourceConfig")
        
        print("=" * 80)
        print("INGESTION CONFIGURATION STATUS")
        print("=" * 80)
        
        # Show all jobs
        print(f"\n📋 Total Jobs: {len(df)}")
        
        # Filter enabled jobs
        if 'enabled' in df.columns:
            enabled_df = df[df['enabled'].astype(str).str.upper() == 'Y']
            print(f"✅ Enabled Jobs: {len(enabled_df)}")
            print(f"❌ Disabled Jobs: {len(df) - len(enabled_df)}")
            
            if len(enabled_df) > 0:
                print("\n" + "=" * 80)
                print("ENABLED JOBS DETAILS:")
                print("=" * 80)
                
                for idx, row in enabled_df.iterrows():
                    print(f"\n{idx + 1}. Job: {row.get('source_name', 'N/A')}.{row.get('table_name', 'N/A')}")
                    print(f"   Source Type: {row.get('source_type', 'N/A')}")
                    print(f"   Load Type: {row.get('load_type', 'N/A')}")
                    print(f"   Enabled: {row.get('enabled', 'N/A')}")
                    
                    # Check for incremental settings
                    if row.get('load_type', '').upper() == 'INCREMENTAL':
                        print(f"   Watermark Column: {row.get('watermark_column', 'N/A')}")
                        print(f"   Last Watermark: {row.get('last_watermark', 'N/A')}")
            else:
                print("\n⚠️  WARNING: No jobs are enabled!")
                print("   To enable jobs, open config/ingestion_config.xlsx")
                print("   and set 'enabled' column to 'Y' for desired jobs.")
        else:
            print("⚠️  WARNING: 'enabled' column not found in configuration!")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_jobs()
