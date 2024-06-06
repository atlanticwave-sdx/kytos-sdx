"""SDX topology Utility functions"""
from datetime import datetime
import pytz


def get_timestamp(timestamp=None):
    """Function to obtain the current time_stamp in a specific format"""
    if timestamp is not None:
        if len(timestamp) >= 19:
            return timestamp[:10]+"T"+timestamp[11:19]+"Z"
    return datetime.now(
            pytz.timezone("America/New_York")).strftime("%Y-%m-%dT%H:%M:%SZ")
