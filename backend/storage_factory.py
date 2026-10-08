"""
Storage factory returning either AWSStorageAdapter or LocalStorageManager
based on STORAGE_MODE environment variable.
"""

import os
from local_storage_manager import LocalStorageManager
from aws_storage_adapter import AWSStorageAdapter


def get_storage():
    """Returns active storage adapter (Local or AWS)."""
    mode = os.getenv("STORAGE_MODE", "local").lower()
    if mode == "aws":
        return AWSStorageAdapter()
    return LocalStorageManager()
