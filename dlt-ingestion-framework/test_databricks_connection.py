"""
Test Databricks CLI Configuration
Verifies that Databricks CLI is properly configured and can connect.
"""
from databricks_cli.sdk import ApiClient
from databricks_cli.clusters.api import ClusterApi
from pathlib import Path
import configparser

def test_connection():
    """Test Databricks connection using configured credentials."""
    
    print("=" * 70)
    print("Testing Databricks Connection")
    print("=" * 70)
    print()
    
    # Read configuration
    config_file = Path.home() / ".databrickscfg"
    
    if not config_file.exists():
        print("❌ Configuration file not found!")
        print(f"Expected location: {config_file}")
        print()
        print("Please run: python configure_databricks.py")
        return False
    
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        
        host = config['DEFAULT']['host']
        token = config['DEFAULT']['token']
        
        print(f"📍 Host: {host}")
        print(f"🔑 Token: {'*' * 10}{token[-4:]}")  # Show last 4 chars only
        print()
        
        # Create API client
        print("Connecting to Databricks...")
        api_client = ApiClient(host=host, token=token)
        
        # Test connection by listing clusters
        cluster_api = ClusterApi(api_client)
        clusters = cluster_api.list_clusters()
        
        print("✅ Connection Successful!")
        print()
        
        if clusters:
            print(f"Found {len(clusters.get('clusters', []))} cluster(s):")
            for cluster in clusters.get('clusters', [])[:5]:  # Show first 5
                print(f"  - {cluster.get('cluster_name')} (ID: {cluster.get('cluster_id')})")
        else:
            print("No clusters found (this is normal if you haven't created any yet)")
        
        print()
        print("=" * 70)
        print("✅ Databricks CLI is properly configured!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Create secret scope:")
        print("     python create_databricks_scope.py")
        print()
        print("  2. Upload your secrets:")
        print("     python upload_secrets_to_databricks.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Verify your Databricks workspace URL is correct")
        print("  2. Check that your access token is valid (tokens can expire)")
        print("  3. Ensure your IP is allowed in Databricks workspace settings")
        print()
        print("To reconfigure, run: python configure_databricks.py")
        return False

if __name__ == "__main__":
    test_connection()
