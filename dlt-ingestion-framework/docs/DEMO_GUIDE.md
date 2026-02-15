# DLT Multi-Source Ingestion Framework - Demo Guide

**Date:** January 29, 2026  
**Purpose:** Production demo of DLT-based data ingestion framework with modular architecture

---

## 🎯 What We Built

A **100% configuration-driven** data ingestion framework using **dlthub** that:
- Ingests from **multiple sources** (PostgreSQL, Oracle, MSSQL, Azure SQL, REST APIs)
- Lands data in **Azure ADLS Gen2** as **date-partitioned Parquet files**
- Requires **zero code changes** for new sources - only Excel config updates
- Supports **full and incremental loads** with automatic watermark tracking
- Provides **complete audit trail** and logging

---

## 📁 Key Files & What They Contain

### **Core Production Files (Modular Structure)**
| File | Purpose | Lines |
|------|---------|-------|
| **`run.py`** | Simple launcher script | 10 |
| **`src/main.py`** | Main entry point - initializes orchestrator | 60 |
| **`src/core/orchestrator.py`** | **DLT PIPELINE ORCHESTRATION** | 500 |
| | - `IngestionOrchestrator`: Main orchestration class | |
| | - `build_connection_string()`: Database connections | |
| | - `execute_job()`: Single job execution | |
| | - `_execute_database_job()`: DLT sql_table pattern | |
| | - `_execute_api_job()`: DLT rest_api_source pattern | |
| **`src/config/loader.py`** | Config & secrets loading | 150 |
| | - `ConfigLoader`: Excel config + TOML/Key Vault secrets | |
| **`src/metadata/tracker.py`** | Audit trail recording | 80 |
| | - `MetadataTracker`: CSV audit trail writer | |
| **`src/auth/keyvault_manager.py`** | Azure Key Vault integration | 100 |
| | - `KeyVaultManager`: Production credential management | |
| **`src/utils/logger.py`** | Logging configuration | 30 |

### **Configuration Files**
| File | Purpose |
|------|---------|
| **`config/ingestion_config.xlsx`** | **USER INTERFACE** - All job definitions (sources, tables, load types) |
| **`.dlt/secrets.toml`** | DLT native secrets location - credentials, ADLS keys |
| `config/config_schema.json` | Excel validation schema |

### **Auto-Generated Outputs**
| Location | Purpose |
|----------|---------|
| **`logs/ingestion_YYYYMMDD_HHMMSS.log`** | Detailed execution logs (rotating) |
| **`metadata/audit_YYYYMMDD.csv`** | Daily audit trail (job status, rows, duration, errors) |

### **Documentation**
| File | Content |
|------|---------|
| `README.md` | Architecture overview & patterns |
| `REFACTORING_COMPLETE.md` | Modular architecture documentation |
| `ARCHITECTURE_CLEANUP.md` | File organization & cleanup summary |
| `KEYVAULT_SETUP.md` | Azure Key Vault setup guide |
| `QUICKSTART.md` | 5-minute setup guide |
| `FEATURES.md` | Roadmap & tech debt |

### **Archived Files (in `_obsolete/` folder)**
| File | Purpose |
|------|---------|
| `run_simple.py` | Old single-file implementation (705 lines) |
| `check.py`, `diagnose.py`, etc. | Old diagnostic scripts |

**Note:** Archived files can be deleted after 30 days of stable operation

---

## 🚀 Demo Flow

### **1. Show the Configuration (No Code!)**

**Open `config/ingestion_config.xlsx`:**
```
Excel columns:
- source_type: postgresql | oracle | mssql | azure_sql | api
- source_name: my_postgres_db
- table_name: orders
- load_type: FULL | INCREMENTAL
- watermark_column: updated_at (for incremental)
- enabled: Y | N (job on/off switch)
- partition_by: date,region (optional)
- cluster_by: customer_id (optional)
```

