"""
Analytics Package
Provides both legacy and new analytics modules

This package bridges the legacy analytics.py module with the new modular structure.
"""

import sys
import os
import importlib.util

# Import from legacy analytics.py file for backwards compatibility
# We need to use importlib to avoid circular import issues
_legacy_module = None
try:
    # Get the path to the legacy analytics.py file
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    legacy_analytics_path = os.path.join(parent_dir, 'analytics.py')

    if os.path.exists(legacy_analytics_path):
        # Load the legacy analytics.py as a separate module
        spec = importlib.util.spec_from_file_location("analytics_legacy", legacy_analytics_path)
        _legacy_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_legacy_module)

        # Export PlatformAnalytics from legacy module
        PlatformAnalytics = _legacy_module.PlatformAnalytics
    else:
        print("Warning: Legacy analytics.py not found")
        PlatformAnalytics = None
except Exception as e:
    print(f"Warning: Could not import legacy PlatformAnalytics: {e}")
    PlatformAnalytics = None

# Export new modules
from .platform_metrics import PlatformMetrics
from .market_metrics import MarketMetrics
from .user_metrics import UserMetrics

__all__ = [
    'PlatformAnalytics',  # Legacy
    'PlatformMetrics',    # New
    'MarketMetrics',      # New
    'UserMetrics'         # New
]
