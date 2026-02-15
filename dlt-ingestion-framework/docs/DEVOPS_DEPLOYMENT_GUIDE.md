# DLT Ingestion Framework - DevOps Deployment Guide

**Document Version**: 1.0  
**Last Updated**: January 30, 2026  
**Framework Version**: Production-Ready

---

##  Overview

This document provides a complete deployment checklist for moving the DLT Multi-Source ADLS Gen2 Ingestion Framework from development to production. It clearly separates responsibilities between **DevOps Team** and **Data Team**.

---

##  Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION ENVIRONMENT                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │  Azure Container │───────▶│  Azure Key Vault │          │
│  │   Instances      │        │   (Secrets)      │          │
│  │  (App Runtime)   │        └──────────────────┘          │
│  └──────────────────┘                 │                      │
│          │                             │                      │
│          │                             ▼                      │
│          │                  ┌──────────────────┐            │
│          │                  │  Managed Identity │            │
│          │                  │  (Authentication) │            │
│          │                  └──────────────────┘            │
│          │                                                    │
│          ▼                                                    │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │   ADLS Gen2      │◀───────│  Source Databases │          │
│  │  (raw-data/)     │        │  PostgreSQL       │          │
│  │  Parquet Files   │        │  Oracle           │          │
│  └──────────────────┘        │  SQL Server       │          │
│                               │  REST APIs        │          │
│                               └──────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

##  Phase 1: Pre-Deployment (DevOps + Data Team)

###  DevOps Team Responsibilities

#### 1.1 Azure Resource Provisioning

**Create Resource Group**:
```bash
az group create \
  --name rg-dlt-ingestion-prod \
  --location eastus \
  --tags Environment=Production Application=DataIngestion
```

**Create ADLS Gen2 Storage Account**:
```bash
az storage account create \
  --name dltprodstorage \
  --resource-group rg-dlt-ingestion-prod \
  --location eastus \
  --sku Standard_LRS \
  --kind StorageV2 \
  --hierarchical-namespace true \
  --tags Environment=Production
```

**Create Container (Filesystem)**:
```bash
az storage fs create \
  --name raw-data \
  --account-name dltprodstorage \
  --auth-mode login
```

**Create Azure Key Vault**:
```bash
az keyvault create \
  --name kv-dlt-prod \
  --resource-group rg-dlt-ingestion-prod \
  --location eastus \
  --enable-rbac-authorization false \
  --tags Environment=Production
```

**Create Azure Container Registry** (for Docker images):
```bash
az acr create \
  --name acrdltprod \
  --resource-group rg-dlt-ingestion-prod \
  --sku Basic \
  --admin-enabled true
```

#### 1.2 Network Security

**Configure Firewall Rules for Source Databases**:

**PostgreSQL**:
```bash
az postgres server firewall-rule create \
  --resource-group rg-databases \
  --server-name postgres-prod \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

**Azure SQL**:
```bash
az sql server firewall-rule create \
  --resource-group rg-databases \
  --server sql-prod \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

**Note**: For on-premises databases (Oracle/SQL Server), configure firewall to allow Azure IP ranges.

#### 1.3 Managed Identity Setup

**Create User-Assigned Managed Identity**:
```bash
az identity create \
  --name mi-dlt-ingestion \
  --resource-group rg-dlt-ingestion-prod
```

**Get Identity Details** (save for later):
```bash
IDENTITY_ID=$(az identity show \
  --name mi-dlt-ingestion \
  --resource-group rg-dlt-ingestion-prod \
  --query id -o tsv)

PRINCIPAL_ID=$(az identity show \
  --name mi-dlt-ingestion \
  --resource-group rg-dlt-ingestion-prod \
  --query principalId -o tsv)

echo "Identity Resource ID: $IDENTITY_ID"
echo "Principal ID: $PRINCIPAL_ID"
```

#### 1.4 Grant Permissions

