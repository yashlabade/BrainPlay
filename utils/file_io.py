"""
File I/O Utilities Module
Demonstrates file operations, JSON handling, and async I/O patterns.
Enhanced with session-aware data management.
"""

import json
import asyncio
import aiofiles
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """
    Centralized file management class with session awareness.
    Demonstrates file operations organization and error handling.
    """
    
    def __init__(self, base_path: str = "data"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        logger.info(f"FileManager initialized with base path: {self.base_path}")
    
    def get_path(self, filename: str) -> Path:
        """Get full path for a filename."""
        return self.base_path / filename


# Global file manager instance
file_manager = FileManager()


async def save_game_history(game_data_list: List[Dict], final_score: int) -> None:
    """
    Save comprehensive game history to JSON file asynchronously.
    Enhanced to handle session-aware data.
    
    Args:
        game_data_list: List of game session data
        final_score: Final game score
    """
    try:
        # Load existing history
        history_file = file_manager.get_path("game_history.json")
        existing_history = []
        
        if history_file.exists():
            existing_history = await load_json_async(history_file)
            if not isinstance(existing_history, list):
                existing_history = []
        
        # Add new game data to history
        for game_data in game_data_list:
            # Ensure we have all required fields
            if 'timestamp' not in game_data:
                game_data['timestamp'] = datetime.now().isoformat()
            
            # Add comprehensive statistics
            if 'rounds' in game_data and isinstance(game_data['rounds'], list):
                game_data['statistics'] = _calculate_session_statistics(game_data['rounds'])
            
            existing_history.append(game_data)
        
        # Keep only last 100 games to prevent file from growing too large
        if len(existing_history) > 100:
            existing_history = existing_history[-100:]
        
        # Save updated history
        await save_json_async(history_file, existing_history)
        
        # Also save individual session files for detailed analysis
        for game_data in game_data_list:
            if 'session_id' in game_data:
                session_file = file_manager.get_path(f"session_{game_data['session_id'][:8]}.json")
                await save_json_async(session_file, game_data)
        
        logger.info(f"Game history saved successfully. Total games: {len(existing_history)}")
        
    except Exception as e:
        logger.error(f"Failed to save game history: {e}")
        raise


async def load_game_history() -> List[Dict]:
    """
    Load game history from JSON file with enhanced error handling.
    """
    try:
        history_file = file_manager.get_path("game_history.json")
        
        if not history_file.exists():
            logger.info("No game history file found")
            return []
        
        history = await load_json_async(history_file)
        
        if not isinstance(history, list):
            logger.warning("Invalid game history format, returning empty list")
            return []
        
        logger.info(f"Loaded {len(history)} games from history")
        return history
        
    except Exception as e:
        logger.error(f"Failed to load game history: {e}")
        return []


async def save_json_async(file_path: Union[str, Path], data: Any, indent: int = 2) -> None:
    """
    Save data to JSON file asynchronously with enhanced error handling.
    """
    try:
        file_path = Path(file_path)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Serialize to JSON string first (for better error handling)
        json_string = json.dumps(data, indent=indent, default=_json_serializer, ensure_ascii=False)
        
        # Write asynchronously
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(json_string)
        
        logger.debug(f"JSON saved: {file_path}")
        
    except Exception as e:
        logger.error(f"Failed to save JSON {file_path}: {e}")
        raise


async def load_json_async(file_path: Union[str, Path]) -> Any:
    """
    Load data from JSON file asynchronously with enhanced error handling.
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"JSON file not found: {file_path}")
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
        
        data = json.loads(content)
        logger.debug(f"JSON loaded: {file_path}")
        return data
        
    except Exception as e:
        logger.error(f"Failed to load JSON {file_path}: {e}")
        raise


def _json_serializer(obj):
    """
    Custom JSON serializer for non-standard types.
    Enhanced to handle session-specific objects.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Path):
        return str(obj)
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)


def _calculate_session_statistics(rounds_data: List[Dict]) -> Dict:
    """
    Calculate comprehensive session statistics.
    Enhanced with session-specific metrics.
    """
    if not rounds_data:
        return {}
    
    # Use list comprehensions and functional programming
    correct_answers = [r for r in rounds_data if r.get('is_correct', False)]
    wrong_answers = [r for r in rounds_data if not r.get('is_correct', False)]
    
    # Calculate statistics using map, filter, and reduce
    from functools import reduce
    
    total_points = reduce(lambda acc, r: acc + r.get('points_earned', 0), rounds_data, 0)
    question_types = list(set(r.get('question_type', 'unknown') for r in rounds_data))
    
    # Type distribution using dictionary comprehension
    type_distribution = {
        qtype: len([r for r in rounds_data if r.get('question_type') == qtype])
        for qtype in question_types
    }
    
    # Calculate response times if available
    response_times = [
        r.get('response_time', 0) for r in rounds_data 
        if r.get('response_time') is not None
    ]
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    return {
        'total_rounds': len(rounds_data),
        'correct_answers': len(correct_answers),
        'wrong_answers': len(wrong_answers),
        'accuracy': len(correct_answers) / len(rounds_data) * 100 if rounds_data else 0,
        'total_points': total_points,
        'average_points_per_round': total_points / len(rounds_data) if rounds_data else 0,
        'question_types': question_types,
        'type_distribution': type_distribution,
        'average_response_time': avg_response_time,
        'session_duration': rounds_data[-1].get('timestamp', '') if rounds_data else ''
    }


async def export_session_report(session_id: str, output_format: str = 'json') -> str:
    """
    Export detailed session report.
    Demonstrates advanced file operations and data export.
    """
    try:
        session_file = file_manager.get_path(f"session_{session_id[:8]}.json")
        
        if not session_file.exists():
            raise FileNotFoundError(f"Session file not found: {session_file}")
        
        session_data = await load_json_async(session_file)
        
        if output_format.lower() == 'json':
            report_file = file_manager.get_path(f"report_{session_id[:8]}.json")
            await save_json_async(report_file, session_data)
        else:
            # Could implement CSV, HTML, or other formats here
            raise ValueError(f"Unsupported output format: {output_format}")
        
        logger.info(f"Session report exported: {report_file}")
        return str(report_file)
        
    except Exception as e:
        logger.error(f"Failed to export session report: {e}")
        raise


# Example usage and testing
if __name__ == "__main__":
    """
    Module testing and demonstration.
    Shows file I/O operations and async patterns.
    """
    
    async def test_file_operations():
        print("Testing Enhanced File I/O Operations...")
        
        # Test session data saving
        session_data = {
            'session_id': 'test-session-123',
            'player_name': 'Test Player',
            'mode': 'normal',
            'final_score': 42,
            'rounds': [
                {
                    'round_number': 1,
                    'question_type': 'number_guess',
                    'is_correct': True,
                    'points_earned': 10,
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'round_number': 2,
                    'question_type': 'square_root',
                    'is_correct': False,
                    'points_earned': -5,
                    'timestamp': datetime.now().isoformat()
                }
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        # Save session data
        await save_game_history([session_data], 42)
        
        # Load and verify
        history = await load_game_history()
        print(f"Session data test passed: {len(history)} sessions saved")
        
        # Test session report export
        if history:
            session_id = history[-1].get('session_id', 'unknown')
            try:
                report_file = await export_session_report(session_id)
                print(f"Session report exported: {report_file}")
            except Exception as e:
                print(f"Report export test skipped: {e}")
    
    # Run async tests
    asyncio.run(test_file_operations())