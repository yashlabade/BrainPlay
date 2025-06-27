"""
Unit Tests for Custom Exceptions
Demonstrates exception testing, error handling validation, and edge cases.
"""

import unittest
from unittest.mock import patch, MagicMock
import logging

# Import modules to test
from exceptions import (
    BrainPlayException, GameExitException, InvalidInputException,
    QuestionGenerationException, ScoreException, FileOperationException,
    NetworkException, ConfigurationException, ExceptionFactory,
    handle_exceptions, safe_execute, ExceptionContext, chain_exception
)


class TestBrainPlayException(unittest.TestCase):
    """
    Test cases for base BrainPlayException class.
    Demonstrates testing exception hierarchies and custom behavior.
    """
    
    def test_basic_exception_creation(self):
        """Test basic exception creation and attributes."""
        message = "Test error message"
        exception = BrainPlayException(message)
        
        self.assertEqual(str(exception), f"[BRAINPLAYEXCEPTION] {message}")
        self.assertEqual(exception.message, message)
        self.assertEqual(exception.error_code, "BRAINPLAYEXCEPTION")
        self.assertEqual(exception.details, {})
    
    def test_exception_with_error_code(self):
        """Test exception creation with custom error code."""
        message = "Custom error"
        error_code = "CUSTOM_ERROR"
        exception = BrainPlayException(message, error_code=error_code)
        
        self.assertEqual(exception.error_code, error_code)
        self.assertEqual(str(exception), f"[{error_code}] {message}")
    
    def test_exception_with_details(self):
        """Test exception creation with additional details."""
        message = "Error with details"
        details = {"user_id": 123, "action": "test"}
        exception = BrainPlayException(message, details=details)
        
        self.assertEqual(exception.details, details)
    
    def test_exception_repr(self):
        """Test exception string representation."""
        exception = BrainPlayException("Test", error_code="TEST")
        expected_repr = "BrainPlayException(message='Test', error_code='TEST')"
        self.assertEqual(repr(exception), expected_repr)
    
    def test_exception_to_dict(self):
        """Test exception serialization to dictionary."""
        message = "Serialization test"
        error_code = "SERIALIZE_TEST"
        details = {"key": "value"}
        
        exception = BrainPlayException(message, error_code=error_code, details=details)
        exception_dict = exception.to_dict()
        
        expected_dict = {
            'exception_type': 'BrainPlayException',
            'message': message,
            'error_code': error_code,
            'details': details
        }
        
        self.assertEqual(exception_dict, expected_dict)
    
    @patch('exceptions.logger')
    def test_exception_logging(self, mock_logger):
        """Test that exceptions are logged when created."""
        message = "Logged error"
        BrainPlayException(message)
        
        # Should log error when exception is created
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args[0][0]
        self.assertIn(message, call_args)


