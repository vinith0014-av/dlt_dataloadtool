# Azure Key Vault Integration Guide

## Overview

The DLT framework supports **Azure Key Vault** for production-grade secret management instead of storing credentials in `.dlt/secrets.toml`. This provides enterprise security with centralized secret management, access auditing, and role-based access control.

### Key Benefits

- ✅ **No credentials in code** - Secrets stored in Azure cloud, not local files
- ✅ **Auto-detection** - Set `AZURE_KEY_VAULT_URL` environment variable to enable
- ✅ **Multiple auth methods** - Supports Azure CLI, Managed Identity, Service Principal
- ✅ **Fallback support** - Automatically falls back to `secrets.toml` if Key Vault unavailable
- ✅ **Zero code changes** - Framework automatically detects and uses Key Vault

## Quick Start

### 1. Install Dependencies

```bash
pip install azure-identity azure-keyvault-secrets
```

### 2. Create Azure Key Vault

```bash
# Login to Azure
az login

# Create resource group (if needed)
az group create --name rg-data-ingestion --location eastus

# Create Key Vault
az keyvault create \
  --name kv-dlt-prod \
  --resource-group rg-data-ingestion \
  --location eastus

# Get Key Vault URL
az keyvault show --name kv-dlt-prod --query properties.vaultUri -o tsv
# Output: https://kv-dlt-prod.vault.azure.net/
```

### 3. Grant Access Permissions

```bash
# Get your user principal ID
USER_ID=$(az ad signed-in-user show --query id -o tsv)

# Grant yourself access to secrets
az keyvault set-policy \
  --name kv-dlt-prod \
  --object-id $USER_ID \
  --secret-permissions get list set delete
```

### 4. Migrate Secrets to Key Vault

Use the provided migration script to copy secrets from `.dlt/secrets.toml` to Key Vault:

```python
# migrate_to_keyvault.py
import toml
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

VAULT_URL = "https://kv-dlt-prod.vault.azure.net/"

# Load current secrets
secrets = toml.load(".dlt/secrets.toml")

# Initialize Key Vault client
credential = DefaultAzureCredential()
client = SecretClient(vault_url=VAULT_URL, credential=credential)

# Migrate PostgreSQL source
if 'postgres_source' in secrets['sources']:
    pg = secrets['sources']['postgres_source']
    client.set_secret('postgres-source-host', pg['host'])
    client.set_secret('postgres-source-port', str(pg['port']))
    client.set_secret('postgres-source-database', pg['database'])
    client.set_secret('postgres-source-username', pg['username'])
    client.set_secret('postgres-source-password', pg['password'])
    print("✅ Migrated postgres_source")

# Migrate Oracle source
if 'oracle_db' in secrets['sources']:
    ora = secrets['sources']['oracle_db']
    client.set_secret('oracle-db-host', ora['host'])
    client.set_secret('oracle-db-port', str(ora['port']))
    client.set_secret('oracle-db-sid', ora['sid'])
    client.set_secret('oracle-db-username', ora['username'])
    client.set_secret('oracle-db-password', ora['password'])
    print("✅ Migrated oracle_db")

# Migrate ADLS credentials
if 'destination' in secrets and 'filesystem' in secrets['destination']:
    fs = secrets['destination']['filesystem']
    client.set_secret('adls-storage-account-name', fs['credentials']['azure_storage_account_name'])
    client.set_secret('adls-storage-account-key', fs['credentials']['azure_storage_account_key'])
    client.set_secret('adls-bucket-url', fs['bucket_url'])
    print("✅ Migrated ADLS credentials")

print("\n🎉 Migration complete! Run: export AZURE_KEY_VAULT_URL='https://kv-dlt-prod.vault.azure.net/'")
```

Run migration:
```bash
python migrate_to_keyvault.py
```

### 5. Enable Key Vault in Framework

Set environment variable to enable auto-detection:

**Linux/Mac:**
```bash
export AZURE_KEY_VAULT_URL='https://kv-dlt-prod.vault.azure.net/'
python run_simple.py
```

**Windows PowerShell:**
```powershell
$env:AZURE_KEY_VAULT_URL = 'https://kv-dlt-prod.vault.azure.net/'
python run_simple.py
```

**Windows CMD:**
```cmd
set AZURE_KEY_VAULT_URL=https://kv-dlt-prod.vault.azure.net/
python run_simple.py
```

## Secret Naming Convention

The framework uses a **standardized naming pattern** for Key Vault secrets:

### Database Sources

Format: `{source-name}-{config-key}`

Example for `postgres_source`:
```
postgres-source-host         = "mydb.postgres.database.azure.com"
postgres-source-port         = "5432"
postgres-source-database     = "adventureworks"
postgres-source-username     = "pgadmin"
postgres-source-password     = "SecureP@ssw0rd!"
```

Example for `oracle_db`:
```
oracle-db-host      = "oracle-server.example.com"
oracle-db-port      = "1521"
oracle-db-sid       = "ORCL"
oracle-db-username  = "admin"
oracle-db-password  = "OracleP@ss123"
```

### ADLS Gen2 Credentials

```
adls-storage-account-name  = "dltpoctest"
adls-storage-account-key   = "your-storage-account-key-here"
adls-bucket-url           = "az://raw-data"
```

## Authentication Methods

Azure Key Vault supports multiple authentication methods (priority order):

### 1. Azure CLI (Development - Recommended)

```bash
az login
python run_simple.py
```

- ✅ **Best for local development**
- ✅ Inherits your Azure Portal permissions
- ❌ Requires `az` CLI installed

### 2. Managed Identity (Production - Azure VMs/App Service)

Automatically uses Azure VM or App Service managed identity - **no configuration needed**.

