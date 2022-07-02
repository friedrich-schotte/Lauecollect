"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-05
Revision comment:
"""
__version__ = "1.0"


def to_int(x):
    """Try to convert x to an integer number without raising an exception."""
    # noinspection PyBroadException
    try:
        return int(x)
    except Exception:
        return x
