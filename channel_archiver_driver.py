#!/usr/bin/env python
"""
Archive EPICS process variables via Channel Access
Author: Friedrich Schotte
Date created: 2017-10-04
Date last modified: 2022-03-23
Revision comment: Simplified logfile
"""
__version__ = "1.3.8"

from logging import info
from cached_function import cached_function


@cached_function()
def channel_archiver_driver(domain_name):
    return Channel_Archiver_Driver(domain_name)


channel_archiver = channel_archiver_driver  # for backward compatibility


class Channel_Archiver_Driver(object):
    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.domain_name)

    def start(self):
        self.archiving_enabled = True

    def stop(self):
        self.archiving_enabled = False

    domain_name = "BioCARS"

    @property
    def db_name(self):
        return "channel_archiver/%s" % self.domain_name

    from db_property import db_property
    from monitored_property import monitored_property
    from monitored_value_property import monitored_value_property

    PVs = db_property("PVs", [])
    __archiving_requested__ = db_property("archiving_requested", True)
    __directory__ = db_property("directory", ".")
    monitored_PVs = []
    __archiving__ = monitored_value_property(default_value=False)
    __archiving_enabled__ = monitored_value_property(default_value=False)

    def get_archiving_enabled(self):
        return self.__archiving_enabled__

    def set_archiving_enabled(self, enabled):
        if enabled:
            self.archiving = self.archiving_requested
        else:
            self.archiving = False
        self.__archiving_enabled__ = enabled

    def inputs_archiving_enabled(self):
        from reference import reference
        return [reference(self, "__enabled__")]

    archiving_enabled = monitored_property(
        fget=get_archiving_enabled,
        fset=set_archiving_enabled,
        inputs=inputs_archiving_enabled,
    )

    def get_directory(self):
        from normpath import normpath
        return normpath(self.__directory__)

    def set_directory(self, value):
        self.__directory__ = value

    directory = property(get_directory, set_directory)

    def get_archiving_requested(self):
        return self.__archiving_requested__

    def set_archiving_requested(self, value):
        self.__archiving_requested__ = value
        self.archiving = value

    def inputs_archiving_requested(self):
        from reference import reference
        return [reference(self, "__archiving_requested__")]

    archiving_requested = monitored_property(
        fget=get_archiving_requested,
        fset=set_archiving_requested,
        inputs=inputs_archiving_requested,
    )

    def get_archiving(self):
        """Actively collecting data?"""
        return self.__archiving__

    def set_archiving(self, value):
        from threading import Thread
        if value:
            if not self.__archiving__:
                thread = Thread(target=self.keep_archiving)
                thread.daemon = True
                thread.start()
        else:
            self.__archiving__ = False

    def inputs_archiving_archiving(self):
        from reference import reference
        return [reference(self, "__archiving__")]

    archiving = monitored_property(
        fget=get_archiving,
        fset=set_archiving,
        inputs=inputs_archiving_archiving,
    )
    running = archiving  # for backward compatibility

    def keep_archiving(self):
        """Track the list of monitored process variables"""
        info("Archiving started.")
        from time import sleep
        self.__archiving__ = True
        while self.__archiving__:
            self.monitor_PVs(self.PVs)
            sleep(1)
        self.stop_monitoring()
        info("Archiving stopped.")

    def monitor_PVs(self, PVs):
        """Update list of monitored process variables"""
        from CA import camonitor, camonitor_clear
        for PV in self.monitored_PVs + []:
            if PV not in PVs:
                camonitor_clear(PV, self.callback)
                self.monitored_PVs.remove(PV)
        for PV in PVs:
            if PV not in self.monitored_PVs:
                camonitor(PV, callback=self.callback)
                self.monitored_PVs += [PV]

    def stop_monitoring(self):
        """Undo 'monitor_PVs'"""
        from CA import camonitor_clear
        for PV in self.monitored_PVs + []:
            camonitor_clear(PV, self.callback)
            self.monitored_PVs.remove(PV)

    def callback(self, PV_name, value, _char_value, timestamp):
        """Handle an update fo a process variable"""
        # debug("%s = %s" % (PV_name,value))
        self.log(PV_name, value, timestamp)

    def log(self, PV_name, value, timestamp):
        """Archive a value"""
        self.logfile(PV_name).log(value, time=timestamp)

    def logfile(self, PV_name):
        """logfile object"""
        from channel_archiver_logfile import logfile
        return logfile(self.filename(PV_name))

    def filename(self, PV_name):
        filename = "%s/%s.txt" % (self.directory, PV_name.replace(":", "."))
        return filename

    def history(self, PV_name, start_time, end_time):
        """Retrieve values from the archive
        PV_name: string, e.g. "NIH:TEMP.RBV"
        start_time: seconds since 1970-01-01 00:00:00 UT
        end_time: seconds since 1970-01-01 00:00:00 UT
        """
        values = self.logfile(PV_name).history("date time", "value",
                                               time_range=(start_time, end_time))
        return values


if __name__ == "__main__":  # for testing
    import logging

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")

    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    self = channel_archiver_driver(domain_name)

    print('self.domain_name = %r' % self.domain_name)
    print('')
    print('self.PVs = %r' % self.PVs)
    print('self.directory = %r' % self.directory)
    print('')
    print('self.PVs = ["NIH:TEMP.RBV","BNCHI:BunchCurrentAI.VAL"]')
    print('self.archiving_requested = True')
    print('self.archiving_requested = False')
    print('self.history("NIH:TEMP.RBV",time()-1,time())')


    def report(obj, name): info("%r.%s = %r" % (obj, name, getattr(obj, name)))


    print('from monitor import monitor; monitor(self,"archiving_requested",report,self,"archiving_requested")')
    print('from monitor import monitor; monitor(self,"archiving",report,self,"archiving")')
    print('self.archiving_requested = True')
