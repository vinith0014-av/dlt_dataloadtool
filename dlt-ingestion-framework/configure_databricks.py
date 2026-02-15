"""
Databricks CLI Configuration Helper
This script helps configure Databricks CLI credentials interactively.
"""
import os
from pathlib import Path

def configure_databricks():
    """Interactive configuration for Databricks CLI."""
    
    print("=" * 70)
    print("Databricks CLI Configuration")
    print("=" * 70)
    print()
    
    # Get Databricks workspace URL
    print("Step 1: Enter your Databricks workspace URL")
    print("Examples:")
    print("  - Azure: https://adb-1234567890123456.12.azuredatabricks.net")
    print("  - AWS: https://dbc-1234567890-abcd.cloud.databricks.com")
    print("  - GCP: https://1234567890123456.7.gcp.databricks.com")
    print()
    host = input("Databricks Host: ").strip()
    
    if not host:
        print("❌ Error: Host cannot be empty")
        return
    
    # Ensure host starts with https://
    if not host.startswith("http"):
        host = f"https://{host}"
    
    print()
    print("Step 2: Generate an Access Token")
    print("  1. Go to your Databricks workspace")
    print("  2. Click on your username (top right)")
    print("  3. Select 'User Settings'")
    print("  4. Go to 'Access Tokens' tab")
    print("  5. Click 'Generate New Token'")
    print("  6. Copy the token (you won't be able to see it again!)")
    print()
    token = input("Databricks Token: ").strip()
    
    if not token:
        print("❌ Error: Token cannot be empty")
        return
    
    # Create .databrickscfg file
    home = Path.home()
    config_file = home / ".databrickscfg"
    
    config_content = f"""[DEFAULT]
host = {host}
token = {token}
"""
    
    # Write configuration
    try:
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print()
        print("=" * 70)
        print("✅ Configuration Successful!")
        print("=" * 70)
        print(f"Configuration saved to: {config_file}")
        print()
        print("Next steps:")
        print("  1. Test connection:")
        print("     python test_databricks_connection.py")
        print()
        print("  2. Create secret scope:")
        print("     python -m databricks_cli.secrets.api create-scope --scope dlt-framework")
        print()
        print("  3. Upload secrets:")
        print("     python upload_secrets_to_databricks.py")
        
    except Exception as e:
        print(f"❌ Error writing configuration: {e}")
        return

if __name__ == "__main__":
    configure_databricks()
