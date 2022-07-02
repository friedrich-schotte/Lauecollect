#!/usr/bin/env python
"""Efficient vectorized version of "exists".
Author: Friedrich Schotte,
Date created: 2014-12-01
Date last modified: 2021-10-21
Revision comment: Issue: exist_files([]) -> array([], dtype=float64)
    existing = exist_files(filenames)
    filenames = filenames[existing]
    IndexError: arrays used as indices must be of integer (or boolean) type
"""

__version__ = "1.0.3"

timeout = 10.0
directories = {}


def exist_files(filenames):
    """filenames: list of pathnames
    return value: list of booleans"""
    from os import listdir
    from os.path import dirname, basename
    from time import time
    from normpath import normpath
    from numpy import array
    exist_files = []
    for f in filenames:
        d = dirname(f)
        if d not in directories or time() - directories[d]["time"] > timeout:
            try:
                files = listdir(normpath(d) if d else ".")
            except OSError:
                files = []
            directories[d] = {"files": files, "time": time()}
        exist_files += [basename(f) in directories[d]["files"]]
    exist_files = array(exist_files, dtype=bool)
    return exist_files
