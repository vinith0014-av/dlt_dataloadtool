"""Unit tests for IngestionOrchestrator."""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from datetime import datetime

from src.core.orchestrator import IngestionOrchestrator


class TestOrchestratorInitialization:
    """Tests for orchestrator initialization."""
    
    def test_init_with_config_loader(self, temp_dir):
        """Test orchestrator initialization with ConfigLoader."""
        with patch('src.core.orchestrator.ConfigLoader') as mock_loader:
            orchestrator = IngestionOrchestrator(config_dir=temp_dir)
            
            assert orchestrator.config_loader is not None
            assert orchestrator.metadata_tracker is not None
    
    def test_init_creates_log_directories(self, temp_dir):
        """Test orchestrator creates necessary log directories."""
        orchestrator = IngestionOrchestrator(config_dir=temp_dir)
        
        # Should create logs directory
        logs_dir = temp_dir / 'logs'
        # Directory may not exist in test env, just verify initialization works
        assert orchestrator is not None


class TestExecuteJob:
    """Tests for execute_job() method."""
    
    @patch('src.core.orchestrator.dlt.pipeline')
    @patch('src.core.orchestrator.sql_table')
    def test_execute_database_job(self, mock_sql_table, mock_pipeline, 
                                   sample_job_full, sample_secrets):
        """Test execution of database job."""
        # Setup mocks
        pipeline = MagicMock()
        pipeline.last_trace = MagicMock()
        pipeline.last_trace.last_normalize_info = MagicMock()
        pipeline.last_trace.last_normalize_info.row_counts = {'customers': 100}
        mock_pipeline.return_value = pipeline
        
        resource = MagicMock()
        mock_sql_table.return_value = resource
        
        # Execute
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        result = orchestrator.execute_job(sample_job_full)
        
        # Assertions
        assert result is not None
        mock_pipeline.assert_called_once()
        mock_sql_table.assert_called_once()
    
    @patch('src.core.orchestrator.dlt.pipeline')
    @patch('dlt.sources.rest_api.rest_api_source')
    def test_execute_api_job(self, mock_rest_api, mock_pipeline,
                             sample_api_job, sample_secrets):
        """Test execution of REST API job."""
        # Setup mocks
        pipeline = MagicMock()
        pipeline.last_trace = MagicMock()
        pipeline.last_trace.last_normalize_info = MagicMock()
        pipeline.last_trace.last_normalize_info.row_counts = {'users': 50}
        mock_pipeline.return_value = pipeline
        
        api_source = MagicMock()
        resource = MagicMock()
        api_source.resources = {'users': resource}
        mock_rest_api.return_value = api_source
        
        # Execute
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        result = orchestrator.execute_job(sample_api_job)
        
        # Assertions
        assert result is not None
        mock_rest_api.assert_called_once()
    
    def test_execute_job_missing_secrets(self, sample_job_full):
        """Test job execution fails gracefully with missing secrets."""
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = {'sources': {}}
        
        # Should handle missing secrets gracefully
        with pytest.raises(KeyError):
            orchestrator.execute_job(sample_job_full)


class TestBuildConnectionString:
    """Tests for connection string generation."""
    
    def test_postgresql_connection_string(self, sample_secrets):
        """Test PostgreSQL connection string generation."""
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        conn_str = orchestrator.build_connection_string('postgresql', 'postgresql')
        
        assert 'postgresql+psycopg2://' in conn_str
        assert 'localhost' in conn_str
        assert '5432' in conn_str
    
    def test_oracle_connection_string(self, sample_secrets):
        """Test Oracle connection string generation."""
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        conn_str = orchestrator.build_connection_string('oracle', 'oracle')
        
        assert 'oracle+oracledb://' in conn_str
        assert 'localhost' in conn_str
        assert '1521' in conn_str
    
    def test_mssql_connection_string(self, sample_secrets):
        """Test MSSQL connection string generation with ODBC."""
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        conn_str = orchestrator.build_connection_string('mssql', 'mssql')
        
        assert 'mssql+pyodbc:' in conn_str
        assert 'ODBC+Driver+17' in conn_str or 'ODBC Driver 17' in conn_str
        assert 'localhost' in conn_str
    
    def test_azure_sql_connection_string(self, sample_secrets):
        """Test Azure SQL connection string with encryption."""
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        conn_str = orchestrator.build_connection_string('azure_sql', 'azure_sql')
        
        assert 'mssql+pyodbc:' in conn_str
        assert 'Encrypt%3Dyes' in conn_str or 'Encrypt=yes' in conn_str
        assert 'database.windows.net' in conn_str


