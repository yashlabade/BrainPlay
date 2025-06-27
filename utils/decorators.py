"""
Decorators Module
Demonstrates various decorator patterns, closures, and functional programming concepts.
Enhanced with session-aware logging.
"""

import time
import functools
import logging
from typing import Callable

logger = logging.getLogger(__name__)


def timer(func: Callable) -> Callable:
    """
    Decorator to measure function execution time.
    Demonstrates basic decorator pattern and closure.
    
    Usage:
        @timer
        def my_function():
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
    
    return wrapper


def async_timer(func: Callable) -> Callable:
    """
    Async version of timer decorator.
    Demonstrates async decorator patterns.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.4f} seconds")
    
    return wrapper


def log_calls(level: int = logging.INFO, include_args: bool = False, include_result: bool = False):
    """
    Decorator to log function calls with configurable options.
    Demonstrates parameterized decorators and closure variables.
    
    Args:
        level: Logging level to use
        include_args: Whether to log function arguments
        include_result: Whether to log function return value
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Prepare log message
            log_parts = [f"Calling {func.__name__}"]
            
            if include_args and (args or kwargs):
                args_str = ", ".join([repr(arg) for arg in args])
                kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
                all_args = [args_str, kwargs_str] if args_str and kwargs_str else [args_str or kwargs_str]
                log_parts.append(f"with args: ({', '.join(filter(None, all_args))})")
            
            logger.log(level, " ".join(log_parts))
            
            try:
                result = func(*args, **kwargs)
                
                if include_result:
                    logger.log(level, f"{func.__name__} returned: {repr(result)}")
                
                return result
            except Exception as e:
                logger.log(logging.ERROR, f"{func.__name__} raised {type(e).__name__}: {e}")
                raise
        
        return wrapper
    return decorator


def session_aware_log(func: Callable) -> Callable:
    """
    Decorator to add session context to log messages.
    Demonstrates context-aware logging.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Try to extract session info from args
        session_info = ""
        if args and hasattr(args[0], 'session_id'):
            session_info = f"[Session: {args[0].session_id[:8]}...] "
        elif args and hasattr(args[0], 'player'):
            session_info = f"[Player: {args[0].player.name}] "
        
        logger.info(f"{session_info}Executing {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{session_info}{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{session_info}{func.__name__} failed: {e}")
            raise
    
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator to retry function execution on failure.
    Demonstrates advanced decorator patterns and error handling.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each attempt
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise
                    
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}. Retrying in {current_delay:.1f}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


# Example usage and testing
if __name__ == "__main__":
    """
    Module testing and demonstration.
    Shows various decorator patterns and their usage.
    """
    
    print("Testing Decorators...")
    
    # Test timer decorator
    @timer
    def slow_function():
        time.sleep(0.1)
        return "Done"
    
    result = slow_function()
    print(f"Timer test result: {result}")
    
    # Test log_calls decorator
    @log_calls(include_args=True, include_result=True)
    def add_numbers(a, b):
        return a + b
    
    result = add_numbers(5, 3)
    print(f"Add numbers result: {result}")
    
    # Test session aware logging
    class MockGame:
        def __init__(self):
            self.session_id = "test-session-123"
        
        @session_aware_log
        def play_round(self):
            return "Round played"
    
    game = MockGame()
    result = game.play_round()
    print(f"Session aware test result: {result}")