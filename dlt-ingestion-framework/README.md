# DLT Ingestion Framework (dlthub-powered)

Production-grade, Excel-driven data ingestion framework for loading data from multiple sources into Azure Data Lake Storage Gen2 (ADLS) using **dlthub (dlt library)**.

## 🎯 Overview

This framework provides a **100% configuration-driven** approach to data ingestion, where all behavior is controlled through an Excel configuration file. Built on top of **dlthub**, it leverages battle-tested connectors and pipeline management while adding enterprise-grade configuration management and auditing.

### Key Features

- ✅ **Excel-Driven Configuration** - Single Excel file controls all ingestion behavior
- ✅ **dlthub-Powered** - Uses proven `dlt` library for robust data pipelines
- ✅ **Multi-Source Support** - RDBMS (SQL Server, Oracle, PostgreSQL) via dlt sql_database
- ✅ **Full & Incremental Loads** - Automatic watermark management via dlt state
- ✅ **Azure ADLS Gen2** - Native filesystem destination with Parquet format
- ✅ **Production-Grade** - Comprehensive logging, error handling, audit tracking
- ✅ **Modular & Extensible** - Clean architecture following your existing DLT patterns

---

## 📁 Project Structure

```
dlt-ingestion-framework/
├── config/
│   ├── ingestion_config.xlsx    # Main configuration (USER INPUT)
│   ├── secrets.toml              # Credentials (DO NOT COMMIT)
│   └── config_schema.json        # Validation schema
├── src/
│   ├── main.py                   # Main orchestrator (dlthub-based)
│   ├── config/
│   │   ├── config_loader.py      # Excel reader & secrets loader
│   │   └── config_validator.py   # Configuration validation
│   ├── utils/
│   │   ├── logger.py             # Logging framework
│   │   └── metadata.py           # Audit & metadata tracking
│   └── models/
│       └── ingestion_job.py      # Data models
├── logs/                         # Application logs
├── metadata/                     # Audit files & watermarks
├── .dlt/                         # dlt pipeline state (auto-created)
├── generate_sample_config.py     # Creates sample Excel config
├── requirements.txt
└── README.md
```

**Key Difference from Custom Implementation:** 
- ✅ No custom connectors - uses `dlt.sources.sql_database`
- ✅ No custom writers - uses `dlt.destinations.filesystem`
- ✅ dlt handles retries, state management, schema evolution
- ✅ Pipeline state stored in `.dlt/` directory

---

## 🚀 Quick Start

### 1. Installation

```bash
# Navigate to framework directory
cd dlt-ingestion-framework

# Install dependencies
pip install -r requirements.txt
```

**Key dependency:** `dlt[filesystem,sql_database]>=1.4.0`

### 2. Configure Credentials

Edit `config/secrets.toml` with your credentials:

```toml
[sources.postgresql]
host = "your-pg-host.database.windows.net"
port = 5432
database = "your_database"
username = "your_username"
password = "your_password"

[sources.oracle]
host = "your-oracle-host.net"
port = 1521
service_name = "your_service_name"
username = "your_username"
password = "your_password"

[sources.mssql]
host = "your-mssql-host.database.windows.net"
database = "your_database"
username = "your_username"
password = "your_password"
driver = "ODBC Driver 18 for SQL Server"
trusted_connection = false

[destinations.adls]
storage_account_name = "yourstorageaccount"
storage_account_key = "your_storage_account_key_here"
container_name = "raw-data"
```

**⚠️ SECURITY:** Add `config/secrets.toml` and `.dlt/` to `.gitignore`!

### 3. Configure Ingestion Jobs

A sample Excel file is already created at `config/ingestion_config.xlsx` with 4 example configurations:

- `pg_customers_full` - PostgreSQL FULL load
- `pg_orders_incr` - PostgreSQL INCREMENTAL load
- `oracle_employees_full` - Oracle FULL load
- `mssql_products_incr` - MSSQL INCREMENTAL load (disabled)

Edit this file to add your tables.

### 4. Run the Framework

```bash
# From project root
python src/main.py
```

Or programmatically:

```python
from src.main import IngestionOrchestrator

orchestrator = IngestionOrchestrator()
results = orchestrator.run_all()

# Check results
for result in results:
    print(f"{result.job_id}: {result.status.value}")
```

---

## 📊 Excel Configuration Reference

### **Sheet: SourceConfig**

This is the primary input. Each row defines one ingestion job.

