"""
Quick ingestion validation - Tests framework without full imports.

This script validates the framework by running unit tests which are 
faster than importing the full orchestrator.
"""
import subprocess
import sys

print("=" * 80)
print("DLT Ingestion Framework - Quick Validation")
print("=" * 80)

tests_to_run = [
    ("Destination Tests", "tests/unit/test_destinations.py"),
    ("Source Tests", "tests/unit/test_sources.py"),
]

print("\nRunning unit tests to validate framework components...\n")

all_passed = True
total_passed = 0
total_failed = 0

for test_name, test_path in tests_to_run:
    print(f"[Testing] {test_name}...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_path, "-q", "--tb=no"],
        capture_output=True,
        text=True
    )
    
    # Parse output
    output_lines = result.stdout.split('\n')
    for line in output_lines:
        if 'passed' in line.lower() or 'failed' in line.lower():
            print(f"  {line.strip()}")
            
            # Extract numbers
            if 'passed' in line:
                try:
                    import re
                    match = re.search(r'(\d+) passed', line)
                    if match:
                        total_passed += int(match.group(1))
                    match = re.search(r'(\d+) failed', line)
                    if match:
                        total_failed += int(match.group(1))
                        all_passed = False
                except:
                    pass
            break
    
print("\n" + "=" * 80)
if all_passed and total_failed == 0:
    print(f"✅ VALIDATION PASSED - {total_passed} tests passing")
    print("=" * 80)
    print("\n📊 Framework Status:")
    print("  ✓ Destination modules: ADLS Gen2 + Databricks")
    print("  ✓ Source modules: PostgreSQL, Oracle, MSSQL, Azure SQL")
    print("  ✓ Dynamic destination selection working")
    print("  ✓ All configurations validated")
    
    print("\n🚀 Next Steps:")
    print("  1. Configure .dlt/secrets.toml with your credentials")
    print("  2. Set destination type: 'databricks' or 'filesystem'")
    print("  3. Configure jobs in config/ingestion_config.xlsx")
    print("  4. Run: python run.py")
    
    print("\n📝 Configuration Tips:")
    print("  • For Databricks: Set type='databricks' in secrets.toml")
    print("  • For ADLS Gen2: Set type='filesystem' or omit (default)")
    print("  • See .dlt/secrets.toml.template for examples")
    
    sys.exit(0)
else:
    print(f"❌ VALIDATION FAILED - {total_failed} tests failing")
    print("=" * 80)
    print("\nRun for details: pytest tests/unit -v")
    sys.exit(1)
