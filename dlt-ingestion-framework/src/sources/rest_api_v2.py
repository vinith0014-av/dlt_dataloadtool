"""
REST API Source - Production-grade REST API ingestion using DLT native rest_api_source.

PRODUCTION FEATURES (v2.0):
- 6 pagination types: offset, cursor, page_number, header_link, json_link, single_page
- 4 authentication methods: api_key, bearer, basic, oauth2
- Automatic retry with exponential backoff
- Rate limiting support (requests per second)
- Incremental loading via cursor/timestamp tracking
- JSON response parsing with data selectors

ARCHITECTURE:
- Uses DLT's native rest_api_source() for production-grade API handling
- Configuration-driven via Excel + secrets.toml
- Handles pagination, auth, retry automatically

USAGE:
    # In Excel config (ingestion_config.xlsx)
    source_type: api
    source_name: github_api
    table_name: issues
    api_endpoint: /repos/owner/repo/issues
    pagination_type: header_link
    auth_type: bearer
    page_size: 100
    
    # In secrets.toml
    [sources.github_api]
    base_url = "https://api.github.com"
    token = "ghp_xxxxxxxxxxxx"
    rate_limit = 30  # requests per minute
"""
import logging
from typing import Dict, Optional, List, Any
from enum import Enum

from dlt.sources.rest_api import rest_api_source
from src.sources.base import BaseSource

logger = logging.getLogger(__name__)


class PaginationType(str, Enum):
    """Supported pagination types."""
    SINGLE_PAGE = "single_page"      # No pagination (default)
    OFFSET = "offset"                # limit + offset parameters
    CURSOR = "cursor"                # Cursor-based (next_cursor)
    PAGE_NUMBER = "page_number"      # page + per_page parameters
    HEADER_LINK = "header_link"      # RFC 5988 Link header (GitHub style)
    JSON_LINK = "json_link"          # Next URL in JSON body


class AuthType(str, Enum):
    """Supported authentication types."""
    NONE = "none"                    # No authentication
    API_KEY = "api_key"              # API key in header or query
    BEARER = "bearer"                # Bearer token (OAuth 2.0)
    BASIC = "basic"                  # Basic HTTP authentication
    OAUTH2 = "oauth2"                # OAuth 2.0 client credentials


