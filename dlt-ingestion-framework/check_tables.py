"""Check what tables exist in source databases."""
import psycopg2
import pyodbc
import oracledb

def check_postgresql():
    """Check PostgreSQL tables."""
    print("=" * 80)
    print("POSTGRESQL DATABASE: poc_db")
    print("=" * 80)
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="poc_db",
            user="poc_user",
            password="poc_pwd"
        )
        cur = conn.cursor()
        
        # List all tables
        cur.execute("""
            SELECT schemaname, tablename 
            FROM pg_tables 
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, tablename
        """)
        
        tables = cur.fetchall()
        print(f"\n✅ Connected successfully!")
        print(f"\n📋 Found {len(tables)} tables:\n")
        
        for schema, table in tables:
            # Get row count
            cur.execute(f'SELECT COUNT(*) FROM "{schema}"."{table}"')
            count = cur.fetchone()[0]
            print(f"   {schema}.{table:30} - {count:,} rows")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_mssql():
    """Check MSSQL tables."""
    print("\n" + "=" * 80)
    print("MSSQL DATABASE: master")
    print("=" * 80)
    
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=localhost,1433;"
            "DATABASE=master;"
            "UID=sa;"
            "PWD=StrongPassword!123;"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
        )
        conn = pyodbc.connect(conn_str)
        cur = conn.cursor()
        
        # List user tables
        cur.execute("""
            SELECT 
                s.name AS schema_name,
                t.name AS table_name
            FROM sys.tables t
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE t.is_ms_shipped = 0
            ORDER BY s.name, t.name
        """)
        
        tables = cur.fetchall()
        print(f"\n✅ Connected successfully!")
        print(f"\n📋 Found {len(tables)} tables:\n")
        
        for schema, table in tables:
            # Get row count
            cur.execute(f'SELECT COUNT(*) FROM [{schema}].[{table}]')
            count = cur.fetchone()[0]
            print(f"   {schema}.{table:30} - {count:,} rows")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_oracle():
    """Check Oracle tables."""
    print("\n" + "=" * 80)
    print("ORACLE DATABASE: XE")
    print("=" * 80)
    
    try:
        conn = oracledb.connect(
            user="system",
            password="YourPassword123",
            host="localhost",
            port=1521,
            service_name="XE"
        )
        cur = conn.cursor()
        
        # List all tables (excluding system tables)
        cur.execute("""
            SELECT owner, table_name
            FROM all_tables
            WHERE owner NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'DBSNMP', 'APPQOSSYS',
                                'WMSYS', 'XDB', 'MDSYS', 'CTXSYS', 'ORDSYS',
                                'OLAPSYS', 'FLOWS_FILES', 'APEX_030200')
            ORDER BY owner, table_name
        """)
        
        tables = cur.fetchall()
        print(f"\n✅ Connected successfully!")
        print(f"\n📋 Found {len(tables)} tables:\n")
        
        for owner, table in tables:
            # Get row count
            try:
                cur.execute(f'SELECT COUNT(*) FROM {owner}.{table}')
                count = cur.fetchone()[0]
                print(f"   {owner}.{table:30} - {count:,} rows")
            except:
                print(f"   {owner}.{table:30} - (no access)")
        
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Check all databases."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "DATABASE TABLE CHECK" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝\n")
    
    check_postgresql()
    check_mssql()
    check_oracle()
    
    print("\n" + "=" * 80)
    print("💡 CONFIGURATION TIPS:")
    print("=" * 80)
    print("\nIf tables are missing, update config/ingestion_config.xlsx:")
    print("  1. Change 'table_name' to match actual table names")
    print("  2. For Oracle, set 'schema_name' to the owner (e.g., 'HR')")
    print("  3. Set 'enabled' to 'N' for tables you don't want to ingest")
    print("=" * 80)

if __name__ == "__main__":
    main()
