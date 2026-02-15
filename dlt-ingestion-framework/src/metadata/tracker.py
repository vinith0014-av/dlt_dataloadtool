"""
Metadata Tracker - Records job execution audit trail to CSV files.
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd

logger = logging.getLogger(__name__)


class MetadataTracker:
    """Tracks job execution metadata and writes audit trail to daily CSV files.
    
    Features:
        - Daily CSV files (one per day): metadata/audit_YYYYMMDD.csv
        - Records job success/failure with timestamps
        - Captures row counts, duration, partition paths, and errors
        - Append-only writes (preserves historical data)
    """
    
    def __init__(self, metadata_dir: Path = None):
        """Initialize metadata tracker.
        
        Args:
            metadata_dir: Directory for metadata files (default: ./metadata)
        """
        root_dir = Path(__file__).parent.parent.parent
        self.metadata_dir = metadata_dir or root_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
        
        # Daily audit file
        today = datetime.now().strftime('%Y%m%d')
        self.audit_file = self.metadata_dir / f"audit_{today}.csv"
        
        logger.debug(f"Metadata tracker initialized: {self.audit_file}")
    
    def record_job(
        self, 
        job_name: str, 
        status: str, 
        rows: int, 
        duration: float, 
        partition_path: Optional[str] = None, 
        error_message: Optional[str] = None
    ):
        """Record job execution to audit CSV.
        
        Args:
            job_name: Job identifier (e.g., 'postgres_source.orders')
            status: Execution status ('SUCCESS' or 'FAILED')
            rows: Number of rows processed
            duration: Execution time in seconds
            partition_path: ADLS partition path (e.g., 'postgres_source/orders/2026/01/29')
            error_message: Error message if status is FAILED
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'job_name': job_name,
            'status': status,
            'rows_processed': rows,
            'duration_seconds': round(duration, 2),
            'partition_path': partition_path or '',
            'error_message': error_message or ''
        }
        
        df = pd.DataFrame([record])
        
        try:
            if self.audit_file.exists():
                # Append to existing file
                df.to_csv(self.audit_file, mode='a', header=False, index=False)
            else:
                # Create new file with header
                df.to_csv(self.audit_file, mode='w', header=True, index=False)
            
            logger.debug(f"Recorded job: {job_name} -> {status}")
        
        except Exception as e:
            logger.error(f"Failed to write audit record: {e}")
            # Don't raise - metadata failure shouldn't stop pipeline
