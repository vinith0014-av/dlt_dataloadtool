"""
Upload secrets from .dlt/secrets.toml to Databricks Secrets
"""
import toml
import sys
from pathlib import Path
import configparser
from databricks_cli.sdk import ApiClient
from databricks_cli.secrets.api import SecretApi

def upload_secrets():
    """Upload secrets from secrets.toml to Databricks."""
    
    # Read Databricks configuration
    config_file = Path.home() / ".databrickscfg"
    if not config_file.exists():
        print("❌ Databricks CLI not configured!")
        print("Please run: python configure_databricks.py")
        sys.exit(1)
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        host = config['DEFAULT']['host']
        token = config['DEFAULT']['token']
        
        # Create API client
        api_client = ApiClient(host=host, token=token)
        secret_api = SecretApi(api_client)
        
    except Exception as e:
        print(f"❌ Failed to initialize Databricks API: {e}")
        sys.exit(1)
    
    # Load secrets
    secrets_path = Path(".dlt/secrets.toml")
    if not secrets_path.exists():
        print(f"❌ File not found: {secrets_path}")
        print("Please run from the dlt-ingestion-framework directory")
        sys.exit(1)
    
    print("📖 Loading secrets from .dlt/secrets.toml...")
    secrets = toml.load(secrets_path)
    
    scope = "dlt-framework"
    
    # Check if scope exists
    print(f"\n🔍 Checking if scope '{scope}' exists...")
    try:
        scopes = secret_api.list_scopes()
        existing_scopes = [s['name'] for s in scopes.get('scopes', [])]
        
        if scope not in existing_scopes:
            print(f"❌ Scope '{scope}' does not exist!")
            print("Please run: python create_databricks_scope.py")
            sys.exit(1)
        else:
            print(f"✅ Scope '{scope}' exists")
    except Exception as e:
        print(f"❌ Failed to check scopes: {e}")
        sys.exit(1)
    
    # Upload PostgreSQL secrets
    if 'sources' in secrets and 'postgresql' in secrets['sources']:
        print("\n📤 Uploading PostgreSQL secrets...")
        pg = secrets['sources']['postgresql']
        secrets_to_upload = [
            ('postgresql-host', str(pg.get('host', ''))),
            ('postgresql-port', str(pg.get('port', ''))),
            ('postgresql-database', pg.get('database', '')),
            ('postgresql-username', pg.get('username', '')),
            ('postgresql-password', pg.get('password', ''))
        ]
        
        for key, value in secrets_to_upload:
            if value:
                try:
                    secret_api.put_secret(scope=scope, key=key, string_value=value, bytes_value=None)
                    print(f"  ✅ {key}")
                except Exception as e:
                    print(f"  ❌ {key}: {e}")
    
    # Upload Oracle secrets
    if 'sources' in secrets and 'oracle' in secrets['sources']:
        print("\n📤 Uploading Oracle secrets...")
        ora = secrets['sources']['oracle']
        secrets_to_upload = [
            ('oracle-host', str(ora.get('host', ''))),
            ('oracle-port', str(ora.get('port', ''))),
            ('oracle-sid', ora.get('sid', '')),
            ('oracle-username', ora.get('username', '')),
            ('oracle-password', ora.get('password', ''))
        ]
        
        for key, value in secrets_to_upload:
            if value:
                try:
                    secret_api.put_secret(scope=scope, key=key, string_value=value, bytes_value=None)
                    print(f"  ✅ {key}")
                except Exception as e:
                    print(f"  ❌ {key}: {e}")
    
    # Upload MSSQL secrets
    if 'sources' in secrets and 'mssql' in secrets['sources']:
        print("\n📤 Uploading MSSQL secrets...")
        ms = secrets['sources']['mssql']
        secrets_to_upload = [
            ('mssql-host', str(ms.get('host', ''))),
            ('mssql-port', str(ms.get('port', ''))),
            ('mssql-database', ms.get('database', '')),
            ('mssql-username', ms.get('username', '')),
            ('mssql-password', ms.get('password', ''))
        ]
        
        for key, value in secrets_to_upload:
            if value:
                try:
                    secret_api.put_secret(scope=scope, key=key, string_value=value, bytes_value=None)
                    print(f"  ✅ {key}")
                except Exception as e:
                    print(f"  ❌ {key}: {e}")
    
    # Upload Azure SQL secrets
    if 'sources' in secrets and 'azure_sql' in secrets['sources']:
        print("\n📤 Uploading Azure SQL secrets...")
        az = secrets['sources']['azure_sql']
        secrets_to_upload = [
            ('azure-sql-host', str(az.get('host', ''))),
            ('azure-sql-port', str(az.get('port', ''))),
            ('azure-sql-database', az.get('database', '')),
            ('azure-sql-username', az.get('username', '')),
            ('azure-sql-password', az.get('password', ''))
        ]
        
        for key, value in secrets_to_upload:
            if value:
                try:
                    secret_api.put_secret(scope=scope, key=key, string_value=value, bytes_value=None)
                    print(f"  ✅ {key}")
                except Exception as e:
                    print(f"  ❌ {key}: {e}")
    
    # Upload ADLS credentials
    if 'destination' in secrets and 'filesystem' in secrets['destination']:
        print("\n📤 Uploading ADLS secrets...")
        fs = secrets['destination']['filesystem']
        creds = fs.get('credentials', {})
        
        secrets_to_upload = [
            ('adls-bucket-url', fs.get('bucket_url', '')),
            ('adls-storage-account', creds.get('azure_storage_account_name', '')),
            ('adls-storage-key', creds.get('azure_storage_account_key', ''))
        ]
        
        for key, value in secrets_to_upload:
            if value:
                try:
                    secret_api.put_secret(scope=scope, key=key, string_value=value, bytes_value=None)
                    print(f"  ✅ {key}")
                except Exception as e:
                    print(f"  ❌ {key}: {e}")
    
    # Upload API secrets
    if 'sources' in secrets and 'api' in secrets['sources']:
        print("\n📤 Uploading API secrets...")
        apis = secrets['sources']['api']
        
        for api_name, api_config in apis.items():
            prefix = f"api-{api_name}"
            secrets_to_upload = [
                (f'{prefix}-base-url', api_config.get('base_url', '')),
                (f'{prefix}-api-key', api_config.get('api_key', ''))
            ]
            
            for key, value in secrets_to_upload:
                if value:
                    try:
                        secret_api.put_secret(scope=scope, key=key, string_value=value, bytes_value=None)
                        print(f"  ✅ {key}")
                    except Exception as e:
                        print(f"  ❌ {key}")
    
    # List all secrets
    print(f"\n📋 Listing all secrets in scope '{scope}':")
    try:
        secret_list = secret_api.list_secrets(scope=scope)
        for secret in secret_list.get('secrets', []):
            print(f"  ✅ {secret['key']}")
    except Exception as e:
        print(f"  ⚠️ Could not list secrets: {e}")
    
    print("\n✅ Migration complete!")
    print(f"\n📝 Next steps:")
    print(f"  1. Your framework already supports Databricks Secrets!")
    print(f"  2. Test in Databricks notebook:")
    print(f"     dbutils.secrets.get(scope='{scope}', key='postgresql-host')")
    print(f"  3. Backup secrets.toml: Rename-Item .dlt\\secrets.toml .dlt\\secrets.toml.backup")

if __name__ == "__main__":
    print("=" * 70)
    print("🔐 Databricks Secrets Upload Tool")
    print("=" * 70)
    print("\n⚠️  Prerequisites:")
    print("  1. Databricks CLI configured: python configure_databricks.py")
    print("  2. Secret scope created: python create_databricks_scope.py")
    print("  3. You have WRITE permission on the secret scope\n")
    
    response = input("Ready to proceed? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    upload_secrets()