**Key Vault Access** (Managed Identity):
```bash
az keyvault set-policy \
  --name kv-dlt-prod \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

**ADLS Gen2 Access** (Managed Identity):
```bash
az role assignment create \
  --assignee $PRINCIPAL_ID \
  --role "Storage Blob Data Contributor" \
  --scope /subscriptions/<subscription-id>/resourceGroups/rg-dlt-ingestion-prod/providers/Microsoft.Storage/storageAccounts/dltprodstorage
```

---

###  Data Team Responsibilities

#### 1.5 Prepare Secrets for Migration

**Export Current Secrets** from `.dlt/secrets.toml`:
```toml
# Example structure - Data team provides these values
[sources.postgres_erp]
host = "postgres-prod.postgres.database.azure.com"
database = "erp_db"
username = "dlt_reader"
password = "SecurePassword123!"

[sources.oracle_crm]
host = "10.20.30.40"
port = "1521"
sid = "ORCL"
username = "crm_reader"
password = "OraclePass456!"

[destination.filesystem.credentials]
azure_storage_account_name = "dltprodstorage"
azure_storage_account_key = "base64_key_here=="
```

**Prepare Secret Inventory List**:
Create a spreadsheet with all secrets:

| Secret Name | Source Type | Value | Notes |
|-------------|-------------|-------|-------|
| postgres-erp-host | PostgreSQL | postgres-prod.postgres.database.azure.com | Production server |
| postgres-erp-database | PostgreSQL | erp_db | Database name |
| postgres-erp-username | PostgreSQL | dlt_reader | Read-only user |
| postgres-erp-password | PostgreSQL | SecurePassword123! | Rotate every 90 days |
| oracle-crm-host | Oracle | 10.20.30.40 | On-prem server |
| oracle-crm-sid | Oracle | ORCL | SID not service name |
| adls-storage-account-name | ADLS | dltprodstorage | Gen2 storage |
| adls-storage-account-key | ADLS | base64key... | Primary key |

**Share this securely with DevOps** (use Azure DevOps Secure Files or encrypted email).

---

##  Phase 2: Secret Migration (Data Team → DevOps)

###  DevOps Team Responsibilities

#### 2.1 Upload Secrets to Key Vault

**Using Azure CLI** (DevOps runs these commands):
```bash
# PostgreSQL Secrets
az keyvault secret set --vault-name kv-dlt-prod --name postgres-erp-host --value "postgres-prod.postgres.database.azure.com"
az keyvault secret set --vault-name kv-dlt-prod --name postgres-erp-database --value "erp_db"
az keyvault secret set --vault-name kv-dlt-prod --name postgres-erp-username --value "dlt_reader"
az keyvault secret set --vault-name kv-dlt-prod --name postgres-erp-password --value "SecurePassword123!"
az keyvault secret set --vault-name kv-dlt-prod --name postgres-erp-port --value "5432"

# Oracle Secrets
az keyvault secret set --vault-name kv-dlt-prod --name oracle-crm-host --value "10.20.30.40"
az keyvault secret set --vault-name kv-dlt-prod --name oracle-crm-port --value "1521"
az keyvault secret set --vault-name kv-dlt-prod --name oracle-crm-sid --value "ORCL"
az keyvault secret set --vault-name kv-dlt-prod --name oracle-crm-username --value "crm_reader"
az keyvault secret set --vault-name kv-dlt-prod --name oracle-crm-password --value "OraclePass456!"

# ADLS Secrets
az keyvault secret set --vault-name kv-dlt-prod --name adls-storage-account-name --value "dltprodstorage"
az keyvault secret set --vault-name kv-dlt-prod --name adls-storage-account-key --value "base64_key_here=="
```

**Verify Secrets**:
```bash
az keyvault secret list --vault-name kv-dlt-prod --query "[].name" -o table
```

#### 2.2 Alternative: Data Team Uploads Secrets

**Option A**: Data Team uses migration script (requires Azure CLI authentication):
```bash
# Data team authenticates
az login

# Run migration script
cd dlt-ingestion-framework
python migrate_to_keyvault.py https://kv-dlt-prod.vault.azure.net/

