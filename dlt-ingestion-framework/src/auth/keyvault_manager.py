"""
Azure Key Vault Manager - Secure credential retrieval for production deployments.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Azure Key Vault imports (optional - for production secret management)
try:
    from azure.identity import DefaultAzureCredential
    from azure.keyvault.secrets import SecretClient
    KEYVAULT_AVAILABLE = True
except ImportError:
    KEYVAULT_AVAILABLE = False
    logger.debug("Azure Key Vault libraries not installed (optional)")


class KeyVaultManager:
    """Manages Azure Key Vault integration for secure credential retrieval.
    
    Usage:
        1. Set environment variable: AZURE_KEY_VAULT_URL=https://<vault-name>.vault.azure.net/
        2. Authenticate via Azure CLI: az login
        3. Framework automatically uses Key Vault if AZURE_KEY_VAULT_URL is set
    
    Authentication Methods (priority order):
        1. Azure CLI (dev): az login
        2. Managed Identity (prod): Automatic on Azure VMs/App Service
        3. Service Principal (CI/CD): Environment variables (CLIENT_ID, TENANT_ID, SECRET)
    """
    
    def __init__(self, vault_url: str = None):
        """Initialize Key Vault client.
        
        Args:
            vault_url: Azure Key Vault URL. If None, reads from AZURE_KEY_VAULT_URL env var.
        
        Raises:
            ImportError: If azure-identity or azure-keyvault-secrets not installed
            ValueError: If vault_url not provided and AZURE_KEY_VAULT_URL not set
        """
        if not KEYVAULT_AVAILABLE:
            raise ImportError(
                "Azure Key Vault dependencies not installed. "
                "Run: pip install azure-identity azure-keyvault-secrets"
            )
        
        self.vault_url = vault_url or os.getenv('AZURE_KEY_VAULT_URL')
        if not self.vault_url:
            raise ValueError(
                "Key Vault URL not provided. Set AZURE_KEY_VAULT_URL environment variable"
            )
        
        # Initialize Azure credential (supports CLI, Managed Identity, Service Principal)
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=self.vault_url, credential=self.credential)
        logger.info(f"[KEY VAULT] Initialized: {self.vault_url}")
    
    def get_secret(self, secret_name: str) -> str:
        """Retrieve secret value from Key Vault.
        
        Args:
            secret_name: Name of the secret (e.g., 'postgres-source-password')
        
        Returns:
            Secret value as string
        
        Raises:
            Exception: If secret not found or authentication fails
        """
        try:
            secret = self.client.get_secret(secret_name)
            logger.debug(f"Retrieved secret: {secret_name}")
            return secret.value
        except Exception as e:
            logger.error(f"Failed to retrieve secret '{secret_name}': {e}")
            raise
    
    def get_source_config(self, source_name: str) -> dict:
        """Retrieve complete source configuration from Key Vault.
        
        Secret naming convention: {source-name}-{config-key}
        Example: postgres-source-host, postgres-source-password
        
        Args:
            source_name: Source identifier (e.g., 'postgres_source')
        
        Returns:
            Dictionary with source configuration (host, port, username, password, etc.)
        """
        # Normalize source name for Key Vault (replace underscores with hyphens)
        vault_prefix = source_name.replace('_', '-')
        config = {}
        
        # Common database config keys
        for key in ['host', 'port', 'database', 'username', 'password', 'sid', 'service-name']:
            secret_name = f"{vault_prefix}-{key}"
            try:
                config[key] = self.get_secret(secret_name)
            except:
                # Skip if secret doesn't exist (optional config)
                continue
        
        return config
