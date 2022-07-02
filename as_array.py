"""
Author: Friedrich Schotte
Date created: 2021-09-28
Date last modified: 2021-09-28
Revision comment:
"""
__version__ = "1.0"


def as_array(value):
    if value is None:
        value = []
    elif not is_array(value):
        value = [value]
    return value


def is_array(obj):
    from numpy import ndarray
    return isinstance(obj, (list, tuple, ndarray))