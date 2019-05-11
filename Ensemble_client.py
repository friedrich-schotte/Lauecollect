#!/bin/env python
from __future__ import with_statement
"""
Friedrich Schotte, 31 Jan 2016 - 31 Oct 2017
"""

from pdb import pm # for debugging
from logging import debug,warn,error 

__version__ = "1.0.4" # "if value == "": ..." FutureWarning: elementwise comparison failed

verbose_logging = True

class EnsembleClient(object):
    """"""
    __attributes__ = [
        "ip_address_and_port",
        "caching_enabled",
        "connection",
        "integer_registers_","floating_point_registers_",
        "integer_registers","floating_point_registers",
        "ip_address","port",
        "write","send","query",
    ]

    name="Ensemble"
    from persistent_property import persistent_property
    ip_address_and_port = persistent_property("ip_address",
        "nih-instrumentation.cars.aps.anl.gov:2000")
    caching_enabled = persistent_property("caching_enabled",True)

    timeout = 5.0
    # This is to make the query method multi-thread safe.
    from thread import allocate_lock
    lock = allocate_lock()

    def __init__(self):
        """ip_address may be given as address:port. If :port is omitted, port
        number 2000 is assumed."""
        self.connection = None # network connection
        self.integer_registers_ = ArrayWrapper(self,"integer_registers")
        self.floating_point_registers_ = ArrayWrapper(self,"floating_point_registers")
        self.integer_registers = CachedArrayWrapper(self,"integer_registers")
        self.floating_point_registers = CachedArrayWrapper(self,"floating_point_registers")

    def __repr__(self):
        return "EnsembleClient('"+self.ip_address+":"+str(self.port)+"')"

    def get_ip_address(self):
        return self.ip_address_and_port.split(":")[0]
    def set_ip_address(self,value):
        self.ip_address_and_port = value+":"+str(self.port)
    ip_address = property(get_ip_address,set_ip_address)

    def get_port(self):
        if not ":" in self.ip_address_and_port: return 2000
        return int(self.ip_address_and_port.split(":")[-1])
    def set_port(self,value):
        self.ip_address_and_port = str(self.ip_address)+":"+str(value)
    port = property(get_port,set_port)

    def write(self,command):
        """Sends a command to the server that does not generate a reply,
        e.g. "ClearSweeps.ActNow()" """
        debug("write %s" % torepr(command))
        import socket
        command = command.replace("\n","") # "\n" is command terminator.
        if not command.endswith("\n"): command += "\n"
        with self.lock: # Allow only one thread at a time inside this function.
            for attempt in range(1,2):
                try:
                    if self.connection == None:
                        self.connection = socket.socket()
                        self.connection.settimeout(self.timeout)
                        self.connection.connect((self.ip_address,self.port))
                    # Flush reception buffer before sending.
                    self.connection.settimeout(1e-6)
                    try: junk = self.connection.recv(65536)
                    except socket.timeout: pass
                    self.connection.settimeout(self.timeout)
                    self.connection.sendall (command)
                    return
                except Exception,message:
                    error("write %s attempt %d/3 failed: %s" %
                        (torepr(command),attempt,message))
                    self.connection = None
    send = write

    def query(self,command):
        """To send a command that generates a reply, e.g. "InstrumentID.Value".
        Returns the reply"""
        debug("query %s" % torepr(command))
        import socket
        command = command.replace("\n","") # "\n" is command terminator.
        if not command.endswith("\n"): command += "\n"
        reply = ""
        with self.lock: # Allow only one thread at a time inside this function.
            for attempt in range(1,2):
                try:
                    if self.connection == None:
                        self.connection = socket.socket()
                        self.connection.settimeout(self.timeout)
                        self.connection.connect((self.ip_address,self.port))
                    # Flush reception buffer before sending.
                    self.connection.settimeout(1e-6)
                    try: junk = self.connection.recv(65536)
                    except socket.timeout: pass
                    self.connection.settimeout(self.timeout)
                    self.connection.sendall (command)
                    reply = self.connection.recv(65536)
                    while reply.find("\n") == -1:
                        reply += self.connection.recv(65536)
                    debug("reply %s" % torepr(reply))
                    return reply.rstrip("\n")
                except Exception,message:
                    error("query %s attempt %d/3 failed: %s "
                        "(reply=%s, %r bytes)" %
                        (torepr(command),attempt,message,torepr(reply),len(reply)))
                    self.connection = None
            return ""

    def __getattr__(self,name):
        """A property"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute wasn't found the usual ways.
        if name.startswith("__") and name.endswith("__"):
            return object.__getattribute__(self,name)
        ##debug("EnsembleWrapper.__getattr__(%r)" % name)
        value = self.query("ensemble."+name)
        ##debug("Got reply %s" % torepr(value))
        if "ArrayWrapper(" in value:
            value = value.replace("ArrayWrapper(","").replace(")","")
        from numpy import array,nan,int32,float32,float64 # for eval
        try: value = eval(value)
        except: pass
        return value

    def __setattr__(self,name,value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        alt_name = name.replace("_on",".on")
        if (name.startswith("__") and name.endswith("__")) or \
            name in self.__attributes__:
            object.__setattr__(self,name,value)
        else: self.write("ensemble.%s = %r" % (name,value))

class ArrayWrapper(object):
    def __init__(self,object,name):
        self.object = object
        self.name = name

    def __getitem__(self,index):
        """Called when [0] is used.
        index: integer or list/array of intergers or array of booleans"""
        ##debug("ArrayWrapper.__getitem__(%r)" % (index,))
        command = ("ensemble.%s[%r]" % (self.name,index))
        value = self.object.query(command)
        if "ArrayWrapper(" in value:
            value = value.replace("ArrayWrapper(","").replace(")","")
        from numpy import array,nan,int32,float32,float64 # for eval
        try: value = eval(value)
        except Exception,msg:
            debug("%s: %s" % (torepr(value),msg))
            self.last_reply = value # for debugging
            value = self.default_value(index)
        if type(value) == str and value == "":
            value = self.default_value(index)
        debug("Ensemble: Value: %s" % torepr(value))
        return value

    def __setitem__(self,index,value):
        """Called when [0]= is used.
        index: single index, slice or list of indices
        value: single value or array of values"""
        ##debug("ArrayWrapper.__setitem__(%r,%r)" % (index,value))
        command = ("ensemble.%s[%r] = %r" % (self.name,index,value))
        self.object.send(command)

    def __len__(self):
        """Length of array. Called when len(x) is used."""
        command = ("len(ensemble.%s)" % (self.name))
        value = self.object.query(command)
        try: value = eval(value)
        except Exception,msg:
            debug("%s: %s" % (torepr(value),msg))
            value = 0
        return value

    def default_value(self,index):
        """Return this when a comminocation error occurs"""
        from numpy import array,nan
        if type(index) != slice and not hasattr(index,"__len__"): return nan
        return array([nan]*len(tolist(index)))


class CachedArrayWrapper(ArrayWrapper):
    def __init__(self,object,name):
        ArrayWrapper.__init__(self,object,name)
        self.cache = {}

    def __getitem__(self,index):
        """Called when [0] is used.
        index: integer or list/array of intergers or array of booleans"""
        ##debug("CachedArrayWrapper.__getitem__(%r)" % (index,))
        from numpy import array
        items = tolist(index,len(self))
        cache = dict(self.cache)
        if self.caching_enabled:
            items_to_get = [i for i in items if not i in cache]
        else: items_to_get = items
        if len(items_to_get) > 0:
            new_values = ArrayWrapper.__getitem__(self,items_to_get)
            for (i,v) in zip(items_to_get,new_values): cache[i]=v
        values = array([cache[i] for i in items])
        if isscalar(index): values = values[0]
        return values

    def __len__(self):
        """Length of array. Called when len(x) is used."""
        if not "__len__" in self.cache or not self.caching_enabled: 
            self.cache["__len__"] = ArrayWrapper.__len__(self)
        return self.cache["__len__"]

    def __setitem__(self,index,value):
        """Called when [0]= is used.
        index: single index, slice or list of indices
        value: single value or array of values"""
        ##debug("CachedArrayWrapper.__setitem__(%r,%r)" % (index,value))
        from numpy import atleast_1d
        ArrayWrapper.__setitem__(self,index,value)
        items = tolist(index,len(self))
        values = atleast_1d(value)
        for (i,v) in zip(items,values): self.cache[i]=v

    def get_caching_enabled(self): return self.object.caching_enabled
    def set_caching_enabled(self,value): self.object.caching_enabled = value
    caching_enabled = property(get_caching_enabled,set_caching_enabled)


def timestamp():
    """Current date and time as formatted ASCII text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3] # omit microsconds

