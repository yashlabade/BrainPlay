"""
Test package initialization.
Demonstrates test organization and structure.
"""

import sys
from pathlib import Path

# Add parent directory to path for importing modules
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

__version__ = "1.0.0"