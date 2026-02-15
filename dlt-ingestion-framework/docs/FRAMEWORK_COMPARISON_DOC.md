# DLT Multi-Source Ingestion Framework - Technical Documentation

> **Framework Version**: v2.1 (Production-Grade)
> **Last Updated**: February 9, 2026
> **Author**: [Your Name / Team Name]

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Overview](#2-architecture-overview)
3. [Folder Structure](#3-folder-structure)
4. [Core Modules](#4-core-modules)
5. [Source Connectors](#5-source-connectors)
6. [Destination Handler](#6-destination-handler)
7. [Configuration Management](#7-configuration-management)
8. [Secret Management](#8-secret-management)
9. [Error Handling & Retry Logic](#9-error-handling--retry-logic)
10. [Monitoring & Metrics](#10-monitoring--metrics)
11. [Logging Strategy](#11-logging-strategy)
12. [Data Quality & Validation](#12-data-quality--validation)
13. [Performance Features](#13-performance-features)
14. [Execution Flow](#14-execution-flow)
15. [Dependencies](#15-dependencies)
16. [Deployment Options](#16-deployment-options)
17. [Comparison Matrix Template](#17-comparison-matrix-template)

---

## 1. Executive Summary

### What is this framework?
A **production-grade, modular DLT framework** using **dlthub** for ingesting data from multiple sources (PostgreSQL, Oracle, MSSQL, Azure SQL, REST APIs) into **Azure ADLS Gen2** as date-partitioned Parquet files.

### Key Characteristics

| Aspect | Implementation |
|--------|----------------|
| **DLT Library** | dlthub v1.4+ |
| **Configuration** | 100% Excel-driven (no code changes for new sources) |
| **Destination** | Azure ADLS Gen2 with date partitioning |
| **File Format** | Parquet |
| **Architecture** | Modular with separate source/destination modules |
| **Version** | v2.1 (Production) |

### Production Features
- ✅ Pre-flight validation (config + secrets)
- ✅ Exponential backoff retry logic
- ✅ Circuit breaker pattern
- ✅ Health scoring (0-100)
- ✅ Per-source logging
- ✅ Metrics collection with JSON export
- ✅ Multi-secret source support (Databricks, Key Vault, Env Vars, TOML)

---

## 2. Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DLT Ingestion Framework v2.1                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │  ConfigLoader   │    │   Validators    │    │ MetricsCollector│         │
│  │  (Excel + TOML) │    │ (Config/Secrets)│    │ (Health Scoring)│         │
│  └────────┬────────┘    └────────┬────────┘    └────────┬────────┘         │
│           │                      │                      │                   │
│           └──────────────────────┼──────────────────────┘                   │
│                                  ▼                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    IngestionOrchestrator (v2.1)                       │  │
│  │  • Single DLT pipeline (reused)     • Pre-flight validation          │  │
│  │  • Retry with exponential backoff   • Circuit breakers per source    │  │
│  │  • Metrics collection               • Health scoring                  │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│  ┌──────────────────────────────────┼───────────────────────────────────┐  │
│  │                         Source Modules                                │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         │  │
│  │  │ PostgreSQL │ │   Oracle   │ │   MSSQL    │ │  REST API  │         │  │
│  │  │   Source   │ │   Source   │ │   Source   │ │   Source   │         │  │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘         │  │
│  └──────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    ADLS Gen2 Destination                              │  │
│  │          az://raw-data/{table}/{YYYY}/{MM}/{DD}/*.parquet             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern | Implementation | Purpose |
|---------|---------------|---------|
| **Modular Architecture** | Separate modules for each source type | Easy extension, single responsibility |
| **Factory Pattern** | Source instantiation based on type | Flexible source creation |
| **Circuit Breaker** | Per-source circuit breakers | Prevent cascade failures |
| **Exponential Backoff** | RetryHandler class | Graceful retry with increasing delays |
| **Strategy Pattern** | Different connection string builders | Source-specific logic |
| **Observer Pattern** | Metrics hooks | Extensible monitoring |

---

## 3. Folder Structure

```
dlt-ingestion-framework/
├── run.py                              # Entry point (10 lines)
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Container deployment
├── run_framework.bat                   # Windows launcher
│
├── src/                                # SOURCE CODE
│   ├── main.py                         # Main entry point (60 lines)
│   ├── __init__.py
│   │
│   ├── core/                           # CORE ORCHESTRATION
│   │   ├── orchestrator.py             # Main orchestrator (706 lines, v2.1)
│   │   ├── validators.py               # Pre-flight validators (375 lines)
│   │   ├── retry_handler.py            # Retry + Circuit Breaker (326 lines)
│   │   ├── metrics.py                  # Metrics collection (329 lines)
│   │   └── __init__.py
│   │
│   ├── sources/                        # SOURCE CONNECTORS
│   │   ├── base.py                     # Abstract base source
│   │   ├── postgresql.py               # PostgreSQL connector
│   │   ├── oracle.py                   # Oracle connector
│   │   ├── mssql.py                    # SQL Server connector
│   │   ├── azure_sql.py                # Azure SQL connector
│   │   ├── rest_api.py                 # REST API connector
│   │   └── __init__.py
│   │
│   ├── destinations/                   # DESTINATION HANDLERS
│   │   ├── base.py                     # Abstract base destination
│   │   ├── adls_gen2.py                # ADLS Gen2 handler
│   │   └── __init__.py
│   │
│   ├── config/                         # CONFIGURATION
│   │   ├── loader.py                   # Config + secrets loading (247 lines)
│   │   └── __init__.py
│   │
│   ├── auth/                           # AUTHENTICATION
│   │   ├── keyvault_manager.py         # Azure Key Vault integration
│   │   └── __init__.py
│   │
│   ├── metadata/                       # AUDIT TRAIL
│   │   ├── tracker.py                  # CSV audit logging (83 lines)
│   │   └── __init__.py
│   │
│   └── utils/                          # UTILITIES
│       ├── logger.py                   # Logging setup
│       ├── log_manager.py              # Per-source logging (210 lines)
│       └── __init__.py
│
├── config/                             # CONFIGURATION FILES
│   ├── ingestion_config.xlsx           # Job definitions (ONLY USER INTERFACE)
│   └── config_schema.json              # Validation schema
│
├── .dlt/                               # DLT NATIVE
│   └── secrets.toml                    # Credentials (local dev)
│
├── logs/                               # AUTO-GENERATED LOGS
│   └── errors/                         # Error-only logs
│
├── metadata/                           # AUDIT FILES
│   └── audit_YYYYMMDD.csv              # Daily execution records
│
└── docs/                               # DOCUMENTATION
    ├── QUICKSTART.md
    ├── SECRET_MANAGEMENT_GUIDE.md
    ├── DATABRICKS_DEPLOYMENT_GUIDE.md
    └── FEATURES.md
```

### File Count Summary

| Category | Files | Lines of Code (approx) |
|----------|-------|------------------------|
| Core Modules | 4 | ~1,800 |
| Source Modules | 6 | ~600 |
| Destination Modules | 2 | ~250 |
| Config/Utils | 5 | ~700 |
| **Total Python** | **17** | **~3,350** |

---

## 4. Core Modules

### 4.1 IngestionOrchestrator (`src/core/orchestrator.py`)

**Purpose**: Main coordinator for all data ingestion jobs.

**Key Features**:
- Single DLT pipeline instance (reused for all jobs)
- Pre-flight validation before execution
- Retry handling with circuit breakers
- Metrics collection and health scoring
- Per-source logging

**Key Methods**:
```python
class IngestionOrchestrator:
    def __init__(self, validate_on_init: bool = True)
    def run_all(self, parallel: bool = False) -> Dict
    def execute_job(self, job: Dict) -> bool
    def _execute_database_job(self, job: Dict) -> Tuple[bool, int, float]
    def _execute_api_job(self, job: Dict) -> Tuple[bool, int, float]
```

**DLT Pipeline Configuration**:
```python
self.pipeline = dlt.pipeline(
    pipeline_name="multi_source_ingestion",
    destination="filesystem",  # ADLS Gen2
    dataset_name="raw_data"
)
```

### 4.2 ConfigValidator (`src/core/validators.py`)

**Purpose**: Pre-flight validation of job configuration.

**Validates**:
- Required columns present
- Valid source_type values
- Valid load_type values
- Incremental requires watermark_column
- Oracle requires schema_name
- chunk_size range (1,000 - 10,000,000)

### 4.3 RetryHandler (`src/core/retry_handler.py`)

**Purpose**: Fault tolerance with exponential backoff.

**Features**:
- Configurable max retries
- Exponential backoff with jitter
- Circuit breaker integration
- Per-source retry configuration

**Default Configuration**:
```python
# Database sources
RetryConfig(max_retries=3, initial_delay=2.0, max_delay=30.0)

# API sources
RetryConfig(max_retries=5, initial_delay=1.0, max_delay=60.0)
```

### 4.4 MetricsCollector (`src/core/metrics.py`)

**Purpose**: Performance monitoring and health scoring.

**Metrics Tracked**:
- Rows processed
- Duration (seconds)
- Throughput (rows/sec)
- Retry count
- Error count
- Schema version

**Health Score Calculation**:
```python
def get_health_score(self) -> float:
    # Based on: success rate, avg throughput, error count
    # Returns: 0-100 score
```

**JSON Export**:
```python
metrics.export_json("metadata/metrics_20260209.json")
```

---

## 5. Source Connectors

### 5.1 Supported Sources

| Source | Module | Driver | Connection String Pattern |
|--------|--------|--------|---------------------------|
| PostgreSQL | `postgresql.py` | psycopg2 | `postgresql+psycopg2://user:pass@host:port/db` |
| Oracle | `oracle.py` | oracledb | `oracle+oracledb://user:pass@host:port/sid` |
| MSSQL | `mssql.py` | pyodbc | ODBC connection string |
| Azure SQL | `azure_sql.py` | pyodbc | ODBC with Encrypt=yes |
| REST API | `rest_api.py` | requests | Uses `rest_api_source()` |

### 5.2 Base Source Interface

```python
class BaseSource(ABC):
    @abstractmethod
    def get_source_type(self) -> str
    
    @abstractmethod
    def build_connection_string(self, source_name: str) -> str
    
    def supports_schema(self) -> bool
    def estimate_table_size(self, conn_str, table_name) -> Tuple[int, int]
    def get_metadata(self, source_name: str) -> Dict
```

### 5.3 PostgreSQL Source Example

```python
class PostgreSQLSource(BaseSource):
    def build_connection_string(self, source_name: str) -> str:
        pg = self.secrets['sources'][source_name]
        return f"postgresql+psycopg2://{pg['username']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}"
```

### 5.4 REST API Source (Using DLT Native)

```python
# Uses dlthub's rest_api_source() for automatic:
# - Pagination handling
# - Retry logic
# - State management

from dlt.sources.rest_api import rest_api_source

rest_config = {
    "client": {"base_url": base_url},
    "resources": [{
        "name": table_name,
        "endpoint": {"path": endpoint_path}
    }]
}
api_source = rest_api_source(rest_config)
```

---

## 6. Destination Handler

### 6.1 ADLS Gen2 Destination

**Module**: `src/destinations/adls_gen2.py`

**Features**:
- Date-partitioned Parquet output
- Azure Storage Account authentication
- Automatic directory creation

**Partition Layout**:
```
az://raw-data/{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.parquet
```

**Example Output Path**:
```
az://raw-data/orders/2026/02/09/1770622036.4548528.a7edb2b378.parquet
```

### 6.2 DLT Destination Configuration

```python
config = {
    'destination': 'filesystem',
    'bucket_url': 'az://raw-data',
    'layout': '{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}',
    'credentials': {
        'azure_storage_account_name': 'dltpoctest',
        'azure_storage_account_key': '...'
    }
}
```

### 6.3 Destination Validation

```python
def validate_connection(self) -> bool:
    # Uses azure-storage-blob to verify connectivity
    # Lists containers to confirm access
```

---

## 7. Configuration Management

### 7.1 Excel Configuration (`ingestion_config.xlsx`)

**Sheet**: `SourceConfig`

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| source_type | string | ✅ | postgresql, oracle, mssql, azure_sql, api |
| source_name | string | ✅ | Reference to secrets.toml source |
| table_name | string | ✅ | Table to ingest |
| load_type | string | ✅ | FULL or INCREMENTAL |
| enabled | string | ✅ | Y or N |
| schema_name | string | Oracle only | Database schema |
| watermark_column | string | INCREMENTAL only | Column for incremental tracking |
| last_watermark | string | Optional | Last watermark value |
| chunk_size | integer | Optional | Rows per chunk (default: 100,000) |
| api_endpoint | string | API only | REST endpoint path |

### 7.2 Configuration Schema (`config_schema.json`)

```json
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "version": "2.1",
    "required_columns": ["source_type", "source_name", "table_name", "load_type", "enabled"],
    "valid_values": {
        "source_type": ["postgresql", "oracle", "mssql", "azure_sql", "api"],
        "load_type": ["FULL", "INCREMENTAL"]
    },
    "validation_rules": {
        "chunk_size": {"min": 1000, "max": 10000000, "default": 100000}
    }
}
```

---

## 8. Secret Management

### 8.1 Secret Sources (Priority Order)

| Priority | Source | Auto-Detection |
|----------|--------|----------------|
| 1 | Databricks Secrets | Running in Databricks |
| 2 | Azure Key Vault | `AZURE_KEY_VAULT_URL` env var |
| 3 | Environment Variables | `DLT_*` vars exist |
| 4 | .dlt/secrets.toml | Always (fallback) |

### 8.2 Secrets Structure (`secrets.toml`)

```toml
# Database Sources
[sources.postgresql]
host = "localhost"
port = 5432
database = "poc_db"
username = "poc_user"
password = "poc_pwd"

# API Sources
[sources.coingecko]
base_url = "https://api.coingecko.com/api/v3"
api_key = "your_api_key"

# Destination
[destination.filesystem]
bucket_url = "az://raw-data"
layout = "{table_name}/{YYYY}/{MM}/{DD}/{load_id}.{file_id}.{ext}"

[destination.filesystem.credentials]
azure_storage_account_name = "dltpoctest"
azure_storage_account_key = "..."
```

### 8.3 Databricks Secrets Format

```bash
# Scope: dlt-framework
# Key format: {source}-{field}

postgresql-host
postgresql-port
postgresql-database
postgresql-username
postgresql-password
adls-storage-account
adls-storage-key
```

---

## 9. Error Handling & Retry Logic

### 9.1 Retry Configuration

```python
@dataclass
class RetryConfig:
    max_retries: int = 3
    initial_delay: float = 1.0        # seconds
    max_delay: float = 60.0           # seconds
    exponential_base: float = 2.0
    jitter: float = 0.1               # randomness factor
```

### 9.2 Circuit Breaker

```python
@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5   # failures before opening
    success_threshold: int = 2   # successes to close
    timeout: float = 30.0        # seconds before retry
```

**States**:
- `CLOSED`: Normal operation
- `OPEN`: Rejecting calls (source failing)
- `HALF_OPEN`: Testing recovery

### 9.3 Retry Flow

```
[Job Execution] 
    → Success → Record metrics → Next job
    → Failure → Check circuit breaker
        → OPEN → Skip with warning
        → CLOSED/HALF_OPEN → Retry with backoff
            → Retry 1: 2.0s delay
            → Retry 2: 4.0s delay
            → Retry 3: 8.0s delay
            → Max retries → Record failure → Next job
```

---

## 10. Monitoring & Metrics

### 10.1 Metrics Collected

| Metric | Type | Description |
|--------|------|-------------|
| rows_processed | Counter | Total rows ingested |
| duration_seconds | Timer | Execution time |
| rows_per_second | Gauge | Throughput |
| retry_count | Counter | Retry attempts |
| error_count | Counter | Failed jobs |
| schema_version | Gauge | Schema evolution tracking |

### 10.2 Health Score

```python
def get_health_score(self) -> float:
    """
    Score: 0-100
    Based on:
    - Success rate (weight: 50%)
    - Throughput (weight: 30%)
    - Error rate (weight: 20%)
    """
```

### 10.3 Metrics Export

```json
// metadata/metrics_20260209_125653.json
{
    "pipeline_name": "dlt_ingestion",
    "execution_time": "2026-02-09T12:56:53",
    "summary": {
        "total_jobs": 5,
        "successful": 4,
        "failed": 1,
        "total_rows": 19948,
        "total_duration_seconds": 38.29,
        "avg_throughput": 521,
        "health_score": 100.0
    },
    "jobs": [...]
}
```

---

## 11. Logging Strategy

### 11.1 Log Files Structure

```
logs/
├── main_orchestrator_20260209_143022.log    # Main log
├── source_sales_db_20260209_143022.log      # Per-source
├── destination_adls_20260209_143022.log     # Destination
└── errors/
    └── sales_db_errors_20260209.log         # Error-only
```

### 11.2 Log Format

```
2026-02-09 12:57:31,771 | INFO     | [ORCHESTRATOR v2.1] Production-grade initialization
2026-02-09 12:57:31,771 | INFO     |   DLT Pipeline: multi_source_ingestion
2026-02-09 12:57:31,771 | INFO     |   Destination: filesystem
2026-02-09 12:57:31,771 | ERROR    | [FAILED] Job failed: oracle.orders - Connection refused
```

### 11.3 Log Manager Features

- Automatic source-specific log files
- Separate error logs for quick debugging
- Consistent timestamp format
- UTF-8 encoding support

---

## 12. Data Quality & Validation

### 12.1 Pre-flight Validation

**ConfigValidator** checks:
- Required columns present
- Valid enum values (source_type, load_type)
- Conditional requirements (INCREMENTAL → watermark_column)
- SQL injection prevention (table_name pattern)
- Numeric range validation (chunk_size)

### 12.2 SecretsValidator

Checks:
- Source exists in secrets
- Required fields present (host, port, database, username, password)
- Destination credentials exist

### 12.3 DataQualityValidator

Checks:
- Row count > 0 (optional)
- Schema stability (version tracking)

---

## 13. Performance Features

### 13.1 Dynamic Chunk Sizing

```python
# Based on estimated table size
if estimated_rows < 100,000:      chunk_size = 50,000
elif estimated_rows < 1,000,000:  chunk_size = 100,000
elif estimated_rows < 10,000,000: chunk_size = 250,000
elif estimated_rows < 50,000,000: chunk_size = 500,000
else:                             chunk_size = 1,000,000
```

### 13.2 PyArrow Backend

```python
resource = sql_table(
    credentials=conn_str,
    table=table_name,
    backend="pyarrow",          # Columnar processing
    chunk_size=100000,
    detect_precision_hints=True,
    defer_table_reflect=True
)
```

### 13.3 Performance Metrics (Tested)

| Metric | Value |
|--------|-------|
| Rows Processed | 19,948 |
| Total Duration | 38.29s |
| Throughput | 521 rows/sec |
| Jobs Successful | 4/5 (80%) |
| Health Score | 100/100 |

---

## 14. Execution Flow

```mermaid
flowchart TD
    A[Start] --> B[Initialize Orchestrator]
    B --> C[Load Excel Config]
    C --> D[Load Secrets]
    D --> E[Validate Destination]
    E --> F{Pre-flight Validation}
    F -->|Pass| G[For Each Job]
    F -->|Fail| Z[Exit with Error]
    G --> H{Check Circuit Breaker}
    H -->|OPEN| I[Skip Job]
    H -->|CLOSED| J[Execute with Retry]
    J --> K{Success?}
    K -->|Yes| L[Record Metrics]
    K -->|No| M{Retries Left?}
    M -->|Yes| N[Exponential Backoff]
    N --> J
    M -->|No| O[Record Failure]
    L --> P{More Jobs?}
    O --> P
    I --> P
    P -->|Yes| G
    P -->|No| Q[Generate Summary]
    Q --> R[Export Metrics JSON]
    R --> S[End]
```

---

## 15. Dependencies

### 15.1 Core Dependencies

```text
# DLT Framework
dlt[filesystem,sql_database]>=1.4.0

# Configuration
pandas>=2.0.0
openpyxl>=3.1.0
toml>=0.10.2

# Database Drivers
psycopg2-binary>=2.9.0    # PostgreSQL
oracledb>=1.3.0           # Oracle
pyodbc>=5.0.0             # SQL Server

# Azure
azure-storage-blob>=12.19.0
azure-identity>=1.15.0
adlfs>=2023.4.0
azure-keyvault-secrets>=4.7.0  # Optional

# Data Processing
pyarrow>=14.0.0
sqlalchemy>=1.4.0
```

### 15.2 Python Version

- **Tested**: Python 3.13.12
- **Minimum**: Python 3.9+

---

## 16. Deployment Options

### 16.1 Local Development

```bash
cd dlt-ingestion-framework
python -m src.main
```

### 16.2 Databricks Workflow

- Upload to DBFS
- Create Databricks Job
- Configure cluster with ODBC Driver 17 init script
- Use Databricks Secrets (scope: `dlt-framework`)

### 16.3 Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "-m", "src.main"]
```

---

## 17. Comparison Matrix Template

Use this table to compare with your colleague's implementation:

| Aspect | **Your Implementation** | **Colleague's Implementation** |
|--------|------------------------|-------------------------------|
| **Framework Version** | v2.1 | |
| **DLT Library Version** | dlthub v1.4+ | |
| **Configuration Source** | Excel (.xlsx) | |
| **Configuration Schema** | JSON Schema v2.1 | |
| **Secrets Storage** | TOML / Key Vault / Databricks / Env | |
| **Destination** | ADLS Gen2 (filesystem) | |
| **File Format** | Parquet | |
| **Partition Strategy** | Date-based (YYYY/MM/DD) | |
| | | |
| **Sources Supported** | | |
| - PostgreSQL | ✅ | |
| - Oracle | ✅ | |
| - MSSQL | ✅ | |
| - Azure SQL | ✅ | |
| - REST APIs | ✅ | |
| - MySQL | ❌ | |
| - MongoDB | ❌ | |
| | | |
| **Error Handling** | | |
| - Retry Logic | ✅ Exponential Backoff | |
| - Circuit Breaker | ✅ Per-source | |
| - Pre-flight Validation | ✅ | |
| - Graceful Fallback | ✅ | |
| | | |
| **Monitoring** | | |
| - Metrics Collection | ✅ | |
| - Health Scoring | ✅ (0-100) | |
| - JSON Export | ✅ | |
| - Per-source Logs | ✅ | |
| - Error-only Logs | ✅ | |
| - Audit CSV | ✅ | |
| | | |
| **Performance** | | |
| - Dynamic Chunking | ✅ | |
| - Parallel Execution | ⚠️ Sequential only | |
| - PyArrow Backend | ✅ | |
| - Tested Throughput | 521 rows/sec | |
| | | |
| **Architecture** | | |
| - Modular Sources | ✅ Separate files | |
| - Base Class Pattern | ✅ | |
| - Single Pipeline Reuse | ✅ | |
| - Lines of Code | ~3,350 | |
| - Python Files | 17 | |
| | | |
| **DLT Features Used** | | |
| - sql_table() | ✅ | |
| - rest_api_source() | ✅ | |
| - dlt.sources.incremental() | ✅ | |
| - ConnectionStringCredentials | ✅ | |
| - pipeline.last_trace | ✅ | |
| - Schema Evolution | ✅ Monitoring | |
| | | |
| **Deployment** | | |
| - Local | ✅ | |
| - Databricks | ✅ | |
| - Docker | ✅ | |
| - Azure DevOps | ✅ Documentation | |

---

## Document Information

| Field | Value |
|-------|-------|
| Document Created | February 9, 2026 |
| Framework Version | v2.1 |
| Author | [Your Name] |
| Last Test Run | 5 jobs, 4 successful, 19,948 rows |

---

*This document is intended for technical comparison purposes. Copy the Comparison Matrix Template above and fill in your colleague's implementation details for a side-by-side analysis.*
