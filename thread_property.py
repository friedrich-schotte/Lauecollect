"""
A propery object to be used inside a class
Author: Friedrich Schotte
Date created: 2018-11-01
"""
from logging import debug,warn,info,error
__version__ = "1.0" 

def thread_property(procedure_name):
    """A propery object to be used inside a class"""
    def get(self):
        thread = getattr(self,procedure_name+"_thread",None)
        return thread is not None and thread.isAlive()
    def set(self,value):
        if value != get(self):
            if value:
                procedure = getattr(self,procedure_name)
                from threading import Thread
                thread = Thread(target=procedure)
                setattr(self,procedure_name+"_thread",thread)
                thread.daemon = True
                self.cancelled = False
                thread.start()
            else: self.cancelled = True
    return property(get,set)


if __name__ == "__main__":
    from pdb import pm
    class Test(object):
        cancelled = False
        def procedure(self):
            from time import time,sleep
            t0 = time()
            while time()-t0 < 10 and not self.cancelled: sleep(0.1)
        procedure_running = thread_property("procedure")
    test = Test()
    print("test.procedure_running = True")
    print("test.procedure_running")
    print("test.cancelled = True")
