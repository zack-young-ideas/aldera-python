"""
Defines a global settings registry used by other modules.

Copyright (c) 2025 Zachary Young.
All rights reserved.
"""

_config = {}


def set(**kwargs):
    _config.update(kwargs)


def load_dict(dict_items):
    _config.update(dict_items)


def get(key, default=None):
    return _config.get(key, default)
