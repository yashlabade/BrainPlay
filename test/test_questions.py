"""
Unit Tests for Question Generation
Demonstrates async testing, mocking, and comprehensive test coverage.
"""

import unittest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

# Import modules to test
from questions import (
    QuestionFactory, QuestionResult, NumberGuessGenerator,
    SquareRootGenerator, MathExpressionGenerator
)
from exceptions import QuestionGenerationException


class TestQuestionResult(unittest.TestCase):
    """
    Test cases for QuestionResult data class.
    Demonstrates testing data classes and validation logic.
    """
    
    def test_question_result_creation(self):
        """Test QuestionResult creation and attributes."""
        question = QuestionResult(
            text="What is 2+2?",
            answer=4,
            question_type="math",
            difficulty="normal"
        )
        
        self.assertEqual(question.text, "What is 2+2?")
        self.assertEqual(question.answer, 4)
        self.assertEqual(question.question_type, "math")
        self.assertEqual(question.difficulty, "normal")
    
    def test_check_answer_integer(self):
        """Test answer checking with integer answers."""
        question = QuestionResult("What is 5*5?", 25, "math", "normal")
        
        # Correct answers
        self.assertTrue(question.check_answer("25"))
        self.assertTrue(question.check_answer("25.0"))
        
        # Wrong answers
        self.assertFalse(question.check_answer("24"))
        self.assertFalse(question.check_answer("26"))
        self.assertFalse(question.check_answer("invalid"))
    
    def test_check_answer_float(self):
        """Test answer checking with float answers."""
        question = QuestionResult("What is sqrt(2)?", 1.414, "math", "normal")
        
        # Should allow small floating point errors
        self.assertTrue(question.check_answer("1.414"))
        self.assertTrue(question.check_answer("1.4141"))  # Close enough
        
        # Should reject significantly different answers
        self.assertFalse(question.check_answer("1.5"))
        self.assertFalse(question.check_answer("1.0"))
    
    def test_check_answer_string(self):
        """Test answer checking with string answers."""
        question = QuestionResult("What color?", "blue", "color", "easy")
        
        # Case insensitive matching
        self.assertTrue(question.check_answer("blue"))
        self.assertTrue(question.check_answer("BLUE"))
        self.assertTrue(question.check_answer("Blue"))
        self.assertTrue(question.check_answer(" blue "))  # Whitespace handling
        
        # Wrong answers
        self.assertFalse(question.check_answer("red"))
        self.assertFalse(question.check_answer(""))