class TestSpecificExceptions(unittest.TestCase):
    """
    Test cases for specific exception types.
    Demonstrates testing specialized exception behavior.
    """
    
    def test_game_exit_exception(self):
        """Test GameExitException specific behavior."""
        exit_reason = "user_quit"
        exception = GameExitException(exit_reason=exit_reason)
        
        self.assertEqual(exception.error_code, "GAME_EXIT")
        self.assertEqual(exception.exit_reason, exit_reason)
        self.assertEqual(exception.details['exit_reason'], exit_reason)
    
    def test_invalid_input_exception(self):
        """Test InvalidInputException with input context."""
        message = "Invalid number format"
        input_value = "abc123"
        expected_format = "integer"
        
        exception = InvalidInputException(
            message, 
            input_value=input_value, 
            expected_format=expected_format
        )
        
        self.assertEqual(exception.error_code, "INVALID_INPUT")
        self.assertEqual(exception.input_value, input_value)
        self.assertEqual(exception.expected_format, expected_format)
        self.assertEqual(exception.details['input_value'], str(input_value))
        self.assertEqual(exception.details['expected_format'], expected_format)
    
    def test_question_generation_exception(self):
        """Test QuestionGenerationException with context."""
        message = "Failed to generate math question"
        question_type = "algebra"
        difficulty = "hard"
        
        exception = QuestionGenerationException(
            message,
            question_type=question_type,
            difficulty=difficulty
        )
        
        self.assertEqual(exception.error_code, "QUESTION_GENERATION_FAILED")
        self.assertEqual(exception.question_type, question_type)
        self.assertEqual(exception.difficulty, difficulty)
    
    def test_score_exception(self):
        """Test ScoreException with score context."""
        message = "Invalid score operation"
        current_score = 42
        attempted_operation = "subtract_negative"
        
        exception = ScoreException(
            message,
            current_score=current_score,
            attempted_operation=attempted_operation
        )
        
        self.assertEqual(exception.error_code, "SCORE_ERROR")
        self.assertEqual(exception.current_score, current_score)
        self.assertEqual(exception.attempted_operation, attempted_operation)
    
    def test_file_operation_exception(self):
        """Test FileOperationException with file context."""
        message = "Cannot write to file"
        file_path = "/path/to/file.txt"
        operation = "write"
        
        exception = FileOperationException(
            message,
            file_path=file_path,
            operation=operation
        )
        
        self.assertEqual(exception.error_code, "FILE_OPERATION_FAILED")
        self.assertEqual(exception.file_path, file_path)
        self.assertEqual(exception.operation, operation)
    
    def test_network_exception(self):
        """Test NetworkException with network context."""
        message = "API request failed"
        url = "https://api.example.com/data"
        status_code = 404
        timeout = True
        
        exception = NetworkException(
            message,
            url=url,
            status_code=status_code,
            timeout=timeout
        )
        
        self.assertEqual(exception.error_code, "NETWORK_ERROR")
        self.assertEqual(exception.url, url)
        self.assertEqual(exception.status_code, status_code)
        self.assertEqual(exception.timeout, timeout)
    
    def test_configuration_exception(self):
        """Test ConfigurationException with config context."""
        message = "Invalid configuration value"
        config_key = "max_retries"
        config_value = -1
        
        exception = ConfigurationException(
            message,
            config_key=config_key,
            config_value=config_value
        )
        
        self.assertEqual(exception.error_code, "CONFIGURATION_ERROR")
        self.assertEqual(exception.config_key, config_key)
        self.assertEqual(exception.config_value, config_value)


class TestExceptionFactory(unittest.TestCase):
    """
    Test cases for ExceptionFactory.
    Demonstrates testing factory patterns for exceptions.
    """
    
    def test_create_input_exception(self):
        """Test creating input validation exceptions."""
        input_value = "invalid_number"
        expected_type = int
        
        exception = ExceptionFactory.create_input_exception(
            input_value, 
            expected_type=expected_type
        )
        
        self.assertIsInstance(exception, InvalidInputException)
        self.assertEqual(exception.input_value, input_value)
        self.assertEqual(exception.expected_format, "int")
        self.assertIn("expected int", exception.message)
    
    def test_create_input_exception_custom_message(self):
        """Test creating input exception with custom message."""
        custom_message = "Custom validation error"
        input_value = "test"
        
        exception = ExceptionFactory.create_input_exception(
            input_value,
            custom_message=custom_message
        )
        
        self.assertEqual(exception.message, custom_message)
    
    def test_create_file_exception(self):
        """Test creating file operation exceptions."""
        file_path = "/tmp/test.txt"
        operation = "read"
        original_exception = FileNotFoundError("File not found")
        
        exception = ExceptionFactory.create_file_exception(
            file_path,
            operation,
            original_exception
        )
        
        self.assertIsInstance(exception, FileOperationException)
        self.assertEqual(exception.file_path, file_path)
        self.assertEqual(exception.operation, operation)
        self.assertIn("File not found", exception.message)
    
    def test_create_network_exception_timeout(self):
        """Test creating network exception for timeout."""
        url = "https://slow-api.com"
        operation = "fetching data"
        
        exception = ExceptionFactory.create_network_exception(
            url,
            operation,
            timeout=True
        )
        
        self.assertIsInstance(exception, NetworkException)
        self.assertEqual(exception.url, url)
        self.assertTrue(exception.timeout)
        self.assertIn("Timeout", exception.message)
    
    def test_create_network_exception_status_code(self):
        """Test creating network exception with status code."""
        url = "https://api.com/endpoint"
        operation = "POST request"
        status_code = 500
        
        exception = ExceptionFactory.create_network_exception(
            url,
            operation,
            status_code=status_code
        )
        
        self.assertEqual(exception.status_code, status_code)
        self.assertIn("HTTP 500", exception.message)


