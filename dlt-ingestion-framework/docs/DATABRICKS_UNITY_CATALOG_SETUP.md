# Databricks Unity Catalog Destination - Setup Guide

**Created**: February 11, 2026  
**Feature**: Phase 2.1 - Databricks Unity Catalog Destination  
**Status**: ✅ **COMPLETE** - 18/18 tests passing

---

## 📋 Overview

The Databricks Unity Catalog destination enables direct loading of data from DLT into Databricks Delta Lake tables using Unity Catalog three-level namespace (`catalog.schema.table`).

### Architecture

```
┌─────────────┐       ┌──────────────┐       ┌────────────────┐       ┌─────────────────────┐
│   Sources   │  →    │  DLT Pipeline │  →   │  ADLS Staging  │  →   │  Databricks Delta   │
│ (PostgreSQL,│       │   (Parquet)   │      │   (Parquet)    │      │   Lake Tables       │
│  Oracle,    │       │               │      │                │      │  (Unity Catalog)    │
│  MSSQL,     │       │               │      │                │      │                     │
│  APIs)      │       │               │      │                │      │                     │
└─────────────┘       └──────────────┘       └────────────────┘       └─────────────────────┘
```

### Key Features

✅ **Unity Catalog Integration**
- Three-level namespace: `catalog.schema.table`
- Automatic schema evolution
- Delta Lake ACID transactions
- Time travel and versioning

✅ **Cross-Tenant Support**
- ADLS staging can be in different Azure tenant than Databricks
- SAS token authentication for maximum flexibility
- Storage account key support as alternative

✅ **Production-Ready**
- Connection validation before data load
- Staging validation for ADLS access
- Comprehensive error handling
- Detailed logging and monitoring

✅ **Fully Tested**
- 18 unit tests covering all functionality
- Validation of credentials, configuration, and metadata
- Mock testing for external dependencies

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install databricks-sql-connector for Unity Catalog access
pip install databricks-sql-connector
```

### 2. Configure Secrets

Copy `.dlt/secrets.toml.template` to `.dlt/secrets.toml` and configure:

```toml
# ============================================================================
# Databricks Unity Catalog Destination
# ============================================================================

[destination]
type = "databricks"  # Set destination type

[destination.databricks]
server_hostname = "adb-1234567890123456.12.azuredatabricks.net"
http_path = "/sql/1.0/warehouses/abc123def456"
catalog = "main"  # Unity Catalog name
schema = "raw"    # Default schema

[destination.databricks.credentials]
server_hostname = "adb-1234567890123456.12.azuredatabricks.net"
http_path = "/sql/1.0/warehouses/abc123def456"
access_token = "dapi1234567890abcdef1234567890abcdef"

# ============================================================================
# ADLS Staging Configuration (Required)
# ============================================================================

[destination.filesystem]
bucket_url = "az://staging@yourstaging.dfs.core.windows.net"