class AsyncTestCase(unittest.TestCase):
    """
    Base class for async test cases.
    Demonstrates async testing setup patterns.
    """
    
    def setUp(self):
        """Set up async test environment."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
    
    def tearDown(self):
        """Clean up async test environment."""
        self.loop.close()
    
    def run_async(self, coro):
        """Helper method to run async functions in tests."""
        return self.loop.run_until_complete(coro)


class TestNumberGuessGenerator(AsyncTestCase):
    """
    Test cases for NumberGuessGenerator.
    Demonstrates async testing and mocking external APIs.
    """
    
    def test_generator_initialization(self):
        """Test generator initialization with different difficulties."""
        # Normal difficulty
        generator = NumberGuessGenerator("normal")
        self.assertEqual(generator.difficulty, "normal")
        self.assertEqual(generator.difficulty_multiplier, 1.0)
        
        # Easy difficulty
        easy_gen = NumberGuessGenerator("easy")
        self.assertEqual(easy_gen.difficulty_multiplier, 0.5)
        
        # Hard difficulty
        hard_gen = NumberGuessGenerator("hard")
        self.assertEqual(hard_gen.difficulty_multiplier, 1.5)
    
    def test_difficulty_adjustment(self):
        """Test difficulty range adjustment."""
        generator = NumberGuessGenerator("easy")
        
        # Test range adjustment
        adjusted_range = generator._adjust_for_difficulty((1, 100))
        self.assertEqual(adjusted_range[0], 1)
        self.assertLessEqual(adjusted_range[1], 60)  # Easy mode reduces max
        
        # Hard mode
        hard_gen = NumberGuessGenerator("hard")
        hard_range = hard_gen._adjust_for_difficulty((1, 100))
        self.assertEqual(hard_range[0], 1)
        self.assertGreaterEqual(hard_range[1], 100)  # Hard mode increases max
    
    async def test_generate_question_basic(self):
        """Test basic question generation."""
        generator = NumberGuessGenerator("normal")
        
        question = await generator.generate()
        
        # Check question structure
        self.assertIsInstance(question, QuestionResult)
        self.assertEqual(question.question_type, "number_guess")
        self.assertEqual(question.difficulty, "normal")
        self.assertIn("Guess the number", question.text)
        self.assertIsInstance(question.answer, int)
        self.assertGreaterEqual(question.answer, 1)
        self.assertLessEqual(question.answer, 100)
    
    @patch('aiohttp.ClientSession.get')
    async def test_generate_with_api_success(self, mock_get):
        """Test question generation with successful API call."""
        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="42 is the answer to everything")
        
        mock_context = AsyncMock()
        mock_context.__aenter__ = AsyncMock(return_value=mock_response)
        mock_context.__aexit__ = AsyncMock(return_value=None)
        mock_get.return_value = mock_context
        
        generator = NumberGuessGenerator("normal")
        question = await generator.generate()
        
        # Should include the fun fact in the question
        self.assertIn("Hint:", question.text)
        self.assertIn("42 is the answer", question.text)
    
    @patch('aiohttp.ClientSession.get')
    async def test_generate_with_api_failure(self, mock_get):
        """Test question generation with API failure."""
        # Mock API failure
        mock_get.side_effect = aiohttp.ClientError("Network error")
        
        generator = NumberGuessGenerator("normal")
        question = await generator.generate()
        
        # Should still generate question without hint
        self.assertIsInstance(question, QuestionResult)
        self.assertNotIn("Hint:", question.text)
    
    @patch('aiohttp.ClientSession.get')
    async def test_generate_with_api_timeout(self, mock_get):
        """Test question generation with API timeout."""
        # Mock timeout
        mock_get.side_effect = asyncio.TimeoutError()
        
        generator = NumberGuessGenerator("normal")
        question = await generator.generate()
        
        # Should handle timeout gracefully
        self.assertIsInstance(question, QuestionResult)
        self.assertNotIn("Hint:", question.text)


class TestSquareRootGenerator(AsyncTestCase):
    """
    Test cases for SquareRootGenerator.
    Demonstrates mathematical testing and edge cases.
    """
    
    def test_perfect_squares_generation(self):
        """Test perfect squares generation for different difficulties."""
        # Easy mode
        easy_gen = SquareRootGenerator("easy")
        self.assertEqual(len(easy_gen.perfect_squares), 5)  # 1² to 5²
        self.assertEqual(easy_gen.perfect_squares, [1, 4, 9, 16, 25])
        
        # Normal mode
        normal_gen = SquareRootGenerator("normal")
        self.assertEqual(len(normal_gen.perfect_squares), 50)  # 1² to 50²
        self.assertIn(1, normal_gen.perfect_squares)
        self.assertIn(2500, normal_gen.perfect_squares)  # 50²
        
        # Hard mode
        hard_gen = SquareRootGenerator("hard")
        self.assertEqual(len(hard_gen.perfect_squares), 100)  # 1² to 100²
        self.assertIn(10000, hard_gen.perfect_squares)  # 100²
    
    async def test_generate_question(self):
        """Test square root question generation."""
        generator = SquareRootGenerator("easy")
        
        question = await generator.generate()
        
        # Check question structure
        self.assertIsInstance(question, QuestionResult)
        self.assertEqual(question.question_type, "square_root")
        self.assertEqual(question.difficulty, "easy")
        self.assertIn("square root", question.text)
        
        # Verify answer is correct
        # Extract the number from question text
        import re
        match = re.search(r'square root of (\d+)', question.text)
        self.assertIsNotNone(match)
        
        number = int(match.group(1))
        expected_answer = int(number ** 0.5)
        self.assertEqual(question.answer, expected_answer)
        
        # Verify it's actually a perfect square
        self.assertEqual(expected_answer * expected_answer, number)
    
    async def test_multiple_generations(self):
        """Test multiple question generations for variety."""
        generator = SquareRootGenerator("normal")
        
        questions = []
        for _ in range(10):
            question = await generator.generate()
            questions.append(question)
        
        # Should generate different questions
        answers = [q.answer for q in questions]
        self.assertGreater(len(set(answers)), 1)  # At least some variety
        
        # All should be valid
        for question in questions:
            self.assertIsInstance(question.answer, int)
            self.assertGreater(question.answer, 0)


class TestMathExpressionGenerator(AsyncTestCase):
    """
    Test cases for MathExpressionGenerator.
    Demonstrates testing mathematical operations and expression evaluation.
    """
    
    async def test_generate_easy_expressions(self):
        """Test generation of easy math expressions."""
        generator = MathExpressionGenerator("easy")
        
        question = await generator.generate()
        
        # Check question structure
        self.assertIsInstance(question, QuestionResult)
        self.assertEqual(question.question_type, "math_expression")
        self.assertEqual(question.difficulty, "easy")
        self.assertIn("Calculate:", question.text)
        
        # Should only use + or - in easy mode
        self.assertTrue(any(op in question.text for op in ['+', '-']))
        self.assertNotIn('*', question.text)
        self.assertNotIn('/', question.text)
    
    async def test_generate_hard_expressions(self):
        """Test generation of hard math expressions."""
        generator = MathExpressionGenerator("hard")
        
        # Generate multiple questions to test variety
        operators_used = set()
        for _ in range(20):
            question = await generator.generate()
            
            # Extract operator from question text
            import re
            match = re.search(r'\d+\s*([+\-*])\s*\d+', question.text)
            if match:
                operators_used.add(match.group(1))
        
        # Hard mode should use multiplication
        self.assertIn('*', operators_used)
    
    async def test_expression_evaluation(self):
        """Test that generated expressions evaluate correctly."""
        generator = MathExpressionGenerator("normal")
        
        for _ in range(10):
            question = await generator.generate()
            
            # Extract expression from question text
            import re
            match = re.search(r'Calculate: (.+)', question.text)
            self.assertIsNotNone(match)
            
            expression = match.group(1).strip()
            
            # Safely evaluate the expression
            try:
                expected_result = eval(expression)
                self.assertEqual(question.answer, int(expected_result))
            except:
                self.fail(f"Invalid expression generated: {expression}")
    
    async def test_safe_evaluation(self):
        """Test that expression evaluation is safe."""
        generator = MathExpressionGenerator("normal")
        
        # Generate many expressions to ensure they're all safe
        for _ in range(50):
            question = await generator.generate()
            
            # Should not contain dangerous operations
            self.assertNotIn('import', question.text)
            self.assertNotIn('exec', question.text)
            self.assertNotIn('eval', question.text)
            self.assertNotIn('__', question.text)
            
            # Should be a simple arithmetic expression
            import re
            pattern = r'Calculate: \d+\s*[+\-*/]\s*\d+'
            self.assertRegex(question.text, pattern)


class TestQuestionFactory(AsyncTestCase):
    """
    Test cases for QuestionFactory.
    Demonstrates factory pattern testing and integration testing.
    """
    
    def test_factory_initialization(self):
        """Test factory initialization."""
        factory = QuestionFactory()
        
        # Check available generators
        expected_types = ['number_guess', 'square_root', 'math_expression']
        self.assertEqual(set(factory.generators.keys()), set(expected_types))
        
        # Check weights
        self.assertIn('number_guess', factory.question_weights)
        self.assertIn('square_root', factory.question_weights)
        self.assertIn('math_expression', factory.question_weights)
        
        # Weights should sum to approximately 1.0
        total_weight = sum(factory.question_weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=1)
    
    async def test_create_random_question(self):
        """Test random question creation."""
        factory = QuestionFactory()
        
        question = await factory.create_question("normal")
        
        # Check question is valid
        self.assertIsInstance(question, QuestionResult)
        self.assertIn(question.question_type, factory.generators.keys())
        self.assertEqual(question.difficulty, "normal")
        self.assertIsNotNone(question.text)
        self.assertIsNotNone(question.answer)
    
    async def test_create_specific_question(self):
        """Test creating specific question types."""
        factory = QuestionFactory()
        
        # Test each question type
        for question_type in factory.generators.keys():
            question = await factory.create_specific_question(question_type, "easy")
            
            self.assertEqual(question.question_type, question_type)
            self.assertEqual(question.difficulty, "easy")
    
    async def test_create_invalid_question_type(self):
        """Test error handling for invalid question types."""
        factory = QuestionFactory()
        
        with self.assertRaises(ValueError):
            await factory.create_specific_question("invalid_type", "normal")
    
    async def test_question_distribution(self):
        """Test that question types are distributed according to weights."""
        factory = QuestionFactory()
        
        # Generate many questions
        question_counts = {}
        total_questions = 100
        
        for _ in range(total_questions):
            question = await factory.create_question("normal")
            question_type = question.question_type
            question_counts[question_type] = question_counts.get(question_type, 0) + 1
        
        # Check that all types were generated
        for question_type in factory.generators.keys():
            self.assertIn(question_type, question_counts)
            self.assertGreater(question_counts[question_type], 0)
        
        # Check distribution roughly matches weights (with some tolerance)
        for question_type, expected_weight in factory.question_weights.items():
            actual_ratio = question_counts[question_type] / total_questions
            expected_ratio = expected_weight
            
            # Allow 20% tolerance for randomness
            tolerance = 0.2
            self.assertAlmostEqual(actual_ratio, expected_ratio, delta=tolerance)
    
    def test_get_available_types(self):
        """Test getting available question types."""
        factory = QuestionFactory()
        
        available_types = factory.get_available_types()
        expected_types = ['number_guess', 'square_root', 'math_expression']
        
        self.assertEqual(set(available_types), set(expected_types))
    
    async def test_different_difficulties(self):
        """Test question generation with different difficulties."""
        factory = QuestionFactory()
        
        difficulties = ['easy', 'normal', 'hard']
        
        for difficulty in difficulties:
            question = await factory.create_question(difficulty)
            self.assertEqual(question.difficulty, difficulty)


class TestQuestionIntegration(AsyncTestCase):
    """
    Integration tests for question system.
    Demonstrates integration testing patterns.
    """
    
    async def test_full_question_lifecycle(self):
        """Test complete question lifecycle from generation to answer checking."""
        factory = QuestionFactory()
        
        # Generate question
        question = await factory.create_question("normal")
        
        # Simulate correct answer
        correct_answer = str(question.answer)
        self.assertTrue(question.check_answer(correct_answer))
        
        # Simulate wrong answer
        if isinstance(question.answer, int):
            wrong_answer = str(question.answer + 1)
        else:
            wrong_answer = "definitely_wrong"
        
        self.assertFalse(question.check_answer(wrong_answer))
    
    async def test_question_variety_across_difficulties(self):
        """Test that different difficulties produce varied questions."""
        factory = QuestionFactory()
        
        # Generate questions for each difficulty
        difficulties = ['easy', 'normal', 'hard']
        questions_by_difficulty = {}
        
        for difficulty in difficulties:
            questions = []
            for _ in range(10):
                question = await factory.create_question(difficulty)
                questions.append(question)
            questions_by_difficulty[difficulty] = questions
        
        # Check that questions vary by difficulty
        # (This is a basic check - more sophisticated analysis could be done)
        for difficulty, questions in questions_by_difficulty.items():
            # All questions should have correct difficulty
            for question in questions:
                self.assertEqual(question.difficulty, difficulty)
            
            # Should have some variety in question types
            question_types = set(q.question_type for q in questions)
            self.assertGreater(len(question_types), 1)


class TestQuestionPerformance(AsyncTestCase):
    """
    Performance tests for question generation.
    Demonstrates performance testing patterns.
    """
    
    async def test_generation_performance(self):
        """Test question generation performance."""
        import time
        
        factory = QuestionFactory()
        
        start_time = time.time()
        
        # Generate many questions
        questions = []
        for _ in range(100):
            question = await factory.create_question("normal")
            questions.append(question)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete in reasonable time
        self.assertLess(execution_time, 5.0)  # Less than 5 seconds
        
        # All questions should be valid
        self.assertEqual(len(questions), 100)
        for question in questions:
            self.assertIsInstance(question, QuestionResult)
    
    async def test_concurrent_generation(self):
        """Test concurrent question generation."""
        factory = QuestionFactory()
        
        # Generate questions concurrently
        tasks = []
        for _ in range(20):
            task = factory.create_question("normal")
            tasks.append(task)
        
        questions = await asyncio.gather(*tasks)
        
        # All should be valid
        self.assertEqual(len(questions), 20)
        for question in questions:
            self.assertIsInstance(question, QuestionResult)


if __name__ == '__main__':
    """
    Run tests when module is executed directly.
    Demonstrates async test execution.
    """
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestQuestionResult,
        TestNumberGuessGenerator,
        TestSquareRootGenerator,
        TestMathExpressionGenerator,
        TestQuestionFactory,
        TestQuestionIntegration,
        TestQuestionPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)