# Output shows migrated secrets:
# [SUCCESS] Migrated postgres-erp-host
# [SUCCESS] Migrated oracle-crm-password
# ... (all secrets)
```

**Option B**: DevOps creates Service Principal for data team:
```bash
# DevOps creates SP
az ad sp create-for-rbac --name sp-dlt-secret-migration

# Grant Key Vault permissions
az keyvault set-policy \
  --name kv-dlt-prod \
  --spn <sp-app-id> \
  --secret-permissions set list

# Data team uses SP credentials
export AZURE_CLIENT_ID="<sp-app-id>"
export AZURE_CLIENT_SECRET="<sp-password>"
export AZURE_TENANT_ID="<tenant-id>"

python migrate_to_keyvault.py https://kv-dlt-prod.vault.azure.net/
```

---

##  Phase 3: Container Deployment (DevOps)

###  DevOps Team Responsibilities

#### 3.1 Build Docker Image

**From Project Root**:
```bash
cd dlt-ingestion-framework

# Build image
docker build -t dlt-ingestion:v1.0 .

# Test locally (optional)
docker run --rm \
  -e AZURE_KEY_VAULT_URL='https://kv-dlt-prod.vault.azure.net/' \
  -e AZURE_CLIENT_ID='<your-sp-id>' \
  -e AZURE_CLIENT_SECRET='<your-sp-secret>' \
  -e AZURE_TENANT_ID='<your-tenant-id>' \
  dlt-ingestion:v1.0
```

#### 3.2 Push to Azure Container Registry

```bash
# Login to ACR
az acr login --name acrdltprod

# Tag image
docker tag dlt-ingestion:v1.0 acrdltprod.azurecr.io/dlt-ingestion:v1.0
docker tag dlt-ingestion:v1.0 acrdltprod.azurecr.io/dlt-ingestion:latest

# Push to registry
docker push acrdltprod.azurecr.io/dlt-ingestion:v1.0
docker push acrdltprod.azurecr.io/dlt-ingestion:latest
```

#### 3.3 Deploy Azure Container Instance

**Production Deployment**:
```bash
az container create \
  --resource-group rg-dlt-ingestion-prod \
  --name dlt-ingestion-prod \
  --image acrdltprod.azurecr.io/dlt-ingestion:latest \
  --registry-login-server acrdltprod.azurecr.io \
  --registry-username <acr-username> \
  --registry-password <acr-password> \
  --assign-identity $IDENTITY_ID \
  --environment-variables \
    AZURE_KEY_VAULT_URL='https://kv-dlt-prod.vault.azure.net/' \
  --cpu 2 \
  --memory 4 \
  --restart-policy Never \
  --os-type Linux
```

**Verify Deployment**:
```bash
# Check container status
az container show \
  --resource-group rg-dlt-ingestion-prod \
  --name dlt-ingestion-prod \
  --query "{Status:instanceView.state, IP:ipAddress.ip}" -o table

# View logs
az container logs \
  --resource-group rg-dlt-ingestion-prod \
  --name dlt-ingestion-prod \
  --follow
```

---

##  Phase 4: Scheduling & Automation (DevOps)

###  DevOps Team Responsibilities

#### 4.1 Option A: Azure Logic Apps (Recommended)

**Create Logic App for Daily Execution**:
```bash
# Create Logic App
az logic workflow create \
  --resource-group rg-dlt-ingestion-prod \
  --name logic-dlt-scheduler \
  --definition schedule-workflow.json
