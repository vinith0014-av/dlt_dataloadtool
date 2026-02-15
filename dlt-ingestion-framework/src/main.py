"""
Main entry point for DLT Multi-Source Ingestion Framework.

Production-grade orchestrator for ingesting data from PostgreSQL, Oracle, MSSQL, 
Azure SQL, and REST APIs into Azure ADLS Gen2 as date-partitioned Parquet files.

Features:
    - 100% configuration-driven (no code changes for new sources)
    - Azure Key Vault integration for production credentials
    - Automatic row count extraction and schema evolution monitoring
    - Full and incremental loads with watermark management
    - Comprehensive audit logging to CSV

Usage:
    python run.py
    
    # Enable Azure Key Vault (production)
    set AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
    python run.py
"""
import logging
import sys
from pathlib import Path
from datetime import datetime

from src.core import IngestionOrchestrator
from src.utils import setup_logger


def main():
    """Execute all enabled ingestion jobs from Excel configuration."""
    # Setup logging
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"ingestion_{timestamp}.log"
    
    setup_logger(log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # Create and run orchestrator
        orchestrator = IngestionOrchestrator()
        orchestrator.run_all()
        
        logger.info("Framework execution completed successfully")
        return 0
    
    except KeyboardInterrupt:
        logger.warning("Execution interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
