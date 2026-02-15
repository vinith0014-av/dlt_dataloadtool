"""
Entry point for DLT Ingestion Framework.
Run this file to execute all enabled jobs.
"""
import sys
from pathlib import Path

# Add src to Python path
# This ensures the 'src' directory is available for imports
# by adding it to the beginning of sys.path
src_path = Path(__file__).parent / "src"  # Get the absolute path to the src directory
sys.path.insert(0, str(src_path))  # Insert at position 0 for highest priority

# Now run the main module
if __name__ == "__main__":
    from main import main
    main()
