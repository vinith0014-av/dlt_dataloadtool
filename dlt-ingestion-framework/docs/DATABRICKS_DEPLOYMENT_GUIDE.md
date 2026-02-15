# DLT Framework - Databricks Deployment Guide

## 🎯 Secret Management in Databricks

When deploying to Databricks, you have **three excellent options** for secret management:

### Option 1: Databricks Secrets (✅ COMPLETED)

**Status:** ✅ **Setup Complete - 25 secrets uploaded to scope 'dlt-framework'**

**What you have:**
- ✅ Databricks CLI configured with your workspace
- ✅ Secret scope 'dlt-framework' created
- ✅ All secrets migrated (PostgreSQL, Oracle, MSSQL, Azure SQL, ADLS, APIs)
- ✅ Framework automatically detects and uses these secrets when running in Databricks

**Your secrets:**
- PostgreSQL: 5 secrets (host, port, database, username, password)
- Oracle: 5 secrets  
- MSSQL: 5 secrets
- Azure SQL: 5 secrets
- ADLS Gen2: 3 secrets
- CoinGecko API: 2 secrets

**Why choose this:**
- ✅ Native Databricks integration
- ✅ No Azure subscription needed
- ✅ Simpler setup than Key Vault
- ✅ Works on AWS, Azure, or GCP Databricks
- ✅ Built-in access control

#### Setup Steps (Already Completed ✅)

**1. Install Databricks CLI locally:** ✅
```powershell
pip install databricks-cli
```

**2. Configure Databricks CLI:** ✅
```powershell
python configure_databricks.py
```
Your workspace: `https://dbc-b0d51bcf-8a1a.cloud.databricks.com`

**3. Test Connection:** ✅
```powershell
python test_databricks_connection.py
```
Result: Connection successful

**4. Create Secret Scope:** ✅
```powershell
python create_databricks_scope.py
```
Scope created: `dlt-framework`

**5. Upload Secrets:** ✅
```powershell
python upload_secrets_to_databricks.py
```
Result: All 25 secrets uploaded successfully

**6. Verify Secrets:**
```powershell
databricks secrets list --scope dlt-framework
```

**To add/update a secret:**
```python
from databricks_cli.sdk import ApiClient
from databricks_cli.secrets.api import SecretApi
import configparser
from pathlib import Path

config = configparser.ConfigParser()
config.read(Path.home() / ".databrickscfg")

api_client = ApiClient(host=config['DEFAULT']['host'], token=config['DEFAULT']['token'])
secret_api = SecretApi(api_client)

# Add or update a secret
secret_api.put_secret(scope='dlt-framework', key='new-key', string_value='new-value', bytes_value=None)
```

---

## ✅ Current Setup Status

**What You Have Configured:**

| Component | Status | Details |
|-----------|--------|---------|
| **Databricks CLI** | ✅ Configured | Workspace: `dbc-b0d51bcf-8a1a.cloud.databricks.com` |
| **Secret Scope** | ✅ Created | Scope name: `dlt-framework` |
| **Secrets** | ✅ Uploaded | 25 secrets from secrets.toml |
| **Framework Support** | ✅ Ready | Auto-detects Databricks environment |
| **Local Development** | ✅ Active | Uses secrets.toml |

**Secret Management Flow:**
```
Local Development → secrets.toml (current)
Databricks Deployment → Databricks Secrets (ready to use)
```

**No code changes needed!** Framework automatically switches based on environment.

---

### Option 2: Azure Key Vault (Not Set Up Yet)

**Yes, you CAN use Azure Key Vault with Databricks!** Even if Databricks is your only Azure service.

#### How it works:
1. Databricks notebooks can authenticate to Azure Key Vault using:
   - **Service Principal** (credentials stored in Databricks Secrets)
   - **Managed Identity** (if running on Azure Databricks)
   - **Azure CLI** (for local testing)

2. Your framework's `KeyVaultManager` works seamlessly in Databricks

#### Setup for Databricks + Key Vault:

**1. Create Azure Key Vault:**
```bash
az keyvault create --name kv-dlt-databricks --resource-group your-rg --location eastus
```

