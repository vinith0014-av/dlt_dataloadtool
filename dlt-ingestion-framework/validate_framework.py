"""
Quick validation script to test framework initialization.

Tests:
1. Orchestrator initializes successfully
2. Destination selection works correctly
3. Source modules load properly
4. Secrets are loaded correctly
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("DLT Ingestion Framework - Validation Test")
print("=" * 70)

try:
    # Test 1: Import core modules
    print("\n[1/6] Testing imports...")
    from src.config import ConfigLoader
    from src.core.orchestrator import IngestionOrchestrator
    from src.destinations import ADLSGen2Destination, DatabricksDestination
    from src.sources import PostgreSQLSource, OracleSource
    print("✅ All core modules imported successfully")
    
    # Test 2: Load secrets
    print("\n[2/6] Loading secrets...")
    config_loader = ConfigLoader()
    secrets = config_loader.load_secrets()
    print(f"✅ Secrets loaded from .dlt/secrets.toml")
    
    # Test 3: Check destination type
    print("\n[3/6] Checking destination configuration...")
    dest_type = secrets.get('destination', {}).get('type', 'filesystem')
    print(f"   Destination type: {dest_type}")
    print(f"✅ Destination type detected: {dest_type}")
    
    # Test 4: Initialize orchestrator (no validation to speed up)
    print("\n[4/6] Initializing orchestrator (no validation)...")
    orchestrator = IngestionOrchestrator(validate_on_init=False)
    print(f"✅ Orchestrator initialized")
    print(f"   Pipeline: {orchestrator.pipeline.pipeline_name}")
    print(f"   Destination: {orchestrator.destination.get_destination_type()}")
    print(f"   Sources: {len(orchestrator.sources)} configured")
    
    # Test 5: Check destination instance
    print("\n[5/6] Validating destination instance...")
    if dest_type == 'databricks':
        assert isinstance(orchestrator.destination, DatabricksDestination), \
            f"Expected DatabricksDestination, got {type(orchestrator.destination)}"
        print(f"✅ DatabricksDestination instance created")
        print(f"   Catalog: {orchestrator.destination.get_catalog_name()}")
        print(f"   Schema: {orchestrator.destination.get_schema_name()}")
    else:
        assert isinstance(orchestrator.destination, ADLSGen2Destination), \
            f"Expected ADLSGen2Destination, got {type(orchestrator.destination)}"
        print(f"✅ ADLSGen2Destination instance created")
    
    # Test 6: Check source modules
    print("\n[6/6] Validating source modules...")
    for source_type, source_instance in orchestrator.sources.items():
        print(f"   ✓ {source_type}: {type(source_instance).__name__}")
    print(f"✅ All {len(orchestrator.sources)} source modules loaded")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ VALIDATION SUCCESSFUL - Framework ready for ingestion")
    print("=" * 70)
    print(f"\nConfiguration Summary:")
    print(f"  • Destination: {orchestrator.destination.get_destination_type()}")
    print(f"  • Pipeline: {orchestrator.pipeline.pipeline_name}")
    print(f"  • DLT Destination: {orchestrator.pipeline.destination}")
    print(f"  • Sources: {', '.join(orchestrator.sources.keys())}")
    
    if dest_type == 'databricks':
        print(f"\nDatabricks Configuration:")
        metadata = orchestrator.destination.get_metadata()
        print(f"  • Server: {metadata.get('server_hostname', 'N/A')}")
        print(f"  • Catalog: {metadata.get('catalog', 'N/A')}")
        print(f"  • Schema: {metadata.get('schema', 'N/A')}")
        print(f"  • File Format: {metadata.get('file_format', 'N/A')}")
    
    print("\nNext Steps:")
    print("  1. Configure jobs in config/ingestion_config.xlsx")
    print("  2. Run: python run.py")
    print("  3. Monitor logs in logs/ directory")
    
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ VALIDATION FAILED")
    print(f"\nError: {e}")
    print(f"\nDetails:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