```

**schedule-workflow.json**:
```json
{
  "definition": {
    "$schema": "https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#",
    "triggers": {
      "Recurrence": {
        "type": "Recurrence",
        "recurrence": {
          "frequency": "Day",
          "interval": 1,
          "schedule": {
            "hours": ["2"],
            "minutes": [0]
          },
          "timeZone": "Eastern Standard Time"
        }
      }
    },
    "actions": {
      "Create_Container_Group": {
        "type": "ApiConnection",
        "inputs": {
          "host": {
            "connection": {
              "name": "@parameters('$connections')['aci']['connectionId']"
            }
          },
          "method": "put",
          "path": "/subscriptions/@{encodeURIComponent('<subscription-id>')}/resourceGroups/@{encodeURIComponent('rg-dlt-ingestion-prod')}/providers/Microsoft.ContainerInstance/containerGroups/@{encodeURIComponent('dlt-ingestion-prod')}",
          "queries": {
            "x-ms-api-version": "2021-09-01"
          },
          "body": {
            "location": "eastus",
            "properties": {
              "containers": [{
                "name": "dlt-ingestion",
                "properties": {
                  "image": "acrdltprod.azurecr.io/dlt-ingestion:latest",
                  "resources": {
                    "requests": {
                      "cpu": 2,
                      "memoryInGB": 4
                    }
                  },
                  "environmentVariables": [{
                    "name": "AZURE_KEY_VAULT_URL",
                    "value": "https://kv-dlt-prod.vault.azure.net/"
                  }]
                }
              }],
              "osType": "Linux",
              "restartPolicy": "Never"
            }
          }
        }
      }
    }
  }
}
```

#### 4.2 Option B: Azure Data Factory

**Create ADF Pipeline**:
```bash
az datafactory create \
  --resource-group rg-dlt-ingestion-prod \
  --factory-name adf-dlt-prod \
  --location eastus

# Create linked service for Container Instance execution
# Use ADF UI to create pipeline with Custom Activity
```

**ADF Pipeline JSON** (Custom Activity):
```json
{
  "name": "DLT_Ingestion_Pipeline",
  "properties": {
    "activities": [{
      "name": "Run_DLT_Container",
      "type": "Custom",
      "policy": {
        "timeout": "02:00:00",
        "retry": 2
      },
      "typeProperties": {
        "command": "python -m src.main",
        "resourceLinkedService": {
          "referenceName": "AzureBatchLinkedService",
          "type": "LinkedServiceReference"
        }
      }
    }],
    "triggers": [{
      "name": "DailyTrigger",
      "type": "ScheduleTrigger",
      "properties": {
        "recurrence": {
          "frequency": "Day",
          "interval": 1,
          "schedule": {
            "hours": [2],
            "minutes": [0]
          },
          "timeZone": "Eastern Standard Time"
        }
      }
    }]
  }
}
```

#### 4.3 Option C: Simple Cron Job (Azure VM)

**Install on Azure VM**:
```bash
# Setup cron job
crontab -e

# Add daily execution at 2 AM
0 2 * * * az container start --resource-group rg-dlt-ingestion-prod --name dlt-ingestion-prod >> /var/log/dlt-cron.log 2>&1
```

---

##  Phase 5: Monitoring & Alerting (DevOps)

###  DevOps Team Responsibilities

#### 5.1 Application Insights Setup

**Create Application Insights**:
```bash
az monitor app-insights component create \
  --app dlt-ingestion-insights \
  --location eastus \
  --resource-group rg-dlt-ingestion-prod \
  --application-type other
```

**Get Instrumentation Key**:
```bash
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app dlt-ingestion-insights \
  --resource-group rg-dlt-ingestion-prod \
  --query instrumentationKey -o tsv)

echo "Instrumentation Key: $INSTRUMENTATION_KEY"
```

**Add to Container Deployment**:
```bash
az container create \
  --resource-group rg-dlt-ingestion-prod \
  --name dlt-ingestion-prod \
  ... (previous parameters) \
  --environment-variables \
    AZURE_KEY_VAULT_URL='https://kv-dlt-prod.vault.azure.net/' \
    APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY
```

#### 5.2 Log Analytics Workspace

**Create Workspace**:
```bash
az monitor log-analytics workspace create \
  --resource-group rg-dlt-ingestion-prod \
  --workspace-name law-dlt-prod
```

**Link Container Instance**:
```bash
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group rg-dlt-ingestion-prod \
  --workspace-name law-dlt-prod \
  --query customerId -o tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group rg-dlt-ingestion-prod \
  --workspace-name law-dlt-prod \
  --query primarySharedKey -o tsv)

# Add to container deployment
az container create \
  ... (previous parameters) \
  --log-analytics-workspace $WORKSPACE_ID \
  --log-analytics-workspace-key $WORKSPACE_KEY
