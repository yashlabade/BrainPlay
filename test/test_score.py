"""
Unit Tests for Score Management
Demonstrates unittest, pytest patterns, and comprehensive testing strategies.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import json
import threading
import time

# Import modules to test
from score import ScoreManager
from exceptions import ScoreException


class TestScoreManager(unittest.TestCase):
    """
    Test cases for ScoreManager class.
    Demonstrates unit testing patterns and test organization.
    """
    
    def setUp(self):
        """
        Set up test environment before each test.
        Demonstrates test setup and isolation.
        """
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.original_score_file = None
        
        # Reset singleton instance for clean testing
        if hasattr(ScoreManager, '_instance'):
            ScoreManager._instance = None
        
        # Patch the score file path to use test directory
        self.score_manager = ScoreManager()
        self.score_manager._score_file = Path(self.test_dir) / "test_score.json"
        self.score_manager._ensure_data_directory()
    
    def tearDown(self):
        """
        Clean up after each test.
        Demonstrates test cleanup and resource management.
        """
        # Clean up temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        # Reset singleton
        if hasattr(ScoreManager, '_instance'):
            ScoreManager._instance = None
    
    def test_singleton_pattern(self):
        """Test that ScoreManager implements singleton pattern correctly."""
        manager1 = ScoreManager()
        manager2 = ScoreManager()
        
        # Should be the same instance
        self.assertIs(manager1, manager2)
        
        # Changes in one should reflect in the other
        manager1.add_points(10)
        self.assertEqual(manager2.get_score(), 10)
    
    def test_initial_score(self):
        """Test initial score is zero."""
        self.assertEqual(self.score_manager.get_score(), 0)
        self.assertEqual(self.score_manager._round_count, 0)
        self.assertEqual(self.score_manager._correct_answers, 0)
        self.assertEqual(self.score_manager._wrong_answers, 0)
    
    def test_add_positive_points(self):
        """Test adding positive points."""
        self.score_manager.add_points(10)
        
        self.assertEqual(self.score_manager.get_score(), 10)
        self.assertEqual(self.score_manager._round_count, 1)
        self.assertEqual(self.score_manager._correct_answers, 1)
        self.assertEqual(self.score_manager._wrong_answers, 0)
    
    def test_add_negative_points(self):
        """Test adding negative points."""
        self.score_manager.add_points(-5)
        
        self.assertEqual(self.score_manager.get_score(), -5)
        self.assertEqual(self.score_manager._round_count, 1)
        self.assertEqual(self.score_manager._correct_answers, 0)
        self.assertEqual(self.score_manager._wrong_answers, 1)
    
    def test_multiple_rounds(self):
        """Test multiple rounds of scoring."""
        # Add various points
        points_sequence = [10, -5, 10, 10, -5]
        expected_score = sum(points_sequence)
        
        for points in points_sequence:
            self.score_manager.add_points(points)
        
        self.assertEqual(self.score_manager.get_score(), expected_score)
        self.assertEqual(self.score_manager._round_count, len(points_sequence))
        self.assertEqual(self.score_manager._correct_answers, 3)  # positive points
        self.assertEqual(self.score_manager._wrong_answers, 2)   # negative points
    
    def test_accuracy_calculation(self):
        """Test accuracy percentage calculation."""
        # No rounds yet
        self.assertEqual(self.score_manager.accuracy, 0.0)
        
        # Add some rounds
        self.score_manager.add_points(10)  # correct
        self.score_manager.add_points(10)  # correct
        self.score_manager.add_points(-5)  # wrong
        
        expected_accuracy = (2 / 3) * 100  # 2 correct out of 3
        self.assertAlmostEqual(self.score_manager.accuracy, expected_accuracy, places=2)
    
    def test_score_history(self):
        """Test score history tracking."""
        self.score_manager.add_points(10)
        self.score_manager.add_points(-5)
        
        history = self.score_manager._score_history
        self.assertEqual(len(history), 2)
        
        # Check first entry
        first_entry = history[0]
        self.assertEqual(first_entry['round'], 1)
        self.assertEqual(first_entry['points_added'], 10)
        self.assertEqual(first_entry['old_score'], 0)
        self.assertEqual(first_entry['new_score'], 10)
        
        # Check second entry
        second_entry = history[1]
        self.assertEqual(second_entry['round'], 2)
        self.assertEqual(second_entry['points_added'], -5)
        self.assertEqual(second_entry['old_score'], 10)
        self.assertEqual(second_entry['new_score'], 5)
    
    def test_achievements(self):
        """Test achievement system."""
        # Test "First Points" achievement
        self.score_manager.add_points(10)
        self.assertIn("First Points", self.score_manager._achievements)
        
        # Test "Half Century" achievement
        self.score_manager.add_points(40)  # Total: 50
        self.assertIn("Half Century", self.score_manager._achievements)
        
        # Test "Century" achievement
        self.score_manager.add_points(50)  # Total: 100
        self.assertIn("Century", self.score_manager._achievements)
    
    def test_hot_streak_achievement(self):
        """Test hot streak achievement (5 correct answers in a row)."""
        # Add 5 correct answers
        for _ in range(5):
            self.score_manager.add_points(10)
        
        self.assertIn("Hot Streak", self.score_manager._achievements)
    
    def test_reset_score(self):
        """Test score reset functionality."""
        # Add some points and achievements
        self.score_manager.add_points(25)
        self.score_manager.add_points(10)
        
        # Reset
        self.score_manager.reset_score()
        
        # Check everything is reset
        self.assertEqual(self.score_manager.get_score(), 0)
        self.assertEqual(self.score_manager._round_count, 0)
        self.assertEqual(self.score_manager._correct_answers, 0)
        self.assertEqual(self.score_manager._wrong_answers, 0)
        self.assertEqual(len(self.score_manager._score_history), 0)
        self.assertEqual(len(self.score_manager._achievements), 0)
    
    def test_statistics(self):
        """Test comprehensive statistics generation."""
        # Add some game data
        self.score_manager.add_points(10)
        self.score_manager.add_points(-5)
        self.score_manager.add_points(10)
        
        stats = self.score_manager.get_statistics()
        
        # Check all expected keys are present
        expected_keys = [
            'current_score', 'rounds_played', 'correct_answers', 'wrong_answers',
            'accuracy', 'game_duration', 'achievements', 'score_progression',
            'average_points_per_round'
        ]
        
        for key in expected_keys:
            self.assertIn(key, stats)
        
        # Check specific values
        self.assertEqual(stats['current_score'], 15)
        self.assertEqual(stats['rounds_played'], 3)
        self.assertEqual(stats['correct_answers'], 2)
        self.assertEqual(stats['wrong_answers'], 1)
        self.assertAlmostEqual(stats['accuracy'], 66.67, places=2)
        self.assertAlmostEqual(stats['average_points_per_round'], 5.0, places=2)
    
    def test_file_persistence(self):
        """Test score persistence to file."""
        # Add some points
        self.score_manager.add_points(25)
        
        # Check file was created and contains correct data
        self.assertTrue(self.score_manager._score_file.exists())
        
        with open(self.score_manager._score_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['score'], 25)
        self.assertEqual(saved_data['round_count'], 1)
        self.assertEqual(saved_data['correct_answers'], 1)
    
    def test_load_from_file(self):
        """Test loading score from existing file."""
        # Create test data file
        test_data = {
            'score': 42,
            'round_count': 3,
            'correct_answers': 2,
            'wrong_answers': 1,
            'score_history': [
                {'round': 1, 'points_added': 10, 'old_score': 0, 'new_score': 10},
                {'round': 2, 'points_added': -5, 'old_score': 10, 'new_score': 5},
                {'round': 3, 'points_added': 37, 'old_score': 5, 'new_score': 42}
            ],
            'achievements': ['First Points'],
            'game_start_time': '2023-01-01T12:00:00'
        }
        
        with open(self.score_manager._score_file, 'w') as f:
            json.dump(test_data, f)
        
        # Create new manager instance (should load from file)
        ScoreManager._instance = None
        new_manager = ScoreManager()
        new_manager._score_file = self.score_manager._score_file
        new_manager._load_score()
        
        # Check loaded values
        self.assertEqual(new_manager.get_score(), 42)
        self.assertEqual(new_manager._round_count, 3)
        self.assertEqual(new_manager._correct_answers, 2)
        self.assertEqual(new_manager._wrong_answers, 1)
        self.assertEqual(len(new_manager._score_history), 3)
        self.assertIn('First Points', new_manager._achievements)
    
    def test_invalid_points_type(self):
        """Test error handling for invalid point types."""
        with self.assertRaises(TypeError):
            self.score_manager.add_points("invalid")
        
        with self.assertRaises(TypeError):
            self.score_manager.add_points(10.5)  # Should be int
    
    def test_thread_safety(self):
        """Test thread safety of singleton pattern."""
        instances = []
        
        def create_instance():
            instances.append(ScoreManager())
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All instances should be the same
        first_instance = instances[0]
        for instance in instances[1:]:
            self.assertIs(instance, first_instance)
    
    def test_export_report(self):
        """Test detailed report export."""
        # Add some game data
        self.score_manager.add_points(10)
        self.score_manager.add_points(-5)
        self.score_manager.add_points(15)
        
        # Export report
        report_file = self.score_manager.export_detailed_report()
        
        # Check file was created
        self.assertTrue(Path(report_file).exists())
        
        # Check file content
        with open(report_file, 'r') as f:
            content = f.read()
        
        self.assertIn("BRAINPLAY GAME REPORT", content)
        self.assertIn("Final Score: 20", content)
        self.assertIn("Rounds Played: 3", content)
        self.assertIn("Accuracy:", content)


class TestScoreManagerIntegration(unittest.TestCase):
    """
    Integration tests for ScoreManager.
    Demonstrates integration testing patterns.
    """
    
    def setUp(self):
        """Set up integration test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Reset singleton
        if hasattr(ScoreManager, '_instance'):
            ScoreManager._instance = None
    
    def tearDown(self):
        """Clean up integration test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        if hasattr(ScoreManager, '_instance'):
            ScoreManager._instance = None
    
    def test_full_game_simulation(self):
        """Test a complete game simulation."""
        manager = ScoreManager()
        manager._score_file = Path(self.test_dir) / "integration_test.json"
        
        # Simulate a full game
        game_rounds = [
            (10, True),   # Correct answer
            (-5, False),  # Wrong answer
            (10, True),   # Correct answer
            (10, True),   # Correct answer
            (-5, False),  # Wrong answer
            (10, True),   # Correct answer
            (10, True),   # Correct answer - should trigger Hot Streak
        ]
        
        for points, expected_correct in game_rounds:
            manager.add_points(points)
        
        # Check final state
        expected_score = sum(points for points, _ in game_rounds)
        self.assertEqual(manager.get_score(), expected_score)
        
        # Check achievements
        self.assertIn("First Points", manager._achievements)
        self.assertIn("Half Century", manager._achievements)
        
        # Check statistics
        stats = manager.get_statistics()
        self.assertEqual(stats['rounds_played'], len(game_rounds))
        self.assertEqual(stats['correct_answers'], 5)
        self.assertEqual(stats['wrong_answers'], 2)


# Test utilities and fixtures
class ScoreManagerTestCase(unittest.TestCase):
    """
    Base test case class with common setup for ScoreManager tests.
    Demonstrates test inheritance and reusable test patterns.
    """
    
    def setUp(self):
        """Common setup for all ScoreManager tests."""
        self.test_dir = tempfile.mkdtemp()
        
        # Reset singleton
        if hasattr(ScoreManager, '_instance'):
            ScoreManager._instance = None
        
        self.score_manager = ScoreManager()
        self.score_manager._score_file = Path(self.test_dir) / "test_score.json"
    
    def tearDown(self):
        """Common cleanup for all ScoreManager tests."""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        
        if hasattr(ScoreManager, '_instance'):
            ScoreManager._instance = None
    
    def add_test_rounds(self, rounds_data):
        """Helper method to add multiple test rounds."""
        for points in rounds_data:
            self.score_manager.add_points(points)


# Performance tests
class TestScoreManagerPerformance(ScoreManagerTestCase):
    """
    Performance tests for ScoreManager.
    Demonstrates performance testing patterns.
    """
    
    def test_large_number_of_rounds(self):
        """Test performance with large number of rounds."""
        import time
        
        start_time = time.time()
        
        # Add 1000 rounds
        for i in range(1000):
            points = 10 if i % 2 == 0 else -5
            self.score_manager.add_points(points)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second)
        self.assertLess(execution_time, 1.0)
        
        # Check final state
        self.assertEqual(self.score_manager._round_count, 1000)
        self.assertEqual(self.score_manager._correct_answers, 500)
        self.assertEqual(self.score_manager._wrong_answers, 500)


# Mock and patch examples
class TestScoreManagerMocking(unittest.TestCase):
    """
    Tests using mocking and patching.
    Demonstrates advanced testing techniques.
    """
    
    def setUp(self):
        """Set up mocking tests."""
        if hasattr(ScoreManager, '_instance'):
            ScoreManager._instance = None
    
    def test_file_save_error_handling(self):
        """Test error handling when file save fails."""
        from unittest.mock import patch, mock_open
        
        manager = ScoreManager()
        
        # Mock file operations to raise an exception
        with patch('builtins.open', mock_open()) as mock_file:
            mock_file.side_effect = IOError("Disk full")
            
            # This should not raise an exception (error should be handled)
            manager.add_points(10)
            
            # Score should still be updated in memory
            self.assertEqual(manager.get_score(), 10)


if __name__ == '__main__':
    """
    Run tests when module is executed directly.
    Demonstrates test execution patterns.
    """
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestScoreManager))
    test_suite.addTest(unittest.makeSuite(TestScoreManagerIntegration))
    test_suite.addTest(unittest.makeSuite(TestScoreManagerPerformance))
    test_suite.addTest(unittest.makeSuite(TestScoreManagerMocking))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)