[destination.filesystem.credentials]
azure_storage_account_name = "yourstaging"
# Option A: SAS Token (recommended for cross-tenant)
azure_storage_sas_token = "?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx..."
# Option B: Storage Account Key
# azure_storage_account_key = "your_account_key_here"
```

### 3. Run Framework

```bash
python run.py
```

The framework will automatically:
1. Detect Databricks destination from `type = "databricks"`
2. Validate Databricks and staging connectivity
3. Stage Parquet files to ADLS Gen2
4. Load data into Delta Lake tables using `COPY INTO`
5. Create tables in Unity Catalog if they don't exist

---

## 🔧 Configuration Details

### Obtaining Databricks Credentials

#### 1. Server Hostname
- Navigate to: Databricks Workspace → Compute → SQL Warehouses
- Click on your SQL Warehouse
- Copy **Server hostname** from **Connection details** tab
- Format: `adb-1234567890123456.12.azuredatabricks.net`

#### 2. HTTP Path
- Same location as Server Hostname
- Copy **HTTP path** from **Connection details** tab
- Format: `/sql/1.0/warehouses/abc123def456`

#### 3. Access Token
- Navigate to: Databricks → Settings → User Settings → Access Tokens
- Click **Generate new token**
- Name: `dlt-ingestion-framework`
- Lifetime: Select appropriate lifetime (90 days recommended)
- Copy and save token immediately (cannot be retrieved later)
- Format: `dapi1234567890abcdef1234567890abcdef`

#### 4. Unity Catalog Configuration
- **Catalog**: Unity Catalog name (default: `main`)
- **Schema**: Default schema for tables (default: `raw`)
- Tables will be created as: `catalog.schema.table_name`

### ADLS Staging Configuration

#### Why Staging is Required

Databricks destination uses a two-stage loading process:
1. **Stage**: DLT writes Parquet files to ADLS Gen2
2. **Load**: Databricks runs `COPY INTO` to load staged files into Delta Lake

Benefits:
- **Cross-tenant support**: ADLS can be in different tenant than Databricks
- **Efficient bulk loading**: `COPY INTO` is optimized for large datasets
- **Idempotency**: Failed loads can be retried without duplicates
- **Audit trail**: Staged files available for debugging

#### SAS Token Generation (Recommended)

1. Navigate to: Azure Portal → Storage Account → Security + networking → Shared access signature
2. Configure permissions:
   - **Allowed services**: ☑️ Blob ☑️ File ☑️ Queue ☑️ Table
   - **Allowed resource types**: ☑️ Service ☑️ Container ☑️ Object
   - **Allowed permissions**: ☑️ Read ☑️ Write ☑️ Delete ☑️ List ☑️ Add ☑️ Create ☑️ Update ☑️ Process
   - **Start time**: Current date/time
   - **End time**: 1 year from now (or as per security policy)
3. Click **Generate SAS and connection string**
4. Copy **SAS token** (starts with `?sv=...`)
5. Paste into `azure_storage_sas_token` in secrets

#### Storage Account Key (Alternative)

1. Navigate to: Azure Portal → Storage Account → Security + networking → Access keys
2. Click **Show keys**
3. Copy **key1** or **key2**
4. Paste into `azure_storage_account_key` in secrets

**Note**: SAS token is recommended for:
- Cross-tenant deployments
- Principle of least privilege
- Easier key rotation

---

## 📊 Usage Examples

### Basic Usage (Default Catalog and Schema)

With `catalog = "main"` and `schema = "raw"`:

```python
# Table will be created as: main.raw.customers
# No job-level configuration needed
```

### Custom Schema per Job

In `config/ingestion_config.xlsx`, add `target_schema` column:

| source_name | table_name | target_schema | ... |
|------------|------------|---------------|-----|
| postgresql | customers  | staging       | ... |
| oracle     | orders     | landing       | ... |

Results:
- `customers` → `main.staging.customers`
- `orders` → `main.landing.orders`

### Custom Catalog Configuration

In `.dlt/secrets.toml`:

```toml
[destination.databricks]
catalog = "bronze"  # Custom catalog
schema = "ingestion"
```

All tables will be created in: `bronze.ingestion.<table_name>`

---

## 🧪 Testing

### Run Unit Tests

```bash
# Run all Databricks destination tests
pytest tests/unit/test_destinations.py::TestDatabricksDestination -v

# Run specific test
pytest tests/unit/test_destinations.py::TestDatabricksDestination::test_full_table_name -v

