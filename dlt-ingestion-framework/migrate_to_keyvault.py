"""
Azure Key Vault Migration Script
Migrates secrets from .dlt/secrets.toml to Azure Key Vault

Usage:
    python migrate_to_keyvault.py <vault-url>

Example:
    python migrate_to_keyvault.py https://kv-dlt-prod.vault.azure.net/
"""
import sys
import toml
from pathlib import Path

try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
except ImportError:
    print(" Azure Key Vault libraries not installed")
    print("   Run: pip install azure-identity azure-keyvault-secrets")
    sys.exit(1)


def migrate_secrets(vault_url: str):
    """Migrate all secrets from secrets.toml to Azure Key Vault."""
    
    # Load secrets.toml
    secrets_file = Path(".dlt/secrets.toml")
    if not secrets_file.exists():
        print(f" Secrets file not found: {secrets_file}")
        print("   Make sure you're running from the dlt-ingestion-framework directory")
        sys.exit(1)
    
    print(f" Loading secrets from: {secrets_file}")
    secrets = toml.load(secrets_file)
    
    # Initialize Key Vault client
    print(f" Connecting to Key Vault: {vault_url}")
    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
    except Exception as e:
        print(f" Failed to connect to Key Vault: {e}")
        print("   Make sure you're authenticated (run: az login)")
        sys.exit(1)
    
    migrated_count = 0
    
    # Migrate source configurations
    if 'sources' in secrets:
        print("\n Migrating data source credentials...")
        
        for source_name, source_config in secrets['sources'].items():
            print(f"\n  Source: {source_name}")
            vault_prefix = source_name.replace('_', '-')
            
            # Migrate each configuration key
            for key, value in source_config.items():
                secret_name = f"{vault_prefix}-{key}"
                try:
                    client.set_secret(secret_name, str(value))
                    print(f"     {secret_name}")
                    migrated_count += 1
                except Exception as e:
                    print(f"     {secret_name}: {e}")
    
    # Migrate ADLS credentials
    if 'destination' in secrets and 'filesystem' in secrets['destination']:
        print("\n Migrating ADLS Gen2 credentials...")
        
        fs_config = secrets['destination']['filesystem']
        
        # Bucket URL
        if 'bucket_url' in fs_config:
            try:
                client.set_secret('adls-bucket-url', fs_config['bucket_url'])
                print(f"     adls-bucket-url")
                migrated_count += 1
            except Exception as e:
                print(f"     adls-bucket-url: {e}")
        
        # Storage account credentials
        if 'credentials' in fs_config:
            creds = fs_config['credentials']
            
            if 'azure_storage_account_name' in creds:
                try:
                    client.set_secret('adls-storage-account-name', creds['azure_storage_account_name'])
                    print(f"     adls-storage-account-name")
                    migrated_count += 1
                except Exception as e:
                    print(f"     adls-storage-account-name: {e}")
            
            if 'azure_storage_account_key' in creds:
                try:
                    client.set_secret('adls-storage-account-key', creds['azure_storage_account_key'])
                    print(f"     adls-storage-account-key")
                    migrated_count += 1
                except Exception as e:
                    print(f"     adls-storage-account-key: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f" Migration complete!")
    print(f"   Total secrets migrated: {migrated_count}")
    print(f"{'='*60}")
    
    # Next steps
    print("\n Next steps:")
    print(f"   1. Set environment variable:")
    print(f"      export AZURE_KEY_VAULT_URL='{vault_url}'")
    print(f"   2. Test the framework:")
    print(f"      python run_simple.py")
    print(f"   3. Verify logs show: ' Credential Source: Azure Key Vault'")
    print(f"   4. (Optional) Backup and remove .dlt/secrets.toml for production")


def list_migrated_secrets(vault_url: str):
    """List all secrets currently in Key Vault."""
    print(f"🔍 Listing secrets in: {vault_url}")
    
    try:
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        
        secrets = list(client.list_properties_of_secrets())
        
        if not secrets:
            print("   No secrets found in Key Vault")
            return
        
        print(f"\n   Found {len(secrets)} secrets:")
        for secret in sorted(secrets, key=lambda x: x.name):
            print(f"   - {secret.name}")
    
    except Exception as e:
        print(f" Failed to list secrets: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("="*60)
    print("Azure Key Vault Migration Tool")
    print("="*60)
    
    if len(sys.argv) < 2:
        print("\n Usage: python migrate_to_keyvault.py <vault-url> [--list]")
        print("\nExamples:")
        print("  Migrate secrets:")
        print("    python migrate_to_keyvault.py https://kv-dlt-prod.vault.azure.net/")
        print("\n  List existing secrets:")
        print("    python migrate_to_keyvault.py https://kv-dlt-prod.vault.azure.net/ --list")
        sys.exit(1)
    
    vault_url = sys.argv[1]
    
    if not vault_url.startswith("https://"):
        print(" Invalid Key Vault URL. Must start with 'https://'")
        print(f"   Example: https://kv-dlt-prod.vault.azure.net/")
        sys.exit(1)
    
    # Check for --list flag
    if len(sys.argv) > 2 and sys.argv[2] == "--list":
        list_migrated_secrets(vault_url)
    else:
        migrate_secrets(vault_url)
