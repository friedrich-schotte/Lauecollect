#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-05-29
Date last modified: 2020-06-03
Revision comment: Added: module logger
"""
__version__ = "1.0.1"

import logging
logger = logging.getLogger(__name__)
if not logger.level: logger.level = logging.INFO
debug   = logger.debug
info    = logger.info
warning = logger.warning
error   = logger.error

from traceback import format_exc

class Timing_System_Simulator_Overlay_File_System(object):
    mount_points = {}
    
    def __init__(self,timing_system):
        self.timing_system = timing_system
        self.mount(self.timing_system.sequencer.sysctl,"/proc/sys/dev/sequencer")
        
    def __repr__(self):
        return "%s(%r)" % (type(self).__name__,self.timing_system)

    from alias_property import alias_property
    name = alias_property("timing_system.name")
    
    def mount(self,file_system,mount_point):
        self.mount_points[mount_point] = file_system

    def put_file(self,filename,content):
        self.operation("put_file",filename,content)

    def get_file(self,filename):
        return self.operation("get_file",filename)
     
    def del_file(self,filename):
        self.operation("del_file",filename)

    def exists_file(self,filename):
        return self.operation("exists_file",filename)

    def file_size(self,filename):
        return self.operation("file_size",filename)
    
    def expand_filename_pattern(self,filename_pattern):
        return self.operation("expand_filename_pattern",filename_pattern)
    
    def operation(self,name,filename,*args,**kwargs):
        ##debug("%s %.80r,%.80r..." % (name,filename,args))
        result = self.default_values.get(name,None)
        fs = self.file_system(filename)
        path = self.path(filename)
        mount_point = self.mount_point(filename)
        try: result = fs.operation(name,path,*args,**kwargs)
        except: error("%s" % format_exc())
        if type(result) == list: result = [mount_point+f for f in result]
        debug("%s %.80r,%.80r: %.80r" % (name,filename,args,result))
        return result
    
    default_values = {
        "get_file": b"",    
        "exists_file": False,    
        "file_size": 0,
        "expand_filename_pattern": [],
    }
    
    def file_system(self,filename):
        for mount_point,file_system in self.mount_points.items():
            if filename.startswith(mount_point): break
        else: file_system = self.timing_system.file_system
        return file_system
        
    def path(self,filename):
        for mount_point,file_system in self.mount_points.items():
            if filename.startswith(mount_point):
                path = filename[len(mount_point):]
                break
        else: path = filename
        return path

    def mount_point(self,filename):
        for mount_point,file_system in self.mount_points.items():
            if filename.startswith(mount_point): break
        else: mount_point = ""
        return mount_point

if __name__ == "__main__":
    from pdb import pm
    import logging
    for handler in logging.root.handlers: logging.root.removeHandler(handler)
    format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    level = logging.DEBUG
    logging.basicConfig(level=level,format=format)
    
    from timing_system_simulator import timing_system_simulator
    timing_system = timing_system_simulator("LaserLab")
    file_system = timing_system.overlay_file_system
    
    self = file_system
    
    print("self.get_file('/')")
    print("self.get_file('/tmp/sequencer_fs')")
    print("self.get_file('/tmp/sequencer_fs/queue1')")
    print("self.get_file('/proc/sys/dev/sequencer')")
    print("self.get_file('/proc/sys/dev/sequencer/buffer_size')")
    print("self.expand_filename_pattern('/proc/sys/dev/sequencer/*')")
