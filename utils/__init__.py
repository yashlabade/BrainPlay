"""
Utils package initialization.
Demonstrates package structure and imports.
"""

# Make key utilities available at package level
from .decorators import timer, log_calls
from .context import game_session
from .file_io import save_game_history, load_game_history

__all__ = [
    'timer', 'log_calls',
    'game_session',
    'save_game_history', 'load_game_history'
]

__version__ = "2.0.0"