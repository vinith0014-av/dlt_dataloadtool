"""
Retry Handler - Production-grade fault tolerance with exponential backoff.

Provides retry logic, circuit breaker pattern, and graceful error handling
for robust data ingestion pipelines.
"""
import logging
import time
import functools
from typing import Callable, Optional, Any, Type, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class RetryConfig:
    """Configuration for retry behavior.
    
    Attributes:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        exponential_base: Multiplier for exponential backoff
        jitter: Add randomness to delay (0.0-1.0)
        retryable_exceptions: Tuple of exception types to retry
    """
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: float = 0.1
    retryable_exceptions: Tuple[Type[Exception], ...] = (
        ConnectionError,
        TimeoutError,
        OSError,
    )


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker.
    
    Attributes:
        failure_threshold: Number of failures before opening circuit
        success_threshold: Number of successes to close circuit
        timeout: Time to wait before testing recovery (seconds)
    """
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 30.0


class CircuitBreaker:
    """Circuit breaker pattern implementation.
    
    Prevents cascade failures by temporarily disabling calls
    to failing services.
    """
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        """Initialize circuit breaker.
        
        Args:
            name: Identifier for this circuit breaker
            config: Circuit breaker configuration
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if timeout has elapsed
                if self._last_failure_time:
                    elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                    if elapsed >= self.config.timeout:
                        self._state = CircuitState.HALF_OPEN
                        logger.info(f"[CIRCUIT BREAKER] {self.name}: OPEN -> HALF_OPEN")
            return self._state
    
    def record_success(self):
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    logger.info(f"[CIRCUIT BREAKER] {self.name}: HALF_OPEN -> CLOSED")
            elif self._state == CircuitState.CLOSED:
                self._failure_count = 0
    
    def record_failure(self):
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._success_count = 0
                logger.warning(f"[CIRCUIT BREAKER] {self.name}: HALF_OPEN -> OPEN")
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(f"[CIRCUIT BREAKER] {self.name}: CLOSED -> OPEN")
    
    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        return self.state != CircuitState.OPEN


class RetryHandler:
    """Handles retry logic with exponential backoff.
    
    Features:
    - Exponential backoff with jitter
    - Configurable retryable exceptions
    - Optional circuit breaker integration
    - Detailed logging of retry attempts
    """
    
    def __init__(self, config: RetryConfig = None, 
                 circuit_breaker: CircuitBreaker = None):
        """Initialize retry handler.
        
        Args:
            config: Retry configuration
            circuit_breaker: Optional circuit breaker instance
        """
        self.config = config or RetryConfig()
        self.circuit_breaker = circuit_breaker
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next retry attempt.
        
        Args:
            attempt: Current attempt number (1-based)
        
        Returns:
            Delay in seconds
        """
        import random
        
        delay = self.config.initial_delay * (
            self.config.exponential_base ** (attempt - 1)
        )
        delay = min(delay, self.config.max_delay)
        
        # Add jitter
        if self.config.jitter > 0:
            jitter_range = delay * self.config.jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0.1, delay)  # Minimum 100ms
    
    def should_retry(self, exception: Exception) -> bool:
        """Check if exception is retryable.
        
        Args:
            exception: The exception that occurred
        
        Returns:
            True if should retry
        """
        # Check circuit breaker first
        if self.circuit_breaker and not self.circuit_breaker.allow_request():
            logger.warning("[RETRY] Circuit breaker is OPEN - not retrying")
            return False
        
        # Check if exception type is retryable
        return isinstance(exception, self.config.retryable_exceptions)
    
    def execute_with_retry(self, func: Callable[..., Any], 
                           *args, **kwargs) -> Any:
        """Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        
        Returns:
            Result of function execution
        
        Raises:
            Exception: Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(1, self.config.max_retries + 1):
            try:
                # Check circuit breaker
                if self.circuit_breaker and not self.circuit_breaker.allow_request():
                    raise RuntimeError(
                        f"Circuit breaker {self.circuit_breaker.name} is OPEN"
                    )
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Record success
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()
                
                if attempt > 1:
                    logger.info(f"[RETRY] Succeeded on attempt {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # Record failure
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                
                # Check if should retry
                if not self.should_retry(e) or attempt >= self.config.max_retries:
                    logger.error(
                        f"[RETRY] Failed after {attempt} attempts: {type(e).__name__}: {e}"
                    )
                    raise
                
                # Calculate delay
                delay = self.calculate_delay(attempt)
                
                logger.warning(
                    f"[RETRY] Attempt {attempt}/{self.config.max_retries} failed: "
                    f"{type(e).__name__}: {e}. Retrying in {delay:.1f}s..."
                )
                
                time.sleep(delay)
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception


def with_retry(config: RetryConfig = None, 
               circuit_breaker_name: str = None):
    """Decorator for adding retry logic to functions.
    
    Args:
        config: Retry configuration
        circuit_breaker_name: Optional circuit breaker name
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @with_retry(RetryConfig(max_retries=5))
        def fetch_data():
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Create circuit breaker if name provided
        cb = CircuitBreaker(circuit_breaker_name) if circuit_breaker_name else None
        handler = RetryHandler(config, cb)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return handler.execute_with_retry(func, *args, **kwargs)
        
        return wrapper
    return decorator


# Database-specific retryable exceptions
DATABASE_RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    # Add sqlalchemy-specific exceptions at runtime
)

# API-specific retryable exceptions  
API_RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    # Add requests-specific exceptions at runtime
)


def get_database_retry_config() -> RetryConfig:
    """Get retry configuration optimized for database operations."""
    return RetryConfig(
        max_retries=3,
        initial_delay=2.0,
        max_delay=30.0,
        exponential_base=2.0,
        jitter=0.2,
        retryable_exceptions=DATABASE_RETRYABLE_EXCEPTIONS
    )


def get_api_retry_config() -> RetryConfig:
    """Get retry configuration optimized for API operations."""
    return RetryConfig(
        max_retries=5,
        initial_delay=1.0,
        max_delay=60.0,
        exponential_base=2.0,
        jitter=0.3,
        retryable_exceptions=API_RETRYABLE_EXCEPTIONS
    )
