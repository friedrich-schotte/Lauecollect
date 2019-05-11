#!/usr/bin/env python
"""Efficient vectorized version of "exists".
Friedrich Schotte, Dec 2014 - 27 Feb 2017"""

__version__ = "1.0.2" # global var for caching, exist_files returns array

timeout = 10.0
directories = {}

def exist_files(filenames):
    """filenames: list of pathnames
    return value: list of booleans"""
    from os import listdir
    from os.path import exists,dirname,basename
    from time import time
    from normpath import normpath
    from numpy import array
    exist_files = []
    for f in filenames:
        d = dirname(f)
        if not d in directories or time() - directories[d]["time"] > timeout:
            try: files = listdir(normpath(d) if d else ".")
            except OSError: files = []
            directories[d] = {"files":files,"time":time()}
        exist_files += [basename(f) in directories[d]["files"]]
    exist_files = array(exist_files)
    return exist_files
