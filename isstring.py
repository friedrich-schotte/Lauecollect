#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-06-09
Date last modified: 2020-06-09
Python Version: 2.7, 3.6
Revision comment: Cleanup
"""

__version__ = "1.0"

string_types = type(''),type(u''),type(b'')

def isstring(value):
    return isinstance(value,string_types)