**2. Create Service Principal:**
```bash
# Create service principal
az ad sp create-for-rbac --name sp-dlt-databricks --skip-assignment

# Output (save these!):
{
  "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "password": "your-secret",
  "tenant": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
}

# Grant access to Key Vault
az keyvault set-policy --name kv-dlt-databricks \
  --spn <appId> \
  --secret-permissions get list
```

**3. Store Service Principal credentials in Databricks Secrets:**
```powershell
databricks secrets create-scope --scope azure-keyvault-auth
databricks secrets put --scope azure-keyvault-auth --key client-id
# (Paste appId)
databricks secrets put --scope azure-keyvault-auth --key client-secret
# (Paste password)
databricks secrets put --scope azure-keyvault-auth --key tenant-id
# (Paste tenant)
```

**4. Update framework to use Databricks-stored credentials:**
Create a new file: `src/auth/databricks_keyvault.py`

```python
import os
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient

# Get credentials from Databricks secrets
def get_keyvault_client(vault_url: str):
    """Initialize Key Vault client using Service Principal from Databricks."""
    try:
        # Try to import dbutils (only available in Databricks)
        from pyspark.dbutils import DBUtils
        dbutils = DBUtils(spark)
        
        # Get credentials from Databricks secrets
        client_id = dbutils.secrets.get(scope="azure-keyvault-auth", key="client-id")
        client_secret = dbutils.secrets.get(scope="azure-keyvault-auth", key="client-secret")
        tenant_id = dbutils.secrets.get(scope="azure-keyvault-auth", key="tenant-id")
        
        # Create credential
        credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
        
        return SecretClient(vault_url=vault_url, credential=credential)
    except:
        # Fallback to DefaultAzureCredential for local testing
        from azure.identity import DefaultAzureCredential
        return SecretClient(vault_url=vault_url, credential=DefaultAzureCredential())
```

---

### Option 3: Databricks Secrets CLI + Framework Integration

**Best of both worlds:** Use Databricks Secrets but integrate seamlessly with your framework.

#### Update ConfigLoader for Databricks:

Add to `src/config/loader.py`:

```python
def _load_from_databricks(self, source_name: str) -> Optional[Dict]:
    """Load configuration from Databricks Secrets.
    
    Format: {source-name}-{key} in scope 'dlt-framework'
    Example: postgresql-host, postgresql-password
    """
    try:
        # Check if running in Databricks
        from pyspark.dbutils import DBUtils
        from pyspark.sql import SparkSession
        
        spark = SparkSession.builder.getOrCreate()
        dbutils = DBUtils(spark)
        
        config = {}
        scope = "dlt-framework"
        
        # Common keys to try
        keys = ['host', 'port', 'database', 'username', 'password', 
                'sid', 'schema', 'base-url', 'api-key', 'bucket-url',
                'storage-account', 'storage-key']
        
        for key in keys:
            secret_name = f"{source_name}-{key}"
            try:
                value = dbutils.secrets.get(scope=scope, key=secret_name)
                if value:
                    config[key.replace('-', '_')] = value
            except:
                continue
        
        return config if config else None
    except:
        # Not running in Databricks
        return None
```

Then update `get_source_config()` priority:

```python
def get_source_config(self, source_name: str) -> Optional[Dict]:
    # Priority order:
    # 1. Databricks Secrets (if in Databricks)
    # 2. Azure Key Vault
    # 3. Environment Variables
    # 4. secrets.toml
    
    # Try Databricks first
    db_config = self._load_from_databricks(source_name)
    if db_config:
        logger.info(f"[DATABRICKS] Retrieved config from Databricks Secrets")
        return db_config
    
    # ... rest of existing logic
```

---

## Deployment to Databricks (Ready to Deploy)

**Prerequisites:** ✅ All completed!
- ✅ Databricks Secrets configured
- ✅ Framework code ready
- ✅ Excel configuration file ready

### 1. Package Framework

```powershell
# Navigate to framework directory
cd dlt-ingestion-framework

# Create zip file (excluding unnecessary files)
Compress-Archive -Path src, config, run.py, requirements.txt -DestinationPath dlt-framework.zip

# Upload to Databricks workspace
# Option A: Use Databricks CLI
databricks fs cp dlt-framework.zip dbfs:/FileStore/dlt-framework/dlt-framework.zip

# Option B: Use Databricks UI
# Workspace → Data → Add Data → Upload File
```

