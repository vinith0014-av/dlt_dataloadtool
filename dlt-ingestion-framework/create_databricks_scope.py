"""
Create Databricks Secret Scope
Creates the 'dlt-framework' secret scope for storing credentials.
"""
from databricks_cli.sdk import ApiClient
from databricks_cli.secrets.api import SecretApi
from pathlib import Path
import configparser

def create_scope():
    """Create secret scope in Databricks."""
    
    print("=" * 70)
    print("Creating Databricks Secret Scope")
    print("=" * 70)
    print()
    
    # Read configuration
    config_file = Path.home() / ".databrickscfg"
    
    if not config_file.exists():
        print("❌ Databricks CLI not configured!")
        print("Please run: python configure_databricks.py")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        
        host = config['DEFAULT']['host']
        token = config['DEFAULT']['token']
        
        # Create API client
        api_client = ApiClient(host=host, token=token)
        secret_api = SecretApi(api_client)
        
        scope_name = "dlt-framework"
        
        # Check if scope already exists
        try:
            scopes = secret_api.list_scopes()
            existing_scopes = [s['name'] for s in scopes.get('scopes', [])]
            
            if scope_name in existing_scopes:
                print(f"✅ Scope '{scope_name}' already exists!")
                print()
                print("To view secrets in this scope:")
                print(f"  python -m databricks_cli.secrets.api list --scope {scope_name}")
                return True
        except:
            pass
        
        # Create scope
        print(f"Creating scope: {scope_name}")
        secret_api.create_scope(
            scope=scope_name, 
            scope_backend_type="DATABRICKS",
            backend_azure_keyvault=None,
            initial_manage_principal="users"
        )
        
        print()
        print("=" * 70)
        print(f"✅ Secret scope '{scope_name}' created successfully!")
        print("=" * 70)
        print()
        print("Next step:")
        print("  Upload your secrets: python upload_secrets_to_databricks.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create scope: {e}")
        print()
        
        # Check if it's a permission error
        if "PERMISSION_DENIED" in str(e):
            print("⚠️  Permission Error:")
            print("  Your user may not have permission to create secret scopes.")
            print("  Options:")
            print("    1. Ask your Databricks admin to create the scope for you")
            print("    2. Use Databricks workspace UI to create the scope:")
            print("       Settings → Secrets → Create Secret Scope")
            print(f"       Scope name: {scope_name}")
        
        return False

if __name__ == "__main__":
    create_scope()