class TestExceptionDecorators(unittest.TestCase):
    """
    Test cases for exception handling decorators.
    Demonstrates testing decorator patterns and error handling.
    """
    
    def test_handle_exceptions_decorator_success(self):
        """Test handle_exceptions decorator with successful function."""
        @handle_exceptions(default_return="error")
        def successful_function():
            return "success"
        
        result = successful_function()
        self.assertEqual(result, "success")
    
    def test_handle_exceptions_decorator_brainplay_exception(self):
        """Test handle_exceptions decorator with BrainPlay exception."""
        @handle_exceptions(default_return="handled")
        def failing_function():
            raise InvalidInputException("Test error")
        
        result = failing_function()
        self.assertEqual(result, "handled")
    
    def test_handle_exceptions_decorator_generic_exception(self):
        """Test handle_exceptions decorator with generic exception."""
        @handle_exceptions(default_return="handled")
        def failing_function():
            raise ValueError("Generic error")
        
        result = failing_function()
        self.assertEqual(result, "handled")
    
    @patch('exceptions.logger')
    def test_handle_exceptions_logging(self, mock_logger):
        """Test that handle_exceptions decorator logs errors."""
        @handle_exceptions(default_return="handled", log_level=logging.WARNING)
        def failing_function():
            raise InvalidInputException("Test logging")
        
        failing_function()
        
        # Should log the exception
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        self.assertEqual(call_args[0][0], logging.WARNING)  # Log level
        self.assertIn("Test logging", call_args[0][1])  # Message


class TestSafeExecute(unittest.TestCase):
    """
    Test cases for safe_execute utility function.
    Demonstrates testing utility functions and error handling.
    """
    
    def test_safe_execute_success(self):
        """Test safe_execute with successful function."""
        def successful_function(x, y):
            return x + y
        
        success, result = safe_execute(successful_function, 2, 3)
        
        self.assertTrue(success)
        self.assertEqual(result, 5)
    
    def test_safe_execute_exception(self):
        """Test safe_execute with function that raises exception."""
        def failing_function():
            raise ValueError("Test error")
        
        success, result = safe_execute(failing_function)
        
        self.assertFalse(success)
        self.assertIsInstance(result, ValueError)
        self.assertEqual(str(result), "Test error")
    
    def test_safe_execute_with_args_kwargs(self):
        """Test safe_execute with arguments and keyword arguments."""
        def function_with_args(a, b, c=None):
            if c is None:
                raise ValueError("c is required")
            return a + b + c
        
        # Test with missing required argument
        success, result = safe_execute(function_with_args, 1, 2)
        self.assertFalse(success)
        self.assertIsInstance(result, ValueError)
        
        # Test with all arguments
        success, result = safe_execute(function_with_args, 1, 2, c=3)
        self.assertTrue(success)
        self.assertEqual(result, 6)


class TestExceptionContext(unittest.TestCase):
    """
    Test cases for ExceptionContext context manager.
    Demonstrates testing context managers and exception handling.
    """
    
    @patch('exceptions.logger')
    def test_exception_context_success(self, mock_logger):
        """Test ExceptionContext with successful operation."""
        with ExceptionContext("test operation") as ctx:
            result = 2 + 2
        
        self.assertFalse(ctx.exception_occurred)
        self.assertIsNone(ctx.exception)
        
        # Should log start and success
        self.assertEqual(mock_logger.debug.call_count, 2)
    
    @patch('exceptions.logger')
    def test_exception_context_with_exception(self, mock_logger):
        """Test ExceptionContext with exception (reraise=True)."""
        with self.assertRaises(ValueError):
            with ExceptionContext("test operation", reraise=True) as ctx:
                raise ValueError("Test error")
        
        self.assertTrue(ctx.exception_occurred)
        self.assertIsInstance(ctx.exception, ValueError)
    
    @patch('exceptions.logger')
    def test_exception_context_suppress_exception(self, mock_logger):
        """Test ExceptionContext with exception suppression."""
        with ExceptionContext("test operation", reraise=False) as ctx:
            raise ValueError("Suppressed error")
        
        self.assertTrue(ctx.exception_occurred)
        self.assertIsInstance(ctx.exception, ValueError)
        
        # Should log the error
        mock_logger.error.assert_called_once()
    
    def test_exception_context_default_return(self):
        """Test ExceptionContext with default return value."""
        default_value = "default"
        
        with ExceptionContext("test", reraise=False, default_return=default_value) as ctx:
            raise RuntimeError("Error")
        
        result = ctx.get_result()
        self.assertEqual(result, default_value)