| Column | Required | Description | Example |
|--------|----------|-------------|---------|
| `job_id` | Yes | Unique identifier for the job | `pg_customers_incr` |
| `source_type` | Yes | Source system type | `PostgreSQL`, `Oracle`, `MSSQL`, `API` |
| `source_name` | Yes | Logical name of source | `sales_db`, `erp_system` |
| `schema_name` | Conditional | Database schema (required for Oracle) | `dbo`, `sales_schema` |
| `table_name` | Yes | Table or object name | `customers`, `orders` |
| `load_type` | Yes | Load strategy | `FULL` or `INCREMENTAL` |
| `enabled` | Yes | Enable/disable job | `Y` or `N` |
| `target_container` | Yes | ADLS container name | `raw-data`, `staging` |
| `target_folder_path` | Yes | Base folder in ADLS | `raw`, `bronze` |
| `watermark_column` | For INCREMENTAL | Column to track changes | `updated_at`, `id` |
| `last_watermark` | For INCREMENTAL | Initial/last watermark value | `2024-01-01`, `12345` |
| `query_filter` | No | Additional WHERE clause | `status = 'active'` |
| `api_endpoint` | For API | API endpoint path | `/api/v1/users` |
| `api_method` | For API | HTTP method | `GET`, `POST` |
| `pagination_type` | For API | Pagination strategy | `none`, `offset`, `cursor`, `page` |
| `chunk_size` | No | Rows per chunk | `100000` (default) |
| `parallelism` | No | Parallel workers | `1` (default) |

### Example Configuration

**PostgreSQL - Full Load:**
```
job_id: pg_products_full
source_type: PostgreSQL
source_name: sales_db
schema_name: public
table_name: products
load_type: FULL
enabled: Y
target_container: raw-data
target_folder_path: raw
```

**MSSQL - Incremental Load:**
```
job_id: mssql_orders_incr
source_type: MSSQL
source_name: erp_system
schema_name: dbo
table_name: orders
load_type: INCREMENTAL
enabled: Y
target_container: raw-data
target_folder_path: raw
watermark_column: updated_date
last_watermark: 2024-01-01
```

**API Source:**
```
job_id: api_users_full
source_type: API
source_name: example_api
table_name: users
load_type: FULL
enabled: Y
target_container: raw-data
target_folder_path: raw
api_endpoint: /api/v1/users
api_method: GET
pagination_type: offset
```

---

## 📂 Output Structure & dlt Pipeline Behavior

Data is written to ADLS following dlt's filesystem destination pattern:

```
az://{storage_account}.blob.core.windows.net/{container}/{target_folder_path}/{dataset_name}/
```

**Example output structure:**
```
az://mystorageaccount.blob.core.windows.net/raw-data/raw/sales_db_customers/
├── customers.parquet
└── _dlt_loads.parquet  (dlt metadata)

az://mystorageaccount.blob.core.windows.net/raw-data/raw/sales_db_orders/
├── orders.parquet
└── _dlt_loads.parquet
```

### How dlt Manages State

- **Pipeline state** stored in `.dlt/` directory (local) or state backend
- **Incremental loads:** dlt automatically tracks watermarks in pipeline state
- **Schema evolution:** dlt handles schema changes automatically
- **Load tracking:** `_dlt_loads.parquet` tracks each pipeline run

---

## 🔧 Key Components (dlthub Integration)

### 1. Main Orchestrator (`src/main.py`)

Creates dlt pipelines dynamically based on Excel config:

```python
pipeline = dlt.pipeline(
    pipeline_name=config.job_id,
    destination=dlt.destinations.filesystem(
        bucket_url=f"az://{account}.blob.core.windows.net/{container}/{path}",
        credentials={"azure_storage_account_name": "...", "azure_storage_account_key": "..."}
    ),
    dataset_name=f"{source_name}_{table_name}",
    progress="log",
)
```

### 2. Resource Creation (Following Your Existing Pattern)

```python
# Create incremental object if needed
incremental_obj = dlt.sources.incremental(
    cursor_path=config.watermark_column,
    initial_value=watermark_value
) if config.load_type == "INCREMENTAL" else None

# Create sql_table resource (same as your BigQuery pipelines)
resource = sql_table(
    credentials=ConnectionStringCredentials(conn_str),
    table=config.table_name.lower(),
    schema=config.schema_name.lower() if config.schema_name else None,
    incremental=incremental_obj,
    detect_precision_hints=True,
    defer_table_reflect=True,
    backend="pyarrow",
    chunk_size=config.chunk_size,
)

# Run pipeline
load_info = pipeline.run(
    resource,
    write_disposition="replace" if FULL else "merge",
    loader_file_format="parquet",
)
```

### 3. Config Loader (`src/config/config_loader.py`)

- Reads Excel configuration
- Loads secrets from TOML
- Builds connection strings (PostgreSQL, Oracle, MSSQL)
- Provides Azure credentials for dlt filesystem destination

### 4. Config Validator (`src/config/config_validator.py`)

- Validates required columns
- Enforces conditional requirements (incremental needs watermark)
- Prevents duplicate job_ids

### 5. Metadata Manager (`src/utils/metadata.py`)

- Audit log (JSONL format) - custom tracking
- Watermark storage - note: dlt manages incremental state internally
- Job history tracking

---

## 🔄 Incremental Load Flow (dlt-managed)

1. **Read last watermark** from dlt pipeline state (or initial_value from config)
2. **dlt builds query** automatically with `WHERE {cursor_path} > {last_value}`
3. **Extract data** using sql_table resource
4. **Write to ADLS** in Parquet format
5. **Update state** - dlt automatically updates pipeline state with new watermark

**Key Advantage:** dlt handles state management, no manual watermark tracking needed!

---

## 📊 Monitoring & Audit

### Log Files