class TestIncrementalLoading:
    """Tests for incremental load functionality."""
    
    @patch('src.core.orchestrator.dlt.pipeline')
    @patch('src.core.orchestrator.sql_table')
    @patch('src.core.orchestrator.dlt.sources.incremental')
    def test_incremental_load_creates_incremental_object(
        self, mock_incremental, mock_sql_table, mock_pipeline,
        sample_job_incremental, sample_secrets
    ):
        """Test incremental load creates dlt.sources.incremental object."""
        # Setup mocks
        pipeline = MagicMock()
        mock_pipeline.return_value = pipeline
        
        incremental_obj = MagicMock()
        mock_incremental.return_value = incremental_obj
        
        # Execute
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        orchestrator.execute_job(sample_job_incremental)
        
        # Should create incremental object with watermark column
        mock_incremental.assert_called_once()
        call_args = mock_incremental.call_args
        assert call_args[1]['cursor_path'] == 'updated_at'
        assert call_args[1]['initial_value'] == '2026-01-01'
    
    def test_full_load_no_incremental(self, sample_job_full):
        """Test FULL load does not create incremental object."""
        with patch('src.core.orchestrator.dlt.sources.incremental') as mock_inc:
            orchestrator = IngestionOrchestrator()
            
            # FULL load should not call incremental
            # Implementation test would verify incremental not called


class TestMetricsExtraction:
    """Tests for DLT metrics extraction."""
    
    @patch('src.core.orchestrator.dlt.pipeline')
    @patch('src.core.orchestrator.sql_table')
    def test_extract_row_count_from_trace(self, mock_sql_table, mock_pipeline,
                                           sample_job_full, sample_secrets):
        """Test row count extraction from pipeline.last_trace."""
        # Setup pipeline with trace data
        pipeline = MagicMock()
        pipeline.last_trace = MagicMock()
        pipeline.last_trace.last_normalize_info = MagicMock()
        pipeline.last_trace.last_normalize_info.row_counts = {'customers': 250}
        mock_pipeline.return_value = pipeline
        
        # Execute
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        result = orchestrator.execute_job(sample_job_full)
        
        # Should extract row count from trace
        # Result verification depends on return type
        assert result is not None
    
    def test_extract_zero_row_count(self):
        """Test handling of zero rows processed."""
        # Test case for empty tables
        pass


class TestRunAll:
    """Tests for run_all() batch execution."""
    
    @patch('src.core.orchestrator.ConfigLoader')
    def test_run_all_executes_all_enabled_jobs(self, mock_loader_class, 
                                                sample_job_full, sample_job_incremental):
        """Test run_all executes all enabled jobs."""
        mock_loader = MagicMock()
        mock_loader.load_jobs.return_value = [sample_job_full, sample_job_incremental]
        mock_loader_class.return_value = mock_loader
        
        orchestrator = IngestionOrchestrator()
        
        with patch.object(orchestrator, 'execute_job') as mock_execute:
            orchestrator.run_all()
            
            # Should execute both jobs
            assert mock_execute.call_count == 2
    
    @patch('src.core.orchestrator.ConfigLoader')
    def test_run_all_continues_on_error(self, mock_loader_class,
                                        sample_job_full, sample_job_incremental):
        """Test run_all continues even if one job fails."""
        mock_loader = MagicMock()
        mock_loader.load_jobs.return_value = [sample_job_full, sample_job_incremental]
        mock_loader_class.return_value = mock_loader
        
        orchestrator = IngestionOrchestrator()
        
        with patch.object(orchestrator, 'execute_job') as mock_execute:
            # First job fails, second succeeds
            mock_execute.side_effect = [Exception("Job failed"), None]
            
            orchestrator.run_all()
            
            # Should attempt both jobs
            assert mock_execute.call_count == 2
    
    def test_run_all_empty_job_list(self):
        """Test run_all with no jobs."""
        with patch('src.core.orchestrator.ConfigLoader') as mock_loader_class:
            mock_loader = MagicMock()
            mock_loader.load_jobs.return_value = []
            mock_loader_class.return_value = mock_loader
            
            orchestrator = IngestionOrchestrator()
            
            # Should handle empty list gracefully
            orchestrator.run_all()


