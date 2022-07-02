"""
A propery object to be used inside a class that represents a thread
of execution

Example:

class Test(object):
    sleeping = action_property("self.sleep(10)",
        stop="self.cancelled = True")

    def sleep(self,duraction):
        self.cancelled = False
        from time import time,sleep
        t = time()
        while time() - t < duration and not self.cancelled: sleep(0.05)

    cancelled = False

test = Test()
test.sleeping = True
test.sleeping = False

Author: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2017-10-17
Date last modified: 2019-10-31
"""
__version__ = "1.0.5" # Python 3 compatibility, documentation, example

from logging import debug,info,warn,error

def action_property(command,stop="",locals=None,globals=None,timeout=30):
    """
    command: executable string
    stop: executable string
    locals: context for execution
    globals: context for execution
    timeout: seconds
    """
    from DB import db,dbset
    from time import time
    def running(self):
        class_name = getattr(self,"name",self.__class__.__name__)
        running = db("%s.%s.running" % (class_name,command),False)
        timeout_start = db("%s.%s.timeout_start" % (class_name,command),0.0)
        timed_out = time() - timeout_start > timeout
        return running and not timed_out
    def set_running(self,value):
        class_name = getattr(self,"name",self.__class__.__name__)
        dbset("%s.%s.running" % (class_name,command),value)
        dbset("%s.%s.timeout_start" % (class_name,command),time())
    def run(self):
        info("action: starting %r..." % command)
        try: exec(command,globals,locals)
        except Exception as msg: error("action: %r: %s" % (command,msg))
        info("action: finished %r" % command)
        set_running(self,False)
    def cancel(self):
        info("action: cancelling %r..." % stop)
        self.cancelled = True
        try: exec(stop,globals,locals)
        except Exception as msg: error("action: %r: %s" % (stop,msg))
        info("action: finished %r" % stop)
    def get_active(self):
        """Is procedure running?"""
        return running(self)
    def set_active(self,value):
        from threading import Thread
        if value:
            set_running(self,True)
            thread = Thread(target=run,args=(self,))
            thread.daemon = True
            thread.start()
        else:
            set_running(self,False)
            self.cancelled = True
            thread = Thread(target=cancel,args=(self,))
            thread.daemon = True
            thread.start()
    active = property(get_active,set_active)
    return active

if __name__ == "__main__":
    class Test(object):
        sleeping = action_property("self.sleep(10)",
            stop="self.cancelled = True")

        def sleep(self,duration):
            self.cancelled = False
            from time import time,sleep
            t = time()
            while time() - t < duration and not self.cancelled: sleep(0.05)

        cancelled = False

    test = Test()
    print("test.sleeping")
    print("test.sleeping = True")
    print("test.sleeping = False")
