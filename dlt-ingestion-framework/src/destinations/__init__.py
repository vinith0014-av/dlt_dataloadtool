"""
Destination modules for DLT ingestion framework.

Each destination type has its own module for better maintainability.
"""
from .base import BaseDestination
from .adls_gen2 import ADLSGen2Destination
from .databricks import DatabricksDestination

__all__ = [
    'BaseDestination',
    'ADLSGen2Destination',
    'DatabricksDestination'
]

