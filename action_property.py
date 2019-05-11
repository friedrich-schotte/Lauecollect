"""
Author: Friedrich Schotte
Date created: 2017-10-17
Date last modified: 2018-03-11
"""
__version__ = "1.0.3" # timeout

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
    from thread import start_new_thread
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
        try: exec command in locals,globals
        except Exception,msg: error("action: %r: %s" % (command,msg))
        info("action: finished %r" % command)
        set_running(self,False)
    def cancel(self):
        info("action: cancelling %r..." % stop)
        self.cancelled = True
        try: exec stop in locals,globals
        except Exception,msg: error("action: %r: %s" % (stop,msg))
        info("action: finished %r" % stop)
    def get_active(self):
        """Is procedure running?"""
        return running(self)
    def set_active(self,value):
        if value:
            set_running(self,True)
            start_new_thread(run,(self,))
        else:
            set_running(self,False)
            self.cancelled = True
            start_new_thread(cancel,(self,))
    active = property(get_active,set_active)
    return active