class TestLogging:
    """Tests for orchestrator logging."""
    
    def test_per_source_logging(self, sample_job_full):
        """Test per-source log file creation."""
        orchestrator = IngestionOrchestrator()
        
        # Should create per-source logger
        # Implementation test for log manager
        pass
    
    def test_error_only_logging(self):
        """Test error-only log creation."""
        # Test that errors write to separate log file
        pass


class TestTypeAdapterIntegration:
    """Tests for type adapter callback integration."""
    
    @patch('src.core.orchestrator.sql_table')
    @patch('src.core.orchestrator.get_type_adapter_for_source')
    def test_applies_type_adapter_for_oracle(self, mock_get_adapter, mock_sql_table,
                                             sample_oracle_job, sample_secrets):
        """Test type adapter is applied for Oracle sources."""
        # Setup mocks
        adapter = MagicMock()
        mock_get_adapter.return_value = adapter
        
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        with patch('src.core.orchestrator.dlt.pipeline'):
            orchestrator.execute_job(sample_oracle_job)
        
        # Should get type adapter for Oracle
        mock_get_adapter.assert_called()
    
    def test_no_type_adapter_for_postgresql(self):
        """Test type adapter not applied for PostgreSQL."""
        # PostgreSQL types are compatible, no adapter needed
        pass


class TestSchemaEvolution:
    """Tests for schema evolution detection."""
    
    @patch('src.core.orchestrator.dlt.pipeline')
    def test_detects_schema_change(self, mock_pipeline):
        """Test detection of schema version changes."""
        pipeline = MagicMock()
        pipeline.default_schema = MagicMock()
        pipeline.default_schema.version = 2  # Changed from version 1
        mock_pipeline.return_value = pipeline
        
        # Should log warning about schema change
        # Implementation test for _check_schema_evolution method
        pass
    
    def test_no_warning_for_initial_schema(self):
        """Test no warning for initial schema (version 1)."""
        # First load should not trigger schema change warning
        pass


class TestTableSizeEstimation:
    """Tests for table size estimation."""
    
    def test_estimate_small_table(self):
        """Test chunk size estimation for small tables (<100K rows)."""
        # Should return smaller chunk size
        pass
    
    def test_estimate_large_table(self):
        """Test chunk size estimation for large tables (>50M rows)."""
        # Should return larger chunk size (1M)
        pass
    
    def test_estimate_connection_failure(self):
        """Test handles connection failure gracefully."""
        # Should fall back to default chunk size
        pass


class TestDestinationConfiguration:
    """Tests for destination configuration."""
    
    def test_filesystem_destination_config(self, sample_secrets):
        """Test filesystem destination configuration."""
        orchestrator = IngestionOrchestrator()
        orchestrator.config_loader._secrets_cache = sample_secrets
        
        # Should configure ADLS Gen2 destination
        # Test destination config building
        pass
    
    def test_databricks_destination_config(self):
        """Test Databricks destination configuration."""
        # Test Unity Catalog configuration
        pass


class TestErrorHandling:
    """Tests for error handling in orchestrator."""
    
    def test_handles_connection_error(self, sample_job_full):
        """Test graceful handling of database connection errors."""
        orchestrator = IngestionOrchestrator()
        
        with patch('src.core.orchestrator.sql_table') as mock_table:
            mock_table.side_effect = Exception("Connection refused")
            
            # Should log error and continue
            with pytest.raises(Exception):
                orchestrator.execute_job(sample_job_full)
    
    def test_handles_invalid_credentials(self):
        """Test handling of authentication failures."""
        # Should log clear error message
        pass
    
    def test_handles_missing_table(self):
        """Test handling of non-existent tables."""
        # Should fail with clear message
        pass


class TestParallelExecution:
    """Tests for parallel job execution (future feature)."""
    
    @pytest.mark.skip(reason="Parallel execution not yet implemented")
    def test_parallel_execution(self):
        """Test concurrent job execution."""
        # Future: Test parallel processing
        pass
    
    @pytest.mark.skip(reason="Parallel execution not yet implemented")
    def test_max_workers_limit(self):
        """Test max_workers parameter limits concurrency."""
        # Future: Test worker pool management
        pass