**Point out:** "This is the ONLY file users edit. No Python coding required."

### **2. Show the Secrets Configuration**

**Open `.dlt/secrets.toml`:**
```toml
[sources.postgresql]
host = "localhost"
port = 5432
database = "sales"
username = "user"
password = "pass"

[sources.mssql]
host = "FRASQLU01122"
port = 1433
database = "Booking_STG"
# Windows Auth supported
[sources.mssql.query]
driver = "ODBC Driver 18 for SQL Server"
Encrypt = "yes"
TrustServerCertificate = "yes"

[destination.filesystem]
bucket_url = "az://raw-data"
layout = "{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}"

[destination.filesystem.credentials]
azure_storage_account_name = "dltpoctest"
azure_storage_account_key = "your_key_here"
```

**Point out:** "DLT native format. Supports Windows Authentication for SQL Server."

### **3. Run the Framework**

**Execute in terminal:**
```powershell
# From framework directory
cd dlt-ingestion-framework
python -m src.main

# Or using the launcher
python run.py
```

**Show output:**
```
================================================================================
DLT Ingestion Framework - Production Grade
================================================================================
Execution Time: 2026-01-29 14:30:00
Partition Path: 2026/01/29
Layout: {table}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.parquet
Destination: az://raw-data (ADLS Gen2)
================================================================================
[LOCAL] Credential Source: .dlt/secrets.toml
Orchestrator initialized
Executing 5 ingestion jobs
================================================================================
2026-01-29 14:30:01 | INFO     | Starting job: postgres_source.orders
2026-01-29 14:30:01 | INFO     |   Source: PostgreSQL
2026-01-29 14:30:01 | INFO     |   Load Type: INCREMENTAL
2026-01-29 14:30:01 | INFO     |   Execution Date: 2026-01-29
2026-01-29 14:30:01 | INFO     |   Partition Path: 2026/01/29
2026-01-29 14:30:01 | INFO     | Incremental load: updated_at > 2025-01-03 00:00:00
2026-01-29 14:30:05 | INFO     | [SUCCESS] Job completed successfully
2026-01-29 14:30:05 | INFO     |   Rows processed: 3
2026-01-29 14:30:05 | INFO     |   Schema version: 76
2026-01-29 14:30:05 | INFO     |   Duration: 16.19s
2026-01-29 14:30:05 | INFO     |   ADLS Path: az://raw-data/postgres_source/orders/2026/01/29
2026-01-29 14:30:05 | INFO     |   Partition: 2026/01/29
```

### **4. Show the Audit Trail**

**Open `metadata/audit_20260127.csv`:**
```csv
timestamp,job_name,status,rows_processed,duration_seconds,partition_path,error_message
2026-01-27T14:30:05,postgres_db.orders,SUCCESS,1523,4.23,postgres_db/orders/2026/01/27,
2026-01-27T14:31:12,mssql_db.bookings,SUCCESS,892,2.45,mssql_db/bookings/2026/01/27,
2026-01-27T14:32:05,oracle_db.inventory,FAILED,0,1.12,,Connection timeout
```

**Point out:** "Complete audit trail - status, row counts, duration, errors."

### **5. Show the ADLS Output**

**Navigate to ADLS Gen2 Storage:**
```
Container: raw-data
├── orders/
│   └── 2026/
│       └── 01/
│           └── 27/
│               └── 1768753214.27267.c81c3f2230.parquet
├── bookings/
│   └── 2026/
│       └── 01/
│           └── 27/
│               └── 1768753345.28934.d92d4g3341.parquet
```

**Point out:** "Date-partitioned folders prevent daily overwrites. Parquet format for optimal storage."

### **6. Show Log File**

**Open `logs/ingestion_20260127_143000.log`:**
- Detailed connection strings
- Row-by-row processing info
- Full error stack traces
- Performance metrics

---

## 🎨 Key Features to Highlight

