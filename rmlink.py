"""
Usage:
from os import symlink
from rmlink import rmlink
shortcut = "/Data"
mountpoint = "/nfs/femto-data2/C/Data"
rmlink(shortcut)
symlink(mountpoint,shortcut)

Author: Friedrich Schotte
Date created: 2020-02-11
Date last mofified: 2020-02-11
"""
__version__ = "1.0"

def rmlink(pathname):
    """Remove a symbolic link or a directory containing only empty directories
    and symbolic links"""
    from os import listdir, remove, rmdir
    from os.path import isdir, exists, isfile 
    import os.path
    if exists(pathname) or os.path.islink(pathname):
        if not islink(pathname):
            raise IOError("%r is not a symbolic link and is not empty" % pathname)
        pathname = pathname.rstrip("/")
        if os.path.islink(pathname): remove(pathname)
        elif isfile(pathname) and ishidden(pathname): remove(pathname)
        elif isdir(pathname):
            entries = listdir(pathname)
            for entry in entries: rmlink(pathname+"/"+entry)
            rmdir(pathname)


def islink(pathname):
    """Is pathname a symbolic linke ro a directory containing no files except
    other directories or symbolic links?"""
    from os import listdir
    from os.path import isdir, isfile
    import os.path
    pathname = pathname.rstrip("/")
    if os.path.islink(pathname): return True
    elif isfile(pathname) and ishidden(pathname): return True
    elif isdir(pathname):
        entries = listdir(pathname)
        for entry in entries:
            if not islink(pathname+"/"+entry): return False
        return True
    else: return False


def ishidden(pathname):
    """Does the filename or a directory of thee pathname start with '.' (dot)?"""
    from os.path import dirname,basename
    if len(pathname) <= 1: return False # '/' ir '\\'
    if basename(pathname).startswith("."): return True
    elif ishidden(dirname(pathname)): return True

usage = """
from os import symlink
from rmlink import rmlink
from os import environ
home = environ["HOME"]
shortcut = home+"/Data"
mountpoint = home+"/nfs/femto-data2/C/Data"
rmlink(shortcut)
symlink(mountpoint,shortcut)
"""

if __name__ == "__main__":
    print(usage)
