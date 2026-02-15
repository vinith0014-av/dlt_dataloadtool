# DLT Multi-Source Ingestion Framework - Complete Guide

**Version:** 2.0  
**Last Updated:** February 12, 2026  
**Status:** Production-Ready with Databricks Deployment

---

## 📑 Table of Contents

1. [Executive Overview](#executive-overview)
2. [Architecture & Design Philosophy](#architecture--design-philosophy)
3. [Project Structure - Where Everything Is](#project-structure---where-everything-is)
4. [Core Components Deep Dive](#core-components-deep-dive)
5. [Supported Features & Capabilities](#supported-features--capabilities)
6. [Configuration Management](#configuration-management)
7. [Secret Management (4 Options)](#secret-management-4-options)
8. [Deployment Options](#deployment-options)
9. [Operations & Monitoring](#operations--monitoring)
10. [Quick Start Guide](#quick-start-guide)
11. [Troubleshooting](#troubleshooting)
12. [Future Roadmap](#future-roadmap)

---

## Executive Overview

### What Is This Framework?

A **production-grade, modular data ingestion framework** that extracts data from multiple sources (databases and REST APIs) and loads them into **Azure Data Lake Storage Gen2** (ADLS) as date-partitioned Parquet files. Built on top of **dlthub** - an industry-standard Python library for data loading pipelines.

### Key Value Propositions

| Feature | Business Value |
|---------|----------------|
| **100% Excel-Driven** | Non-technical users can add/modify data sources without code changes |
| **Multi-Source Support** | Consolidate data from PostgreSQL, Oracle, SQL Server, Azure SQL, REST APIs |
| **Production-Grade** | Enterprise logging, audit trails, error handling, secret management |
| **Zero Infrastructure** | Uses Azure ADLS Gen2 (no databases to maintain) |
| **Built on dlthub** | Battle-tested library handling schema evolution, state management, retries |
| **Modular Architecture** | Easy to extend, test, and maintain by teams |
| **Databricks Ready** | Configured and tested for Databricks deployment |

### When to Use This Framework

✅ **USE for:**
- Loading multiple database tables into a data lake
- Incremental data synchronization with watermark tracking
- API data ingestion (REST APIs)
- Date-partitioned data storage for analytics
- Multi-environment deployments (local dev → Databricks production)

❌ **DON'T USE for:**
- Real-time streaming (use Azure Event Hubs/Kafka)
- Complex transformations (use dbt or Databricks after ingestion)
- Transactional systems (this is for analytics/data lake)

---

## Architecture & Design Philosophy

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA SOURCES                                  │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  PostgreSQL  │    Oracle    │  SQL Server  │    REST APIs       │
│  Azure SQL   │              │              │   (CoinGecko)      │
└──────┬───────┴──────┬───────┴──────┬───────┴────────┬───────────┘
       │              │              │                │
       └──────────────┴──────────────┴────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   DLT Ingestion Framework   │
         │ ┌───────────────────────────┤
         │ │ Config Loader (Excel)     │
         │ │ Secret Manager (4 options)│
         │ │ Source Modules            │
         │ │ DLT Orchestrator          │
         │ │ Metadata Tracker          │
         │ └───────────────────────────┤
         │    Built on dlthub (dlt)    │
         └──────────────┬──────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │   Azure Data Lake Gen2       │
         │ ┌────────────────────────────┤
         │ │ raw-data/                  │
         │ │   ├── orders/              │
         │ │   │   ├── 2026/01/20/      │
         │ │   │   │   └── *.parquet    │
         │ │   ├── customers/           │
         │ │   └── products/            │
         │ └────────────────────────────┤
         │   Date-Partitioned Parquet   │
         └──────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │   Audit & Logs               │
         │ ┌────────────────────────────┤
         │ │ logs/                      │
         │ │   ├── main_*.log           │
         │ │   ├── source_*.log         │
         │ │   └── errors/              │
         │ │ metadata/                  │
         │ │   └── audit_YYYYMMDD.csv   │
         │ └────────────────────────────┤
         │   Execution Tracking         │
         └──────────────────────────────┘
```

### Design Principles

#### 1. **Modular Architecture v2.0**

**OLD (Single-File):**
```
run_simple.py (705 lines)
├── All classes in one file
└── Hard to maintain/test
```

**NEW (Modular v2.0):**
```
src/
├── auth/keyvault_manager.py        (~100 lines)
├── config/loader.py                (~150 lines)
├── metadata/tracker.py             (~80 lines)
├── core/orchestrator.py            (~500 lines)
├── sources/                        (Per-source modules)
│   ├── base.py
│   ├── postgresql.py
│   ├── oracle.py
│   ├── mssql.py
│   ├── azure_sql.py
│   └── rest_api.py
├── destinations/                    (Per-destination modules)
│   ├── base.py
│   ├── adls_gen2.py
│   └── databricks.py
├── utils/logger.py
└── main.py                         (~60 lines)
```

**Benefits:**
- ✅ **Separation of concerns** - each module has one job
- ✅ **Easy to navigate** - find code by function (auth, config, etc.)
- ✅ **Team-friendly** - multiple developers work without conflicts
- ✅ **Testable** - unit test each module independently
- ✅ **Extensible** - add new sources without touching existing code

#### 2. **100% Excel-Driven Configuration**

**Philosophy:** Users edit Excel file, not Python code

**Single Configuration File:** `config/ingestion_config.xlsx`

```
┌────────────┬────────────┬────────────┬─────────────┬─────────────┐
│ source_type│ source_name│ table_name │  load_type  │   enabled   │
├────────────┼────────────┼────────────┼─────────────┼─────────────┤
│ postgresql │ postgres   │ orders     │ INCREMENTAL │      Y      │
│ oracle     │ oracle     │ customers  │    FULL     │      Y      │
│ mssql      │ sqlserver  │ products   │    FULL     │      N      │
│ api        │ coingecko  │ coins      │    FULL     │      Y      │
└────────────┴────────────┴────────────┴─────────────┴─────────────┘
```

**To add a new table:**
1. Add row to Excel with `enabled = Y`
2. Run framework (no code changes!)

#### 3. **DLT Native - Built on Industry Standard**

**Not a custom-built ingestion tool** - leverages proven **dlthub** library:

| Component | What We Use | Why |
|-----------|-------------|-----|
| Database Extraction | `dlt.sources.sql_database.sql_table()` | Proven SQLAlchemy-based connector |
| API Extraction | `dlt.sources.rest_api.rest_api_source()` | Pagination, retry, state management |
| Destination | `dlt.destinations.filesystem` | Native ADLS Gen2 + Parquet support |
| Incremental Loads | `dlt.sources.incremental()` | Watermark tracking, state persistence |
| Pipeline Management | `dlt.pipeline()` | Retry logic, schema evolution, metrics |

**Benefits:**
- ✅ **Maintained by community** - bug fixes/features from dlthub team
- ✅ **Production-tested** - used by thousands of companies
- ✅ **Schema evolution** - handles column additions automatically
- ✅ **State management** - tracks incremental load checkpoints

#### 4. **Enterprise Security**

**4 Secret Management Options** (automatic fallback):
```
Priority 1: Databricks Secrets  ← Best for Databricks deployment
Priority 2: Azure Key Vault     ← Best for multi-service Azure
Priority 3: Environment Variables ← Quick local alternative
Priority 4: secrets.toml        ← Local development only
```

Framework **auto-detects** and uses the highest priority available - **zero manual configuration**.

---

## Project Structure - Where Everything Is

### Root Directory Structure

```
dlt-ingestion-framework/
│
├── 📋 CONFIGURATION (User Input)
│   ├── config/
│   │   ├── ingestion_config.xlsx         ⭐ MAIN CONFIG - Edit this!
│   │   ├── config_schema.json            (Validation rules)
│   │   └── EXCEL_TEMPLATE_INSTRUCTIONS.md
│   └── .dlt/secrets.toml                 🔒 Credentials (local dev)
│
├── 🐍 SOURCE CODE (Core Framework)
│   ├── src/
│   │   ├── main.py                       🚀 Entry point (60 lines)
│   │   ├── auth/
│   │   │   └── keyvault_manager.py       🔑 Azure Key Vault integration
│   │   ├── config/
│   │   │   └── loader.py                 📖 Excel + secrets loader
│   │   ├── metadata/
│   │   │   └── tracker.py                📊 Audit trail CSV writer
│   │   ├── core/
│   │   │   └── orchestrator.py           🎯 Main DLT pipeline logic
│   │   ├── sources/                      📥 Per-source modules
│   │   │   ├── base.py
│   │   │   ├── postgresql.py
│   │   │   ├── oracle.py
│   │   │   ├── mssql.py
│   │   │   ├── azure_sql.py
│   │   │   └── rest_api.py
│   │   ├── destinations/                 📤 Per-destination modules
│   │   │   ├── base.py
│   │   │   ├── adls_gen2.py
│   │   │   └── databricks.py
│   │   └── utils/
│   │       └── logger.py                 📝 Logging utilities
│   └── run.py                            🏃 Simple launcher script
│
├── 📊 OUTPUTS (Auto-Generated)
│   ├── logs/
│   │   ├── main_orchestrator_*.log       (Main execution log)
│   │   ├── source_{name}_*.log           (Per-source logs)
│   │   ├── destination_*.log             (Destination logs)
│   │   └── errors/                       (Error-only logs)
│   ├── metadata/
│   │   └── audit_YYYYMMDD.csv            (Execution audit trail)
│   └── .dlt/                             (DLT pipeline state - auto)
│
├── 🔧 UTILITIES (Setup & Management)
│   ├── configure_databricks.py           (Databricks CLI setup)
│   ├── create_databricks_scope.py        (Create secret scope)
│   ├── upload_secrets_to_databricks.py   (Upload secrets ✅ DONE)
│   ├── migrate_to_keyvault.py            (Migrate to Key Vault)
│   ├── setup_env_secrets.ps1             (Environment variables)
│   └── test_connectivity.py              (Test database connections)
│
├── 📚 DOCUMENTATION
│   ├── README.md                         (Quick start)
│   ├── COMPLETE_FRAMEWORK_GUIDE.md       ⭐ THIS FILE
│   ├── SECRET_MANAGEMENT_QUICKSTART.md   (Secrets quick reference)
│   └── docs/
│       ├── REFACTORING_COMPLETE.md       (Architecture v2.0)
│       ├── DATABRICKS_DEPLOYMENT_GUIDE.md
│       ├── KEYVAULT_SETUP.md
│       ├── SECRET_MANAGEMENT_GUIDE.md
│       ├── FEATURES.md                   (Roadmap)
│       └── QUICKSTART.md
│
└── 🗑️ ARCHIVED
    └── _obsolete/                        (Old single-file version)
```

### Key Files - What They Do

| File | Purpose | Who Edits? |
|------|---------|------------|
| **config/ingestion_config.xlsx** | Define all data sources & tables | ✏️ **Users/Analysts** |
| **.dlt/secrets.toml** | Store credentials (local dev) | ✏️ Developers |
| **src/main.py** | Application entry point | ❌ No edits needed |
| **src/core/orchestrator.py** | Main DLT pipeline execution | 🔧 Framework developers |
| **logs/main_*.log** | Execution logs | 👀 Read-only (monitoring) |
| **metadata/audit_*.csv** | Job execution audit trail | 👀 Read-only (auditing) |

### **Quick Navigation Guide**

**Want to...**

| Task | Go to File/Folder |
|------|-------------------|
| Add a new table to ingest | `config/ingestion_config.xlsx` |
| Check if job succeeded | `metadata/audit_YYYYMMDD.csv` |
| Debug a failed job | `logs/main_orchestrator_*.log` or `logs/errors/` |
| Add PostgreSQL credentials | `.dlt/secrets.toml` (local) or upload to Databricks |
| Add a new database source | `src/sources/` - create new module |
| Customize logging | `src/utils/logger.py` |
| Change ADLS destination | `src/destinations/adls_gen2.py` |
| Setup Databricks secrets | `upload_secrets_to_databricks.py` |

---

## Core Components Deep Dive

### 1. Main Entry Point: `src/main.py`

**Purpose:** Application launcher and error handling

**Code Location:** `src/main.py` (~60 lines)

**What it does:**
```python
def main():
    # 1. Setup logging
    setup_logger()
    
    # 2. Create orchestrator
    orchestrator = IngestionOrchestrator()
    
    # 3. Execute all enabled jobs
    orchestrator.run_all()
    
    # 4. Handle errors gracefully
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error("Fatal error", exc_info=True)
```

**Key Features:**
- ✅ Centralized error handling
- ✅ Keyboard interrupt (Ctrl+C) support
- ✅ Clean exit codes (0=success, 1=failure)

**Usage:**
```bash
# From framework root
python run.py

# Or directly
python -m src.main
```

---

### 2. Configuration Loader: `src/config/loader.py`

**Purpose:** Load Excel configuration and credentials

**Code Location:** `src/config/loader.py` (~150 lines)

**Key Methods:**

```python
class ConfigLoader:
    def load_jobs(self) -> list[dict]:
        """
        Load jobs from config/ingestion_config.xlsx
        Returns: List of enabled jobs only (enabled='Y')
        """
        
    def load_secrets(self) -> dict:
        """
        Load secrets with automatic fallback:
        1. Databricks Secrets (if in Databricks)
        2. Azure Key Vault (if AZURE_KEY_VAULT_URL set)
        3. Environment Variables (if DLT_* vars exist)
        4. secrets.toml (always available)
        """
        
    def get_source_config(self, source_type: str, source_name: str) -> dict:
        """
        Get credentials for a specific source
        Returns: {host, port, database, username, password}
        """
```

**Excel Structure:**

| Column | Example | Required | Purpose |
|--------|---------|----------|---------|
| `source_type` | postgresql | ✅ | Database type |
| `source_name` | postgres | ✅ | Config key in secrets |
| `table_name` | orders | ✅ | Table to extract |
| `schema_name` | dbo | ⚠️ Oracle only | Schema owner |
| `load_type` | INCREMENTAL | ✅ | FULL or INCREMENTAL |
| `watermark_column` | updated_at | ⚠️ For incremental | Timestamp column |
| `last_watermark` | 2026-01-01 | ⚠️ For incremental | Last successful value |
| `enabled` | Y | ✅ | Y=run, N=skip |

**Example Excel Row:**
```
source_type:  postgresql
source_name:  postgres
table_name:   orders
load_type:    INCREMENTAL
watermark_column: updated_at
last_watermark:   2026-01-15
enabled:      Y
```

**Corresponding secrets.toml:**
```toml
[sources.postgres]
host = "myserver.database.windows.net"
port = 5432
database = "sales_db"
username = "admin"
password = "SecurePass123!"
```

---

### 3. Orchestrator: `src/core/orchestrator.py`

**Purpose:** Main DLT pipeline execution engine

**Code Location:** `src/core/orchestrator.py` (~500 lines)

**Architecture:**

```python
class IngestionOrchestrator:
    def __init__(self):
        self.config_loader = ConfigLoader()
        self.metadata_tracker = MetadataTracker()
        self.logger = setup_logger()
    
    def run_all(self, parallel=False, max_workers=3):
        """Execute all enabled jobs"""
        
    def execute_job(self, job: dict):
        """Execute single job with error handling"""
        
    def _execute_database_job(self, job: dict):
        """Database-specific execution (DLT sql_table)"""
        
    def _execute_api_job(self, job: dict):
        """API-specific execution (DLT rest_api_source)"""
        
    def build_connection_string(self, job: dict) -> str:
        """Build SQLAlchemy connection string"""
```

**Execution Flow:**

```
run_all()
  ↓
  Load jobs from Excel (enabled='Y' only)
  ↓
  For each job:
    ↓
    execute_job(job)
      ↓
      ├─ Build connection string
      ├─ Create DLT pipeline
      ├─ Create DLT resource (sql_table or rest_api_source)
      ├─ Run pipeline (pipeline.run())
      ├─ Extract metrics (row count, duration)
      └─ Record to audit CSV
```

**Key Features:**

✅ **Automatic Source Detection:**
```python
if source_type == 'postgresql':
    conn_str = f"postgresql+psycopg2://{user}:{pass}@{host}:{port}/{db}"
elif source_type == 'oracle':
    conn_str = f"oracle+oracledb://{user}:{pass}@{host}:{port}/{sid}"
```

✅ **Incremental Load Support:**
```python
if job['load_type'] == 'INCREMENTAL':
    incremental_obj = dlt.sources.incremental(
        cursor_path=job['watermark_column'],
        initial_value=job['last_watermark']
    )
```

✅ **Error Handling:**
```python
try:
    load_info = pipeline.run(resource)
except Exception as e:
    logger.error(f"Job failed: {job_name}", exc_info=True)
    metadata_tracker.record_job(status="FAILED", error_message=str(e))
```

---

### 4. Source Modules: `src/sources/`

**Purpose:** Per-source connection and extraction logic

**Code Location:** `src/sources/` (modular structure v2.0)

**Architecture:**

```
src/sources/
├── base.py              (Abstract base class)
├── postgresql.py        (PostgreSQL implementation)
├── oracle.py            (Oracle implementation)
├── mssql.py             (SQL Server implementation)
├── azure_sql.py         (Azure SQL implementation)
└── rest_api.py          (REST API implementation)
```

**Base Class Pattern:**

```python
# src/sources/base.py
class BaseSource(ABC):
    @abstractmethod
    def build_connection_string(self, config: dict) -> str:
        """Build connection string for this source"""
        
    def validate_connection(self, conn_str: str) -> bool:
        """Test connection before extraction"""
        
    def estimate_table_size(self, table_name: str) -> int:
        """Get row count for chunk sizing"""
```

**Example Implementation:**

```python
# src/sources/postgresql.py
class PostgreSQLSource(BaseSource):
    def build_connection_string(self, config: dict) -> str:
        return (
            f"postgresql+psycopg2://"
            f"{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}"
            f"/{config['database']}"
        )
```

**Benefits of Modular Sources:**
- ✅ **Easy to add new sources** - copy template, implement methods
- ✅ **No conflicts** - team members work on separate files
- ✅ **Unit testable** - test each source independently
- ✅ **Clean imports** - `from src.sources.postgresql import PostgreSQLSource`

**Supported Sources:**

| Source | Module | Driver | Status |
|--------|--------|--------|--------|
| PostgreSQL | `postgresql.py` | psycopg2 | ✅ Production |
| Oracle | `oracle.py` | oracledb (thin) | ✅ Production |
| SQL Server | `mssql.py` | pyodbc | ✅ Production |
| Azure SQL | `azure_sql.py` | pyodbc + SSL | ✅ Production |
| REST API | `rest_api.py` | DLT native | ✅ Production |

---

### 5. Destination Modules: `src/destinations/`

**Purpose:** Per-destination configuration and validation

**Code Location:** `src/destinations/`

```
src/destinations/
├── base.py              (Abstract base class)
├── adls_gen2.py         (Azure Data Lake Gen2) ⭐ Primary
└── databricks.py        (Databricks Unity Catalog)
```

**ADLS Gen2 Configuration:**

```python
# src/destinations/adls_gen2.py
class ADLSGen2Destination(BaseDestination):
    def __init__(self, config: dict):
        self.storage_account = config['storage_account_name']
        self.storage_key = config['storage_account_key']
        self.container = config.get('container_name', 'raw-data')
        
    def get_dlt_config(self) -> dict:
        return {
            'bucket_url': f'az://{self.container}',
            'credentials': {
                'azure_storage_account_name': self.storage_account,
                'azure_storage_account_key': self.storage_key
            },
            'layout': '{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}'
        }
```

**Date Partitioning Pattern:**

Output files land in this structure:
```
az://raw-data/
├── orders/
│   ├── 2026/
│   │   ├── 01/
│   │   │   ├── 20/
│   │   │   │   └── 1768753214.27267.c81c3f2230.parquet
│   │   │   └── 21/
│   │   │       └── 1768839614.38291.d92d4g3341.parquet
```

**Why Date Partitioning?**
- ✅ **Prevents overwrites** - each run creates new dated folder
- ✅ **Analytics-friendly** - query by date range efficiently
- ✅ **Audit trail** - historical data preserved
- ✅ **Time travel** - revert to previous day's data

---

### 6. Metadata Tracker: `src/metadata/tracker.py`

**Purpose:** Audit trail and execution tracking

**Code Location:** `src/metadata/tracker.py` (~80 lines)

**What it does:**

```python
class MetadataTracker:
    def record_job(
        self,
        job_name: str,
        status: str,          # SUCCESS or FAILED
        rows: int,            # Row count processed
        duration: float,      # Execution time (seconds)
        partition_path: str,  # ADLS path
        error_message: str = None
    ):
        """Write execution record to CSV"""
```

**Output Format:**

File: `metadata/audit_20260212.csv`

```csv
timestamp,job_name,status,rows_processed,duration_seconds,partition_path,error_message
2026-02-12 10:15:30,postgres.orders,SUCCESS,15234,45.2,orders/2026/02/12,
2026-02-12 10:16:45,oracle.customers,FAILED,0,12.1,,Connection timeout
2026-02-12 10:17:00,sqlserver.products,SUCCESS,8921,38.5,products/2026/02/12,
```

**Usage Patterns:**

**Check today's jobs:**
```powershell
# PowerShell
Get-Content metadata/audit_20260212.csv | Select-String "SUCCESS"
```

**Count failures:**
```python
# Python
import pandas as pd
df = pd.read_csv('metadata/audit_20260212.csv')
failures = df[df['status'] == 'FAILED']
print(f"Failed jobs: {len(failures)}")
```

**Total rows ingested:**
```python
df = pd.read_csv('metadata/audit_20260212.csv')
total_rows = df[df['status'] == 'SUCCESS']['rows_processed'].sum()
print(f"Total rows: {total_rows:,}")
```

---

### 7. Secret Management: `src/auth/keyvault_manager.py`

**Purpose:** Azure Key Vault integration (optional)

**Code Location:** `src/auth/keyvault_manager.py` (~100 lines)

**When to use:**
- ✅ Multi-service Azure deployments
- ✅ Centralized secret management
- ✅ Enterprise compliance requirements

**Authentication Methods:**

```python
from azure.identity import DefaultAzureCredential

# Auto-detects and tries in order:
# 1. Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
# 2. Azure CLI (az login)
# 3. Managed Identity (if running in Azure)
# 4. Visual Studio Code
# 5. Azure PowerShell
```

**Usage:**

```python
from src.auth import KeyVaultManager

# Initialize (auto-detects from AZURE_KEY_VAULT_URL)
kv = KeyVaultManager()

# Get specific secret
password = kv.get_secret('postgres-source-password')

# Get complete source config
config = kv.get_source_config('postgresql')
# Returns: {host, port, database, username, password}
```

**Not Required!** Framework works without Key Vault - uses secrets.toml by default.

---

### 8. Logging: `src/utils/logger.py`

**Purpose:** Structured logging and log file management

**Code Location:** `src/utils/logger.py`

**Log File Structure:**

```
logs/
├── main_orchestrator_20260212_101530.log     (Main execution)
├── source_postgres_20260212_101530.log       (Per-source logs)
├── source_oracle_20260212_101530.log
├── destination_adls_gen2_20260212_101530.log (Destination logs)
└── errors/
    ├── postgres_errors_20260212.log          (Error-only logs)
    └── oracle_errors_20260212.log
```

**Log Format:**

```
2026-02-12 10:15:30 | INFO     | Starting job: postgres.orders
2026-02-12 10:15:30 | INFO     |   Source: postgresql
2026-02-12 10:15:30 | INFO     |   Load Type: INCREMENTAL
2026-02-12 10:15:31 | INFO     |   Watermark: updated_at > 2026-01-15
2026-02-12 10:16:15 | INFO     | ✅ SUCCESS: Processed 15,234 rows in 45.2s
2026-02-12 10:16:15 | INFO     |   Partition: orders/2026/02/12
```

**Error Log Example:**

```
logs/errors/postgres_errors_20260212.log:

2026-02-12 10:20:15 | ERROR    | [FAILED] Job postgres.orders
Traceback (most recent call last):
  File "src/core/orchestrator.py", line 245, in execute_job
    load_info = pipeline.run(resource)
  ...
psycopg2.OperationalError: connection timeout
```

**Benefits:**
- ✅ **Quick debugging** - check error-only logs first
- ✅ **Per-source logs** - isolate issues to specific sources
- ✅ **Timestamped** - easy to correlate with audit CSV
- ✅ **Console + file** - see output live AND save for later

---

## Supported Features & Capabilities

### Data Sources (5 Types)

#### 1. PostgreSQL

**Status:** ✅ Production-Ready

**Supported Features:**
- ✅ FULL loads (replace table)
- ✅ INCREMENTAL loads (watermark tracking)
- ✅ Schema detection (auto-discovers columns)
- ✅ SSL connections
- ✅ Custom ports

**Configuration Example:**

Excel:
```
source_type: postgresql
source_name: postgres
table_name: orders
load_type: INCREMENTAL
watermark_column: updated_at
enabled: Y
```

secrets.toml:
```toml
[sources.postgres]
host = "myserver.postgres.database.azure.com"
port = 5432
database = "sales_db"
username = "admin@myserver"
password = "SecurePass!"
```

**Connection String:**
```
postgresql+psycopg2://admin@myserver:SecurePass!@myserver.postgres.database.azure.com:5432/sales_db
```

---

#### 2. Oracle

**Status:** ✅ Production-Ready

**Supported Features:**
- ✅ Thin client (no Oracle installation required)
- ✅ SID and service_name support
- ✅ Direct connections (no tnsnames.ora)
- ✅ Schema owner specification

**Configuration Example:**

Excel:
```
source_type: oracle
source_name: oracle
table_name: CUSTOMERS
schema_name: SCOTT          ← Required for Oracle!
load_type: FULL
enabled: Y
```

secrets.toml:
```toml
[sources.oracle]
host = "oracleserver.company.com"
port = 1521
service_name = "ORCL"       # Or use 'sid' instead
username = "SCOTT"
password = "tiger"
```

**Important:** Always specify `schema_name` in Excel for Oracle tables.

---

#### 3. SQL Server (On-Premises)

**Status:** ✅ Production-Ready

**Supported Features:**
- ✅ ODBC Driver 17 for SQL Server
- ✅ Windows Authentication (trusted_connection)
- ✅ SQL Authentication
- ✅ Custom instances

**Configuration Example:**

Excel:
```
source_type: mssql
source_name: sqlserver
table_name: Products
load_type: FULL
enabled: Y
```

secrets.toml:
```toml
[sources.sqlserver]
host = "SQLSERVER01"
port = 1433
database = "AdventureWorks"
username = "sa"
password = "P@ssw0rd"
driver = "ODBC Driver 17 for SQL Server"
trusted_connection = false
```

**Windows Authentication:**
```toml
[sources.sqlserver]
host = "localhost"
database = "MyDB"
trusted_connection = true
```

---

#### 4. Azure SQL Database

**Status:** ✅ Production-Ready

**Supported Features:**
- ✅ SSL encryption (required)
- ✅ Firewall IP whitelisting
- ✅ Azure AD authentication
- ✅ Connection retry logic

**Configuration Example:**

Excel:
```
source_type: azure_sql
source_name: azure_sql
table_name: Sales
load_type: INCREMENTAL
watermark_column: ModifiedDate
enabled: Y
```

secrets.toml:
```toml
[sources.azure_sql]
host = "myazuresql.database.windows.net"
port = 1433
database = "SalesDB"
username = "sqladmin"
password = "AzureP@ss123"
driver = "ODBC Driver 17 for SQL Server"
encrypt = true              # Required for Azure SQL
trust_server_certificate = false
```

**Important:** Add your Databricks cluster IP to Azure SQL firewall whitelist.

---

#### 5. REST APIs

**Status:** ✅ Production-Ready (DLT native)

**Supported Features:**
- ✅ Automatic pagination (cursor-based)
- ✅ Retry logic with exponential backoff
- ✅ API key authentication
- ✅ Custom headers
- ✅ JSON response parsing

**Configuration Example:**

Excel:
```
source_type: api
source_name: coingecko
table_name: coins
api_endpoint: coins/markets
load_type: FULL
enabled: Y
```

secrets.toml:
```toml
[sources.coingecko]
base_url = "https://api.coingecko.com/api/v3"
api_key = "CG-your-api-key-here"

[sources.coingecko.params]
vs_currency = "usd"
per_page = "100"
```

**How it works:**

Framework uses DLT's `rest_api_source()`:
```python
from dlt.sources.rest_api import rest_api_source

api_source = rest_api_source({
    "client": {
        "base_url": "https://api.coingecko.com/api/v3",
        "headers": {"x-cg-demo-api-key": "your-key"}
    },
    "resources": [{
        "name": "coins",
        "endpoint": {
            "path": "coins/markets",
            "params": {"vs_currency": "usd", "per_page": "100"}
        }
    }]
})
```

**Benefits:**
- ✅ **No manual pagination code** - DLT handles it
- ✅ **Automatic retries** - handles rate limits
- ✅ **State management** - tracks last checkpoint
- ✅ **Schema inference** - auto-detects JSON structure

---

### Load Types (2 Modes)

#### FULL Load (Replace)

**When to use:**
- Small tables (< 1M rows)
- Tables without timestamps
- Complete refresh required
- Reference/dimension tables

**How it works:**
1. Extract ALL rows from source
2. Write to new dated folder in ADLS
3. Old data remains (date partitioning prevents overwrites)

**Excel Configuration:**
```
load_type: FULL
watermark_column:           ← Leave empty
last_watermark:             ← Leave empty
```

**Performance:**
- 1M rows: ~5 minutes
- 10M rows: ~30 minutes
- 100M rows: ~3 hours (consider incremental instead)

---

#### INCREMENTAL Load (Merge)

**When to use:**
- Large tables (1M+ rows)
- Tables with update timestamps
- Daily/hourly syncs
- Fact tables

**How it works:**
1. Extract ONLY new/updated rows (`WHERE updated_at > last_watermark`)
2. Write to ADLS
3. Update `last_watermark` in audit CSV

**Excel Configuration:**
```
load_type: INCREMENTAL
watermark_column: updated_at      ← Timestamp column
last_watermark: 2026-01-15        ← Last successful value
```

**Requirements:**
- ✅ Table must have timestamp column (updated_at, modified_date, etc.)
- ✅ Timestamp must be indexed for performance
- ✅ Timestamp must be updated on every row change

**DLT Implementation:**
```python
incremental_obj = dlt.sources.incremental(
    cursor_path='updated_at',
    initial_value='2026-01-15'
)

resource = sql_table(
    credentials=credentials,
    table='orders',
    incremental=incremental_obj
)
```

**Automatic Watermark Update:**

After successful run, audit CSV tracks new watermark:
```csv
timestamp,job_name,last_watermark
2026-02-12 10:15:30,orders,2026-02-12 09:00:00
```

**Performance:**
- Daily sync of 100K new rows: ~2 minutes
- Hourly sync of 10K new rows: ~20 seconds

---

### Destination: Azure Data Lake Storage Gen2

**Why ADLS Gen2?**
- ✅ **Scalable** - petabyte-scale storage
- ✅ **Cost-effective** - $0.02/GB/month (hot tier)
- ✅ **Analytics-ready** - native Databricks integration
- ✅ **Secure** - encryption at rest + in transit

**Output Format:** Parquet

**Why Parquet?**
- ✅ **Columnar storage** - 10x compression vs CSV
- ✅ **Fast queries** - read only needed columns
- ✅ **Schema embedded** - no separate schema file
- ✅ **Analytics optimized** - Spark, Databricks, Synapse

**Folder Structure:**

```
Azure Storage Account: dltpoctest
Container: raw-data

raw-data/
├── orders/                     ← Table name
│   ├── 2026/                   ← Year
│   │   ├── 01/                 ← Month
│   │   │   ├── 15/             ← Day
│   │   │   │   └── 1768753214.27267.c81c3f2230.parquet
│   │   │   └── 16/
│   │   │       └── 1768839614.38291.d92d4g3341.parquet
│   │   └── 02/
│   │       └── 12/
│   │           └── 1770123857.12345.e03e5h4452.parquet
├── customers/
│   └── 2026/01/15/...
└── products/
    └── 2026/01/15/...
```

**File Naming Convention:**

```
{load_id}.{file_id}.{random_hash}.parquet

Example: 1768753214.27267.c81c3f2230.parquet
         └─ load_id (timestamp)
                    └─ file_id (chunk number)
                                └─ random_hash (uniqueness)
```

**Configuration:**

secrets.toml:
```toml
[destination.filesystem]
bucket_url = "az://raw-data"
layout = "{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}"

[destination.filesystem.credentials]
azure_storage_account_name = "dltpoctest"
azure_storage_account_key = "your_storage_account_key_here=="
```

**Access Patterns:**

**Query all data:**
```sql
-- Databricks
SELECT * FROM parquet.`az://raw-data/orders/**/*.parquet`
```

**Query specific date:**
```sql
-- Databricks
SELECT * FROM parquet.`az://raw-data/orders/2026/02/12/*.parquet`
```

**Query date range:**
```sql
-- Databricks
SELECT * FROM parquet.`az://raw-data/orders/2026/02/*/*.parquet`
WHERE date >= '2026-02-01' AND date < '2026-03-01'
```

---

### Production Features

#### ✅ Row Count Tracking

**Where:** Audit CSV `metadata/audit_YYYYMMDD.csv`

**How it works:**

After each job, framework extracts row count from DLT pipeline:
```python
# Extract from pipeline trace
row_counts = pipeline.last_trace.last_normalize_info.row_counts
rows_processed = row_counts[table_name]
```

**Output:**
```csv
timestamp,job_name,rows_processed
2026-02-12 10:15:30,orders,15234
2026-02-12 10:16:45,customers,8921
```

**Usage:**
```python
# Daily summary
import pandas as pd
df = pd.read_csv('metadata/audit_20260212.csv')
print(f"Total rows today: {df['rows_processed'].sum():,}")
```

---

#### ✅ Execution Time Tracking

**Where:** Audit CSV `duration_seconds` column

**Usage:**
```python
# Find slow jobs
df = pd.read_csv('metadata/audit_20260212.csv')
slow_jobs = df[df['duration_seconds'] > 300].sort_values('duration_seconds', ascending=False)
print(slow_jobs[['job_name', 'duration_seconds']])
```

**Output:**
```
job_name             duration_seconds
orders               472.3
customers            345.1
products             125.7
```

---

#### ✅ Schema Evolution Detection

**What it does:** Detects when source table schema changes (new columns, type changes)

**How it works:** DLT tracks schema version in pipeline state

**Log Output:**
```
[SCHEMA CHANGE] Detected in orders table
  Schema version: 2 (changed from 1)
  Check _dlt_version/ folder in ADLS for migration details
```

**ADLS Output:**
```
raw-data/
├── orders/
│   └── 2026/02/12/...
└── _dlt_version/
    ├── loads_20260212_101530.jsonl      ← Load metadata
    └── schemas_20260212_101530.jsonl    ← Schema history
```

---

#### ✅ Error-Only Logs

**Purpose:** Quick debugging without reading full logs

**Location:** `logs/errors/{source_name}_errors_{date}.log`

**Example:**
```
logs/errors/postgres_errors_20260212.log

2026-02-12 10:20:15 | ERROR | Job postgres.orders failed
Traceback:
  psycopg2.OperationalError: connection timeout

2026-02-12 14:35:22 | ERROR | Job postgres.customers failed
Traceback:
  KeyError: 'watermark_column' not found
```

**Benefits:**
- ✅ **Fast troubleshooting** - only errors, no noise
- ✅ **Per-source** - isolate issues to specific databases
- ✅ **Daily files** - easy to track error trends

---

#### ✅ Graceful Error Handling

**What it does:** One job failure doesn't stop other jobs

**Behavior:**
```
10:15:30 | Starting job: postgres.orders
10:16:15 | ✅ SUCCESS: postgres.orders
10:16:16 | Starting job: oracle.customers
10:16:30 | ❌ FAILED: oracle.customers (connection timeout)
10:16:31 | Starting job: sqlserver.products    ← Continues!
10:17:05 | ✅ SUCCESS: sqlserver.products
```

**Audit CSV:**
```csv
timestamp,job_name,status,error_message
2026-02-12 10:16:15,postgres.orders,SUCCESS,
2026-02-12 10:16:30,oracle.customers,FAILED,connection timeout
2026-02-12 10:17:05,sqlserver.products,SUCCESS,
```

**Summary Report:**
```
=== Execution Summary ===
Total Jobs: 3
Successful: 2
Failed: 1

Failed Jobs:
  - oracle.customers: connection timeout
```

---

#### ✅ Per-Source Logging (v2.0)

**What's New:** Separate log file for each source

**Structure:**
```
logs/
├── main_orchestrator_20260212_101530.log      (Main execution flow)
├── source_postgres_20260212_101530.log        (PostgreSQL jobs)
├── source_oracle_20260212_101530.log          (Oracle jobs)
├── source_sqlserver_20260212_101530.log       (SQL Server jobs)
└── destination_adls_gen2_20260212_101530.log  (ADLS operations)
```

**Benefits:**
- ✅ **Isolated debugging** - focus on one source
- ✅ **Smaller files** - easier to read
- ✅ **Parallel development** - team members own specific sources

---

## Configuration Management

### Excel Configuration File

**Location:** `config/ingestion_config.xlsx`

**Sheet:** `SourceConfig`

#### Column Reference

| Column | Type | Required | Values | Purpose |
|--------|------|----------|--------|---------|
| **source_type** | Text | ✅ Yes | postgresql, oracle, mssql, azure_sql, api | Database/API type |
| **source_name** | Text | ✅ Yes | Any | Key in secrets.toml |
| **table_name** | Text | ✅ Yes | Any | Table/resource to extract |
| **schema_name** | Text | ⚠️ Oracle only | dbo, SCOTT, etc. | Schema owner (Oracle) |
| **load_type** | Text | ✅ Yes | FULL, INCREMENTAL | Extraction mode |
| **watermark_column** | Text | ⚠️ Incremental only | updated_at, modified_date, etc. | Timestamp column |
| **last_watermark** | DateTime | ⚠️ Incremental only | 2026-01-15 00:00:00 | Last successful value |
| **api_endpoint** | Text | ⚠️ API only | coins/markets | API path |
| **enabled** | Text | ✅ Yes | Y, N | Job on/off switch |
| **last_run_date** | DateTime | ❌ Auto | Auto-filled | Last execution timestamp |
| **last_run_status** | Text | ❌ Auto | SUCCESS/FAILED | Last execution result |

#### Example Configurations

**PostgreSQL - Incremental Load:**
```
source_type:      postgresql
source_name:      postgres
table_name:       orders
schema_name:      
load_type:        INCREMENTAL
watermark_column: updated_at
last_watermark:   2026-01-15 00:00:00
enabled:          Y
```

**Oracle - Full Load:**
```
source_type:      oracle
source_name:      oracle
table_name:       CUSTOMERS
schema_name:      SCOTT        ← Required!
load_type:        FULL
watermark_column: 
last_watermark:   
enabled:          Y
```

**REST API - Full Load:**
```
source_type:      api
source_name:      coingecko
table_name:       coins
api_endpoint:     coins/markets
load_type:        FULL
enabled:          Y
```

#### Adding a New Table

**Step-by-step:**

1. **Open Excel:** `config/ingestion_config.xlsx`

2. **Add new row:**
```
source_type:  postgresql
source_name:  postgres
table_name:   new_table     ← Your new table
load_type:    FULL
enabled:      Y
```

3. **Save Excel**

4. **Run framework:**
```bash
python run.py
```

**That's it!** No code changes needed.

---

### Secrets Configuration

**Location:** `.dlt/secrets.toml` (local dev) or Databricks Secrets (production)

#### secrets.toml Structure

**PostgreSQL:**
```toml
[sources.postgres]
host = "myserver.postgres.database.azure.com"
port = 5432
database = "sales_db"
username = "admin@myserver"
password = "SecurePass!"
```

**Oracle:**
```toml
[sources.oracle]
host = "oracleserver.company.com"
port = 1521
service_name = "ORCL"         # Or use 'sid' instead
username = "SCOTT"
password = "tiger"
```

**SQL Server:**
```toml
[sources.sqlserver]
host = "SQLSERVER01"
port = 1433
database = "AdventureWorks"
username = "sa"
password = "P@ssw0rd"
driver = "ODBC Driver 17 for SQL Server"
trusted_connection = false
```

**Azure SQL:**
```toml
[sources.azure_sql]
host = "myazuresql.database.windows.net"
port = 1433
database = "SalesDB"
username = "sqladmin"
password = "AzureP@ss123"
driver = "ODBC Driver 17 for SQL Server"
encrypt = true
trust_server_certificate = false
```

**REST API:**
```toml
[sources.coingecko]
base_url = "https://api.coingecko.com/api/v3"
api_key = "CG-your-api-key-here"

[sources.coingecko.params]
vs_currency = "usd"
per_page = "100"
```

**ADLS Gen2 Destination:**
```toml
[destination.filesystem]
bucket_url = "az://raw-data"
layout = "{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}"

[destination.filesystem.credentials]
azure_storage_account_name = "dltpoctest"
azure_storage_account_key = "your_storage_account_key_here=="
```

#### Security Best Practices

**❌ NEVER:**
- Commit secrets.toml to Git
- Share secrets.toml via email
- Store in shared drives

**✅ ALWAYS:**
- Keep secrets.toml in `.gitignore`
- Use Databricks Secrets for production
- Use Azure Key Vault for enterprise
- Rotate credentials regularly

---

## Secret Management (4 Options)

### Overview: Automatic Fallback

Framework checks for secrets in priority order:

```
Priority 1: Databricks Secrets     ← Production (Databricks)
            ↓ (if not available)
Priority 2: Azure Key Vault        ← Enterprise (multi-service)
            ↓ (if not available)
Priority 3: Environment Variables  ← Quick local alternative
            ↓ (if not available)
Priority 4: secrets.toml           ← Local development
```

**Zero configuration needed** - framework auto-detects which option is available.

---

### Option 1: Databricks Secrets ⭐ RECOMMENDED (Production)

**Status:** ✅ **CONFIGURED & READY**

**When to use:**
- ✅ Deploying to Databricks (any cloud: AWS, Azure, GCP)
- ✅ Need secure production secret management
- ✅ Don't want to manage Azure Key Vault

**What's already set up:**
- ✅ Databricks CLI configured
- ✅ Secret scope `dlt-framework` created
- ✅ **25 secrets uploaded** (PostgreSQL, Oracle, MSSQL, Azure SQL, ADLS, APIs)
- ✅ Framework auto-detects Databricks environment

**Your Workspace:**
- URL: `https://dbc-b0d51bcf-8a1a.cloud.databricks.com`
- Scope: `dlt-framework`
- Secrets: 25

**How it works:**

**In Databricks notebook:**
```python
# Framework automatically uses Databricks secrets
from pyspark.dbutils import DBUtils
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
dbutils = DBUtils(spark)

# Framework retrieves secrets like this:
host = dbutils.secrets.get(scope='dlt-framework', key='postgresql-host')
password = dbutils.secrets.get(scope='dlt-framework', key='postgresql-password')
```

**Secret naming convention:**
```
{source}-{config-key}

Examples:
- postgresql-host
- postgresql-port
- postgresql-database
- postgresql-username
- postgresql-password
- oracle-host
- adls-storage-account-name
- adls-storage-account-key
- coingecko-api-key
```

**To add/update a secret:**

**Method 1: Using CLI (Recommended)**
```powershell
databricks secrets put --scope dlt-framework --key new-key --string-value "new-value"
```

**Method 2: Using Python Script**
```powershell
# Add to upload_secrets_to_databricks.py and re-run
python upload_secrets_to_databricks.py
```

**Method 3: Programmatically**
```python
from databricks_cli.sdk import ApiClient
from databricks_cli.secrets.api import SecretApi
import configparser
from pathlib import Path

config = configparser.ConfigParser()
config.read(Path.home() / ".databrickscfg")

api_client = ApiClient(
    host=config['DEFAULT']['host'],
    token=config['DEFAULT']['token']
)
secret_api = SecretApi(api_client)

secret_api.put_secret(
    scope='dlt-framework',
    key='new-key',
    string_value='new-value',
    bytes_value=None
)
```

**Benefits:**
- ✅ **Native Databricks integration** - seamless
- ✅ **No Azure subscription needed** - works on any Databricks
- ✅ **Access control** - Databricks RBAC integration
- ✅ **Audit trail** - Databricks logs secret access
- ✅ **Framework auto-detects** - zero code changes

**Verification:**

```powershell
# List all secrets
databricks secrets list --scope dlt-framework

# Output:
postgresql-host
postgresql-port
postgresql-database
...
```

---

### Option 2: Azure Key Vault (Enterprise)

**Status:** ⚠️ Not configured (optional)

**When to use:**
- ✅ Using multiple Azure services (Functions, Logic Apps, etc.)
- ✅ Need centralized secret management across services
- ✅ Enterprise compliance requirements

**Requirements:**
- Azure subscription
- Resource group
- Azure CLI installed

**Setup Steps:**

**1. Install Azure CLI:**
```powershell
# Download from https://aka.ms/installazurecliwindows
# Or via winget
winget install Microsoft.AzureCLI
```

**2. Login:**
```powershell
az login
```

**3. Create Key Vault:**
```powershell
# Create resource group
az group create --name rg-dlt-prod --location eastus

# Create Key Vault
az keyvault create \
  --name kv-dlt-databricks \
  --resource-group rg-dlt-prod \
  --location eastus
```

**4. Migrate secrets:**
```powershell
# Run migration script
python migrate_to_keyvault.py https://kv-dlt-databricks.vault.azure.net/

# Output:
Migrating 25 secrets from secrets.toml to Key Vault...
✅ Uploaded: postgres-source-host
✅ Uploaded: postgres-source-port
...
Migration complete!
```

**5. Set environment variable:**
```powershell
# User-level (persistent)
[System.Environment]::SetEnvironmentVariable(
    'AZURE_KEY_VAULT_URL',
    'https://kv-dlt-databricks.vault.azure.net/',
    'User'
)

# Current session only
$env:AZURE_KEY_VAULT_URL = "https://kv-dlt-databricks.vault.azure.net/"
```

**6. Test:**
```powershell
python run.py
# Should see in logs: [AZURE KEY VAULT] Credential Source: Azure Key Vault
```

**Using with Databricks:**

You CAN use Key Vault with Databricks! Two methods:

**Method A: Service Principal (Recommended)**

1. Create service principal:
```bash
az ad sp create-for-rbac --name sp-dlt-databricks --skip-assignment

# Output (save these!):
{
  "appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "password": "your-secret",
  "tenant": "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
}
```

2. Grant access to Key Vault:
```bash
az keyvault set-policy --name kv-dlt-databricks \
  --spn <appId> \
  --secret-permissions get list
```

3. Store SP credentials in Databricks Secrets:
```powershell
databricks secrets create-scope --scope azure-keyvault-auth
databricks secrets put --scope azure-keyvault-auth --key client-id --string-value "<appId>"
databricks secrets put --scope azure-keyvault-auth --key client-secret --string-value "<password>"
databricks secrets put --scope azure-keyvault-auth --key tenant-id --string-value "<tenant>"
```

4. Framework retrieves SP credentials from Databricks, then uses them to access Key Vault.

**Method B: Managed Identity (Azure Databricks only)**

If using Azure Databricks (not AWS/GCP):
1. Enable managed identity on Databricks workspace
2. Grant managed identity access to Key Vault
3. Framework auto-authenticate

**Benefits:**
- ✅ **Centralized** - one place for all secrets
- ✅ **Multi-service** - use in Functions, Logic Apps, etc.
- ✅ **Audit trail** - Azure Monitor integration
- ✅ **RBAC** - fine-grained access control

---

### Option 3: Environment Variables (Quick)

**Status:** ⚠️ Not configured

**When to use:**
- ✅ Better than secrets.toml but don't want cloud setup
- ✅ Quick local development
- ✅ CI/CD pipelines (GitHub Actions, Azure DevOps)

**Setup (5 minutes):**

**Automated Setup:**
```powershell
# Run setup script
.\setup_env_secrets.ps1

# Reads secrets.toml and creates environment variables
# Format: DLT_{SOURCE}_{KEY}
```

**Manual Setup:**
```powershell
# PostgreSQL
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_HOST', 'myserver.com', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_PORT', '5432', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_DATABASE', 'sales_db', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_USERNAME', 'admin', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_POSTGRESQL_PASSWORD', 'SecurePass!', 'User')

# ADLS Gen2
[System.Environment]::SetEnvironmentVariable('DLT_ADLS_STORAGE_ACCOUNT_NAME', 'dltpoctest', 'User')
[System.Environment]::SetEnvironmentVariable('DLT_ADLS_STORAGE_ACCOUNT_KEY', 'your_key_here', 'User')
```

**Verification:**
```powershell
# Check variable
$env:DLT_POSTGRESQL_HOST

# Run framework
python run.py
# Should see in logs: [ENV VARS] Credential Source: Environment Variables
```

**Benefits:**
- ✅ **Fast setup** - 5 minutes
- ✅ **No cloud dependency** - works offline
- ✅ **CI/CD friendly** - easy to set in pipelines
- ✅ **Better than files** - not committed to Git

**Limitations:**
- ⚠️ **User-specific** - each developer sets their own
- ⚠️ **No centralization** - not shared across team
- ⚠️ **Less secure** - visible in environment

---

### Option 4: secrets.toml (Development Only)

**Status:** ✅ Currently active (local development)

**When to use:**
- ✅ Local development only
- ✅ Quick prototyping
- ❌ **NEVER for production**

**Location:** `.dlt/secrets.toml`

**Pros:**
- ✅ **Simple** - edit text file
- ✅ **Fast** - no setup required
- ✅ **DLT native** - standard dlt pattern

**Cons:**
- ❌ **Insecure** - plaintext passwords
- ❌ **Not shareable** - each developer maintains own file
- ❌ **Git risk** - might be accidentally committed

**Security:**

Always keep in `.gitignore`:
```
# .gitignore
.dlt/secrets.toml
config/secrets.toml
*.toml
```

**Recommendation:** Use for local dev, switch to Databricks Secrets for production.

---

## Deployment Options

### Option 1: Databricks Workflows ⭐ RECOMMENDED

**Status:** ✅ **READY TO DEPLOY**

**Why Databricks:**
- ✅ **Large data handling** - distributed processing (GB to TB scale)
- ✅ **Scalable compute** - auto-scaling clusters
- ✅ **Native ADLS integration** - direct access to Data Lake
- ✅ **Secret management** - Databricks Secrets (already configured)
- ✅ **Workflow orchestration** - scheduled jobs with dependencies
- ✅ **Enterprise security** - Azure AD integration

**Architecture:**

```
Databricks Workflow (Job)
├── Task 1: Run DLT Framework
│   ├── Cluster: Standard_DS4_v2 (8 cores, 28GB)
│   ├── Runtime: DBR 12.2 LTS
│   ├── Script: run.py
│   └── Output: ADLS Gen2 (az://raw-data)
└── Task 2: Data Quality Checks (future)
```

**Deployment Steps:**

**1. Upload framework to DBFS:**

```powershell
# Create workspace folder
databricks workspace mkdirs /Workspace/dlt-ingestion-framework

# Upload all files
databricks fs cp --recursive ./dlt-ingestion-framework dbfs:/FileStore/dlt-ingestion-framework/

# Or upload via Databricks UI:
# Workspace → Upload → Select folder
```

**2. Create Databricks cluster:**

```json
{
  "cluster_name": "dlt-ingestion-cluster",
  "spark_version": "12.2.x-scala2.12",
  "node_type_id": "Standard_DS4_v2",
  "autoscale": {
    "min_workers": 2,
    "max_workers": 8
  },
  "spark_env_vars": {
    "AZURE_KEY_VAULT_URL": ""
  }
}
```

**3. Create Job:**

Databricks UI → Workflows → Create Job

**Job Configuration:**
- **Name:** DLT Ingestion Framework
- **Task Type:** Python script
- **Script Path:** `/Workspace/dlt-ingestion-framework/run.py`
- **Cluster:** dlt-ingestion-cluster
- **Schedule:** Daily at 2:00 AM UTC

**4. Add init script (for ODBC driver):**

Create `dbfs:/databricks/scripts/install_odbc.sh`:
```bash
#!/bin/bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

In cluster config:
```json
{
  "init_scripts": [{
    "dbfs": {
      "destination": "dbfs:/databricks/scripts/install_odbc.sh"
    }
  }]
}
```

**5. Install Python dependencies:**

Create `requirements.txt` on DBFS, then in notebook:
```python
%pip install -r dbfs:/FileStore/dlt-ingestion-framework/requirements.txt
```

**6. Run Job:**

```python
# Databricks notebook
%run /Workspace/dlt-ingestion-framework/run.py
```

**Monitoring:**

- **Logs:** Databricks Workspace → Jobs → <job_name> → Runs → Latest → Logs
- **Metrics:** Spark UI → SQL/DataFrame metrics
- **Errors:** Check DBFS logs: `dbfs:/FileStore/dlt-ingestion-framework/logs/`

**Benefits:**
- ✅ **Production-ready** - enterprise-grade platform
- ✅ **Scalable** - handles 100GB+ tables
- ✅ **Monitored** - built-in alerting
- ✅ **Scheduled** - automated daily/hourly runs

---

### Option 2: Local Execution (Development)

**Status:** ✅ Active

**When to use:**
- ✅ Local development
- ✅ Testing new configurations
- ✅ Debugging
- ❌ Not for production

**Requirements:**
- Python 3.9+
- ODBC Driver 17 for SQL Server
- Oracle Instant Client (optional, using thin client)

**Setup:**

```powershell
# 1. Clone repository
git clone <repo-url>
cd dlt-ingestion-framework

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure secrets
# Edit .dlt/secrets.toml with your credentials

# 5. Configure jobs
# Edit config/ingestion_config.xlsx

# 6. Run
python run.py
```

**Output:**
```
2026-02-12 10:15:30 | INFO     | Starting ingestion orchestrator
2026-02-12 10:15:31 | INFO     | Loaded 3 enabled jobs
2026-02-12 10:15:31 | INFO     | Starting job: postgres.orders
...
2026-02-12 10:20:45 | INFO     | === Execution Summary ===
2026-02-12 10:20:45 | INFO     | Total Jobs: 3
2026-02-12 10:20:45 | INFO     | Successful: 3
2026-02-12 10:20:45 | INFO     | Failed: 0
```

**Logs:**
- Main log: `logs/main_orchestrator_20260212_101530.log`
- Per-source: `logs/source_{name}_*.log`
- Errors: `logs/errors/*.log`

**Audit:**
- CSV: `metadata/audit_20260212.csv`

---

### Option 3: Azure DevOps Pipelines

**Status:** ⚠️ Not configured

**When to use:**
- ✅ Enterprise CI/CD
- ✅ Integration with existing DevOps
- ✅ Scheduled runs outside Databricks

**Sample Pipeline (`azure-pipelines.yml`):**

```yaml
trigger: none

schedules:
- cron: "0 2 * * *"  # Daily at 2 AM UTC
  displayName: Daily ingestion run
  branches:
    include:
    - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.10'

- script: |
    pip install -r requirements.txt
  displayName: 'Install dependencies'

- task: AzureCLI@2
  inputs:
    azureSubscription: 'Azure-Subscription'
    scriptType: 'bash'
    scriptLocation: 'inlineScript'
    inlineScript: |
      # Set Key Vault URL
      export AZURE_KEY_VAULT_URL="https://kv-dlt-prod.vault.azure.net/"
      
      # Run framework
      python run.py
  displayName: 'Run DLT Ingestion'

- task: PublishBuildArtifacts@1
  inputs:
    PathtoPublish: 'logs'
    ArtifactName: 'ingestion-logs'
  condition: always()

- task: PublishBuildArtifacts@1
  inputs:
    PathtoPublish: 'metadata'
    ArtifactName: 'audit-trail'
  condition: always()
```

**Benefits:**
- ✅ **Enterprise CI/CD** - integration with existing workflows
- ✅ **Artifact publishing** - logs archived
- ✅ **Email notifications** - built-in alerting

---

### Option 4: Azure Functions (Future)

**Status:** ⚠️ Not implemented

**Use case:** Event-driven ingestion (e.g., trigger on file upload)

**Not recommended** due to timeout limits (10 min max).

---

## Operations & Monitoring

### Running the Framework

#### Local Execution

**From framework root:**
```powershell
cd dlt-ingestion-framework
python run.py
```

**With virtual environment:**
```powershell
.\venv\Scripts\Activate.ps1
python run.py
```

**Direct module execution:**
```powershell
python -m src.main
```

---

#### Databricks Execution

**Method 1: Interactive Notebook**
```python
# Databricks notebook
%run /Workspace/dlt-ingestion-framework/run.py
```

**Method 2: Scheduled Job**
- Databricks UI → Workflows → <job_name> → Run Now

**Method 3: Databricks CLI**
```powershell
databricks runs submit --json '{
  "run_name": "dlt-ingestion-manual",
  "existing_cluster_id": "<cluster-id>",
  "spark_python_task": {
    "python_file": "dbfs:/FileStore/dlt-ingestion-framework/run.py"
  }
}'
```

---

### Monitoring Execution

#### 1. Console Output

**Live monitoring:**
```
2026-02-12 10:15:30 | INFO     | Starting ingestion orchestrator
2026-02-12 10:15:31 | INFO     | Loaded 3 enabled jobs
2026-02-12 10:15:31 | INFO     | ===================================
2026-02-12 10:15:31 | INFO     | Starting job: postgres.orders
2026-02-12 10:15:31 | INFO     |   Source: postgresql
2026-02-12 10:15:31 | INFO     |   Table: orders
2026-02-12 10:15:31 | INFO     |   Load Type: INCREMENTAL
2026-02-12 10:15:32 | INFO     |   Connected to: myserver.postgres.database.azure.com
2026-02-12 10:15:35 | INFO     |   Extracting rows where updated_at > 2026-01-15
2026-02-12 10:16:15 | INFO     | ✅ SUCCESS: Processed 15,234 rows in 45.2s
2026-02-12 10:16:15 | INFO     |   Partition: orders/2026/02/12
2026-02-12 10:16:15 | INFO     | ===================================
```

---

#### 2. Log Files

**Main orchestrator log:**
```powershell
# View latest log
Get-Content logs/main_orchestrator_*.log -Tail 50

# Follow live
Get-Content logs/main_orchestrator_*.log -Wait
```

**Per-source logs:**
```powershell
# PostgreSQL jobs only
Get-Content logs/source_postgres_*.log

# SQL Server jobs only
Get-Content logs/source_sqlserver_*.log
```

**Error-only logs (quick debugging):**
```powershell
# Today's PostgreSQL errors
Get-Content logs/errors/postgres_errors_20260212.log

# All errors today
Get-ChildItem logs/errors/*_20260212.log | ForEach-Object { Get-Content $_ }
```

---

#### 3. Audit CSV

**Check today's jobs:**
```powershell
# PowerShell
Import-Csv metadata/audit_20260212.csv | Format-Table
```

**Python analysis:**
```python
import pandas as pd

# Load audit data
df = pd.read_csv('metadata/audit_20260212.csv')

# Summary
print(f"Total jobs: {len(df)}")
print(f"Successful: {len(df[df['status'] == 'SUCCESS'])}")
print(f"Failed: {len(df[df['status'] == 'FAILED'])}")
print(f"Total rows: {df['rows_processed'].sum():,}")

# Failed jobs
failures = df[df['status'] == 'FAILED'][['job_name', 'error_message']]
print("\nFailed Jobs:")
print(failures)

# Slowest jobs
slow_jobs = df.nlargest(5, 'duration_seconds')[['job_name', 'duration_seconds']]
print("\nSlowest Jobs:")
print(slow_jobs)
```

---

#### 4. ADLS Gen2 Verification

**Using Azure Storage Explorer:**
1. Open Azure Storage Explorer
2. Connect to storage account: `dltpoctest`
3. Navigate to container: `raw-data`
4. Check for today's folders: `{table_name}/2026/02/12/`

**Using Azure CLI:**
```powershell
# List today's partitions
az storage blob list \
  --account-name dltpoctest \
  --container-name raw-data \
  --prefix "orders/2026/02/12/" \
  --output table
```

**Using Databricks:**
```python
# List files
dbutils.fs.ls("az://raw-data/orders/2026/02/12/")

# Read data
df = spark.read.parquet("az://raw-data/orders/2026/02/12/*.parquet")
df.show()
print(f"Row count: {df.count()}")
```

---

### Troubleshooting Common Issues

#### Issue 1: Connection Timeout

**Error:**
```
psycopg2.OperationalError: timeout expired
```

**Solutions:**
1. **Check network:** Ping database server
2. **Firewall:** Add client IP to database firewall (Azure SQL)
3. **Credentials:** Verify username/password in secrets
4. **Timeout setting:** Increase in connection string

**Fix for Azure SQL:**
```powershell
# Add your IP to firewall
az sql server firewall-rule create \
  --resource-group <rg-name> \
  --server <server-name> \
  --name "AllowMyIP" \
  --start-ip-address <your-ip> \
  --end-ip-address <your-ip>
```

---

#### Issue 2: Missing Secret

**Error:**
```
KeyError: 'postgresql' not found in secrets
```

**Solutions:**
1. **Check secrets.toml:** Ensure `[sources.postgresql]` section exists
2. **Check source_name:** Excel `source_name` must match secrets key
3. **Databricks:** Verify secrets uploaded to scope

**Verification:**
```powershell
# Local - check secrets.toml
cat .dlt/secrets.toml | Select-String "postgresql"

# Databricks - list secrets
databricks secrets list --scope dlt-framework
```

---

#### Issue 3: Schema Not Found (Oracle)

**Error:**
```
ORA-00942: table or view does not exist
```

**Solution:**

**Always specify `schema_name` for Oracle tables in Excel:**
```
source_type:  oracle
source_name:  oracle
table_name:   CUSTOMERS
schema_name:  SCOTT        ← Required!
enabled:      Y
```

---

#### Issue 4: ODBC Driver Not Found

**Error:**
```
[Microsoft][ODBC Driver Manager] Data source name not found
```

**Solution:**

**Install ODBC Driver 17:**

**Windows:**
```powershell
# Download and install
# https://go.microsoft.com/fwlink/?linkid=2249006
```

**Ubuntu (Databricks):**
```bash
# Init script
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql17
```

**Verification:**
```powershell
# Windows
odbcad32

# Linux
odbcinst -j
```

---

#### Issue 5: Row Count Shows Zero

**Symptom:**
```csv
timestamp,job_name,rows_processed
2026-02-12 10:15:30,orders,0
```

**Possible causes:**
1. **No new data:** Incremental load with no updates since last run
2. **Wrong watermark:** `last_watermark` is in the future
3. **Table empty:** Source table has no data

**Debugging:**
```python
# Check source table
# PostgreSQL
SELECT COUNT(*) FROM orders WHERE updated_at > '2026-01-15';

# Check watermark
SELECT MAX(updated_at) FROM orders;
```

---

#### Issue 6: Permission Denied (ADLS)

**Error:**
```
azure.core.exceptions.ClientAuthenticationError: authentication failed
```

**Solutions:**
1. **Check storage key:** Verify `azure_storage_account_key` in secrets
2. **Container exists:** Ensure `raw-data` container created
3. **Access tier:** Verify storage account is Gen2 (hierarchical namespace enabled)

**Verification:**
```powershell
# Test connection
az storage container show \
  --name raw-data \
  --account-name dltpoctest \
  --account-key "<your-key>"
```

---

### Performance Optimization

#### Large Table Strategies

**Problem:** 50M+ row table takes hours

**Solutions:**

**1. Incremental Load:**
```
# Excel config
load_type: INCREMENTAL
watermark_column: updated_at
last_watermark: 2026-02-11
```

**2. Custom Chunk Size:**

Add `chunk_size` column to Excel (framework auto-optimization in roadmap):
```
table_name: large_table
chunk_size: 500000       ← Process 500K rows at a time
```

**3. Parallel Execution (future):**
```python
# In main.py
orchestrator.run_all(parallel=True, max_workers=3)
```

**4. Databricks Optimization:**
- **Larger cluster:** Standard_DS5_v2 (16 cores, 56GB)
- **More workers:** Increase autoscale max to 12
- **Spot instances:** Enable for 80% cost savings

---

## Quick Start Guide

### For New Team Members

**Time to first run: 15 minutes**

#### Step 1: Get the Code (2 min)

```powershell
# Clone repository
git clone <repo-url>
cd dlt-ingestion-framework
```

---

#### Step 2: Install Python Dependencies (3 min)

```powershell
# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

#### Step 3: Configure Credentials (5 min)

**Edit `.dlt/secrets.toml`:**

```toml
# PostgreSQL (example)
[sources.postgres]
host = "myserver.postgres.database.azure.com"
port = 5432
database = "sales_db"
username = "admin@myserver"
password = "ask_team_lead_for_password"

# ADLS Gen2
[destination.filesystem]
bucket_url = "az://raw-data"

[destination.filesystem.credentials]
azure_storage_account_name = "dltpoctest"
azure_storage_account_key = "ask_team_lead_for_key"
```

**Ask team lead for:**
- Database passwords
- ADLS storage account key
- API keys

---

#### Step 4: Configure Jobs (3 min)

**Open Excel:** `config/ingestion_config.xlsx`

**Enable one job for testing:**
```
source_type:  postgresql
source_name:  postgres      ← Must match secrets.toml key
table_name:   orders
load_type:    FULL
enabled:      Y              ← Set to Y
```

**Disable other jobs:**
```
enabled: N                   ← Set others to N for now
```

**Save Excel**

---

#### Step 5: Run! (2 min)

```powershell
python run.py
```

**Expected output:**
```
2026-02-12 10:15:30 | INFO | Starting ingestion orchestrator
2026-02-12 10:15:31 | INFO | Loaded 1 enabled jobs
2026-02-12 10:15:31 | INFO | Starting job: postgres.orders
2026-02-12 10:16:15 | INFO | ✅ SUCCESS: Processed 15,234 rows in 45.2s
2026-02-12 10:16:15 | INFO | === Execution Summary ===
2026-02-12 10:16:15 | INFO | Total Jobs: 1
2026-02-12 10:16:15 | INFO | Successful: 1
2026-02-12 10:16:15 | INFO | Failed: 0
```

---

#### Step 6: Verify Output

**Check logs:**
```powershell
Get-Content logs/main_orchestrator_*.log -Tail 20
```

**Check audit:**
```powershell
Import-Csv metadata/audit_20260212.csv | Format-Table
```

**Check ADLS (Azure Storage Explorer):**
```
Container: raw-data
Path: orders/2026/02/12/
File: *.parquet
```

---

### For Data Analysts (Adding New Tables)

**Time: 5 minutes**

#### Prerequisites

- Excel editing skills only
- No Python knowledge required

#### Steps

**1. Open Excel:** `config/ingestion_config.xlsx`

**2. Add new row:**

```
source_type:      postgresql        ← Database type
source_name:      postgres          ← Which database (from secrets)
table_name:       new_table         ← Your table name
schema_name:                        ← Leave blank (Oracle only)
load_type:        FULL              ← FULL or INCREMENTAL
watermark_column:                   ← For INCREMENTAL only
last_watermark:                     ← For INCREMENTAL only
api_endpoint:                       ← For APIs only
enabled:          Y                 ← Must be Y to run
```

**3. Save Excel**

**4. Ask developer to run:**
```powershell
python run.py
```

**5. Check output:**
- Audit CSV: `metadata/audit_YYYYMMDD.csv`
- ADLS: `az://raw-data/new_table/YYYY/MM/DD/`

**That's it!** No code changes needed.

---

### For DevOps Engineers (Databricks Deployment)

**Time: 30 minutes**

#### Prerequisites

- Databricks workspace access
- `databricks` CLI installed
- Databricks token generated

#### Steps

**1. Configure Databricks CLI:**

```powershell
python configure_databricks.py

# Prompts:
# Databricks URL: https://your-workspace.cloud.databricks.com
# Token: dapi1234567890abcdef...
```

**2. Test connection:**

```powershell
python test_databricks_connection.py

# Expected output:
# ✅ Connection successful
# Workspace: https://your-workspace.cloud.databricks.com
```

**3. Upload secrets:**

```powershell
# Creates scope 'dlt-framework' and uploads all secrets
python upload_secrets_to_databricks.py

# Expected output:
# ✅ Created scope: dlt-framework
# ✅ Uploaded 25 secrets
```

**4. Upload framework to DBFS:**

```powershell
# Upload all files
databricks fs cp --recursive ./dlt-ingestion-framework dbfs:/FileStore/dlt-ingestion-framework/
```

**5. Create cluster:**

Databricks UI → Compute → Create Cluster

**Config:**
- **Name:** dlt-ingestion-cluster
- **Runtime:** DBR 12.2 LTS
- **Node type:** Standard_DS4_v2
- **Autoscale:** Min 2, Max 8
- **Init script:** `dbfs:/databricks/scripts/install_odbc.sh` (see Deployment section)

**6. Create job:**

Databricks UI → Workflows → Create Job

**Config:**
- **Name:** DLT Ingestion Framework
- **Task type:** Python script
- **Path:** `/Workspace/dlt-ingestion-framework/run.py`
- **Cluster:** dlt-ingestion-cluster
- **Schedule:** Daily at 2:00 AM UTC

**7. Test run:**

Databricks UI → Workflows → DLT Ingestion Framework → Run Now

**8. Monitor:**

Check logs in Databricks UI → Jobs → <job> → Runs → Latest

---

## Future Roadmap

### ✅ Completed Features

- ✅ Multi-source ingestion (5 types)
- ✅ FULL and INCREMENTAL loads
- ✅ Excel-driven configuration
- ✅ ADLS Gen2 with date partitioning
- ✅ Comprehensive logging (per-source + errors)
- ✅ Audit trail CSV
- ✅ Row count tracking
- ✅ Schema evolution detection
- ✅ 4 secret management options
- ✅ Databricks Secrets integration
- ✅ Modular architecture v2.0

---

### 🚀 Planned Features (Priority Order)

#### Priority 1: Reliability & Observability

**1. Email Notifications** (Effort: 2 hours)
- Send email on job failure with error details
- Daily summary report (successful/failed, row counts)
- SMTP configuration in secrets
- HTML formatted emails

**2. Retry Mechanism** (Effort: 3 hours)
- Exponential backoff (3 retries: 2s, 4s, 8s)
- Retry on transient errors only
- Skip retry on auth failures
- Log retry attempts

**3. Row Count Validation** (Effort: 2 hours)
- Compare source count vs destination count
- Alert if mismatch > threshold (1%)
- Log validation results in audit CSV

**4. Schema Drift Alerting** (Effort: 3 hours)
- Store schema snapshot after each run
- Compare current vs previous
- Alert on column additions/deletions/type changes
- Schema history tracking

---

#### Priority 2: Performance & Scale

**5. Parallel Execution** (Effort: 3 hours)
- Process multiple tables concurrently
- ThreadPoolExecutor with configurable workers
- Thread-safe logging
- Reduce total runtime by 60%

**6. Dynamic Chunk Sizing** (Effort: 4 hours)
- Pre-flight table size estimation
- Auto-calculate optimal chunk_size
- Memory-aware chunking
- Excel override option

**7. Delta Lake Support** (Effort: 5 hours)
- True MERGE/UPSERT operations
- ACID transactions
- Time travel
- Better for incremental loads

---

#### Priority 3: Advanced Features

**8. Data Quality Checks** (Effort: 4 hours)
- Null value detection
- Duplicate detection
- Data type validation
- Custom validation rules in Excel

**9. CDC (Change Data Capture)** (Effort: 8 hours)
- Binary log reading (PostgreSQL, SQL Server)
- Real-time change tracking
- Insert/Update/Delete flags
- Reduces load on source databases

**10. REST API Pagination Improvements** (Effort: 3 hours)
- Offset-based pagination
- Token-based pagination
- Custom pagination logic
- Rate limiting handling

---

#### Priority 4: Enterprise Features

**11. Multi-Destination Support** (Effort: 6 hours)
- Write to multiple destinations simultaneously
- ADLS + Databricks Unity Catalog
- ADLS + Snowflake
- Destination routing rules in Excel

**12. Data Lineage Tracking** (Effort: 8 hours)
- Track data movement (source → ADLS → downstream)
- Lineage visualization
- Impact analysis
- Integration with Unity Catalog

**13. Incremental Schema Evolution** (Effort: 5 hours)
- Automatic ALTER TABLE in destinations
- Schema version control
- Backward compatibility checks
- Migration scripts generation

---

### 🔮 Future Considerations (6+ months)

- **Streaming Support** (Azure Event Hubs)
- **Data Transformation** (dbt integration)
- **Machine Learning Integration** (Auto ML on ingested data)
- **Multi-Cloud** (AWS S3, GCS support)
- **Web UI Dashboard** (Flask/Streamlit)

---

## Appendix

### A. Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Core Framework** | Python | 3.9, 3.10, 3.11 | Base language |
| **Data Pipeline** | dlthub (dlt) | >= 1.4.0 | ETL framework |
| **Database Drivers** | psycopg2-binary | latest | PostgreSQL |
| | oracledb | latest | Oracle (thin client) |
| | pyodbc | latest | SQL Server, Azure SQL |
| **Cloud Storage** | azure-storage-blob | >= 12.19.0 | ADLS Gen2 |
| **Secret Management** | azure-identity | >= 1.15.0 | Azure Auth |
| | azure-keyvault-secrets | >= 4.7.0 | Key Vault |
| | databricks-cli | latest | Databricks Secrets |
| **Configuration** | pandas | >= 2.0.0 | Excel reading |
| | openpyxl | >= 3.1.0 | Excel support |
| | toml | >= 0.10.2 | TOML parsing |
| **Data Format** |SQLAlchemy | >= 1.4.0 | Database abstraction |
| | pyarrow | latest | Parquet format |

---

### B. File Extensions & Formats

| Extension | Purpose | Tool |
|-----------|---------|------|
| **.py** | Python source code | VS Code, PyCharm |
| **.xlsx** | Excel configuration | Excel, LibreOffice |
| **.toml** | Secrets configuration | Text editor |
| **.log** | Execution logs | Text viewer |
| **.csv** | Audit trails | Excel, Python |
| **.parquet** | Output data files | Databricks, Spark |
| **.md** | Documentation | Markdown viewer |
| **.json** | Schema validation | Text editor |

---

### C. Important URLs & Resources

**Databricks:**
- Workspace: `https://dbc-b0d51bcf-8a1a.cloud.databricks.com`
- Secret scope: `dlt-framework` (25 secrets)

**dlthub Documentation:**
- Main: https://dlthub.com/docs
- SQL Database: https://dlthub.com/docs/dlt-sources/sql_database
- REST API: https://dlthub.com/docs/dlt-sources/rest_api
- Filesystem: https://dlthub.com/docs/dlt-destinations/filesystem

**Azure Resources:**
- Storage Account: `dltpoctest`
- Container: `raw-data`
- Portal: https://portal.azure.com

**Driver Downloads:**
- ODBC Driver 17: https://go.microsoft.com/fwlink/?linkid=2249006
- Oracle Instant Client: https://www.oracle.com/database/technologies/instant-client.html

---

### D. Contact & Support

**Framework Maintainers:**
- Lead Developer: [Your Name]
- DevOps: [DevOps Lead]
- Data Engineering: [Data Lead]

**Documentation:**
- This guide: `COMPLETE_FRAMEWORK_GUIDE.md`
- Quick start: `README.md`
- Secret management: `SECRET_MANAGEMENT_QUICKSTART.md`
- Architecture: `docs/REFACTORING_COMPLETE.md`

**Getting Help:**
1. Check this guide first
2. Review error logs: `logs/errors/`
3. Check audit CSV: `metadata/audit_*.csv`
4. Open issue in repository
5. Contact framework maintainers

---

## Summary

This **DLT Multi-Source Ingestion Framework** provides:

✅ **Production-grade** - comprehensive logging, error handling, audit trails  
✅ **Excel-driven** - non-technical users can add tables without code changes  
✅ **Multi-source** - PostgreSQL, Oracle, SQL Server, Azure SQL, REST APIs  
✅ **Scalable** - handles GB to TB datasets on Databricks  
✅ **Secure** - 4 secret management options (Databricks Secrets ready)  
✅ **Modular** - clean architecture, easy to maintain and extend  
✅ **DLT-native** - built on proven dlthub library  
✅ **Date-partitioned** - analytics-friendly Parquet output structure  

**Next Steps:**
1. **Analysts:** Add tables to `config/ingestion_config.xlsx`
2. **Developers:** Extend sources in `src/sources/`
3. **DevOps:** Deploy to Databricks using `upload_secrets_to_databricks.py`
4. **Everyone:** Monitor via logs and audit CSVs

**Questions?** Refer to this guide or contact framework maintainers.

---

**Document Version:** 1.0  
**Last Updated:** February 12, 2026  
**Maintained by:** DLT Framework Team






Folder	Purpose	Size	Update Frequency
_dlt_loads/	Execution history	~2.3 MB	Every pipeline run
dlt_pipeline_.../	Pipeline state	~74 KB	Every run (state updates)
_dlt_version/	Schema history	~10 KB	When schema changes

1. Troubleshooting:

Check _dlt_loads/ to see which loads failed
Review exact error messages from last run
2. Incremental Load Verification:

Check dlt_pipeline_*/state.jsonl for last watermark
Verify incremental loads are progressing
3. Schema Change Monitoring:

Review _dlt_version/ when new columns appear
Track when table structures changed
4. Audit & Compliance:

Use _dlt_loads/ for complete audit trail
Prove when data was ingested and by whom