```

#### 5.3 Create Alerts

**Job Failure Alert**:
```bash
az monitor metrics alert create \
  --name alert-dlt-job-failure \
  --resource-group rg-dlt-ingestion-prod \
  --scopes /subscriptions/<subscription-id>/resourceGroups/rg-dlt-ingestion-prod \
  --condition "count ContainerExitCode_1 > 0" \
  --description "DLT Ingestion Job Failed" \
  --evaluation-frequency 5m \
  --window-size 15m \
  --action email devops@company.com
```

**Container Restart Alert**:
```bash
az monitor metrics alert create \
  --name alert-dlt-container-restart \
  --resource-group rg-dlt-ingestion-prod \
  --scopes /subscriptions/<subscription-id>/resourceGroups/rg-dlt-ingestion-prod \
  --condition "count ContainerRestartCount > 3" \
  --description "DLT Container Restarted Multiple Times" \
  --action email devops@company.com
```

#### 5.4 ADLS Monitoring

**Storage Analytics Logs**:
```bash
az storage logging update \
  --account-name dltprodstorage \
  --services b \
  --log rwd \
  --retention 90
```

**Create Dashboard**:
```bash
# Query Log Analytics for ingestion metrics
# Example Kusto query:
ContainerInstanceLog_CL
| where Message contains "SUCCESS" or Message contains "FAILED"
| summarize SuccessCount=countif(Message contains "SUCCESS"), 
            FailureCount=countif(Message contains "FAILED") 
  by bin(TimeGenerated, 1d)
| render timechart
```

---

##  Phase 6: Production Validation (Data Team + DevOps)

###  Data Team Responsibilities

#### 6.1 Validate Job Configuration

**Check ingestion_config.xlsx**:
- ✅ All enabled jobs (`enabled='Y'`) are production tables
- ✅ Watermark columns are correct for incremental loads
- ✅ Source names match Key Vault secret naming (e.g., `postgres_erp` → `postgres-erp-*`)
- ✅ ADLS layout configuration is correct

**Verify ADLS Output Structure**:
```bash
# Use Azure Storage Explorer or CLI
az storage fs file list \
  --file-system raw-data \
  --account-name dltprodstorage \
  --auth-mode login

# Expected structure:
# raw-data/
#   orders/2026/01/30/123456.0.abc123.parquet
#   customers/2026/01/30/123457.0.def456.parquet
```

#### 6.2 Test Data Quality

**Run Sample Queries** (Azure Synapse/Databricks):
```sql
-- Example: Verify row counts match source
SELECT 
    DATE(file_path) AS partition_date,
    COUNT(*) AS row_count
FROM parquet.`abfss://raw-data@dltprodstorage.dfs.core.windows.net/orders/**/*.parquet`
GROUP BY DATE(file_path)
ORDER BY partition_date DESC
LIMIT 10;
```

**Validate Incremental Loads**:
```bash
# Check watermark progression in audit CSV
cat metadata/audit_20260130.csv | grep "orders" | tail -5
```

#### 6.3 Document Data Lineage

**Create Data Catalog Entry**:
- Source: PostgreSQL `erp_db.orders`
- Destination: `az://raw-data/orders/YYYY/MM/DD/`
- Schedule: Daily at 2 AM EST
- Owner: Data Engineering Team
- SLA: 99.5% availability

---

###  DevOps Team Responsibilities

#### 6.4 Performance Validation

**Monitor Container Resources**:
```bash
# Check CPU/Memory usage
az container show \
  --resource-group rg-dlt-ingestion-prod \
  --name dlt-ingestion-prod \
  --query "containers[0].instanceView.currentState.{CPU:cpuUsage,Memory:memoryUsage}" -o table
```

**Tune Resources if Needed**:
- Increase CPU if jobs timeout
- Increase memory if seeing OOM errors
- Consider parallel execution for large table counts

#### 6.5 Disaster Recovery

