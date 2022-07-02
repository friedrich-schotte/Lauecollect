#!/usr/bin/env python
"""
File system interface of "sequencer" system driver
Author: Friedrich Schotte
Date created: 2020-06-01
Date last modified: 2021-08-27
Revision comment: Added: next_queue_repeat_count
"""
__version__ = "1.2"

import logging
logger = logging.getLogger(__name__)
if not logger.level: logger.level = logging.INFO
debug   = logger.debug
info    = logger.info
warning = logger.warning
error   = logger.error

from traceback import format_exc

class Timing_System_Simulator_Sequencer_Sysctl(object):
    def __init__(self,sequencer):
        self.sequencer = sequencer
        
    def __repr__(self):
        return "%s(%r)" % (type(self).__name__,self.sequencer)
    
    types = {
        "version": str,
        "buffer_size": int,
        "interrupt_handler_enabled": int,
        "queue_name": str,
        "next_queue_name": str,
        "default_queue_name": str,
        "descriptor": str,
        "next_queue_sequence_count": int,
        "next_queue_repeat_count": int,
        "current_sequence": str,
        "current_sequence_length": int,
        "phase_matching_period": int,      
    }
    names = list(types.keys())

    def operation(self,name,filename,*args,**kwargs):
        result = self.default_values.get(name,None)
        if hasattr(self,name):
            operation = getattr(self,name)
            try: result = operation(filename,*args,**kwargs)
            except: error("%s" % format_exc())
        ##debug("%s %.80r:,%.80r: %.80r" % (name,filename,args,result))
        return result
    
    default_values = {
        "get_file": b"",    
        "exists_file": False,    
        "file_size": 0,
        "expand_filename_pattern": [],
    }

    def put_file(self,filename,content):
        debug("%.80r, %.80r" % (filename,content))
        name = self.name(filename)
        content = content.rstrip(b"\n")
        if name in self.names:
            value = None
            type = self.types[name]
            if type == bytes:
                value = content
            elif type == str:
                try: value = content.decode("utf-8")
                except: error("%s: %s(%r): %s" % (filename,type,content,format_exc()))
            else:
                try: value = type(content)
                except Exception as x: error("%s: %s(%r): %s" % (filename,type,content,x))
            if value is not None:
                setattr(self.sequencer,name,value)
        else: error("%r: cannot create" % filename)

    def get_file(self,filename):
        content = b""
        name = self.name(filename)
        if name in self.names:
            try: value = getattr(self.sequencer,name)
            except: error("%s" % format_exc())
            else:
                dtype = self.types[name]
                try: value = dtype(value)
                except: error("%s: %r(%r): %s" % (name,dtype,value,format_exc()))
                if type(value) == bytes: 
                    content = value
                elif type(value) == str: 
                    content = value.encode("utf-8")
                else: 
                    content = str(value).encode("utf-8")
        elif name == "":
            content = "".join([n+"\n" for n in self.names])
            content = content.encode("utf-8")
        else: error("%r: No such file or directory" % filename)
        ##debug("%.80r: %.80r" % (filename,content))
        return content
     
    def del_file(self,filename):
        debug("%.80r" % filename)

    def exists_file(self,filename):
        name = self.name(filename)
        file_exists = name in self.names
        debug("%.80r: %r" % (filename,file_exists))
        return file_exists

    def file_size(self,filename):
        size = 0
        debug("%.80r: %r" % (filename,size))
        return size
    
    def expand_filename_pattern(self,filename_pattern):
        filenames = ["/"+n for n in self.names]
        debug("%.80r: %r" % (filename_pattern,filenames))
        return filenames
        
    def name(self,filename):
        return filename.replace("/","")


if __name__ == "__main__":
    from pdb import pm
    import logging
    for handler in logging.root.handlers: logging.root.removeHandler(handler)
    format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    level = logging.DEBUG
    logging.basicConfig(level=level,format=format)
    
    from timing_system_simulator import timing_system_simulator
    timing_system = timing_system_simulator("LaserLab")
    sysctl = timing_system.sequencer.sysctl
    
    self = sysctl
    
    print("self")