### 2. Create Databricks Notebook

Create a new notebook in Databricks workspace:

```python
# Cell 1: Install dependencies
%pip install dlt[filesystem] pandas openpyxl azure-storage-blob oracledb psycopg2-binary pyodbc

# Cell 2: Upload your config file
# Use Databricks UI to upload config/ingestion_config.xlsx to DBFS

# Cell 3: Extract framework
import zipfile
import shutil

# Extract framework
with zipfile.ZipFile('/dbfs/FileStore/dlt-framework/dlt-framework.zip', 'r') as zip_ref:
    zip_ref.extractall('/tmp/dlt-framework')

# Add to Python path
import sys
sys.path.insert(0, '/tmp/dlt-framework')

# Cell 4: Test secret access
test_secret = dbutils.secrets.get(scope='dlt-framework', key='postgresql-host')
print(f"✅ Successfully retrieved secret: {test_secret}")

# Cell 5: Run framework
from src.main import main

# Framework will automatically use Databricks Secrets
main()

# Cell 6: View results
# Check ADLS container for Parquet files
display(dbutils.fs.ls("az://raw-data/"))
```

### 3. Alternative: Install as Python Package

```python
# If you have setup.py configured
%pip install /dbfs/FileStore/dlt-framework/dlt-framework.zip

# Then simply import and run
from src.main import main
main()
```

### 4. Schedule as Job

Create a Databricks Job:

1. **Go to:** Workflows → Create Job
2. **Task Type:** Notebook
3. **Notebook:** Select your created notebook
4. **Cluster:** Choose or create cluster
5. **Schedule:** Set desired frequency (daily, hourly, etc.)
6. **Advanced Options:**
   - Timeout: 2 hours (adjust based on data volume)
   - Max retries: 2
   - Email notifications: Your email

**Job Configuration Example:**
```json
{
  "name": "DLT_Ingestion_Daily",
  "tasks": [{
    "task_key": "run_ingestion",
    "notebook_task": {
      "notebook_path": "/Users/your-email/DLT_Ingestion"
    },
    "timeout_seconds": 7200,
    "max_retries": 2
  }],
  "schedule": {
    "quartz_cron_expression": "0 0 2 * * ?",
    "timezone_id": "UTC"
  },
  "email_notifications": {
    "on_failure": ["your-email@example.com"]
  }
}
```

---

## Testing Your Databricks Deployment

### Test Secret Access in Notebook

```python
# Test all secrets
secrets_to_test = [
    'postgresql-host',
    'oracle-host',
    'mssql-host',
    'adls-storage-account',
    'api-coingecko-base-url'
]

print("🔍 Testing Databricks Secrets Access:\n")
for secret_key in secrets_to_test:
    try:
        value = dbutils.secrets.get(scope='dlt-framework', key=secret_key)
        # Don't print actual value for security
        print(f"✅ {secret_key}: Retrieved successfully")
    except Exception as e:
        print(f"❌ {secret_key}: {e}")
```

### Verify Framework Auto-Detection

```python
# This will show which credential source is being used
import logging
logging.basicConfig(level=logging.INFO)

from src.config.loader import ConfigLoader

loader = ConfigLoader()
# Should log: [DATABRICKS] Credential Source: Databricks Secrets

config = loader.get_source_config('postgresql')
print(f"✅ Config loaded: {list(config.keys())}")
```

---

## Deployment to Databricks (Next Steps)

### 1. Upload Framework to DBFS

```powershell
# Zip the framework
Compress-Archive -Path dlt-ingestion-framework\* -DestinationPath dlt-framework.zip

# Upload to Databricks
databricks fs cp dlt-framework.zip dbfs:/FileStore/dlt-framework.zip

# Or use UI: Workspace → Data → Upload File
```

### 2. Create Databricks Notebook

```python
# Notebook: /Users/your-email/DLT_Ingestion

# Install from zip
%pip install /dbfs/FileStore/dlt-framework.zip

# Or install from requirements
%pip install dlt[filesystem] pandas openpyxl azure-storage-blob

# Run framework
from src.main import main
main()
```