Located in `logs/ingestion_YYYYMMDD.log`:

```
2024-01-15 14:30:22 | INFO     | Starting Job: pg_customers_incr
2024-01-15 14:30:25 | INFO     | Extracted 15,432 rows from customers
2024-01-15 14:30:28 | INFO     | Successfully wrote 15,432 rows to ADLS
```

### Audit Metadata

Located in `metadata/audit_log.jsonl`:

```json
{
  "job_id": "pg_customers_incr",
  "status": "SUCCESS",
  "rows_extracted": 15432,
  "rows_written": 15432,
  "duration_seconds": 6.2,
  "start_time": "2024-01-15T14:30:22",
  "end_time": "2024-01-15T14:30:28"
}
```

### Watermarks

Located in `metadata/watermarks.json`:

```json
{
  "pg_customers_incr": {
    "value": "2024-01-15 14:30:00",
    "updated_at": "2024-01-15T14:30:28"
  }
}
```

---

## 🛠 Extending the Framework

### Adding New Tables

Just add a row to `config/ingestion_config.xlsx` - no code changes needed!

### Supporting New Source Types

1. Create custom dlt source (see [dlt documentation](https://dlthub.com/docs))
2. Add routing logic in `src/main.py` `_execute_XXX_job()` method
3. Update `SourceType` enum in `src/models/ingestion_job.py`

### Switching to Delta Lake

Change filesystem destination to use Delta format:

```python
pipeline = dlt.pipeline(
    destination=dlt.destinations.filesystem(...),
    loader_file_format="delta",  # Instead of "parquet"
)
```

### Using Databricks

Replace filesystem destination with Databricks SQL:

```python
pipeline = dlt.pipeline(
    destination="databricks",
    dataset_name="your_catalog.your_schema",
)
```

---

## 🔐 Security Best Practices

- ✅ **Never commit** `config/secrets.toml` or `.dlt/` directory
- ✅ Add to `.gitignore`:
  ```
  config/secrets.toml
  .dlt/
  *.log
  ```
- ✅ Use **Azure Key Vault** for production credentials
- ✅ Use **Managed Identity** when running on Azure VMs/Databricks
- ✅ Restrict ADLS access with **RBAC** and **ACLs**

---

## 🐛 Troubleshooting

### Common Issues

**1. "dlt module not found"**
```bash
pip install "dlt[filesystem,sql_database]>=1.4.0"
```

**2. "secrets.toml not found"**
- Ensure `config/secrets.toml` exists with all required sections

**3. Oracle "table does not exist"**
- Use **lowercase** table names and specify `schema_name`
- Example: `schema_name: "hr"`, `table_name: "employees"` (not "HR", "EMPLOYEES")

**4. ADLS authentication failure**
- Verify `storage_account_key` in secrets.toml
- Check storage account firewall rules
- Ensure container exists or framework has permission to create it

**5. Incremental load not working**
- Check dlt pipeline state in `.dlt/` directory
- Verify `watermark_column` exists in source table
- Check logs for dlt incremental query

---

## 📈 Comparison: Custom vs dlthub Implementation

| Aspect | Custom (Previous) | dlthub (Current) |
|--------|------------------|------------------|
| **Connectors** | Custom SQLAlchemy code | `dlt.sources.sql_database` |
| **Destinations** | Custom Azure SDK | `dlt.destinations.filesystem` |
| **State Management** | Manual watermark tracking | Automatic via dlt pipeline state |
| **Retry Logic** | Custom decorator | Built into dlt |
| **Schema Evolution** | Manual handling | Automatic with dlt |
| **Code Volume** | ~2500 lines | ~800 lines |
| **Maintenance** | High - custom code | Low - battle-tested library |
| **Features** | Basic | Advanced (versioning, etc.) |

**Recommendation:** dlthub approach is production-ready and maintainable.

---

## 📄 References

- **dlthub Documentation:** https://dlthub.com/docs
- **dlt SQL Database Source:** https://dlthub.com/docs/dlt-ecosystem/verified-sources/sql_database
- **dlt Filesystem Destination:** https://dlthub.com/docs/dlt-ecosystem/destinations/filesystem
- **Azure ADLS Gen2:** https://learn.microsoft.com/en-us/azure/storage/blobs/data-lake-storage-introduction

---

## ✅ V1 Implementation Checklist (dlthub-based)

- [x] Excel configuration loader
- [x] secrets.toml for credentials
- [x] Config validation
- [x] Data models (dataclasses)
- [x] Logging framework
- [x] Metadata & audit tracking
- [x] dlt pipeline orchestration
- [x] RDBMS ingestion (MSSQL, Oracle, PostgreSQL)
- [x] ADLS Gen2 destination (Parquet)
- [x] FULL load support
- [x] INCREMENTAL load support (dlt-managed)
- [x] Error handling & recovery
- [x] Sample Excel template
- [ ] API ingestion (future)
- [ ] Databricks integration (future)
- [ ] Delta Lake support (future)

---

**🎉 Framework Ready for Production Use with dlthub!**

Start by editing `config/ingestion_config.xlsx` and `config/secrets.toml`, then run:
```bash
python src/main.py
```
