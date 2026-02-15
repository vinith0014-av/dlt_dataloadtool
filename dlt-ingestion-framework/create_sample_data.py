"""Create sample tables in source databases for testing."""
import psycopg2
import pyodbc
import oracledb
from datetime import datetime, timedelta
import random

def create_postgresql_tables():
    """Create sample tables in PostgreSQL."""
    print("=" * 80)
    print("CREATING POSTGRESQL TABLES")
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
        
        # Create customers table
        print("\n1. Creating 'customers' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                customer_id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                country VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample data
        print("   Inserting 10 sample customers...")
        for i in range(1, 11):
            cur.execute("""
                INSERT INTO customers (name, email, country, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                f"Customer{i}",
                f"customer{i}@example.com",
                random.choice(['USA', 'UK', 'Canada', 'Australia']),
                datetime.now() - timedelta(days=random.randint(1, 365))
            ))
        
        # Create orders table
        print("\n2. Creating 'orders' table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id SERIAL PRIMARY KEY,
                customer_id INTEGER,
                product_name VARCHAR(100),
                quantity INTEGER,
                amount DECIMAL(10,2),
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample orders
        print("   Inserting 20 sample orders...")
        products = ['Laptop', 'Monitor', 'Keyboard', 'Mouse', 'Headphones']
        for i in range(1, 21):
            cur.execute("""
                INSERT INTO orders (customer_id, product_name, quantity, amount, order_date, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                random.randint(1, 10),
                random.choice(products),
                random.randint(1, 5),
                round(random.uniform(10, 1000), 2),
                datetime.now() - timedelta(days=random.randint(1, 30)),
                datetime.now() - timedelta(days=random.randint(0, 5))
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ PostgreSQL tables created successfully!")
        print(f"   - customers: 10 rows")
        print(f"   - orders: 20 rows")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL Error: {e}")
        return False

def create_mssql_tables():
    """Create sample tables in MSSQL."""
    print("\n" + "=" * 80)
    print("CREATING MSSQL TABLES")
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
        
        # Create products table
        print("\n1. Creating 'products' table...")
        cur.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='products' AND xtype='U')
            CREATE TABLE products (
                product_id INT IDENTITY(1,1) PRIMARY KEY,
                product_name VARCHAR(100),
                category VARCHAR(50),
                price DECIMAL(10,2),
                stock_quantity INT,
                created_at DATETIME DEFAULT GETDATE()
            )
        """)
        conn.commit()
        
        # Insert sample data
        print("   Inserting 15 sample products...")
        categories = ['Electronics', 'Furniture', 'Clothing', 'Books']
        for i in range(1, 16):
            cur.execute("""
                INSERT INTO products (product_name, category, price, stock_quantity)
                VALUES (?, ?, ?, ?)
            """, (
                f"Product{i}",
                random.choice(categories),
                round(random.uniform(10, 500), 2),
                random.randint(10, 1000)
            ))
        conn.commit()
        
        cur.close()
        conn.close()
        
        print("✅ MSSQL tables created successfully!")
        print(f"   - products: 15 rows")
        return True
        
    except Exception as e:
        print(f"❌ MSSQL Error: {e}")
        print(f"   Make sure SQL Server is running and authentication is correct")
        return False

def create_oracle_tables():
    """Create sample tables in Oracle."""
    print("\n" + "=" * 80)
    print("CREATING ORACLE TABLES")
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
        
        # Create EMPLOYEES table in HR schema
        print("\n1. Creating 'HR.EMPLOYEES' table...")
        
        # Create HR schema if it doesn't exist
        try:
            cur.execute("CREATE USER HR IDENTIFIED BY hr_password DEFAULT TABLESPACE USERS")
            cur.execute("GRANT CONNECT, RESOURCE TO HR")
            print("   Created HR schema")
        except:
            print("   HR schema already exists")
        
        # Create table
        cur.execute("""
            BEGIN
                EXECUTE IMMEDIATE 'DROP TABLE HR.EMPLOYEES';
                EXCEPTION WHEN OTHERS THEN NULL;
            END;
        """)
        
        cur.execute("""
            CREATE TABLE HR.EMPLOYEES (
                EMPLOYEE_ID NUMBER PRIMARY KEY,
                FIRST_NAME VARCHAR2(50),
                LAST_NAME VARCHAR2(50),
                EMAIL VARCHAR2(100),
                DEPARTMENT VARCHAR2(50),
                SALARY NUMBER(10,2),
                HIRE_DATE DATE
            )
        """)
        
        # Insert sample data
        print("   Inserting 12 sample employees...")
        departments = ['Engineering', 'Sales', 'Marketing', 'HR']
        for i in range(1, 13):
            cur.execute("""
                INSERT INTO HR.EMPLOYEES 
                (EMPLOYEE_ID, FIRST_NAME, LAST_NAME, EMAIL, DEPARTMENT, SALARY, HIRE_DATE)
                VALUES (:1, :2, :3, :4, :5, :6, :7)
            """, (
                i,
                f"FirstName{i}",
                f"LastName{i}",
                f"emp{i}@company.com",
                random.choice(departments),
                round(random.uniform(50000, 150000), 2),
                datetime.now() - timedelta(days=random.randint(30, 1825))
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ Oracle tables created successfully!")
        print(f"   - HR.EMPLOYEES: 12 rows")
        return True
        
    except Exception as e:
        print(f"❌ Oracle Error: {e}")
        print(f"   Make sure Oracle is running and credentials are correct")
        return False

def main():
    """Create all sample tables."""
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "DATABASE SAMPLE DATA SETUP" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝\n")
    
    results = []
    
    # Create PostgreSQL tables
    results.append(("PostgreSQL", create_postgresql_tables()))
    
    # Create MSSQL tables
    results.append(("MSSQL", create_mssql_tables()))
    
    # Create Oracle tables
    results.append(("Oracle", create_oracle_tables()))
    
    # Summary
    print("\n" + "=" * 80)
    print("SETUP SUMMARY")
    print("=" * 80)
    for db, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{db:15} {status}")
    
    success_count = sum(1 for _, success in results if success)
    print(f"\nTotal: {success_count}/{len(results)} databases configured successfully")
    
    if success_count > 0:
        print("\n" + "=" * 80)
        print("READY TO RUN INGESTION!")
        print("=" * 80)
        print("\nRun the framework:")
        print("  .venv\\Scripts\\python.exe run.py")
        print("\nExpected results:")
        print("  - PostgreSQL: 10 customers + 20 orders = 30 rows total")
        print("  - MSSQL: 15 products")
        print("  - Oracle: 12 employees")
        print("  - API: CoinGecko crypto prices (depends on API availability)")
        print("=" * 80)

if __name__ == "__main__":
    main()
