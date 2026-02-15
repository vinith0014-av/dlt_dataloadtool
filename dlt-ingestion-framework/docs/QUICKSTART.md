# 🚀 Quick Start Guide

## Your Framework is Ready!

This dlthub-powered framework is fully configured and ready to use. Here's how to get started in 3 simple steps:

---

## Step 1: Install Dependencies

```bash
cd dlt-ingestion-framework
pip install -r requirements.txt
```

This installs:
- `dlt[filesystem,sql_database]` - The dlthub library
- Database drivers (psycopg2, oracledb, pyodbc)
- Azure storage libraries
- Excel/pandas support

---

## Step 2: Configure Your Credentials

Edit `config/secrets.toml` and replace placeholders with your actual credentials:

```toml
[sources.postgresql]
host = "your-actual-host.database.windows.net"
username = "your_username"
password = "your_password"
# ... etc
```

**Important:** The file is already in `.gitignore` so it won't be committed.

---

## Step 3: Review Sample Configuration

Open `config/ingestion_config.xlsx` in Excel. You'll see 4 sample configurations:

| Job | Source | Table | Type | Status |
|-----|--------|-------|------|--------|
| pg_customers_full     | PostgreSQL | customers | FULL | ✅ Enabled |
| pg_orders_incr        | PostgreSQL | orders | INCREMENTAL | ✅ Enabled |
| oracle_employees_full | Oracle   | employees | FULL | ✅ Enabled |
| mssql_products_incr   | MSSQL    | products  | INCREMENTAL | ❌ Disabled |

**To add your tables:**
1. Copy an existing row
2. Update `job_id`, `table_name`, `source_name`, etc.
3. Set `enabled` to `Y`
4. Save the file

---

## Step 4: Run the Framework

```bash
python src/main.py
```

You'll see output like:
```
2024-01-15 14:30:22 | INFO | Starting DLT ingestion framework execution (dlthub-powered)
2024-01-15 14:30:22 | INFO | Found 3 enabled job(s) to process
2024-01-15 14:30:25 | INFO | Created dlt pipeline: pg_customers_full
2024-01-15 14:30:28 | INFO | Pipeline completed: 15,432 rows processed
...
```

---

## What Happens During Execution?

1. **Reads Excel** - Loads all configurations from `config/ingestion_config.xlsx`
2. **Validates** - Checks required fields, incremental settings, etc.
3. **For Each Enabled Job:**
   - Creates a dlt pipeline with Azure filesystem destination
   - Extracts data using `sql_table` resource
   - Writes Parquet files to ADLS Gen2
   - Updates pipeline state in `.dlt/` directory
   - Logs metadata to `metadata/audit_log.jsonl`

---

## Where is Your Data?

Data lands in ADLS at:
```
az://{your_storage_account}.blob.core.windows.net/{container}/{target_folder_path}/{dataset_name}/
```

Example:
```
az://mystorageaccount.blob.core.windows.net/raw-data/raw/sales_db_customers/
├── customers.parquet
└── _dlt_loads.parquet
```

---

## Monitoring & Logs

- **Application logs:** `logs/ingestion_YYYYMMDD.log`
- **Audit metadata:** `metadata/audit_log.jsonl`
- **Pipeline state:** `.dlt/` directory (managed by dlthub)

---

## Common Patterns

### Add a New Full Load Table

In Excel, add row:
```
job_id: mydb_newtable_full
source_type: PostgreSQL
source_name: mydb
schema_name: public
table_name: newtable
load_type: FULL
enabled: Y
target_container: raw-data
target_folder_path: raw
```

### Add an Incremental Load Table

In Excel, add row:
```
job_id: mydb_orders_incr
source_type: PostgreSQL
source_name: mydb
table_name: orders
load_type: INCREMENTAL
enabled: Y
watermark_column: updated_at
last_watermark: 2024-01-01
target_container: raw-data
target_folder_path: raw
```

### Disable a Job Temporarily

Change `enabled` from `Y` to `N` in Excel.

---

## Incremental Loads - How It Works

1. **First Run:** Uses `last_watermark` from Excel as starting point
2. **Subsequent Runs:** dlt automatically reads last watermark from `.dlt/` state
3. **Query Generated:** `SELECT * FROM table WHERE watermark_column > last_value`
4. **State Updated:** dlt saves new max watermark automatically

**No manual watermark management needed!**

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Update `config/secrets.toml` with real credentials
3. ✅ Review/modify `config/ingestion_config.xlsx`
4. ✅ Run `python src/main.py`
5. ⏭️ Check logs and ADLS output
6. ⏭️ Add more tables as needed
7. ⏭️ Schedule with cron/Airflow/Azure Data Factory

---

## Getting Help

- **Logs not showing data?** Check `logs/` directory
- **ADLS authentication error?** Verify `secrets.toml` Azure credentials
- **Table not found?** Oracle needs lowercase table names
- **Need more details?** See full [README.md](README.md)
- **dlthub docs:** https://dlthub.com/docs

---

** You're all set! Happy ingesting! **
