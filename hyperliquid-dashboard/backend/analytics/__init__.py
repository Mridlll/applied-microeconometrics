"""
Analytics package that bridges legacy and new module structures
"""
import sys
import os

# Add the parent directory to path to make analytics.py modules accessible
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import from analytics.py for backward compatibility
try:
    from analytics import PlatformAnalytics
except ImportError:
    pass

# Empty imports to make this a valid package
