"""Base class for event-based device drivers
Author: Friedrich Schotte
Date created: 2019-08-15
Date last modified: 2022-07-02
Revision comment: pylint
"""
__version__ = "1.0.1"

import logging
from record import Record


class EPICS_Record(Record):

    def get_started(self):
        from CAServer import casget
        return all([casget(self.prefix + name) is not None for name in self.names])

    def set_started(self, started):
        if started != self.started:
            if started:
                self.start()
            else:
                self.stop()

    started = property(get_started, set_started)
    EPICS_enabled = started

    def start(self):
        from CAServer import casput, casmonitor
        for name in self.names:
            casput(self.prefix + name, getattr(self, name), update=False)
        for name in self.names:
            casmonitor(self.prefix + name, callback=self.on_PV_change)
        for name in self.names:
            self.monitor(name, self.on_property_change, name)

    def stop(self):
        from CAServer import casdel
        for name in self.names:
            casdel(self.prefix + name)

    @property
    def names(self):
        return [name for name in dir(self) if name.isupper()]

    def get_prefix(self):
        prefix = self.__name__
        if not prefix.endswith("."):
            prefix += "."
        return prefix

    def set_prefix(self, prefix):
        self.__name__ = prefix.rstrip(".")

    prefix = property(get_prefix, set_prefix)

    def on_PV_change(self, PV_name, value, _formatted_value):
        logging.debug(f"{self.__name__}.{PV_name} = {value!r}")
        name = PV_name.replace(self.prefix, "", 1)
        setattr(self, name, value)

    def on_property_change(self, name):
        new_value = getattr(self, name)
        logging.debug(f"{self.__name__}.{name} = {new_value!r}")
        from CAServer import casput
        casput(self.prefix + name, new_value, update=False)


if __name__ == "__main__":
    msg_format = "%(asctime)s: %(levelname)s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)


    class Test_Record(EPICS_Record):
        TEST = 0


    self = Test_Record("TESTBENCH:TEST")
    print('self.started = True')
    print('self.TEST += 1')
    from CAServer import casget, casput

    print('casget("TESTBENCH:TEST.TEST")')
    print('casput("TESTBENCH:TEST.TEST",1)')

    print('from CA import caget, caput, camonitor')
    print('caget("TESTBENCH:TEST.TEST")')
    print('caput("TESTBENCH:TEST.TEST",1)')
    print('camonitor("TESTBENCH:TEST.TEST")')
