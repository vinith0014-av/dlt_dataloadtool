# Secret Management Options for DLT Framework

## 🔐 Three Ways to Manage Secrets

Your framework now supports **three credential management strategies**, with automatic fallback:

### Priority Order:
1. **Azure Key Vault** (Most Secure - Production)
2. **Environment Variables** (Secure - Medium)
3. **secrets.toml** (Least Secure - Development Only)

---

## Option 1: Azure Key Vault (Recommended for Production)

### Prerequisites
- Azure subscription
- Azure CLI installed
- Contributor access to resource group

### Setup Steps

#### 1. Install Azure CLI
Download from: https://aka.ms/installazurecliwindows

After installation, restart your terminal and verify:
```powershell
az --version
```

#### 2. Login to Azure
```powershell
az login
```

#### 3. Create Key Vault
```powershell
# Create resource group (if needed)
az group create --name rg-dlt-framework --location eastus

# Create Key Vault
az keyvault create `
  --name kv-dlt-prod-unique123 `
  --resource-group rg-dlt-framework `
  --location eastus

# Get the vault URL
az keyvault show --name kv-dlt-prod-unique123 --query properties.vaultUri -o tsv
# Example output: https://kv-dlt-prod-unique123.vault.azure.net/
```

#### 4. Grant Yourself Access
```powershell
# Get your user ID
$userId = az ad signed-in-user show --query id -o tsv

# Grant secret permissions
az keyvault set-policy `
  --name kv-dlt-prod-unique123 `
  --object-id $userId `
  --secret-permissions get list set delete
```

#### 5. Migrate Secrets
```powershell
# Run the built-in migration script
python migrate_to_keyvault.py https://kv-dlt-prod-unique123.vault.azure.net/
```

#### 6. Enable Key Vault in Framework
```powershell
# Set environment variable (permanent)
[System.Environment]::SetEnvironmentVariable('AZURE_KEY_VAULT_URL', 'https://kv-dlt-prod-unique123.vault.azure.net/', 'User')

# Close and reopen terminal, then test
python run.py
```

### Expected Output
```
[KEY VAULT] Credential Source: Azure Key Vault
✅ Successfully loaded credentials from Key Vault
```

---

## Option 2: Environment Variables (Quickest Setup)

### Advantages
- ✅ No Azure account needed
- ✅ No additional software required
- ✅ More secure than file-based secrets
- ✅ Works immediately

### Setup Steps

#### 1. Run the Setup Script
```powershell
# This sets all your current secrets as environment variables
.\setup_env_secrets.ps1
```

#### 2. Close and Reopen Terminal
Environment variables require a fresh session to load.

#### 3. Verify
```powershell
# Check if variables are set
$env:DLT_POSTGRESQL_HOST
$env:DLT_ADLS_STORAGE_ACCOUNT
```

#### 4. Backup secrets.toml
```powershell
# Rename as backup
Rename-Item .dlt\secrets.toml .dlt\secrets.toml.backup
```

#### 5. Test Framework
```powershell
python run.py
```

### Expected Output
```
[ENV] Credential Source: Environment Variables
✅ Loaded PostgreSQL config from environment
✅ Loaded ADLS config from environment
```

### Environment Variable Naming Convention
```
DLT_<SOURCE>_<KEY>

Examples:
DLT_POSTGRESQL_HOST=localhost
DLT_POSTGRESQL_PASSWORD=secret123
DLT_ORACLE_SID=XE
DLT_ADLS_STORAGE_KEY=your_key_here
```

---

## Option 3: secrets.toml (Development Only)

### Current Setup
You're currently using this method. Credentials are in:
```
.dlt/secrets.toml
```

### ⚠️ Security Concerns
- ❌ Credentials stored in plain text file
- ❌ Risk of accidental git commit
- ❌ No audit trail
- ❌ Must be manually secured

### Recommendation
**Migrate to Option 1 or 2 before deploying to production!**

---

## Comparison Matrix

| Feature | Key Vault | Environment Variables | secrets.toml |
|---------|-----------|----------------------|--------------|
| **Security** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Setup Time** | 15 min | 2 min | 0 min (current) |
| **Requirements** | Azure CLI | None | None |
| **Audit Trail** | ✅ Yes | ❌ No | ❌ No |
| **Centralized** | ✅ Yes | ❌ No | ❌ No |
| **Rotation** | ✅ Easy | ⚠️ Manual | ⚠️ Manual |
| **Production Ready** | ✅ Yes | ⚠️ Medium | ❌ No |

---

## Quick Start (Choose One)

### For Local Development (Fastest)
```powershell
# Use environment variables
.\setup_env_secrets.ps1
# Close and reopen terminal
python run.py
```

### For Production (Most Secure)
```powershell
# 1. Install Azure CLI from: https://aka.ms/installazurecliwindows
# 2. Restart terminal
az login
az keyvault create --name kv-dlt-prod-unique --resource-group your-rg --location eastus
python migrate_to_keyvault.py https://kv-dlt-prod-unique.vault.azure.net/
[System.Environment]::SetEnvironmentVariable('AZURE_KEY_VAULT_URL', 'https://kv-dlt-prod-unique.vault.azure.net/', 'User')
# Close and reopen terminal
python run.py
```

---

## Testing Your Setup

After configuring any option, run:

```powershell
python run.py
```

**Look for these log messages:**

✅ **Key Vault Mode:**
```
[KEY VAULT] Credential Source: Azure Key Vault
Retrieved config from Key Vault: postgresql
```

✅ **Environment Variable Mode:**
```
[ENV] Credential Source: Environment Variables
Retrieved config from environment variables: postgresql
```

✅ **secrets.toml Mode:**
```
[LOCAL] Credential Source: .dlt/secrets.toml
Retrieved config from secrets.toml: postgresql
```

---

## Troubleshooting

### Azure CLI Not Found
**Error:** `az: command not found`

**Solution:** 
1. Install from https://aka.ms/installazurecliwindows
2. Restart terminal
3. Run `az --version` to verify

### Key Vault Authentication Failed
**Error:** `Key Vault init failed: DefaultAzureCredential`

**Solution:**
```powershell
# Login to Azure
az login

# Verify access
az keyvault secret list --vault-name kv-dlt-prod-unique
```

### Environment Variables Not Working
**Error:** Variables return empty

**Solution:**
1. Close ALL terminal windows
2. Reopen fresh terminal
3. Verify: `$env:DLT_POSTGRESQL_HOST`

### secrets.toml Not Found
**Error:** `Secrets file not found`

**Solution:**
If you've migrated away from secrets.toml, this is expected! The framework will use your new credential source.

---

## Next Steps

**Recommended path:**

1. **Now:** Use environment variables for immediate improvement
   ```powershell
   .\setup_env_secrets.ps1
   ```

2. **Later:** Migrate to Azure Key Vault for production
   - Install Azure CLI when convenient
   - Follow Key Vault setup steps
   - Framework automatically switches to Key Vault

3. **Finally:** Remove secrets.toml
   ```powershell
   Remove-Item .dlt\secrets.toml
   ```

---

## Support

Questions? Check:
- [docs/KEYVAULT_SETUP.md](docs/KEYVAULT_SETUP.md) - Detailed Key Vault guide
- [migrate_to_keyvault.py](migrate_to_keyvault.py) - Migration script
- [setup_env_secrets.ps1](setup_env_secrets.ps1) - Environment variable setup

Framework automatically handles all three methods with graceful fallback! 🚀