**Backup Configuration**:
```bash
# Export Key Vault secrets (secure location)
az keyvault secret list --vault-name kv-dlt-prod --query "[].{Name:name}" -o tsv > secrets_backup.txt

# Backup ingestion_config.xlsx to Azure Blob
az storage blob upload \
  --account-name dltprodstorage \
  --container-name config-backup \
  --file config/ingestion_config.xlsx \
  --name ingestion_config_backup_$(date +%Y%m%d).xlsx
```

**Document Recovery Procedures**:
1. Rebuild container from ACR
2. Restore Key Vault secrets
3. Redeploy container instance with managed identity
4. Verify first successful run

---

##  Phase 7: Handoff & Documentation

###  DevOps Team Deliverables

#### 7.1 Environment Details Document

Create `PRODUCTION_ENVIRONMENT.md`:
```markdown
# Production Environment Details

## Azure Resources
- **Resource Group**: rg-dlt-ingestion-prod
- **Container Instance**: dlt-ingestion-prod
- **Key Vault**: kv-dlt-prod
- **Storage Account**: dltprodstorage (ADLS Gen2)
- **Container Registry**: acrdltprod
- **Managed Identity**: mi-dlt-ingestion

## Access & Permissions
- Managed Identity Principal ID: <principal-id>
- Key Vault URL: https://kv-dlt-prod.vault.azure.net/
- ADLS Endpoint: https://dltprodstorage.dfs.core.windows.net/

## Monitoring
- Application Insights: dlt-ingestion-insights
- Log Analytics Workspace: law-dlt-prod
- Alert Action Group: ag-devops-team

## Schedule
- Execution: Daily at 2:00 AM EST
- Scheduler: Azure Logic App (logic-dlt-scheduler)

## Support Contacts
- DevOps Lead: devops-lead@company.com
- Cloud Architect: cloud-architect@company.com
- On-Call: +1-555-ONCALL
```

#### 7.2 Runbook for Operations

Create `RUNBOOK.md`:
```markdown
# DLT Ingestion Framework - Operations Runbook

## Daily Operations

### Check Job Status
```bash
# View container logs
az container logs --resource-group rg-dlt-ingestion-prod --name dlt-ingestion-prod

# Check last execution
az container show --resource-group rg-dlt-ingestion-prod --name dlt-ingestion-prod --query "containers[0].instanceView.currentState"
```

### Manual Execution
```bash
# Start container
az container start --resource-group rg-dlt-ingestion-prod --name dlt-ingestion-prod

# Monitor execution
az container attach --resource-group rg-dlt-ingestion-prod --name dlt-ingestion-prod
```

### Troubleshooting

**Issue**: Job Failed with Exit Code 1
- **Action**: Check logs for Python exceptions
- **Common Causes**: Source database unreachable, Key Vault permission issue

**Issue**: No New Files in ADLS
- **Action**: Verify container executed (check logs)
- **Common Causes**: Schedule not triggered, container stuck

**Issue**: Schema Evolution Warning
- **Action**: Review `_dlt_version/` folder in ADLS
- **Common Causes**: Source table schema changed (column added/removed)
```

---
###  Data Team Deliverables

#### 7.3 Job Catalog

Create spreadsheet `PRODUCTION_JOBS_CATALOG.xlsx`:

| Job ID | Source Type | Source Name | Table Name | Load Type | Schedule | Owner | Status |
|--------|-------------|-------------|------------|-----------|----------|-------|--------|
| 001 | PostgreSQL | postgres_erp | orders | INCREMENTAL | Daily 2 AM | Data Eng | Active |
| 002 | PostgreSQL | postgres_erp | customers | FULL | Daily 2 AM | Data Eng | Active |
| 003 | Oracle | oracle_crm | contacts | INCREMENTAL | Daily 2 AM | CRM Team | Active |
| 004 | MSSQL | mssql_hr | employees | FULL | Weekly | HR Team | Inactive |

#### 7.4 Data Dictionary

