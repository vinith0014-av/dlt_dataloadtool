"""
Log Manager - Per-source and error-only log file routing.

Automatically creates separate log files for:
- Main orchestrator
- Each source instance (e.g., sales_db_postgresql.log)
- Destination (ADLS Gen2)
- Error-only logs for quick debugging
"""
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class SourceLogFilter(logging.Filter):
    """Filter logs by source name."""
    
    def __init__(self, source_name: str):
        super().__init__()
        self.source_name = source_name
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Only pass logs that match this source."""
        return getattr(record, 'source_name', None) == self.source_name


class ErrorOnlyFilter(logging.Filter):
    """Filter to only capture ERROR and WARNING logs."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Only pass ERROR and WARNING level logs."""
        return record.levelno >= logging.WARNING


class LogManager:
    """Manages per-source and error-only log files.
    
    Features:
    - Automatic source-specific log files
    - Separate error logs for quick debugging
    - Destination-specific logging
    - Consistent timestamp format
    - Automatic directory creation
    
    Log Structure:
        logs/
        ├── main_orchestrator_20260209_143022.log
        ├── source_sales_db_20260209_143022.log
        ├── source_erp_system_20260209_143022.log
        ├── destination_adls_20260209_143022.log
        └── errors/
            ├── sales_db_errors_20260209.log
            └── erp_system_errors_20260209.log
    """
    
    def __init__(self, base_log_dir: Path = None):
        """Initialize log manager.
        
        Args:
            base_log_dir: Base directory for logs (default: ./logs)
        """
        self.base_log_dir = base_log_dir or Path("logs")
        self.error_log_dir = self.base_log_dir / "errors"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.date = datetime.now().strftime("%Y%m%d")
        
        # Create directories
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        self.error_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Track created handlers
        self.handlers: Dict[str, logging.Handler] = {}
    
    def setup_main_logger(self, logger_name: str = None) -> logging.Logger:
        """Set up main orchestrator logger.
        
        Args:
            logger_name: Name of logger (default: root logger)
        
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(logger_name or '')
        logger.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
        console_handler.setFormatter(formatter)
        
        # Main log file
        main_log = self.base_log_dir / f"main_orchestrator_{self.timestamp}.log"
        file_handler = logging.FileHandler(main_log, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        self.handlers['main'] = file_handler
        
        logger.info(f"[LOG MANAGER] Main log: {main_log}")
        
        return logger
    
    def setup_source_logger(self, source_name: str, source_type: str) -> logging.Logger:
        """Set up source-specific logger.
        
        Args:
            source_name: Name of the source (e.g., 'sales_db')
            source_type: Type of source (e.g., 'postgresql')
        
        Returns:
            Configured source logger
        """
        logger_name = f"source.{source_name}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False  # Don't propagate to root logger
        
        # Source-specific log file
        source_log = self.base_log_dir / f"source_{source_name}_{self.timestamp}.log"
        file_handler = logging.FileHandler(source_log, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            f'%(asctime)s | {source_type.upper():12s} | %(levelname)-8s | %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Error-only log file
        error_log = self.error_log_dir / f"{source_name}_errors_{self.date}.log"
        error_handler = logging.FileHandler(error_log, encoding='utf-8')
        error_handler.setLevel(logging.WARNING)
        error_handler.addFilter(ErrorOnlyFilter())
        error_formatter = logging.Formatter(
            f'%(asctime)s | {source_type.upper():12s} | %(levelname)-8s | %(message)s'
        )
        error_handler.setFormatter(error_formatter)
        logger.addHandler(error_handler)
        
        self.handlers[f'source_{source_name}'] = file_handler
        self.handlers[f'error_{source_name}'] = error_handler
        
        logger.info(f"[LOG MANAGER] Source log: {source_log}")
        logger.info(f"[LOG MANAGER] Error log: {error_log}")
        
        return logger
    
    def setup_destination_logger(self, destination_type: str = "adls_gen2") -> logging.Logger:
        """Set up destination-specific logger.
        
        Args:
            destination_type: Type of destination (e.g., 'adls_gen2')
        
        Returns:
            Configured destination logger
        """
        logger_name = f"destination.{destination_type}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
        
        # Destination-specific log file
        dest_log = self.base_log_dir / f"destination_{destination_type}_{self.timestamp}.log"
        file_handler = logging.FileHandler(dest_log, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            f'%(asctime)s | {destination_type.upper():12s} | %(levelname)-8s | %(message)s'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Error-only log
        error_log = self.error_log_dir / f"{destination_type}_errors_{self.date}.log"
        error_handler = logging.FileHandler(error_log, encoding='utf-8')
        error_handler.setLevel(logging.WARNING)
        error_handler.addFilter(ErrorOnlyFilter())
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        self.handlers[f'destination_{destination_type}'] = file_handler
        self.handlers[f'error_{destination_type}'] = error_handler
        
        logger.info(f"[LOG MANAGER] Destination log: {dest_log}")
        logger.info(f"[LOG MANAGER] Error log: {error_log}")
        
        return logger
    
    def get_log_summary(self) -> Dict[str, str]:
        """Get summary of all log file paths.
        
        Returns:
            Dictionary mapping log types to file paths
        """
        return {
            'main_log': str(self.base_log_dir / f"main_orchestrator_{self.timestamp}.log"),
            'error_dir': str(self.error_log_dir),
            'timestamp': self.timestamp
        }
    
    def close_all_handlers(self):
        """Close all log handlers (cleanup)."""
        for handler_name, handler in self.handlers.items():
            try:
                handler.close()
            except Exception as e:
                print(f"Error closing handler {handler_name}: {e}")
