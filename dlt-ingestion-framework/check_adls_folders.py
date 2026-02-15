"""
Check what's inside the three DLT folders in ADLS Gen2
"""
from azure.storage.blob import BlobServiceClient
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from src.config.loader import ConfigLoader

def check_folder_contents():
    # Load secrets
    config_loader = ConfigLoader()
    secrets = config_loader.load_secrets()
    
    # Get ADLS credentials
    storage_account = secrets.get('destination', {}).get('filesystem', {}).get('credentials', {}).get('azure_storage_account_name')
    storage_key = secrets.get('destination', {}).get('filesystem', {}).get('credentials', {}).get('azure_storage_account_key')
    container = 'raw-data'
    
    if not storage_account or not storage_key:
        print("❌ Storage credentials not found in secrets")
        return
    
    # Create blob service client
    account_url = f"https://{storage_account}.blob.core.windows.net"
    blob_service_client = BlobServiceClient(account_url=account_url, credential=storage_key)
    container_client = blob_service_client.get_container_client(container)
    
    print("="*80)
    print("CHECKING DLT FOLDERS IN ADLS GEN2")
    print("="*80)
    print(f"Container: {container}")
    print(f"Storage Account: {storage_account}")
    print()
    
    folders_to_check = ['_dlt_loads', 'dlt_pipeline_multi_source_ingestion', '_dlt_version']
    
    for folder_name in folders_to_check:
        print(f"\n📁 FOLDER: {folder_name}")
        print("-"*80)
        
        try:
            # List blobs in this folder
            blobs = container_client.list_blobs(name_starts_with=folder_name)
            blob_list = list(blobs)
            
            if not blob_list:
                print(f"   ⚠️  Empty or doesn't exist")
                continue
            
            print(f"   Total files: {len(blob_list)}")
            print()
            
            # Show first 10 files
            for idx, blob in enumerate(blob_list[:10], 1):
                size_kb = blob.size / 1024
                print(f"   {idx}. {blob.name}")
                print(f"      Size: {size_kb:.2f} KB")
                print(f"      Modified: {blob.last_modified}")
                print()
            
            if len(blob_list) > 10:
                print(f"   ... and {len(blob_list) - 10} more files")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print()
    print("="*80)
    print("WHAT DO THESE FOLDERS CONTAIN?")
    print("="*80)
    print()
    print("1. 📂 _dlt_loads/")
    print("   Purpose: Load tracking and execution history")
    print("   Contains:")
    print("   - load_id files (JSONL format)")
    print("   - Tracks each pipeline execution")
    print("   - Records: start time, end time, status, tables loaded")
    print("   - Used for incremental load checkpointing")
    print()
    
    print("2. 📂 dlt_pipeline_multi_source_ingestion/")
    print("   Purpose: Pipeline state and configuration")
    print("   Contains:")
    print("   - state.jsonl (pipeline state)")
    print("   - schemas.jsonl (table schemas)")
    print("   - Tracks incremental load watermarks")
    print("   - DLT uses this to resume from last checkpoint")
    print()
    
    print("3. 📂 _dlt_version/")
    print("   Purpose: Schema versioning and evolution")
    print("   Contains:")
    print("   - Schema version history")
    print("   - Migration information")
    print("   - Tracks column additions/deletions/type changes")
    print("   - Used for schema evolution detection")
    print()

if __name__ == "__main__":
    try:
        check_folder_contents()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