### ✅ **Configuration-Driven**
- No code changes for new sources
- Excel-based job definitions
- TOML-based credentials (local)
- Azure Key Vault support (production)

### ✅ **Multi-Source Support**
- **Databases:** PostgreSQL, Oracle, MSSQL, Azure SQL
- **APIs:** REST API support (demonstrated with CoinGecko API)
- **Authentication:** Username/password + Windows Authentication

### ✅ **Load Strategies**
- **FULL:** Complete table replacement
- **INCREMENTAL:** Watermark-based delta loads (auto-updates Excel)

### ✅ **Date Partitioning**
- Files organized by `{table}/{YYYY}/{MM}/{DD}/`
- Prevents daily overwrites
- Optimizes query performance

### ✅ **Partition & Cluster Hints**
- Excel columns: `partition_by`, `cluster_by`
- Prepares data for downstream optimization
- Works with DLT column hints

### ✅ **Production Ready**
- Modular architecture (testable, maintainable)
- Rotating log files
- CSV audit trail
- Error handling & tracking
- Row count extraction (accurate metrics)
- Schema evolution monitoring
- Azure Key Vault integration

### ✅ **Oracle Direct Connection**
- No `tnsnames.ora` required
- Uses SID or service_name directly
- Format: `host:port/sid`

### ✅ **SQL Server Flexibility**
- ODBC Driver 17/18 support
- Raw connection string format
- Handles special characters in passwords
- Windows Authentication support

---

## 🔧 Technical Architecture

### **DLT Integration**
```python
# Pipeline creation
pipeline = dlt.pipeline(
    pipeline_name="postgres_to_adls_mydb",
    destination='filesystem',
    dataset_name='mydb'
)

# Database resource
resource = sql_table(
    credentials=ConnectionStringCredentials(conn_str),
    table='orders',
    incremental=dlt.sources.incremental('updated_at'),
    backend="pyarrow",
    chunk_size=100000
)

# Execute
load_info = pipeline.run(
    resource,
    write_disposition="merge",
    loader_file_format="parquet"
)
```

### **Connection String Examples**

**PostgreSQL:**
```
postgresql+psycopg2://user:pass@host:5432/database
```

**Oracle (SID):**
```
oracle+oracledb://user:pass@host:1521/orcl
```

**MSSQL (Windows Auth):**
```
mssql+pyodbc://@SERVER/DATABASE?trusted_connection=yes&driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes
```

**MSSQL (Username/Password):**
```
mssql+pyodbc:///?odbc_connect=DRIVER={ODBC Driver 17 for SQL Server};SERVER=host,1433;DATABASE=db;UID=user;PWD=pass;Encrypt=yes;TrustServerCertificate=yes;
```

---

## 📊 Demo Data Flow

```
┌─────────────────┐
│  Excel Config   │  ← User edits this ONLY
│ ingestion_      │
│ config.xlsx     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   run.py        │  ← Launcher
│   src/main.py   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ src/core/orchestrator.py│  ← Main orchestrator
│                         │
│  - Load config (loader) │
│  - Build connections    │
│  - Execute DLT          │
│  - Track audit (tracker)│
└────────┬────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌─────────────┐
│ Sources │ │ ADLS Gen2   │
│ - PGSQL │ │             │
│ - Oracle│→│ raw-data/   │
│ - MSSQL │ │ table/      │
│ - APIs  │ │ YYYY/MM/DD/ │
└─────────┘ └──────┬──────┘
                   │
                   ▼
            ┌──────────────┐
            │ Audit Trail  │
            │ audit_*.csv  │
            └──────────────┘
```

---

## 🎤 Demo Script

### **Opening (30 seconds)**
"Today I'll demonstrate our DLT-based multi-source ingestion framework with production-grade modular architecture. It's 100% configuration-driven - users only edit an Excel file to add new data sources. The framework uses a clean, testable structure with 8 core modules. No Python coding required for adding sources."