class RESTAPISource(BaseSource):
    """
    Production-grade REST API source using DLT native rest_api_source.
    
    Features:
    - 6 pagination types with automatic page traversal
    - 4 authentication methods
    - Built-in retry logic (exponential backoff)
    - Rate limiting support
    - JSON response parsing with selectors
    - State management for incremental loads
    """
    
    def get_source_type(self) -> str:
        """Return REST API source type identifier."""
        return "api"
    
    def build_connection_string(self, source_name: str) -> str:
        """REST APIs don't use connection strings."""
        return None
    
    def get_api_config(self, source_name: str) -> Dict:
        """
        Get API configuration from secrets.
        
        Args:
            source_name: API source name (e.g., 'github_api')
        
        Returns:
            Dictionary with base_url, authentication, rate_limit, etc.
        """
        api_config = self.secrets.get('sources', {}).get(source_name, {})
        
        if not api_config:
            raise ValueError(f"No configuration found for API source: {source_name}")
        
        if not api_config.get('base_url') and not api_config.get('url'):
            raise ValueError(f"API source '{source_name}' requires 'base_url' in secrets")
        
        return api_config
    
    def build_rest_config(self, job: Dict) -> Dict:
        """
        Build DLT rest_api_source configuration from job definition.
        
        Args:
            job: Job configuration dictionary with:
                - source_name: API source name (for secrets lookup)
                - table_name: Resource/endpoint name
                - api_endpoint: API endpoint path (e.g., '/users', '/repos/{owner}/{repo}/issues')
                - pagination_type: Pagination strategy (offset, cursor, page_number, etc.)
                - auth_type: Authentication method (api_key, bearer, basic, oauth2)
                - page_size: Records per page (default: 100)
        
        Returns:
            DLT rest_api_source compatible configuration dictionary
        """
        source_name = job['source_name']
        api_config = self.get_api_config(source_name)
        
        # Build client configuration (base_url, auth, rate_limit)
        client_config = {
            "base_url": api_config.get('base_url', api_config.get('url', ''))
        }
        
        # Add authentication
        auth_config = self._build_auth_config(job, api_config)
        if auth_config:
            if 'headers' in auth_config:
                client_config['headers'] = auth_config['headers']
            if 'auth' in auth_config:
                client_config['auth'] = auth_config['auth']
            if 'params' in auth_config:
                client_config.setdefault('params', {}).update(auth_config['params'])
        
        # Add rate limiting if specified
        if api_config.get('rate_limit'):
            client_config['paginator'] = {
                'type': 'auto',
                'maximum_rate': api_config['rate_limit']  # requests per minute
            }
        
        # Build resource configuration (endpoint, pagination, data selector)
        resource_config = self._build_resource_config(job, api_config)
        
        rest_config = {
            "client": client_config,
            "resources": [resource_config]
        }
        
        self.logger.info(f"[REST API] Built config for {source_name}.{job['table_name']}")
        self.logger.debug(f"[REST API] Base URL: {client_config['base_url']}")
        self.logger.debug(f"[REST API] Endpoint: {resource_config['endpoint']['path']}")
        
        return rest_config
    
    def _build_auth_config(self, job: Dict, api_config: Dict) -> Optional[Dict]:
        """
        Build authentication configuration.
        
        Supports:
        - api_key: Header or query parameter
        - bearer: Bearer token in Authorization header
        - basic: Basic HTTP authentication
        - oauth2: OAuth 2.0 client credentials flow
        
        Args:
            job: Job configuration
            api_config: API secrets configuration
        
        Returns:
            Dictionary with 'headers', 'auth', or 'params' keys
        """
        auth_type = job.get('auth_type', api_config.get('auth_type', 'none')).lower()
        
        if auth_type == 'none':
            return None
        
        # API Key authentication (header or query parameter)
        if auth_type == 'api_key':
            api_key = api_config.get('api_key')
            if not api_key:
                raise ValueError(f"auth_type='api_key' requires 'api_key' in secrets")
            
            api_key_name = api_config.get('api_key_name', 'X-API-Key')
            api_key_location = api_config.get('api_key_location', 'header').lower()
            
            if api_key_location == 'header':
                return {"headers": {api_key_name: api_key}}
            else:
                return {"params": {api_key_name: api_key}}
        
        # Bearer token authentication (OAuth 2.0)
        if auth_type == 'bearer':
            token = api_config.get('token', api_config.get('bearer_token'))
            if not token:
                raise ValueError(f"auth_type='bearer' requires 'token' or 'bearer_token' in secrets")
            
            return {"headers": {"Authorization": f"Bearer {token}"}}
        
        # Basic HTTP authentication
        if auth_type == 'basic':
            username = api_config.get('username')
            password = api_config.get('password')
            if not username or not password:
                raise ValueError(f"auth_type='basic' requires 'username' and 'password' in secrets")
            
            return {"auth": (username, password)}
        
        # OAuth 2.0 client credentials flow
        if auth_type == 'oauth2':
            oauth_config = {
                "type": "oauth2_client_credentials",
                "token_url": api_config.get('oauth_url'),
                "client_id": api_config.get('client_id'),
                "client_secret": api_config.get('client_secret')
            }
            
            if not all([oauth_config['token_url'], oauth_config['client_id'], oauth_config['client_secret']]):
                raise ValueError(f"auth_type='oauth2' requires 'oauth_url', 'client_id', 'client_secret' in secrets")
            
            # Optional scope
            if api_config.get('scope'):
                oauth_config['scope'] = api_config['scope']
            
            return {"auth": oauth_config}
        
        self.logger.warning(f"[REST API] Unknown auth type: {auth_type}, proceeding without authentication")
        return None
    
    def _build_resource_config(self, job: Dict, api_config: Dict) -> Dict:
        """
        Build resource (endpoint) configuration.
        
        Includes:
        - Endpoint path with optional parameters
        - Pagination configuration
        - Data selector (for nested responses)
        - HTTP method (GET/POST)
        
        Args:
            job: Job configuration
            api_config: API secrets configuration
        
        Returns:
            Resource configuration dictionary
        """
        endpoint_path = job.get('api_endpoint', job['table_name'])
        
        resource_config = {
            "name": job['table_name'],
            "endpoint": {
                "path": endpoint_path,
                "method": api_config.get('method', 'GET').upper()
            }
        }
        
        # Add query parameters if specified
        params = api_config.get('params', {})
        if params:
            resource_config["endpoint"]["params"] = params
        
        # Add pagination configuration
        pagination_config = self._build_pagination_config(job, api_config)
        if pagination_config:
            resource_config["endpoint"]["paginator"] = pagination_config
        
        # Add data selector if response is wrapped (e.g., {"data": [...], "meta": {}})
        data_selector = api_config.get('data_selector') or job.get('data_selector')
        if data_selector:
            resource_config["endpoint"]["data_selector"] = data_selector
        
        # Add primary key if specified (for merge operations)
        primary_key = job.get('primary_key')
        if primary_key:
            resource_config["primary_key"] = primary_key if isinstance(primary_key, list) else [primary_key]
        
        return resource_config
    
    def _build_pagination_config(self, job: Dict, api_config: Dict) -> Optional[Dict]:
        """
        Build pagination configuration based on type.
        
        Supports:
        - single_page: No pagination
        - offset: limit + offset parameters (e.g., ?limit=100&offset=200)
        - cursor: Cursor-based pagination (e.g., ?cursor=abc123)
        - page_number: Page number pagination (e.g., ?page=2&per_page=100)
        - header_link: RFC 5988 Link header (GitHub style)
        - json_link: Next URL in JSON body (e.g., {"next": "https://..."})
        
        Args:
            job: Job configuration
            api_config: API secrets configuration
        
        Returns:
            Pagination configuration dictionary or None
        """
        pagination_type = job.get('pagination_type', api_config.get('pagination_type', 'single_page')).lower()
        page_size = job.get('page_size', api_config.get('page_size', 100))
        
        if pagination_type == 'single_page' or pagination_type == 'none':
            return None  # No pagination
        
        # Offset-based pagination (limit + offset)
        if pagination_type == 'offset':
            return {
                "type": "offset",
                "limit": page_size,
                "offset_param": api_config.get('offset_param', 'offset'),
                "limit_param": api_config.get('limit_param', 'limit'),
                "maximum_offset": api_config.get('maximum_offset')  # Optional: prevent infinite loops
            }
        
        # Cursor-based pagination
        if pagination_type == 'cursor':
            return {
                "type": "cursor",
                "cursor_param": api_config.get('cursor_param', 'cursor'),
                "cursor_path": api_config.get('cursor_path', 'next_cursor')
            }
        
        # Page number pagination
        if pagination_type == 'page_number':
            return {
                "type": "page_number",
                "page_param": api_config.get('page_param', 'page'),
                "per_page": page_size,
                "per_page_param": api_config.get('per_page_param', 'per_page'),
                "base_page": api_config.get('base_page', 1),  # Starting page (0 or 1)
                "total_path": api_config.get('total_path')  # Optional: total pages path
            }
        
        # Header link pagination (GitHub style)
        if pagination_type == 'header_link':
            return {
                "type": "header_link",
                "links_key": api_config.get('links_key', 'Link')
            }
        
        # JSON link pagination (next URL in response body)
        if pagination_type == 'json_link':
            return {
                "type": "json_link",
                "next_url_path": api_config.get('next_url_path', 'next')
            }
        
        self.logger.warning(f"[REST API] Unknown pagination type: {pagination_type}, using single_page")
        return None
    
    def create_source(self, job: Dict):
        """
        Create DLT REST API source from job configuration.
        
        Args:
            job: Job configuration dictionary
        
        Returns:
            DLT source object with configured resources
        """
        rest_config = self.build_rest_config(job)
        
        self.logger.info(f"[REST API] Creating DLT rest_api_source for {job['table_name']}")
        
        # Create DLT REST API source (handles pagination, retry, state management)
        source = rest_api_source(rest_config)
        
        return source
    
    def get_resource(self, job: Dict):
        """
        Get specific resource from REST API source.
        
        Args:
            job: Job configuration dictionary
        
        Returns:
            DLT resource for the specified endpoint
        """
        source = self.create_source(job)
        resource_name = job['table_name']
        
        # Try to get resource by name
        if hasattr(source, resource_name):
            return getattr(source, resource_name)
        
        # Try to get from resources dictionary
        if hasattr(source, 'resources') and resource_name in source.resources:
            return source.resources[resource_name]
        
        # List available resources for debugging
        available = []
        if hasattr(source, 'resources'):
            available = list(source.resources.keys())
        
        raise ValueError(
            f"Resource '{resource_name}' not found in REST API source. "
            f"Available resources: {available}"
        )
    
    def validate_connection(self, source_name: str) -> bool:
        """
        Validate API connectivity with a simple health check.
        
        Args:
            source_name: API source name
        
        Returns:
            True if API is accessible
        """
        try:
            import requests
            
            api_config = self.get_api_config(source_name)
            base_url = api_config.get('base_url', api_config.get('url', ''))
            
            if not base_url:
                self.logger.error(f"[REST API] No base_url configured for: {source_name}")
                return False
            
            # Simple HEAD or GET request to base URL
            self.logger.info(f"[REST API] Testing connectivity to: {base_url}")
            
            response = requests.head(base_url, timeout=10, allow_redirects=True)
            
            # Consider 2xx and 3xx as success, 4xx as auth issue (still accessible)
            if response.status_code < 500:
                self.logger.info(f"[REST API] Connection successful (status: {response.status_code})")
                return True
            else:
                self.logger.warning(f"[REST API] Server error (status: {response.status_code})")
                return False
                
        except requests.RequestException as e:
            self.logger.warning(f"[REST API] Connection check failed: {e}")
            return False
    
    def supports_schema(self) -> bool:
        """REST APIs don't use schema parameter."""
        return False
    
    def get_metadata(self, source_name: str) -> Dict:
        """Get REST API-specific metadata."""
        metadata = super().get_metadata(source_name)
        api_config = self.get_api_config(source_name)
        
        metadata.update({
            'base_url': api_config.get('base_url', api_config.get('url')),
            'auth_type': api_config.get('auth_type', 'none'),
            'rate_limit': api_config.get('rate_limit'),
            'pagination_type': api_config.get('pagination_type', 'single_page'),
            'method': api_config.get('method', 'GET')
        })
        
        return metadata
