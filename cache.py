"""Caching
Author: Friedrich Schotte
Date created: 2018-10-24
Date last modified: 2018-10-31
"""
__version__ = "1.0.1" # only update file if changed

from logging import debug,info,warn,error

class Cache(object):
    def __init__(self,name="cache"):
        self.name = name
        
    def set(self,key,data):
        """Temporarily store binary data for fast restreival
        key: string"""
        if data != self.get(key) or not self.exists(key):
            from os.path import exists,dirname
            from os import makedirs
            filename = self.filename(key)
            if not exists(dirname(filename)): makedirs(dirname(filename))
            try: file(filename,"wb").write(data)
            except Exception,msg: warn("%s: %s" % (filename,msg))

    def get(self,key):
        """Retreive temporarily stored binary data
        key: string"""
        filename = self.filename(key)
        try: data = file(filename,"rb").read()
        except: data = ""
        return data

    def exists(self,key):
        """Retreive temporarily stored binary data
        key: string"""
        from os.path import exists
        return exists(self.filename(key))

    def clear(self):
        """Erase temporarily stored binary data"""
        from shutil import rmtree
        try: rmtree(self.dir)
        except: pass

    def get_size(self):
        """How many cached data objects are there?"""
        from os import listdir
        try: return len(listdir(self.dir))
        except: return 0
    def set_size(self,value):
        if value == 0: self.clear()
    size = property(get_size,set_size)

    def filename(self,key):
        """Where to store the data associated with key"""
        # If the key exceeds 254 characters, it needs to be shortened
        # by hashing, otherwise the file system would not allow it
        # to be used as a filename.
        key = key.replace(":","_")
        key = key.replace("/","_")
        filename = self.dir+"/"+key
        return filename

    @property
    def dir(self):
        """Where to store temparary files"""
        from tempfile import gettempdir
        basedir = gettempdir()
        dir = basedir+"/"+self.name
        return dir

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging # for debugging
    from time import time # for timing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    cache = Cache("CA")
    PV_name = "NIH:TIMING.registers.cmcnd.count"
    print('cache.get(PV_name) # should be 20228')
    print('cache.set(PV_name,"20228")')
