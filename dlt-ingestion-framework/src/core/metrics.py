"""
Metrics Collector - Production monitoring and observability hooks.

Collects pipeline metrics for monitoring dashboards, alerting,
and performance optimization.
"""
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class Metric:
    """A single metric data point."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'value': self.value,
            'type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags
        }


@dataclass
class PipelineMetrics:
    """Aggregated metrics for a pipeline execution."""
    pipeline_name: str
    job_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    rows_processed: int = 0
    bytes_processed: int = 0
    chunk_count: int = 0
    retry_count: int = 0
    error_count: int = 0
    schema_version: int = 1
    source_type: str = ""
    destination_type: str = ""
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
    
    @property
    def rows_per_second(self) -> float:
        """Calculate ingestion throughput."""
        duration = self.duration_seconds
        return self.rows_processed / duration if duration > 0 else 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'pipeline_name': self.pipeline_name,
            'job_name': self.job_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'duration_seconds': round(self.duration_seconds, 2),
            'rows_processed': self.rows_processed,
            'bytes_processed': self.bytes_processed,
            'rows_per_second': round(self.rows_per_second, 2),
            'chunk_count': self.chunk_count,
            'retry_count': self.retry_count,
            'error_count': self.error_count,
            'schema_version': self.schema_version,
            'source_type': self.source_type,
            'destination_type': self.destination_type,
            'custom_metrics': self.custom_metrics
        }


class MetricsCollector:
    """Collects and aggregates pipeline metrics.
    
    Features:
    - Real-time metric collection during pipeline execution
    - Aggregation for batch summary reports
    - Export to various monitoring systems (logs, JSON, custom hooks)
    - Performance indicators and health scoring
    """
    
    def __init__(self, pipeline_name: str = "dlt_ingestion"):
        """Initialize metrics collector.
        
        Args:
            pipeline_name: Name of the pipeline for metric tagging
        """
        self.pipeline_name = pipeline_name
        self._metrics: List[Metric] = []
        self._active_jobs: Dict[str, PipelineMetrics] = {}
        self._completed_jobs: List[PipelineMetrics] = []
        self._hooks: List[callable] = []
    
    def register_hook(self, hook: callable):
        """Register a custom metric hook.
        
        Hook signature: hook(metrics: PipelineMetrics) -> None
        
        Args:
            hook: Callable to receive metrics updates
        """
        self._hooks.append(hook)
    
    def start_job(self, job_name: str, source_type: str, 
                  destination_type: str = "adls_gen2") -> PipelineMetrics:
        """Start tracking a new job.
        
        Args:
            job_name: Unique job identifier
            source_type: Type of data source
            destination_type: Type of destination
        
        Returns:
            PipelineMetrics object for this job
        """
        metrics = PipelineMetrics(
            pipeline_name=self.pipeline_name,
            job_name=job_name,
            start_time=datetime.now(),
            source_type=source_type,
            destination_type=destination_type
        )
        self._active_jobs[job_name] = metrics
        
        logger.debug(f"[METRICS] Started tracking job: {job_name}")
        return metrics
    
    def update_job(self, job_name: str, **kwargs):
        """Update job metrics.
        
        Args:
            job_name: Job identifier
            **kwargs: Metric updates (rows_processed, etc.)
        """
        if job_name not in self._active_jobs:
            logger.warning(f"[METRICS] Job not found for update: {job_name}")
            return
        
        metrics = self._active_jobs[job_name]
        
        for key, value in kwargs.items():
            if hasattr(metrics, key):
                setattr(metrics, key, value)
            else:
                metrics.custom_metrics[key] = value
    
    def complete_job(self, job_name: str, status: str, 
                     rows_processed: int = 0, error_message: str = None):
        """Mark job as completed and finalize metrics.
        
        Args:
            job_name: Job identifier
            status: Final status (SUCCESS, FAILED, ERROR)
            rows_processed: Total rows processed
            error_message: Error message if failed
        """
        if job_name not in self._active_jobs:
            logger.warning(f"[METRICS] Job not found for completion: {job_name}")
            return
        
        metrics = self._active_jobs.pop(job_name)
        metrics.end_time = datetime.now()
        metrics.status = status
        metrics.rows_processed = rows_processed
        
        if error_message:
            metrics.custom_metrics['error_message'] = error_message
        
        self._completed_jobs.append(metrics)
        
        # Call registered hooks
        for hook in self._hooks:
            try:
                hook(metrics)
            except Exception as e:
                logger.warning(f"[METRICS] Hook failed: {e}")
        
        # Log summary
        self._log_job_summary(metrics)
    
    def _log_job_summary(self, metrics: PipelineMetrics):
        """Log job summary metrics."""
        status_emoji = "[OK]" if metrics.status == "SUCCESS" else "[FAILED]"
        
        logger.info(
            f"[METRICS] {status_emoji} {metrics.job_name}: "
            f"{metrics.rows_processed:,} rows in {metrics.duration_seconds:.2f}s "
            f"({metrics.rows_per_second:.0f} rows/sec)"
        )
        
        if metrics.retry_count > 0:
            logger.info(f"  Retries: {metrics.retry_count}")
        if metrics.error_count > 0:
            logger.warning(f"  Errors: {metrics.error_count}")
    
    def record_metric(self, name: str, value: float, 
                      metric_type: MetricType = MetricType.GAUGE,
                      tags: Dict[str, str] = None):
        """Record a custom metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Optional tags for the metric
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {}
        )
        self._metrics.append(metric)
    
    def increment_counter(self, name: str, value: float = 1, 
                         tags: Dict[str, str] = None):
        """Increment a counter metric.
        
        Args:
            name: Counter name
            value: Amount to increment
            tags: Optional tags
        """
        self.record_metric(name, value, MetricType.COUNTER, tags)
    
    def get_summary(self) -> Dict:
        """Get summary of all collected metrics.
        
        Returns:
            Dictionary with aggregated metrics
        """
        total_rows = sum(m.rows_processed for m in self._completed_jobs)
        total_duration = sum(m.duration_seconds for m in self._completed_jobs)
        success_count = sum(1 for m in self._completed_jobs if m.status == "SUCCESS")
        failed_count = len(self._completed_jobs) - success_count
        
        return {
            'pipeline_name': self.pipeline_name,
            'total_jobs': len(self._completed_jobs),
            'successful_jobs': success_count,
            'failed_jobs': failed_count,
            'success_rate': success_count / len(self._completed_jobs) if self._completed_jobs else 0,
            'total_rows_processed': total_rows,
            'total_duration_seconds': round(total_duration, 2),
            'average_rows_per_second': round(total_rows / total_duration if total_duration > 0 else 0, 2),
            'jobs': [m.to_dict() for m in self._completed_jobs]
        }
    
    def export_json(self, filepath: str):
        """Export metrics to JSON file.
        
        Args:
            filepath: Path to output file
        """
        summary = self.get_summary()
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"[METRICS] Exported to {filepath}")
    
    def get_health_score(self) -> float:
        """Calculate overall pipeline health score (0-100).
        
        Returns:
            Health score based on success rate and performance
        """
        if not self._completed_jobs:
            return 100.0
        
        # Success rate (60% weight)
        success_count = sum(1 for m in self._completed_jobs if m.status == "SUCCESS")
        success_rate = success_count / len(self._completed_jobs)
        
        # Retry rate (20% weight)
        total_retries = sum(m.retry_count for m in self._completed_jobs)
        retry_penalty = min(total_retries * 2, 20)  # Max 20 point penalty
        
        # Error rate (20% weight)
        total_errors = sum(m.error_count for m in self._completed_jobs)
        error_penalty = min(total_errors * 5, 20)  # Max 20 point penalty
        
        score = (success_rate * 60) + (20 - retry_penalty) + (20 - error_penalty)
        return max(0, min(100, score))


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector(pipeline_name: str = "dlt_ingestion") -> MetricsCollector:
    """Get or create global metrics collector.
    
    Args:
        pipeline_name: Name of the pipeline
    
    Returns:
        MetricsCollector instance
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector(pipeline_name)
    return _global_collector
