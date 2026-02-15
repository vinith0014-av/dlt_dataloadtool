# Excel Configuration Template Instructions

Since Excel files cannot be created programmatically in this environment, please follow these steps to create your `ingestion_config.xlsx` file:

## Step 1: Create Excel File

1. Create a new Excel workbook
2. Save it as: `config/ingestion_config.xlsx`

## Step 2: Create "SourceConfig" Sheet

Create a sheet named **SourceConfig** with the following columns:

### Required Columns:
- job_id
- source_type
- source_name
- schema_name
- table_name
- load_type
- enabled
- target_container
- target_folder_path

### Optional Columns (for INCREMENTAL):
- watermark_column
- last_watermark

### Optional Columns (for API):
- api_endpoint
- api_method
- pagination_type

### Optional Columns (for tuning):
- query_filter
- chunk_size
- parallelism

## Step 3: Add Sample Data

### Example Row 1 - PostgreSQL Full Load:
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
watermark_column: (leave empty)
last_watermark: (leave empty)
api_endpoint: (leave empty)
api_method: (leave empty)
pagination_type: (leave empty)
query_filter: (leave empty)
chunk_size: 100000
parallelism: 1
```

### Example Row 2 - MSSQL Incremental Load:
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
api_endpoint: (leave empty)
api_method: (leave empty)
pagination_type: (leave empty)
query_filter: status = 'active'
chunk_size: 50000
parallelism: 1
```

### Example Row 3 - Oracle Full Load:
```
job_id: oracle_customers_full
source_type: Oracle
source_name: erp_db
schema_name: sales_schema
table_name: customers
load_type: FULL
enabled: Y
target_container: raw-data
target_folder_path: raw
watermark_column: (leave empty)
last_watermark: (leave empty)
api_endpoint: (leave empty)
api_method: (leave empty)
pagination_type: (leave empty)
query_filter: (leave empty)
chunk_size: 100000
parallelism: 1
```

### Example Row 4 - API Source:
```
job_id: api_users_full
source_type: API
source_name: example_api
schema_name: (leave empty)
table_name: users
load_type: FULL
enabled: Y
target_container: raw-data
target_folder_path: raw
watermark_column: (leave empty)
last_watermark: (leave empty)
api_endpoint: /api/v1/users
api_method: GET
pagination_type: offset
query_filter: (leave empty)
chunk_size: 100000
parallelism: 1
```

## Step 4: Data Validation Rules

Apply these validations to your Excel:

1. **source_type** column:
   - Data Validation → List
   - Values: MSSQL, Oracle, PostgreSQL, API, Azure

2. **load_type** column:
   - Data Validation → List
   - Values: FULL, INCREMENTAL

3. **enabled** column:
   - Data Validation → List
   - Values: Y, N

4. **api_method** column:
   - Data Validation → List
   - Values: GET, POST

5. **pagination_type** column:
   - Data Validation → List
   - Values: none, offset, cursor, page

## Step 5: Format and Style

1. Format header row:
   - Bold font
   - Background color: Light blue
   - Freeze panes below header row

2. Set column widths appropriately

3. Add a note/comment to the header explaining each column

## Alternative: Use CSV Template

If you prefer to start with CSV, use the template below and convert to Excel:

```csv
job_id,source_type,source_name,schema_name,table_name,load_type,enabled,target_container,target_folder_path,watermark_column,last_watermark,query_filter,api_endpoint,api_method,pagination_type,chunk_size,parallelism
pg_products_full,PostgreSQL,sales_db,public,products,FULL,Y,raw-data,raw,,,,,,,100000,1
mssql_orders_incr,MSSQL,erp_system,dbo,orders,INCREMENTAL,Y,raw-data,raw,updated_date,2024-01-01,status = 'active',,,,50000,1
oracle_customers_full,Oracle,erp_db,sales_schema,customers,FULL,Y,raw-data,raw,,,,,,,100000,1
api_users_full,API,example_api,,users,FULL,Y,raw-data,raw,,,,,/api/v1/users,GET,offset,100000,1
```

Save this CSV and then open in Excel, save as .xlsx format.

## Final Checklist

- [ ] Excel file created: `config/ingestion_config.xlsx`
- [ ] Sheet named "SourceConfig" exists
- [ ] All required columns present
- [ ] At least one row with enabled=Y
- [ ] Data validation rules applied
- [ ] File saved in Excel format (.xlsx)

Once completed, the framework will be ready to run!
