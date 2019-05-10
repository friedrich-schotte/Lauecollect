"""
A propery object to be used inside a class
Author: Friedrich Schotte
Date created: 2018-11-01
Date last modified: 2019-03-06
"""
from logging import debug,warn,info,error
__version__ = "2.0.1" # debug messages

def thread_property(method):
    """A property representing an task to be run in background"""
    name = method.__name__
    thread_name    = name+"_thread"
    cancelled_name = name+"_cancelled"
    def get_running(self):
        thread = getattr(self,thread_name,None)
        return thread is not None and thread.isAlive()
    def set_running(self,running_requested):
        running = get_running(self)
        if running_requested and not running:
            from threading import Thread
            thread = Thread(target=run,args=(self,),name=thread_name)
            thread.daemon = True
            setattr(self,thread_name,thread)
            setattr(self,cancelled_name,False)
            thread.start()
        if not running_requested and running:
            setattr(self,cancelled_name,True)
    def run(self):
        debug("Starting %s..." % name)
        method(self)
        debug("%s finished" % name)
    running = property(get_running,set_running)
    return running


if __name__ == "__main__":
    from pdb import pm
    class Test(object):
        @thread_property
        def running(self):
            from time import time,sleep
            t0 = time()
            while time()-t0 < 10 and not self.running_cancelled:
                sleep(0.1)
    test = Test()
    print("test.running = True")
    print("test.running")
    print("test.running = False")

