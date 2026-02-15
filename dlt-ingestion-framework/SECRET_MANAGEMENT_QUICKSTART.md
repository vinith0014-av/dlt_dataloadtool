# Secret Management - Quick Reference

## ✅ What You Have Now

Your DLT framework supports **FOUR** credential management options:

### 1. Databricks Secrets ⭐ (Recommended for Databricks)
- **Use when:** Deploying to Databricks (AWS, Azure, or GCP)
- **Azure needed?:** ❌ NO
- **Setup time:** 5 minutes
- **Command:** `python upload_secrets_to_databricks.py`

### 2. Azure Key Vault (Recommended for Multi-Service)
- **Use when:** Using multiple Azure services or need centralized secrets
- **Azure needed?:** ✅ YES
- **Setup time:** 15 minutes
- **Command:** `python migrate_to_keyvault.py`

### 3. Environment Variables (Quick Win)
- **Use when:** Need better security than files, but no cloud setup
- **Azure needed?:** ❌ NO
- **Setup time:** 2 minutes
- **Command:** `.\setup_env_secrets.ps1`

### 4. secrets.toml (Development Only)
- **Use when:** Local development/testing only
- **Azure needed?:** ❌ NO
- **Setup time:** 0 (current setup)
- **Security:** ⚠️ LOW - don't use in production

---

## 🎯 Your Situation: Databricks Deployment

Since you're deploying to **Databricks**, here's your best path:

### Option A: Databricks Secrets (Simplest)

```powershell
# 1. Install Databricks CLI
pip install databricks-cli

# 2. Configure (you'll need your Databricks workspace URL and token)
databricks configure --token

# 3. Upload secrets
python upload_secrets_to_databricks.py

# Done! Framework will auto-detect Databricks and use secrets
```

**Advantages:**
- ✅ No Azure subscription needed
- ✅ Works on any Databricks (AWS, Azure, GCP)
- ✅ Native integration
- ✅ Your framework already supports it!

---

### Option B: Azure Key Vault (If You Want Centralization)

If you **also** plan to use other services (Azure Functions, Logic Apps, etc.) or want centralized secret management:

```powershell
# 1. Install Azure CLI
# Download: https://aka.ms/installazurecliwindows

# 2. Login
az login

# 3. Create Key Vault
az keyvault create --name kv-dlt-databricks --resource-group your-rg --location eastus

# 4. Migrate secrets
python migrate_to_keyvault.py https://kv-dlt-databricks.vault.azure.net/

# 5. Set environment variable
[System.Environment]::SetEnvironmentVariable('AZURE_KEY_VAULT_URL', 'https://kv-dlt-databricks.vault.azure.net/', 'User')
```

**To use in Databricks:** Store Azure Service Principal credentials in Databricks Secrets, then access Key Vault (see [DATABRICKS_DEPLOYMENT_GUIDE.md](DATABRICKS_DEPLOYMENT_GUIDE.md))

---

## 📊 Decision Matrix

| Your Scenario | Recommendation |
|---------------|----------------|
| Databricks only, no other Azure services | **Databricks Secrets** ⭐ |
| Databricks + other Azure services | **Azure Key Vault** |
| Local development, no cloud yet | **Environment Variables** |
| Just testing/exploring | **secrets.toml** (current) |

---

## 🚀 Quick Start Commands

### For Databricks (Recommended):
```powershell
pip install databricks-cli
databricks configure --token
python upload_secrets_to_databricks.py
```

### For Environment Variables (Immediate Win):
```powershell
.\setup_env_secrets.ps1
# Close and reopen terminal
python run.py
```

### For Azure Key Vault:
```powershell
# Requires Azure CLI installed
az login
python migrate_to_keyvault.py https://your-vault.vault.azure.net/
```

---

## 🔄 Priority Order (Automatic Fallback)

Your framework checks sources in this order:

1. **Databricks Secrets** (if running in Databricks)
2. **Azure Key Vault** (if `AZURE_KEY_VAULT_URL` is set)
3. **Environment Variables** (if `DLT_*` variables exist)
4. **secrets.toml** (always available as fallback)

You can have multiple configured - framework picks the first available!

---

## ❓ Common Questions

### Q: Do I need Azure to use your framework?
**A:** No! Only if you want Azure Key Vault. Databricks Secrets or Environment Variables work without Azure.

### Q: Can I use Azure Key Vault with Databricks?
**A:** Yes! Both Azure Databricks and non-Azure Databricks can access Azure Key Vault using Service Principal authentication.

### Q: Which is most secure?
**A:** Azure Key Vault > Databricks Secrets > Environment Variables > secrets.toml

### Q: Which is easiest for Databricks?
**A:** Databricks Secrets (native integration)

---

## 📝 Next Steps

Choose one:

**Path 1 - Databricks Secrets (Fastest)**
```powershell
pip install databricks-cli
databricks configure --token
python upload_secrets_to_databricks.py
```

**Path 2 - Environment Variables (No Cloud Setup)**
```powershell
.\setup_env_secrets.ps1
```

**Path 3 - Azure Key Vault (Enterprise)**
1. Install Azure CLI
2. Follow [docs/KEYVAULT_SETUP.md](KEYVAULT_SETUP.md)

---

## 📚 Full Documentation

- [docs/DATABRICKS_DEPLOYMENT_GUIDE.md](DATABRICKS_DEPLOYMENT_GUIDE.md) - Complete Databricks guide
- [docs/KEYVAULT_SETUP.md](KEYVAULT_SETUP.md) - Azure Key Vault guide
- [docs/SECRET_MANAGEMENT_GUIDE.md](SECRET_MANAGEMENT_GUIDE.md) - Detailed comparison

---

**Answer to your question:** Yes, you can use Azure Key Vault with Databricks! But **Databricks Secrets is simpler** and doesn't require Azure. 🚀
