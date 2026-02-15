"""
Data Quality Validators - Production-grade validation and expectations.

Provides pre-flight validation, data quality checks, and DLT expectations
for ensuring data integrity during ingestion.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation failure severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    details: Optional[Dict] = None


class ConfigValidator:
    """Validates Excel configuration before execution.
    
    Performs pre-flight checks to catch configuration errors early,
    before wasting resources on failed pipelines.
    """
    
    REQUIRED_COLUMNS = [
        'source_type', 'source_name', 'table_name', 
        'load_type', 'enabled'
    ]
    
    VALID_SOURCE_TYPES = ['postgresql', 'oracle', 'mssql', 'azure_sql', 'api']
    VALID_LOAD_TYPES = ['FULL', 'INCREMENTAL']
    
    def validate_job(self, job: Dict) -> List[ValidationResult]:
        """Validate a single job configuration.
        
        Args:
            job: Job configuration dictionary
        
        Returns:
            List of validation results
        """
        results = []
        
        # Check required fields
        for col in self.REQUIRED_COLUMNS:
            if col not in job or job[col] is None or str(job[col]).strip() == '':
                results.append(ValidationResult(
                    passed=False,
                    message=f"Missing required field: {col}",
                    severity=ValidationSeverity.CRITICAL
                ))
        
        if not all(r.passed for r in results):
            return results  # Stop if missing required fields
        
        # Validate source_type
        source_type = str(job.get('source_type', '')).lower()
        if source_type not in self.VALID_SOURCE_TYPES:
            results.append(ValidationResult(
                passed=False,
                message=f"Invalid source_type: {source_type}. Must be one of {self.VALID_SOURCE_TYPES}",
                severity=ValidationSeverity.ERROR
            ))
        
        # Validate load_type
        load_type = str(job.get('load_type', '')).upper()
        if load_type not in self.VALID_LOAD_TYPES:
            results.append(ValidationResult(
                passed=False,
                message=f"Invalid load_type: {load_type}. Must be one of {self.VALID_LOAD_TYPES}",
                severity=ValidationSeverity.ERROR
            ))
        
        # Validate incremental configuration
        if load_type == 'INCREMENTAL':
            if not job.get('watermark_column'):
                results.append(ValidationResult(
                    passed=False,
                    message="INCREMENTAL load requires 'watermark_column'",
                    severity=ValidationSeverity.ERROR
                ))
        
        # Validate table_name (no SQL injection risk)
        table_name = str(job.get('table_name', ''))
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
            results.append(ValidationResult(
                passed=False,
                message=f"Invalid table_name format: {table_name}",
                severity=ValidationSeverity.WARNING,
                details={'pattern': '^[a-zA-Z_][a-zA-Z0-9_]*$'}
            ))
        
        # Validate chunk_size if provided (handle NaN/empty values)
        chunk_val = job.get('chunk_size')
        if chunk_val is not None and str(chunk_val).lower() not in ['', 'nan', 'none', 'null']:
            try:
                import math
                if isinstance(chunk_val, float) and math.isnan(chunk_val):
                    pass  # Skip NaN values - use default
                else:
                    chunk_size = int(float(chunk_val))
                    if chunk_size < 1000 or chunk_size > 10000000:
                        results.append(ValidationResult(
                            passed=False,
                            message=f"chunk_size {chunk_size} out of range (1,000 - 10,000,000)",
                            severity=ValidationSeverity.WARNING
                        ))
            except (ValueError, TypeError):
                results.append(ValidationResult(
                    passed=False,
                    message=f"chunk_size must be an integer: {chunk_val}",
                    severity=ValidationSeverity.WARNING  # Downgrade to warning - will use default
                ))
        
        # Oracle requires schema_name
        if source_type == 'oracle' and not job.get('schema_name'):
            results.append(ValidationResult(
                passed=False,
                message="Oracle source requires 'schema_name'",
                severity=ValidationSeverity.ERROR
            ))
        
        # If all checks passed, add success result
        if not results or all(r.passed for r in results):
            results.append(ValidationResult(
                passed=True,
                message=f"Job configuration valid: {job.get('source_name')}.{job.get('table_name')}",
                severity=ValidationSeverity.INFO
            ))
        
        return results
    
    def validate_all_jobs(self, jobs: List[Dict]) -> Tuple[bool, List[ValidationResult]]:
        """Validate all job configurations.
        
        Args:
            jobs: List of job configuration dictionaries
        
        Returns:
            Tuple of (all_valid, all_results)
        """
        all_results = []
        all_valid = True
        
        for job in jobs:
            job_results = self.validate_job(job)
            all_results.extend(job_results)
            
            # Check for critical failures
            for result in job_results:
                if not result.passed and result.severity in [
                    ValidationSeverity.ERROR, ValidationSeverity.CRITICAL
                ]:
                    all_valid = False
        
        return all_valid, all_results


class SecretsValidator:
    """Validates secrets configuration before execution."""
    
    REQUIRED_DB_KEYS = ['host', 'port', 'database', 'username', 'password']
    REQUIRED_API_KEYS = ['base_url']
    REQUIRED_ADLS_KEYS = ['azure_storage_account_name', 'azure_storage_account_key']
    
    def validate_source_secrets(self, secrets: Dict, source_name: str, 
                                 source_type: str) -> List[ValidationResult]:
        """Validate secrets for a specific source.
        
        Args:
            secrets: Full secrets dictionary
            source_name: Name of the source
            source_type: Type of source (postgresql, oracle, etc.)
        
        Returns:
            List of validation results
        """
        results = []
        
        # Check if source exists in secrets
        if 'sources' not in secrets:
            results.append(ValidationResult(
                passed=False,
                message="No 'sources' section found in secrets",
                severity=ValidationSeverity.CRITICAL
            ))
            return results
        
        if source_name not in secrets['sources']:
            results.append(ValidationResult(
                passed=False,
                message=f"Source '{source_name}' not found in secrets",
                severity=ValidationSeverity.CRITICAL
            ))
            return results
        
        source_config = secrets['sources'][source_name]
        
        # Check required keys based on source type
        if source_type == 'api':
            required_keys = self.REQUIRED_API_KEYS
        else:
            required_keys = self.REQUIRED_DB_KEYS
        
        missing_keys = [k for k in required_keys if k not in source_config]
        
        if missing_keys:
            results.append(ValidationResult(
                passed=False,
                message=f"Missing secret keys for {source_name}: {missing_keys}",
                severity=ValidationSeverity.CRITICAL
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                message=f"Secrets valid for source: {source_name}",
                severity=ValidationSeverity.INFO
            ))
        
        return results
    
    def validate_destination_secrets(self, secrets: Dict) -> List[ValidationResult]:
        """Validate ADLS Gen2 destination secrets.
        
        Args:
            secrets: Full secrets dictionary
        
        Returns:
            List of validation results
        """
        results = []
        
        if 'destination' not in secrets or 'filesystem' not in secrets['destination']:
            results.append(ValidationResult(
                passed=False,
                message="ADLS Gen2 destination configuration missing",
                severity=ValidationSeverity.CRITICAL
            ))
            return results
        
        dest = secrets['destination']['filesystem']
        
        if 'credentials' not in dest:
            results.append(ValidationResult(
                passed=False,
                message="ADLS Gen2 credentials section missing",
                severity=ValidationSeverity.CRITICAL
            ))
            return results
        
        creds = dest['credentials']
        missing_keys = [k for k in self.REQUIRED_ADLS_KEYS if k not in creds]
        
        if missing_keys:
            results.append(ValidationResult(
                passed=False,
                message=f"Missing ADLS Gen2 secret keys: {missing_keys}",
                severity=ValidationSeverity.CRITICAL
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                message="ADLS Gen2 destination secrets valid",
                severity=ValidationSeverity.INFO
            ))
        
        return results


class DataQualityValidator:
    """Data quality validation during and after ingestion."""
    
    def validate_row_count(self, expected: int, actual: int, 
                          tolerance_pct: float = 10.0) -> ValidationResult:
        """Validate row count within tolerance.
        
        Args:
            expected: Expected row count
            actual: Actual row count
            tolerance_pct: Acceptable percentage difference
        
        Returns:
            Validation result
        """
        if expected == 0 and actual == 0:
            return ValidationResult(
                passed=True,
                message="Row count validation passed (both zero)",
                severity=ValidationSeverity.INFO
            )
        
        if expected == 0:
            return ValidationResult(
                passed=False,
                message=f"Expected 0 rows but got {actual}",
                severity=ValidationSeverity.WARNING
            )
        
        diff_pct = abs(expected - actual) / expected * 100
        
        if diff_pct <= tolerance_pct:
            return ValidationResult(
                passed=True,
                message=f"Row count within tolerance: expected {expected:,}, got {actual:,} ({diff_pct:.1f}% diff)",
                severity=ValidationSeverity.INFO
            )
        else:
            return ValidationResult(
                passed=False,
                message=f"Row count outside tolerance: expected {expected:,}, got {actual:,} ({diff_pct:.1f}% diff)",
                severity=ValidationSeverity.WARNING,
                details={'expected': expected, 'actual': actual, 'diff_pct': diff_pct}
            )
    
    def validate_not_empty(self, row_count: int, table_name: str) -> ValidationResult:
        """Validate that the result is not empty.
        
        Args:
            row_count: Number of rows ingested
            table_name: Name of the table
        
        Returns:
            Validation result
        """
        if row_count > 0:
            return ValidationResult(
                passed=True,
                message=f"Table '{table_name}' has {row_count:,} rows",
                severity=ValidationSeverity.INFO
            )
        else:
            return ValidationResult(
                passed=False,
                message=f"Table '{table_name}' returned 0 rows",
                severity=ValidationSeverity.WARNING
            )
    
    def validate_schema_stability(self, schema_version: int) -> ValidationResult:
        """Validate schema has not changed unexpectedly.
        
        Args:
            schema_version: Current schema version
        
        Returns:
            Validation result
        """
        if schema_version == 1:
            return ValidationResult(
                passed=True,
                message="Schema is stable (version 1)",
                severity=ValidationSeverity.INFO
            )
        else:
            return ValidationResult(
                passed=True,  # Not a failure, just a warning
                message=f"Schema evolution detected (version {schema_version})",
                severity=ValidationSeverity.WARNING,
                details={'schema_version': schema_version}
            )