# Run with coverage
pytest tests/unit/test_destinations.py::TestDatabricksDestination --cov=src.destinations.databricks
```

### Test Results (18/18 passing)

```
✅ test_init - Initialization
✅ test_get_destination_config_basic - Configuration generation
✅ test_databricks_credentials_required - Validation
✅ test_staging_credentials_required - Validation
✅ test_catalog_name_default - Default catalog
✅ test_catalog_name_custom - Custom catalog
✅ test_schema_name_default - Default schema
✅ test_schema_name_from_job - Job-level schema
✅ test_full_table_name - Fully qualified name
✅ test_full_table_name_with_custom_catalog_schema - Custom names
✅ test_sas_token_credentials - SAS token auth
✅ test_storage_key_credentials - Storage key auth
✅ test_missing_staging_auth - Validation error
✅ test_metadata - Metadata generation
✅ test_validate_connection_no_databricks_connector - Missing package
✅ test_validate_connection_success - Connection validation
✅ test_validate_staging_success - Staging validation
✅ test_bucket_url_configuration - Bucket URL
```

---

## 🔍 Validation and Troubleshooting

### Pre-Flight Validation

The framework automatically validates:

1. **Configuration Completeness**
   - Required fields: `server_hostname`, `http_path`, `access_token`
   - Staging credentials: SAS token OR storage key

2. **Databricks Connectivity**
   - Tests SQL Warehouse connection
   - Executes `SELECT 1` test query
   - Validates Unity Catalog access

3. **Staging Connectivity**
   - Tests ADLS Gen2 storage account access
   - Lists containers to verify permissions
   - Validates SAS token or storage key

### Common Issues

#### Issue: "databricks-sql-connector not installed"

**Solution**:
```bash
pip install databricks-sql-connector
```

#### Issue: "Connection failed: Invalid token"

**Causes**:
- Token expired
- Token copied incorrectly (missing characters)
- Wrong workspace (token from different Databricks workspace)

**Solution**:
1. Regenerate access token in Databricks
2. Copy entire token (usually 64+ characters)
3. Verify workspace hostname matches token source

#### Issue: "Staging validation failed"

**Causes**:
- SAS token expired
- Incorrect storage account name
- Missing container permissions

**Solution**:
1. Verify storage account name is correct
2. Regenerate SAS token with appropriate permissions
3. Ensure SAS token includes blob and container access

#### Issue: "Catalog or schema does not exist"

**Causes**:
- Specified catalog doesn't exist in Unity Catalog
- User doesn't have permissions to create schemas

**Solution**:
1. Verify catalog exists: `SHOW CATALOGS;`
2. Create catalog if needed: `CREATE CATALOG IF NOT EXISTS bronze;`
3. Grant permissions: `GRANT CREATE SCHEMA ON CATALOG bronze TO <user>;`

---

## 📈 Monitoring and Metrics

### Logs

Per-source logs with destination information:
```
logs/source_postgresql_20260211_143052.log
logs/destination_databricks_20260211_143052.log
logs/errors/databricks_errors_20260211.log  # Only errors
```

### Log Messages

```
[DATABRICKS] Configured Unity Catalog destination
  Server: adb-1234567890123456.12.azuredatabricks.net
  HTTP Path: /sql/1.0/warehouses/abc123def456
  Catalog: main
  Schema: raw
  Staging: az://staging@dltstaging.dfs.core.windows.net
  Staging Account: dltstaging

[DATABRICKS] Connection validated successfully
  Server: adb-1234567890123456.12.azuredatabricks.net
  Catalog: main

[DATABRICKS] Staging validation successful
  Storage Account: dltstaging
```

### Metadata

Execution metadata with Databricks-specific fields:
```csv
timestamp,job_name,status,rows_processed,destination_type,catalog,schema,table_name
2026-02-11 14:30:52,postgresql.customers,SUCCESS,10000,databricks,main,raw,customers
```

---

## 🔄 Migration from ADLS Gen2 to Databricks

### Step 1: Update Secrets

Change destination type from `filesystem` to `databricks`:

```toml
[destination]
type = "databricks"  # Was: "filesystem"
```

Add Databricks configuration (keep filesystem config for staging):

```toml
[destination.databricks]
server_hostname = "your-workspace.azuredatabricks.net"
http_path = "/sql/1.0/warehouses/your-warehouse"
catalog = "main"
schema = "raw"

[destination.databricks.credentials]
# ... (see full configuration above)

