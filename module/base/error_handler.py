"""
Error handling utilities for ALAS
Provides error counting and threshold management for various operations
"""
from collections import defaultdict
from datetime import datetime, timedelta
from module.logger import logger
from module.exception import OcrParseError


class ErrorCounter:
    """Track consecutive errors with configurable thresholds"""
    
    def __init__(self, max_errors=3, reset_timeout=300):
        """
        Args:
            max_errors (int): Maximum consecutive errors before raising exception
            reset_timeout (int): Seconds after which error count resets
        """
        self.max_errors = max_errors
        self.reset_timeout = reset_timeout
        self._error_counts = defaultdict(int)
        self._last_error_time = {}
        self._error_messages = defaultdict(list)
    
    def record_error(self, error_type, message=None):
        """
        Record an error occurrence
        
        Args:
            error_type (str): Category of error (e.g. "ocr_duration", "ocr_commission")
            message (str): Optional error message for logging
            
        Returns:
            int: Current error count for this type
            
        Raises:
            ValueError: When max consecutive errors exceeded
        """
        now = datetime.now()
        
        # Reset counter if timeout exceeded
        if error_type in self._last_error_time:
            time_since_last = (now - self._last_error_time[error_type]).total_seconds()
            if time_since_last > self.reset_timeout:
                self.reset_errors(error_type)
                logger.info(f"Reset error counter for {error_type} after {time_since_last:.1f}s timeout")
        
        # Increment error count
        self._error_counts[error_type] += 1
        self._last_error_time[error_type] = now
        
        if message:
            self._error_messages[error_type].append(message)
            # Keep only last 10 messages
            self._error_messages[error_type] = self._error_messages[error_type][-10:]
        
        current_count = self._error_counts[error_type]
        logger.warning(f"Error #{current_count}/{self.max_errors} for {error_type}: {message or 'No details'}")
        
        # Raise exception if threshold exceeded
        if current_count >= self.max_errors:
            error_history = "\n".join(self._error_messages[error_type])
            if "ocr" in error_type.lower():
                raise OcrParseError(
                    f"Maximum consecutive OCR errors ({self.max_errors}) exceeded for {error_type}\n"
                    f"Recent errors:\n{error_history}"
                )
            else:
                raise ValueError(
                    f"Maximum consecutive errors ({self.max_errors}) exceeded for {error_type}\n"
                    f"Recent errors:\n{error_history}"
                )
        
        return current_count
    
    def record_success(self, error_type):
        """
        Record successful operation, resetting error counter
        
        Args:
            error_type (str): Category that succeeded
        """
        if error_type in self._error_counts and self._error_counts[error_type] > 0:
            logger.info(f"Operation succeeded for {error_type}, resetting error counter from {self._error_counts[error_type]}")
        self.reset_errors(error_type)
    
    def reset_errors(self, error_type):
        """Reset error tracking for specific type"""
        self._error_counts[error_type] = 0
        self._error_messages[error_type] = []
        if error_type in self._last_error_time:
            del self._last_error_time[error_type]
    
    def get_error_count(self, error_type):
        """Get current error count for type"""
        return self._error_counts.get(error_type, 0)


# Global error counter instance - will be initialized with config value
OCR_ERROR_COUNTER = None

def init_error_counter(config=None):
    """Initialize error counter with config value"""
    global OCR_ERROR_COUNTER
    max_retries = 3  # default
    if config and hasattr(config, 'Error_OcrMaxRetries'):
        max_retries = config.Error_OcrMaxRetries
    OCR_ERROR_COUNTER = ErrorCounter(max_errors=max_retries, reset_timeout=300)
    return OCR_ERROR_COUNTER

# Initialize with default for import time
init_error_counter()