### 3. Access Secrets in Code

```python
# Databricks automatically provides dbutils
dbutils.secrets.get(scope="dlt-framework", key="postgresql-password")
```

---

## Comparison: Databricks Secrets vs Azure Key Vault

| Feature | Databricks Secrets | Azure Key Vault |
|---------|-------------------|-----------------|
| **Setup Time** | 5 minutes | 15 minutes |
| **Azure Subscription** | ❌ Not needed | ✅ Required |
| **Works on AWS Databricks** | ✅ Yes | ✅ Yes (via Service Principal) |
| **Works on GCP Databricks** | ✅ Yes | ✅ Yes (via Service Principal) |
| **Native Integration** | ✅ Perfect | ⚠️ Requires auth setup |
| **Access Control** | ✅ Databricks ACLs | ✅ Azure RBAC |
| **Audit Logging** | ✅ Yes | ✅ Yes (more detailed) |
| **Centralized (multi-service)** | ❌ Databricks only | ✅ Any Azure/non-Azure service |
| **Cost** | Free | ~$0.03/10k operations |

---

## Recommended Approach

### For Databricks-Only Deployment:
**Use Databricks Secrets** ⭐
- Simplest setup
- No Azure subscription needed
- Works on any Databricks platform

### For Multi-Service Architecture:
**Use Azure Key Vault**
- Centralized secrets across services
- Share secrets between Databricks, Azure Functions, etc.
- Enterprise-grade audit logging

### Quick Start (Databricks Secrets):

```powershell
# 1. Install Databricks CLI
pip install databricks-cli

# 2. Configure
databricks configure --token

# 3. Create scope
databricks secrets create-scope --scope dlt-framework

# 4. Add your secrets (use the helper script below)
python upload_secrets_to_databricks.py
```

---

## Helper Script: Upload Secrets to Databricks

I'll create this for you - it reads your current `secrets.toml` and uploads to Databricks.

Want me to create `upload_secrets_to_databricks.py`?

---

## Quick Reference

### Your Current Setup (Feb 4, 2026)

**Databricks Connection:**
- Workspace: `https://dbc-b0d51bcf-8a1a.cloud.databricks.com`
- Config file: `~/.databrickscfg`
- Status: ✅ Active

**Secret Scope:**
- Name: `dlt-framework`
- Secrets: 25 uploaded
- Status: ✅ Ready

**Helper Scripts:**
```powershell
# Reconfigure Databricks
python configure_databricks.py

# Test connection
python test_databricks_connection.py

# Add new secret
python -c "
from databricks_cli.sdk import ApiClient
from databricks_cli.secrets.api import SecretApi
import configparser
from pathlib import Path

config = configparser.ConfigParser()
config.read(Path.home() / '.databrickscfg')
api = ApiClient(host=config['DEFAULT']['host'], token=config['DEFAULT']['token'])
SecretApi(api).put_secret('dlt-framework', 'new-key', 'value', None)
"

# List all secrets
python -c "
from databricks_cli.sdk import ApiClient
from databricks_cli.secrets.api import SecretApi
import configparser
from pathlib import Path

config = configparser.ConfigParser()
config.read(Path.home() / '.databrickscfg')
api = ApiClient(host=config['DEFAULT']['host'], token=config['DEFAULT']['token'])
secrets = SecretApi(api).list_secrets('dlt-framework')
for s in secrets['secrets']:
    print(s['key'])
"
```

---

## Summary

✅ **Local Development:** Keep using `secrets.toml` - works as before
✅ **Databricks Deployment:** Secrets ready - framework auto-switches
✅ **No Code Changes:** Framework handles everything automatically

**Next Action:** Deploy to Databricks following the "Deployment to Databricks" section above!

---

## Next Steps (Choose Your Path)

**Choose your path:**

✅ **Databricks Only?** → Use Databricks Secrets (no Azure needed!)

✅ **Already have Azure?** → Use Azure Key Vault (works great with Databricks!)

✅ **Need both?** → Use Key Vault backed Databricks Scope (best of both worlds!)

Let me know which option you prefer, and I'll help you set it up! 🚀