def torepr(x,nchars=80):
    """limit string length using ellipses (...)"""
    s = repr(x)
    if len(s) > nchars: s = s[0:nchars-10-3]+"..."+s[-10:]
    return s

def tolist(index,length=1000):
    """Convert index (which may be a slice) to a list"""
    from numpy import atleast_1d,arange
    index_list = atleast_1d(arange(0,length)[index])
    ##debug("tolist: converted %s to %s" % (torepr(index),torepr(index_list)))
    return index_list

def isscalar(x):
    if hasattr(x,"__len__") or type(x) == slice: return False
    return True


ensemble = EnsembleClient()


if __name__ == "__main__": # for testing
    import logging
    from tempfile import gettempdir
    logfile = gettempdir()+"/lauecollect_debug.log"
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    from pdb import pm # for debugging
    self = ensemble # for debugging
    print('ensemble.ip_address = %r' % ensemble.ip_address)
    print('ensemble.caching_enabled = %r' % ensemble.caching_enabled)
    print('ensemble.program_filename = "Home (safe).ab"')
    print('ensemble.program_filename = "PVT_Fly-thru.ab"')
    print('ensemble.program_filename')
    print('ensemble.program_running')
    print('ensemble.floating_point_registers[0]')
    print('ensemble.floating_point_registers[0] = -1')
