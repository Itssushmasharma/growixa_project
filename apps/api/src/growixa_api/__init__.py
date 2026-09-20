"""Growixa backend package."""

import datetime

if not hasattr(datetime, "UTC"):
    datetime.UTC = datetime.timezone.utc

__version__ = "0.1.0"

