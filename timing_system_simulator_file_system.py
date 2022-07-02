#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-05-29
Date last modified: 2020-06-19
Revision comment: Added: reset
"""
__version__ = "1.1"

import logging
logger = logging.getLogger(__name__)
if not logger.level: logger.level = logging.INFO
debug   = logger.debug
info    = logger.info
warning = logger.warning
error   = logger.error

from traceback import format_exc

class Timing_System_Simulator_File_System(object):
    def __init__(self,timing_system):
        self.timing_system = timing_system
        self.monitors = {}
        
    def __repr__(self):
        return "%s(%r)" % (type(self).__name__,self.timing_system)

    def reset(self):
        self.del_file("/tmp")
        self.make_dir("/tmp/sequencer_fs")

    from alias_property import alias_property
    name = alias_property("timing_system.name")

    def operation(self,name,filename,*args,**kwargs):
        result = self.default_values.get(name,None)
        if hasattr(self,name):
            operation = getattr(self,name)
            try: result = operation(filename,*args,**kwargs)
            except: error("%s" % format_exc())
        debug("%s %.80r: %.80r" % (name,args,result))
        return result
    
    default_values = {
        "get_file": b"",    
        "exists_file": False,    
        "file_size": 0,
        "expand_filename_pattern": [],
    }

    def put_file(self,filename,content):
        debug("%.80r, %.80r" % (filename,content))
        from os.path import dirname
        if not self.exists_file(dirname(filename)): 
            self.make_dir(dirname(filename))

        new_file = not self.exists_file(filename)
        open(self.path(filename),"wb").write(content)
        if new_file: self.notify(dirname(filename))
        self.notify(filename)

    def get_file(self,filename):
        content = b""
        path = self.path(filename)
        from os.path import isfile,isdir
        if isfile(path):
            try: content = open(path,"rb").read()
            except OSError: pass 
        if isdir(path):
            from os import listdir
            try: filenames = listdir(path)
            except OSError: filenames = []
            filenames = [f.encode("utf-8") for f in filenames]
            content = b"".join([f+b"\n" for f in filenames])
        debug("%.80r: %.80r" % (filename,content))
        return content

    def del_file(self,filename):
        debug("%.80r" % filename)
        from os.path import dirname,exists
        if exists(self.path(filename)):
            from remove import remove
            try: remove(self.path(filename))
            except OSError: pass
            if not exists(self.path(filename)):
                self.notify(dirname(filename))
                self.notify(filename)

    def exists_file(self,filename):
        from os.path import exists
        file_exists = exists(self.path(filename))
        debug("%.80r: %r" % (filename,file_exists))
        return file_exists

    def file_size(self,filename):
        size = 0
        from os.path import getsize
        try: size = getsize(self.path(filename))
        except OSError: pass 
        debug("%.80r: %r" % (filename,size))
        return size
    
    def expand_filename_pattern(self,filename_pattern):
        from glob import glob
        paths = glob(self.path(filename_pattern))
        filenames = self.filenames(paths)
        debug("%.80r: %r" % (filename_pattern,filenames))
        return filenames

    def make_dir(self,directory):
        debug("%.80r" % directory)
        from os.path import exists,dirname
        if not exists(self.path(directory)):
            from os import makedirs
            makedirs(self.path(directory))
            self.notify(dirname(directory))
    
    def monitor_file(self,filename,proc,*args,**kwargs):
        from handler import Handler
        handler = Handler(proc,*args,**kwargs)
        if not filename in self.monitors:
            self.monitors[filename] = set()
        if not handler in self.monitors[filename]:
            self.monitors[filename].add(handler)
     
    def monitor_clear_file(self,filename,proc,*args,**kwargs):
        from handler import Handler
        handler = Handler(proc,*args,**kwargs)
        if handler in self.monitors.get(filename,set()):
            self.monitors[filename].remove(handler)

    def monitors_file(self,filename):
        return self.monitors.get(filename,set())
    
    def notify(self,filename):
        for handler in self.monitors.get(filename,set()):
            try: handler()
            except: error("%s: %r: %s" % (filename,handler,format_exc()))

    def path(self,filename):
        return self.root+filename
    
    def filenames(self,paths):
        root = self.root
        filenames = [f.replace(root,"",1) for f in paths]
        return filenames

    @property
    def root(self):
        return self.timing_system.directory+"/files"
    
    
if __name__ == "__main__":
    from pdb import pm
    import logging
    for handler in logging.root.handlers: logging.root.removeHandler(handler)
    format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    level = logging.DEBUG
    logging.basicConfig(level=level,format=format)
    
    from timing_system_simulator import timing_system_simulator
    timing_system = timing_system_simulator("LaserLab")
    file_system = timing_system.file_system
    
    self = file_system

    def report(filename): info("%s: %s" % (filename,self.get_file(filename)))    
    print("self.monitor_file('/tmp/sequencer_fs',report,'/tmp/sequencer_fs')")
    print("self.get_file('/tmp/sequencer_fs/test')")
    print("self.del_file('/tmp/sequencer_fs/test')")
    print("self.put_file('/tmp/sequencer_fs/test',b'test')")
    