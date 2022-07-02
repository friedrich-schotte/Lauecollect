"""
Author: Friedrich Schotte
Date created: 2021-06-01
Date last modified: 2021-06-01
Revision comment:
"""
__version__ = "1.0"


def is_array(obj):
    from numpy import ndarray
    return isinstance(obj, (list, tuple, ndarray))