Document all ingested tables:
```markdown
# Data Dictionary

## orders Table
- **Source**: PostgreSQL erp_db.orders
- **Destination**: az://raw-data/orders/YYYY/MM/DD/
- **Load Type**: Incremental (watermark: order_date)
- **Row Count**: ~500K rows/day
- **Columns**: order_id, customer_id, order_date, total_amount, status
- **Business Owner**: Sales Team
- **Data Refresh**: Daily at 2 AM

## customers Table
- **Source**: PostgreSQL erp_db.customers
- **Destination**: az://raw-data/customers/YYYY/MM/DD/
- **Load Type**: Full (small table, ~10K rows)
- **Columns**: customer_id, name, email, created_at
```

---

##  Phase 8: Go-Live Checklist

###  Final Pre-Production Checklist

#### DevOps Team Sign-Off
- [ ] All Azure resources provisioned
- [ ] Managed Identity configured with proper permissions
- [ ] Key Vault secrets populated and verified
- [ ] Container image built and pushed to ACR
- [ ] Container instance deployed and tested
- [ ] Scheduler configured (Logic App/ADF/Cron)
- [ ] Monitoring and alerting configured
- [ ] Log Analytics workspace linked
- [ ] Backup procedures documented
- [ ] Disaster recovery plan documented
- [ ] Runbook created and reviewed

#### Data Team Sign-Off
- [ ] All production tables added to `ingestion_config.xlsx`
- [ ] Secrets migrated to Key Vault
- [ ] Source database connectivity verified
- [ ] ADLS output structure validated
- [ ] Sample data quality checks passed
- [ ] Incremental load watermarks tested
- [ ] Data lineage documented
- [ ] Job catalog created
- [ ] Business stakeholders notified
- [ ] Data SLAs defined

#### Joint Sign-Off
- [ ] End-to-end test execution successful
- [ ] Performance benchmarks met (e.g., < 30 min for full run)
- [ ] Security review passed (secrets, network, RBAC)
- [ ] Change management ticket approved
- [ ] Go-live communication sent to stakeholders

---

##  Post-Production Support

### Week 1: Intensive Monitoring

**Daily Tasks**:
- [ ] Review container logs for errors
- [ ] Verify ADLS file creation
- [ ] Check audit CSV for job success rates
- [ ] Monitor alert emails

**Weekly Tasks**:
- [ ] Review Application Insights dashboards
- [ ] Validate data freshness with business users
- [ ] Check Key Vault access logs
- [ ] Review resource utilization (CPU/memory)

### Ongoing Support

**Monthly Tasks**:
- [ ] Review and optimize slow-running jobs
- [ ] Rotate database credentials (90-day policy)
- [ ] Update Docker image with latest dependencies
- [ ] Review storage costs and optimize retention

**Quarterly Tasks**:
- [ ] Disaster recovery drill (rebuild from backup)
- [ ] Security audit (Key Vault, RBAC, network)
- [ ] Performance tuning review
- [ ] Stakeholder satisfaction survey

---

##  Support Contacts

### DevOps Team
- **Primary**: devops-lead@company.com
- **On-Call**: +1-555-DEVOPS
- **Azure Support**: Portal → Help + Support

### Data Team
- **Primary**: data-engineering@company.com
- **Secondary**: data-architect@company.com

### Escalation Path
1. DevOps Engineer (L1) → DevOps Lead (L2)
2. Data Engineer (L1) → Data Architect (L2)
3. Cloud Architect (L3)
4. VP Engineering (L4)

---

##  Reference Documentation

- **Framework Docs**: `dlt-ingestion-framework/README.md`
- **Key Vault Setup**: `KEYVAULT_SETUP.md`
- **Architecture**: `REFACTORING_COMPLETE.md`
- **DLT Documentation**: https://dlthub.com/docs
- **Azure Container Instances**: https://learn.microsoft.com/azure/container-instances/

---

##  Deployment Complete!

**Congratulations!** Your DLT Ingestion Framework is now production-ready.

**Next Steps**:
1. Monitor first week of executions closely
2. Fine-tune resources based on actual usage
3. Expand to additional data sources as needed
4. Consider implementing advanced features (parallel execution, CDC, Delta Lake)

---

**Document Owner**: DevOps Team  
**Last Review**: January 30, 2026  
**Next Review**: April 30, 2026
