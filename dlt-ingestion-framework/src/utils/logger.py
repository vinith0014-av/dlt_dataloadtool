"""
Logging configuration and utilities.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class FrameworkLogger:
    """Centralized logging for the ingestion framework."""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        """Singleton pattern to ensure one logger instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize logger if not already initialized."""
        if self._logger is None:
            self._setup_logger()
    
    def _setup_logger(self):
        """Configure logging with file and console handlers."""
        # Get project root directory
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Create log filename with timestamp
        log_filename = f"ingestion_{datetime.now().strftime('%Y%m%d')}.log"
        log_filepath = log_dir / log_filename
        
        # Create logger
        self._logger = logging.getLogger("DLT_Ingestion_Framework")
        self._logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self._logger.handlers:
            self._logger.handlers.clear()
        
        # File handler - detailed logs
        file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler - info and above
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)
        
        self._logger.info("="*80)
        self._logger.info("DLT Ingestion Framework - Logging Initialized")
        self._logger.info(f"Log file: {log_filepath}")
        self._logger.info("="*80)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance."""
        return self._logger
    
    @classmethod
    def log_job_start(cls, job_id: str, job_config: dict):
        """Log job start with configuration details."""
        logger = cls().get_logger()
        logger.info("-" * 80)
        logger.info(f"Starting Job: {job_id}")
        logger.info(f"Source: {job_config.get('source_type')} - {job_config.get('source_name')}")
        logger.info(f"Table: {job_config.get('table_name')}")
        logger.info(f"Load Type: {job_config.get('load_type')}")
        logger.info("-" * 80)
    
    @classmethod
    def log_job_end(cls, job_id: str, status: str, duration: float, rows: int):
        """Log job completion with summary."""
        logger = cls().get_logger()
        logger.info("-" * 80)
        logger.info(f"Job Completed: {job_id}")
        logger.info(f"Status: {status}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Rows Processed: {rows:,}")
        logger.info("-" * 80)
    
    @classmethod
    def log_error(cls, job_id: str, error: Exception, context: Optional[str] = None):
        """Log error with context."""
        logger = cls().get_logger()
        logger.error(f"Job {job_id} failed: {str(error)}")
        if context:
            logger.error(f"Context: {context}")
        logger.exception("Full traceback:")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Optional logger name. If None, returns the framework logger.
    
    Returns:
        Configured logger instance.
    """
    if name:
        return logging.getLogger(f"DLT_Ingestion_Framework.{name}")
    return FrameworkLogger().get_logger()


def setup_logger(log_file: Path = None):
    """
    Setup root logger with file and console handlers.
    
    Args:
        log_file: Path to log file (optional)
    """
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log_file provided)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
