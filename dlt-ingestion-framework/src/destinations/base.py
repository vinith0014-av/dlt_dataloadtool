"""
Base class for all data destinations.

Defines the interface that all destination implementations must follow.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class BaseDestination(ABC):
    """Abstract base class for all data destinations.
    
    Each destination type (ADLS Gen2, S3, Delta Lake, etc.) must implement:
    - get_destination_type(): Return destination type identifier
    - get_dlt_destination_config(): Return DLT destination configuration
    
    Optional overrides:
    - validate_connection(): Test connectivity before writing
    - get_metadata(): Additional destination-specific metadata
    """
    
    def __init__(self, name: str, config: Dict):
        """Initialize destination with name and configuration.
        
        Args:
            name: Destination instance name
            config: Dictionary containing destination credentials
        """
        self.name = name
        self.config = config
        # Keep backward compatibility with secrets attribute
        self.secrets = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up destination-specific logger.
        
        Returns:
            Logger instance configured for this destination type
        """
        dest_logger = logging.getLogger(f"{__name__}.{self.get_destination_type()}")
        return dest_logger
    
    @abstractmethod
    def get_destination_type(self) -> str:
        """Return destination type identifier.
        
        Returns:
            Destination type string (e.g., 'adls_gen2', 'delta_lake')
        """
        pass
    
    @abstractmethod
    def get_dlt_destination_config(self) -> Dict[str, Any]:
        """Get DLT destination configuration.
        
        Returns:
            Dictionary with DLT destination parameters
        
        Example:
            {
                'destination': 'filesystem',
                'dataset_name': 'raw_data',
                'credentials': {...}
            }
        """
        pass
    
    def validate_connection(self) -> bool:
        """Test destination connectivity.
        
        Returns:
            True if destination is accessible, False otherwise
        """
        self.logger.info(f"[VALIDATION] Testing {self.get_destination_type()} connectivity...")
        # Base implementation - override in subclasses for specific tests
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get destination-specific metadata.
        
        Returns:
            Dictionary with destination metadata
        """
        return {
            'destination_type': self.get_destination_type()
        }
    
    def get_destination_config(self) -> Dict[str, Any]:
        """Alias for get_dlt_destination_config() for backward compatibility.
        
        Returns:
            Dictionary with DLT destination parameters
        """
        return self.get_dlt_destination_config()

