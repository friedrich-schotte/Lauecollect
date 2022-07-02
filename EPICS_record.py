"""Base class for event-based device drivers
Author: Friedrich Schotte
Date created: 2019-08-15
Date last modified: 2019-08-15
"""
__version__ = "1.0"

from logging import debug,info,warning,error
from traceback import format_exc

from record import Record
class EPICS_Record(Record):

    def get_started(self):
        from CAServer import casget
        return all([casget(self.prefix+name) is not None for name in self.names])
    def set_started(self,value):
        if bool(value) == True:
            if not self.started: self.start()
        if bool(value) == False:
            if self.started: self.stop()
    started = property(get_started,set_started)
    EPICS_enabled = started
        
    def start(self):
        from CAServer import casput,casmonitor
        for name in self.names:
            casput(self.prefix+name,getattr(self,name),update=False)
        for name in self.names:
            casmonitor(self.prefix+name,callback=self.on_PV_change)
        for name in self.names:
            self.monitor(name,self.on_property_change,name)

    def stop(self):
        from CAServer import casdel
        for name in self.names:
            casdel(self.prefix+name)

    @property
    def names(self):
        return [name for name in dir(self) if name.isupper()]

    def get_prefix(self):
        prefix = self.__name__
        if not prefix.endswith("."): prefix += "."
        return prefix
    def set_prefix(self,prefix): self.__name__ = prefix.rstrip(".")
    prefix = property(get_prefix,set_prefix)

    def on_PV_change(self,PV_name,value,formatted_value):
        debug("%s.%s = %r" % (self.__name__,PV_name,value))
        name = PV_name.replace(self.prefix,"",1)
        setattr(self,name,value)

    def on_property_change(self,name):
        new_value = getattr(self,name)
        debug("%s.%s = %r" % (self.__name__,name,new_value))
        from CAServer import casput
        casput(self.prefix+name,new_value,update=False)


if __name__ == "__main__":
    from pdb import pm
    import logging
    format="%(asctime)s: %(levelname)s %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=format)

    class Test_Record(EPICS_Record):
        TEST = 0
        
    self =  Test_Record("TESTBENCH:TEST")
    print('self.started = True')
    print('self.TEST += 1')
    from CAServer import casget,casput
    print('casget("TESTBENCH:TEST.TEST")')
    print('casput("TESTBENCH:TEST.TEST",1)')
    from CA import caget,caput,camonitor
    print('caget("TESTBENCH:TEST.TEST")')
    print('caput("TESTBENCH:TEST.TEST",1)')
    print('camonitor("TESTBENCH:TEST.TEST")')