class TestExceptionChaining(unittest.TestCase):
    """
    Test cases for exception chaining utilities.
    Demonstrates testing exception chaining and context preservation.
    """
    
    def test_chain_exception(self):
        """Test exception chaining functionality."""
        original_error = ValueError("Original error")
        new_message = "New error context"
        
        with self.assertRaises(BrainPlayException) as context:
            try:
                raise original_error
            except ValueError as e:
                chain_exception(e, new_message)
        
        chained_exception = context.exception
        self.assertEqual(chained_exception.message, new_message)
        self.assertIn("Original error", str(chained_exception.details))
        
        # Check exception chaining
        self.assertIs(chained_exception.__cause__, original_error)
    
    def test_chain_exception_custom_class(self):
        """Test exception chaining with custom exception class."""
        original_error = FileNotFoundError("File missing")
        new_message = "Configuration file error"
        
        with self.assertRaises(ConfigurationException) as context:
            try:
                raise original_error
            except FileNotFoundError as e:
                chain_exception(e, new_message, ConfigurationException)
        
        chained_exception = context.exception
        self.assertIsInstance(chained_exception, ConfigurationException)
        self.assertEqual(chained_exception.message, new_message)


class TestExceptionIntegration(unittest.TestCase):
    """
    Integration tests for exception system.
    Demonstrates testing exception handling in realistic scenarios.
    """
    
    def test_nested_exception_handling(self):
        """Test nested exception handling scenarios."""
        @handle_exceptions(default_return="outer_handled")
        def outer_function():
            @handle_exceptions(default_return="inner_handled")
            def inner_function():
                raise InvalidInputException("Inner error")
            
            result = inner_function()
            if result == "inner_handled":
                raise ScoreException("Outer error due to inner failure")
            return result
        
        result = outer_function()
        self.assertEqual(result, "outer_handled")
    
    def test_exception_context_with_multiple_operations(self):
        """Test exception context with multiple operations."""
        operations_completed = []
        
        with ExceptionContext("multi-operation", reraise=False) as ctx:
            operations_completed.append("op1")
            
            # This should not prevent subsequent operations
            if len(operations_completed) == 1:
                operations_completed.append("op2")
            
            # This will cause the exception
            raise RuntimeError("Multi-op error")
        
        self.assertTrue(ctx.exception_occurred)
        self.assertEqual(len(operations_completed), 2)
    
    def test_exception_factory_integration(self):
        """Test exception factory integration with other components."""
        # Simulate a file operation failure
        file_path = "/nonexistent/path/file.txt"
        operation = "read"
        
        try:
            # Simulate file operation
            with open(file_path, 'r') as f:
                content = f.read()
        except FileNotFoundError as e:
            # Use factory to create appropriate exception
            file_exception = ExceptionFactory.create_file_exception(
                file_path, operation, e
            )
            
            # Verify the created exception
            self.assertIsInstance(file_exception, FileOperationException)
            self.assertEqual(file_exception.file_path, file_path)
            self.assertEqual(file_exception.operation, operation)
            self.assertIn("FileNotFoundError", file_exception.message)


if __name__ == '__main__':
    """
    Run tests when module is executed directly.
    Demonstrates comprehensive exception testing.
    """
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestBrainPlayException,
        TestSpecificExceptions,
        TestExceptionFactory,
        TestExceptionDecorators,
        TestSafeExecute,
        TestExceptionContext,
        TestExceptionChaining,
        TestExceptionIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)