```bash
# Enable system-assigned managed identity on Azure VM
az vm identity assign --name my-vm --resource-group my-rg

# Grant Key Vault access to the managed identity
az keyvault set-policy \
  --name kv-dlt-prod \
  --object-id <managed-identity-object-id> \
  --secret-permissions get list
```

- ✅ **Best for production workloads**
- ✅ No credentials to manage
- ❌ Only works on Azure resources

### 3. Service Principal (CI/CD Pipelines)

```bash
# Create service principal
az ad sp create-for-rbac --name sp-dlt-ingestion

# Grant Key Vault access
az keyvault set-policy \
  --name kv-dlt-prod \
  --spn <client-id> \
  --secret-permissions get list
```

Set environment variables:
```bash
export AZURE_CLIENT_ID="<client-id>"
export AZURE_TENANT_ID="<tenant-id>"
export AZURE_CLIENT_SECRET="<client-secret>"
export AZURE_KEY_VAULT_URL="https://kv-dlt-prod.vault.azure.net/"
```

- ✅ **Best for CI/CD pipelines** (GitHub Actions, Azure DevOps)
- ✅ Works outside Azure
- ⚠️ Must protect client secret

## Verification

Check that Key Vault is active:

```bash
python run_simple.py
```

Expected log output:
```
2026-01-29 12:00:00 | INFO     | ✅ Azure Key Vault initialized: https://kv-dlt-prod.vault.azure.net/
2026-01-29 12:00:00 | INFO     | ✅ Credential Source: Azure Key Vault
2026-01-29 12:00:00 | INFO     | Starting job: postgres_source.orders
```

## Troubleshooting

### Issue: `Key Vault URL not provided`

**Solution:** Set environment variable:
```bash
export AZURE_KEY_VAULT_URL='https://your-vault.vault.azure.net/'
```

### Issue: `Authentication failed`

**Solution:** Authenticate via Azure CLI:
```bash
az login
az account show  # Verify correct subscription
```

### Issue: `Secret not found`

**Cause:** Secret doesn't exist or wrong naming convention.

**Solution:** Check secret naming:
```bash
# List all secrets in Key Vault
az keyvault secret list --vault-name kv-dlt-prod --query "[].name" -o table

# Expected format: postgres-source-host (use hyphens, not underscores)
```

### Issue: `Access denied (Forbidden)`

**Cause:** User/Service Principal lacks permissions.

**Solution:** Grant access policy:
```bash
az keyvault set-policy \
  --name kv-dlt-prod \
  --object-id <your-object-id> \
  --secret-permissions get list
```

### Issue: Framework falls back to secrets.toml

**Expected behavior** if:
- `AZURE_KEY_VAULT_URL` not set
- Azure Key Vault libraries not installed
- Authentication fails

**Solution:** Check logs for warning message:
```
⚠️  Key Vault init failed: <error-message>
  Falling back to secrets.toml
```

## Fallback Behavior

The framework **gracefully degrades** if Key Vault is unavailable:

1. **Check environment variable** `AZURE_KEY_VAULT_URL`
   - If not set → use `.dlt/secrets.toml`
   
2. **Check libraries installed** (`azure-identity`, `azure-keyvault-secrets`)
   - If missing → use `.dlt/secrets.toml`
   
3. **Attempt Key Vault connection**
   - If fails → log warning and use `.dlt/secrets.toml`

This ensures:
- ✅ Development works without Azure setup (use `secrets.toml`)
- ✅ Production uses Key Vault for security
- ✅ No manual configuration needed (auto-detection)

## Production Deployment Checklist

- [ ] Azure Key Vault created in production subscription
- [ ] All secrets migrated from `secrets.toml` to Key Vault
- [ ] Managed Identity enabled on Azure VM/App Service
- [ ] Key Vault access policy configured for Managed Identity
- [ ] Environment variable `AZURE_KEY_VAULT_URL` set in production
- [ ] `.dlt/secrets.toml` removed from production deployment (or use `.gitignore`)
- [ ] Test authentication: `az login` (or verify Managed Identity)
- [ ] Run framework and verify log shows "✅ Credential Source: Azure Key Vault"

## Security Best Practices

1. **Rotate secrets regularly** - Update Key Vault secrets every 90 days
2. **Use Managed Identity in production** - Avoid service principal credentials when possible
3. **Enable Key Vault auditing** - Track who accesses secrets
4. **Restrict access with RBAC** - Grant minimum permissions needed
5. **Delete local secrets.toml** - After migrating to Key Vault, remove local credential files
6. **Use separate Key Vaults** - Dev, Test, and Prod environments

## Key Vault vs secrets.toml Comparison

| Feature | secrets.toml | Azure Key Vault |
|---------|-------------|-----------------|
| Security | ❌ Plaintext file | ✅ Encrypted vault |
| Access Control | ❌ File permissions only | ✅ Azure RBAC + policies |
| Auditing | ❌ No audit trail | ✅ Full audit logs |
| Rotation | ❌ Manual file edits | ✅ Centralized rotation |
| Multi-environment | ❌ Different files per env | ✅ Single vault per env |
| Best for | Development | Production |

## Next Steps

- [ ] Set up Azure Key Vault for production environment
- [ ] Migrate secrets using `migrate_to_keyvault.py`
- [ ] Configure Managed Identity on Azure VM
- [ ] Test framework with Key Vault authentication
- [ ] Remove `.dlt/secrets.toml` from production (keep in dev)
- [ ] Document team access process for Key Vault

---

**Questions?** Check framework logs for detailed error messages or consult Azure Key Vault documentation:  
https://learn.microsoft.com/en-us/azure/key-vault/