### **Configuration Demo (2 minutes)**
1. Open `ingestion_config.xlsx`
2. Show example rows with different source types
3. Point out `enabled` column for on/off control
4. Show incremental load with watermark column

### **Execution Demo (3 minutes)**
1. Run `python -m src.main` or `python run.py`
2. Show credential source detection (local TOML or Azure Key Vault)
3. Show real-time log output
4. Highlight success messages with row counts and schema version
5. Open `metadata/audit_YYYYMMDD.csv` to show tracking

### **Output Verification (2 minutes)**
1. Navigate to ADLS Gen2 storage
2. Show date-partitioned folder structure
3. Open a Parquet file (preview if possible)
4. Show multiple days of data (no overwrites)

### **Add New Source Demo (3 minutes)**
1. Open Excel, add new row
2. Set `source_type=postgresql`, `enabled=Y`
3. Add credentials to `.dlt/secrets.toml`
4. Run framework again
5. Show new table in ADLS

### **Closing (1 minute)**
"This framework eliminates custom ETL code with a production-grade modular architecture. Data engineers configure sources in Excel, the framework handles extraction with clean separation of concerns (auth, config, metadata, orchestration), DLT manages loading, and everything lands in date-partitioned Parquet files with full audit trails. The modular structure makes it easy to test, maintain, and extend."

---

## ❓ Anticipated Questions & Answers

**Q: How do I add a new table?**  
A: Add one row to Excel with source details. No code changes.

**Q: What happens if a job fails?**  
A: Framework logs error to `audit_*.csv`, continues with remaining jobs. Check log file for stack trace.

**Q: Can I reprocess historical data?**  
A: Yes. For incremental loads, update `last_watermark` in Excel to desired start date.

**Q: How is Azure SQL different from regular MSSQL?**  
A: Requires `Encrypt=yes`, firewall configuration, and uses FQDN format (`server.database.windows.net`).

**Q: Does it support parallel execution?**  
A: Currently sequential. Parallel execution is on roadmap (see `FEATURES.md`).

**Q: How do I handle API pagination?**  
A: Not implemented yet. Currently fetches single page (100 records). Tech debt item.

**Q: Can I use Windows Authentication for SQL Server?**  
A: Yes. Use `trusted_connection=yes` in ODBC connection string (no username/password needed).

**Q: What about schema drift?**  
A: DLT handles schema evolution automatically. Framework now monitors schema version changes and logs warnings when detected (v76+).

---

## 📋 Pre-Demo Checklist

- [ ] Virtual environment activated (`C:\venv_dlt\Scripts\python.exe`)
- [ ] At least 2 enabled jobs in Excel
- [ ] Credentials verified in `.dlt/secrets.toml`
- [ ] ADLS storage account accessible
- [ ] Database connections tested
- [ ] Previous logs cleared (optional)
- [ ] ADLS storage browser open in separate tab
- [ ] Excel file open for demo
- [ ] Terminal ready with command: `python -m src.main` or `python run.py`
- [ ] Optional: Set `AZURE_KEY_VAULT_URL` to demo production credential management

---

## 🚨 Troubleshooting During Demo

| Issue | Quick Fix |
|-------|-----------|
| Connection refused | Check database is running |
| Azure SQL auth fail | Verify firewall allows client IP |
| ADLS access denied | Check storage account key in secrets.toml |
| No enabled jobs | Set `enabled=Y` in Excel |
| Import error | Activate venv: `C:\venv_dlt\Scripts\python.exe` |

---

## 📈 Success Metrics to Mention

- **Single-file simplicity:** All logic in 474-line `run_simple.py`
- **Zero code changes:** New sources = Excel edit only
- **Multi-database:** PostgreSQL, Oracle, MSSQL, Azure SQL, APIs
- **Production audit:** CSV tracking + rotating logs
- **Date partitioning:** Prevents daily overwrites
- **DLT native:** Uses `dlt.pipeline()`, `sql_table()`, `filesystem` destination

