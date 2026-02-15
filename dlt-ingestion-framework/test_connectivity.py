"""Quick connectivity test for source databases."""
import socket
from datetime import datetime

def test_port(host, port, service_name):
    """Test if a port is open."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:
            return f"✅ {service_name} ({host}:{port}) - REACHABLE"
        else:
            return f"❌ {service_name} ({host}:{port}) - NOT REACHABLE"
    except Exception as e:
        return f"❌ {service_name} ({host}:{port}) - ERROR: {e}"

def main():
    print("=" * 80)
    print(f"DATABASE CONNECTIVITY TEST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test sources from secrets.toml
    tests = [
        ("localhost", 5432, "PostgreSQL"),
        ("localhost", 1521, "Oracle"),
        ("localhost", 1433, "MSSQL"),
    ]
    
    print("\n📡 Testing Database Connectivity:\n")
    for host, port, service in tests:
        print(test_port(host, port, service))
    
    print("\n" + "=" * 80)
    print("NOTE: This only tests if ports are open, not authentication.")
    print("=" * 80)

if __name__ == "__main__":
    main()
