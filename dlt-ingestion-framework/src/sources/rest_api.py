"""
REST API source implementation.

Handles REST API data ingestion using DLT's native rest_api_source.
"""
import logging
from typing import Dict, Optional
from .base import BaseSource

logger = logging.getLogger(__name__)


class RESTAPISource(BaseSource):
    """REST API data source handler.
    
    Features:
    - DLT native rest_api_source() integration
    - Automatic pagination (offset, cursor, page-based)
    - Built-in retry logic with exponential backoff
    - State management for incremental loads
    - JSON schema inference
    - Rate limiting support
    """
    
    def get_source_type(self) -> str:
        """Return REST API source type identifier."""
        return "api"
    
    def build_connection_string(self, source_name: str) -> Optional[str]:
        """REST API sources don't use connection strings.
        
        Args:
            source_name: Name of the API source in secrets
        
        Returns:
            None (APIs use configuration dict instead)
        """
        # REST APIs don't have connection strings
        # They use configuration dictionaries for rest_api_source()
        return None
    
    def get_api_config(self, source_name: str, endpoint_path: str, 
                       params: Optional[Dict] = None) -> Dict:
        """Build DLT rest_api_source configuration.
        
        Args:
            source_name: Name of the API source in secrets
            endpoint_path: API endpoint path (e.g., '/coins/markets')
            params: Optional query parameters
        
        Returns:
            Configuration dict for dlt.sources.rest_api.rest_api_source()
        
        Raises:
            KeyError: If source_name not found in secrets
        
        Example:
            {
                "client": {
                    "base_url": "https://api.example.com",
                    "headers": {"x-api-key": "..."}
                },
                "resources": [{
                    "name": "users",
                    "endpoint": {"path": "/users", "params": {...}}
                }]
            }
        """
        if 'sources' not in self.secrets or source_name not in self.secrets['sources']:
            raise KeyError(f"API source '{source_name}' not found in secrets")
        
        api = self.secrets['sources'][source_name]
        
        # Required field
        if 'base_url' not in api:
            raise ValueError(f"API source '{source_name}' missing 'base_url'")
        
        # Build REST API configuration (DLT native format)
        rest_config = {
            "client": {
                "base_url": api['base_url']
            },
            "resources": [{
                "name": endpoint_path.strip('/').replace('/', '_'),  # Convert path to resource name
                "endpoint": {
                    "path": endpoint_path,
                    "params": params or api.get('params', {})
                }
            }]
        }
        
        # Add API key header if present
        if api.get('api_key'):
            # Support different header formats
            header_name = api.get('api_key_header', 'x-api-key')
            rest_config["client"]["headers"] = {
                header_name: api['api_key']
            }
        
        # Add authentication if present
        if api.get('auth_token'):
            rest_config["client"]["headers"] = rest_config["client"].get("headers", {})
            rest_config["client"]["headers"]["Authorization"] = f"Bearer {api['auth_token']}"
        
        self.logger.debug(f"REST API config: {api['base_url']}{endpoint_path}")
        self.logger.info(f"[REST API] Configured source {source_name}")
        
        return rest_config
    
    def supports_schema(self) -> bool:
        """REST APIs don't use database schemas."""
        return False
    
    def validate_connection(self, source_name: str) -> bool:
        """Test REST API connectivity.
        
        Args:
            source_name: Name of the API source in secrets
        
        Returns:
            True if base_url is accessible, False otherwise
        """
        try:
            import requests
            
            api = self.secrets['sources'][source_name]
            base_url = api['base_url']
            
            # Try HEAD request to base URL
            headers = {}
            if api.get('api_key'):
                header_name = api.get('api_key_header', 'x-api-key')
                headers[header_name] = api['api_key']
            
            response = requests.head(base_url, headers=headers, timeout=10)
            
            if response.status_code < 500:  # Accept 4xx as "reachable"
                self.logger.info(f"[API CONNECTION OK] {source_name} - {base_url}")
                return True
            else:
                self.logger.error(f"[API CONNECTION FAILED] {source_name} - Status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"[API CONNECTION FAILED] {source_name}: {e}")
            return False
    
    def get_metadata(self, source_name: str) -> Dict:
        """Get REST API-specific metadata."""
        metadata = super().get_metadata(source_name)
        api = self.secrets['sources'][source_name]
        
        metadata.update({
            'base_url': api['base_url'],
            'has_api_key': bool(api.get('api_key')),
            'has_auth_token': bool(api.get('auth_token')),
            'pagination_support': 'automatic',
            'retry_logic': 'exponential_backoff'
        })
        
        return metadata
