"""
ReleaseMind — Config Loader
Loads risk_config.yaml relative to the backend directory.
"""

import os
import yaml

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config", "risk_config.yaml")
_cache = None


def load_config(path: str = None) -> dict:
    global _cache
    if _cache is not None:
        return _cache

    target = path or _CONFIG_PATH
    try:
        with open(target, "r") as f:
            _cache = yaml.safe_load(f) or {}
    except FileNotFoundError:
        _cache = {}
    return _cache


def reload_config(path: str = None):
    """Force reload the config (useful after manual YAML edits)."""
    global _cache
    _cache = None
    return load_config(path)
