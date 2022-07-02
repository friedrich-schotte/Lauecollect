"""
This is to play sound in a GUI application

Author: Friedrich Schotte
Date created: 2019-11-13
Date last modified: 2019-11-13

"""
__version__ = "1.0"

from logging import debug,info,warn,error
from traceback import format_exc

class SoundControl(object):
    from persistent_property import persistent_property
    value = persistent_property("value","int(time()/5) % 2")
    event = persistent_property("event",[1,0]) # [1,0] - transition from 1 to 0
    sound = persistent_property("sound","ding")

    def __init__(self,parent=None,name="SoundControl",globals=None,locals=None):
        """parent: not used (for compatibility with WX controls)
        name: used for properties in settings file
        globals: used for eval
        locals: used for eval
        """
        self.parent = parent
        self.name = name
        self.globals = globals
        self.locals = locals
        
        self.previous_value = None
        self.current_value = None
        self.monitor = True

    from thread_property_2 import thread_property

    @thread_property
    def monitor(self):
        while not self.monitor_cancelled:
            if self.parent_window_closed:
                debug("Window closed")
                break
            from time import time 
            if self.globals: self.globals["time"] = time # for eval
            try: self.current_value = eval(self.value,self.globals,self.locals)
            except Exception as x:
                warn("%s: %r: %s\n%s" % (self.name,self.value,x,format_exc()))
                self.current_value = None
            self.last_event = [self.previous_value,self.current_value]
            if self.last_event == self.event: self.play_sound()
            self.previous_value = self.current_value
            from time import sleep
            sleep(0.5)
        debug("Sound off")

    def play_sound(self):
        from sound import play_sound
        play_sound(self.sound)

    def get_parent_window_closed(self):
        window_closed = False
        if self.parent is not None and hasattr(self.parent,"IsBeingDeleted"):
            try: window_closed = self.parent.IsBeingDeleted()
            except: window_closed = True
        return window_closed
    parent_window_closed = property(get_parent_window_closed)
            

if __name__ == '__main__':
    from pdb import pm

    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s",
    )
    print("self = SoundControl()")