# Keep existing filesystem config as staging
[destination.filesystem]
bucket_url = "az://staging@yourstaging.dfs.core.windows.net"
# ... (existing credentials)
```

### Step 2: Test Connection

```bash
python -c "
from src.destinations.databricks import DatabricksDestination
from src.config import ConfigLoader

secrets = ConfigLoader().load_secrets()
dest = DatabricksDestination('databricks', secrets)
print('Databricks:', dest.validate_connection())
print('Staging:', dest.validate_staging())
"
```

Expected output:
```
Databricks: True
Staging: True
```

### Step 3: Run Framework

```bash
python run.py
```

No code changes needed - framework automatically detects Databricks destination!

---

## 🎯 Best Practices

### 1. Use Dedicated SQL Warehouse

- Create dedicated SQL Warehouse for data ingestion
- Size: Small (for < 1 GB/day) to Large (for > 100 GB/day)
- Auto-stop: 10 minutes (balance between cost and latency)
- Scaling: Enable auto-scaling for variable workloads

### 2. Organize Data with Catalogs and Schemas

```toml
# Bronze layer: Raw data
[destination.databricks]
catalog = "bronze"
schema = "ingestion"

# Silver layer: Cleansed data (separate pipeline)
catalog = "silver"
schema = "curated"

# Gold layer: Business-ready data (separate pipeline)
catalog = "gold"
schema = "reporting"
```

### 3. Use SAS Tokens with Scoped Permissions

```
Blob permissions: Read, Write, List, Add, Create
Valid for: 90 days
Allowed protocols: HTTPS only
Allowed services: Blob only
```

### 4. Monitor Staging Storage Costs

- Enable lifecycle policies to delete staged files after 7 days
- Use cool tier for staging storage
- Monitor storage account metrics in Azure Portal

### 5. Implement Table Naming Conventions

```python
# In ingestion_config.xlsx
source_name | table_name        | target_schema
----------- | ----------------- | -------------
postgresql  | customers         | raw
postgresql  | orders            | raw
oracle      | invoices          | raw

# Results in Unity Catalog:
# main.raw.customers
# main.raw.orders
# main.raw.invoices
```

---

## 📚 Additional Resources

### DLT Documentation
- [DLT Databricks Destination](https://dlthub.com/docs/destinations/databricks)
- [DLT Filesystem Staging](https://dlthub.com/docs/destinations/filesystem)

### Databricks Documentation
- [Unity Catalog Overview](https://docs.databricks.com/en/data-governance/unity-catalog/)
- [SQL Warehouses](https://docs.databricks.com/en/compute/sql-warehouse/)
- [Personal Access Tokens](https://docs.databricks.com/en/dev-tools/auth/pat.html)
- [COPY INTO Command](https://docs.databricks.com/en/sql/language-manual/delta-copy-into.html)

### Azure Documentation
- [ADLS Gen2 Documentation](https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction)
- [SAS Token Best Practices](https://learn.microsoft.com/en-us/azure/storage/common/storage-sas-overview)

---

## ✅ Feature Complete

**Phase 2.1: Databricks Unity Catalog Destination** - ✅ **COMPLETE**

**Deliverables**:
- ✅ `src/destinations/databricks.py` - Production-ready module (350 lines)
- ✅ `tests/unit/test_destinations.py` - 18 comprehensive tests (100% pass rate)
- ✅ `.dlt/secrets.toml.template` - Complete configuration template
- ✅ `docs/DATABRICKS_UNITY_CATALOG_SETUP.md` - This comprehensive guide
- ✅ Updated `src/core/orchestrator.py` - Dynamic destination selection
- ✅ Updated `src/destinations/__init__.py` - Export DatabricksDestination

**Next Steps**: Ready for Phase 2.2 - Filesystem Source implementation

---

**Questions or Issues?**
- Review logs in `logs/destination_databricks_*.log`
- Check `logs/errors/databricks_errors_*.log` for error-only view
- Run validation: `pytest tests/unit/test_destinations.py::TestDatabricksDestination -v`
