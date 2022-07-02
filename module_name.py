#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-11-02
Date last modified: 2020-11-02
Revision comment:
"""
__version__ = "1.0"

def module_name(object):
    from inspect import getmodulename, getfile
    return getmodulename(getfile(object))
