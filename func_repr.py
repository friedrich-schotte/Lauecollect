#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-04-21
Date last modified: 2020-12-17
Revision comment: Using __qualname__
"""
__version__ = "1.1"


def func_repr(func, *args, **kwargs):
    s = ""
    if hasattr(func, "__module__"):
        s += func.__module__ + "."
    if hasattr(func, "__self__"):
        s += repr(func.__self__) + "."
    if hasattr(func, "__qualname__"):
        s += func.__qualname__
    elif hasattr(func, "__name__"):
        s += func.__name__
    else:
        s += repr(func)
    for arg in args:
        s += ",%r" % (arg,)
    for key in kwargs:
        s += ",%s=%r" % (key, kwargs[key])
    return s
