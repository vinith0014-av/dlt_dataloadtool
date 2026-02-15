"""
Simple launcher for DLT Ingestion Framework.

Usage:
    python run.py
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run main
from dlt_ingestion_framework.src.main import main

if __name__ == "__main__":
    sys.exit(main())
