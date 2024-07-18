"""SDX topology Utility functions"""

from datetime import datetime, timezone


def get_timestamp():
    """Return the current datetime in UTC formatted as string"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