---

## 📂 Understanding DLT Metadata Folders in ADLS

When you browse your ADLS Gen2 storage container, you'll see DLT's internal metadata folders alongside your data. These are **automatically created by DLT** for tracking pipeline state and load history.

### **`_dlt_loads/`**
**Purpose:** Load package metadata and completion markers

**Contains:**
- `.jsonl` files for each load run
- Records of what was loaded, when, and status
- Example: `api_to_adls_coingecko__1769490843.5974004.jsonl`

**What's inside:**
```json
{
  "load_id": "1769490843.5974004",
  "schema_name": "coingecko",
  "status": 0,  // 0 = success
  "inserted_at": "2026-01-27T10:44:12.584000+00:00",
  "schema_version_hash": "...",
  "completed_at": "2026-01-27T10:44:12.584000+00:00"
}
```

**Use:** Tracks load history, prevents duplicate loads, provides audit trail

---

### **`_dlt_pipeline_state/`**
**Purpose:** Pipeline state persistence across runs

**Contains:**
- State files per pipeline (e.g., `PostgreSQL_to_adls_postgres_source__*.jsonl`)
- Incremental watermarks
- Schema definitions
- Last successful run info

**What's inside:**
```json
{
  "version": 1,
  "engine_version": 6,
  "pipeline_name": "PostgreSQL_to_adls_postgres_source",
  "state": {
    "sources": {
      "orders": {
        "incremental": {
          "updated_at": "2026-01-27 00:00:00"
        }
      }
    }
  },
  "schemas": [...],
  "completed_at": "2026-01-27T10:42:31.794795+00:00"
}
```

**Use:** Enables incremental loads, tracks watermarks, maintains pipeline state between runs

---

### **`_dlt_version/`**
**Purpose:** Schema versioning and evolution tracking

**Contains:**
- Schema version hashes
- Column type evolution history
- Migration tracking

**What's inside:**
```json
{
  "version_hash": "c07a2aab854ade73700ff1fa168209f08",
  "schema_name": "coingecko",
  "version": 1,
  "engine_version": 6,
  "inserted_at": "2026-01-27T10:44:12.584000+00:00",
  "schema": {
    "tables": {
      "crypto_price": {
        "columns": {...}
      }
    }
  }
}
```

**Use:** Schema drift detection, backward compatibility, automatic type evolution

---

### **ADLS Storage Structure Example**

```
raw-data/  (your container)
├── _dlt_loads/           # ← DLT load tracking metadata
├── _dlt_pipeline_state/  # ← DLT pipeline state & watermarks
├── _dlt_version/         # ← DLT schema versioning
├── coingecko/            # ← YOUR DATA ✅
│   └── crypto_price/
│       └── 2026/01/27/
│           └── 1769490843.5974004.d756e8e6cf.parquet
├── postgres_source/      # ← YOUR DATA ✅
│   └── orders/
│       └── 2026/01/27/
│           └── *.parquet
├── oracle_db/            # ← YOUR DATA ✅
│   └── employees/
│       └── 2026/01/27/
└── Source1/              # ← YOUR DATA ✅
    └── users/
        └── 2026/01/27/
```

### **Key Points for Demo**

✅ **Metadata folders** (`_dlt_*`) = DLT housekeeping for production reliability  
✅ **Your data folders** = Actual ingested business data as Parquet files  
✅ **Small overhead:** Metadata files are tiny (KB-sized JSON files)  
✅ **Critical for production:** Enable incremental loads, idempotency, schema evolution  
✅ **Do NOT delete:** Removing these breaks incremental loading and state tracking  

**Demo Talking Point:**  
"DLT automatically manages these metadata folders. They're what make our incremental loads reliable and prevent duplicate data ingestion. The small storage cost is worth the production-grade reliability they provide."

---
