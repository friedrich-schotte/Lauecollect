#!/usr/bin/env python
"""Efficient vectorized version of "exists".
Friedrich Schotte, Dec 2014 - 16 Mar 2017"""
__version__ = "1.1.2" # tunred off debug messages

from logging import debug,info,warn,error

checktime = 10.0 # every how namy seconds to check a directory modification time
directories = {}

def exists(filename):
    """Does the give file exist?"""
    from os.path import dirname,basename
    return directory(dirname(filename)).contains(basename(filename))

def exist_files(filenames):
    """filenames: list of pathnames
    return value: list of booleans"""
    from numpy import array
    return array([exists(f) for f in filenames],dtype=bool) # dtype needed for zero lenght

def directory(pathname):
    """Cached directory info"""
    if not pathname in directories: directories[pathname] = Directory(pathname)
    return directories[pathname]

class Directory(object):
    """Cached directory info"""
    def __init__(self,pathname):
        self.pathname = pathname
        self.checktime = 0
        self.mtime = 0
        self.__files__ = []

    @property
    def files(self):
        """Contents of directory as relative filenames"""
        from time import time
        from normpath import normpath
        from os import listdir
        if time() - self.checktime > checktime:
            mtime = getmtime(self.pathname)
            if mtime != self.mtime:
                self.mtime = mtime
                ##debug("exists: reading dir %r" % self.pathname)
                pathname = normpath(self.pathname) if self.pathname else "."
                try: self.__files__ = set(listdir(pathname))
                except OSError: self.__files__ = set()
            self.checktime = time()
        return self.__files__

    def contains(self,filename):
        """filename: relative pathname"""
        return filename in self.files

def getmtime(pathname):
    """Modification timestamp of file or directory or 0 if it does nor exists"""
    ##debug("exists: checking timestamp of %r" % pathname)
    from os.path import getmtime
    try: return getmtime(pathname)
    except: return 0

if __name__ == "__main__":
    import sys; sys.path += ["../../TReX/Python"] # location of table module
    from table import table
    from os.path import dirname
    from time import time
    import os.path
    ##import logging; logging.basicConfig(level=logging.DEBUG)
    logfile = "/Volumes/data/anfinrud_1702/Data/WAXS/NaCl/NaCl-ramp-1/NaCl-ramp-1.log"
    ##logfile = "/Volumes/data/anfinrud_1702/Data/WAXS/Water/Water-3/Water-3.log"
    def image_filenames(logfile):
        return dirname(logfile)+"/xray_images/"+table(logfile,separator="\t").file        
    print("t = time(); filenames = image_filenames(logfile); time()-t")
    ##print("t = time(); e = exist_files(filenames); time()-t")
    print("t = time(); e = [exists(f) for f in filenames]; time()-t")
    print("t = time(); e = [os.path.exists(f) for f in filenames]; time()-t")
