"""
Context Managers Module
Demonstrates context manager patterns, resource management, and the 'with' statement.
Enhanced with session tracking.
"""

import time
import logging
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)


class GameSession:
    """
    Context manager for game sessions with enhanced tracking.
    Demonstrates class-based context manager with resource management.
    """
    
    def __init__(self, session_name: str, log_performance: bool = True):
        self.session_name = session_name
        self.log_performance = log_performance
        self.start_time = None
        self.end_time = None
        self.session_data = {}
        self.errors = []
    
    def __enter__(self):
        """Enter the context - setup resources."""
        self.start_time = time.time()
        logger.info(f"Starting game session: {self.session_name}")
        
        # Initialize session data
        self.session_data = {
            'session_name': self.session_name,
            'start_time': self.start_time,
            'status': 'active'
        }
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context - cleanup resources."""
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        # Update session data
        self.session_data.update({
            'end_time': self.end_time,
            'duration': duration,
            'status': 'completed' if exc_type is None else 'error'
        })
        
        if exc_type is not None:
            self.errors.append({
                'type': exc_type.__name__,
                'message': str(exc_val),
                'traceback': str(exc_tb)
            })
            self.session_data['errors'] = self.errors
            logger.error(f"Game session {self.session_name} ended with error: {exc_val}")
        else:
            logger.info(f"Game session {self.session_name} completed successfully")
        
        if self.log_performance:
            logger.info(f"Session duration: {duration:.3f} seconds")
        
        # Don't suppress exceptions
        return False
    
    def add_data(self, key: str, value):
        """Add data to the session context."""
        self.session_data[key] = value
    
    def get_data(self, key: str, default=None):
        """Get data from the session context."""
        return self.session_data.get(key, default)


@contextmanager
def game_session(session_name: str, log_performance: bool = True) -> Generator[GameSession, None, None]:
    """
    Function-based context manager for game sessions.
    Demonstrates @contextmanager decorator usage.
    """
    session = GameSession(session_name, log_performance)
    try:
        yield session.__enter__()
    except Exception as e:
        session.__exit__(type(e), e, e.__traceback__)
        raise
    else:
        session.__exit__(None, None, None)


class PerformanceMonitor:
    """
    Context manager for performance monitoring with session awareness.
    Demonstrates timing and resource usage tracking.
    """
    
    def __init__(self, operation_name: str, log_results: bool = True):
        self.operation_name = operation_name
        self.log_results = log_results
        self.start_time = None
        self.end_time = None
        self.metrics = {}
    
    def __enter__(self):
        """Start performance monitoring."""
        self.start_time = time.perf_counter()
        logger.debug(f"Started monitoring: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End performance monitoring and log results."""
        self.end_time = time.perf_counter()
        duration = self.end_time - self.start_time
        
        # Store metrics
        self.metrics = {
            'operation': self.operation_name,
            'duration': duration,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'success': exc_type is None
        }
        
        if exc_type is not None:
            self.metrics['error'] = {
                'type': exc_type.__name__,
                'message': str(exc_val)
            }
        
        # Log results
        if self.log_results:
            status = "completed" if exc_type is None else "failed"
            log_msg = f"Operation {self.operation_name} {status} in {duration:.4f}s"
            
            if exc_type is None:
                logger.info(log_msg)
            else:
                logger.error(f"{log_msg} with error: {exc_val}")
        
        return False  # Don't suppress exceptions
    
    def get_metrics(self) -> dict:
        """Get performance metrics."""
        return self.metrics.copy()


@contextmanager
def performance_monitor(operation_name: str, log_results: bool = True):
    """Function-based performance monitoring context manager."""
    monitor = PerformanceMonitor(operation_name, log_results)
    try:
        yield monitor.__enter__()
    except Exception as e:
        monitor.__exit__(type(e), e, e.__traceback__)
        raise
    else:
        monitor.__exit__(None, None, None)


# Example usage and testing
if __name__ == "__main__":
    """
    Module testing and demonstration.
    Shows various context manager patterns.
    """
    
    print("Testing Context Managers...")
    
    # Test game session
    with game_session("test_session") as session:
        session.add_data("test_key", "test_value")
        time.sleep(0.1)  # Simulate work
        print(f"Session data: {session.get_data('test_key')}")
    
    # Test performance monitoring
    with performance_monitor("test_operation") as monitor:
        time.sleep(0.05)  # Simulate work
        result = sum(range(1000))
    
    print(f"Performance metrics: {monitor.get_metrics()}")
    
    print("Context manager test completed!")