#!/usr/bin/env python
"""
Archive EPICS process variable via Channel Access
Author: Friedrich Schotte
Date created: 2017-10-04
Date last modified: 2019-01-15
"""
__version__ = "1.0.3" # logfile object name -> settings  filename

from logging import debug,info,warn,error

class ChannelArchiver(object):
    name = "channel_archiver"
    from persistent_property import persistent_property
    PVs = persistent_property("PVs",[])
    __directory__ = persistent_property("directory",".")
    monitored_PVs = []
    __running__ = False

    def get_directory(self):
        from normpath import normpath
        return normpath(self.__directory__)
    def set_directory(self,value):
        self.__directory__ = value
    directory = property(get_directory,set_directory)

    def get_running(self):
        """Actively collecting data?"""
        return self.__running__
    def set_running(self,value):
        from thread import start_new_thread
        if value:
            if not self.__running__: start_new_thread(self.run,())
        else: self.__running__ = False
    running = property(get_running,set_running)

    def run(self):
        """Track the list of monitored process variables"""
        from time import sleep
        self.__running__ = True
        while self.__running__:
            self.monitor(self.PVs)
            sleep(1)
        self.stop_monitoring()
    
    def monitor(self,PVs):
        """Update list of monitored process variables"""
        from CA import camonitor,camonitor_clear
        for PV in self.monitored_PVs+[]:
            if not PV in PVs:
                camonitor_clear(PV,self.callback)
                self.monitored_PVs.remove(PV)
        for PV in PVs:
            if not PV in self.monitored_PVs:
                camonitor(PV,callback=self.callback)
                self.monitored_PVs += [PV]

    def stop_monitoring(self):
        """Undo 'monitor'"""
        from CA import camonitor_clear
        for PV in self.monitored_PVs+[]:
            camonitor_clear(PV,self.callback)
            self.monitored_PVs.remove(PV)

    def callback(self,PV_name,value,char_value):
        """Handle an update fo a process variable"""
        ##debug("%s = %s" % (PV_name,value))
        self.log(PV_name,value)

    def log(self,PV_name,value):
        """Archive a value"""
        self.logfile(PV_name).log(value)

    def logfile(self,PV_name):
        """logfile object"""
        from logfile import logfile
        f = logfile(name="channel_archiver/"+PV_name,
            columns=["date time","value"],
            filename=self.filename(PV_name))
        return f

    def filename(self,PV_name):
        filename = "%s/%s.txt" % (self.directory,PV_name.replace(":","."))
        return filename

    def history(self,PV_name,start_time,end_time):
        """Retreive values from the archive
        PV_name: string, e.g. "NIH:TEMP.RBV"
        start_time: seconds since 1970-01-01 00:00:00 UT
        end_time: seconds since 1970-01-01 00:00:00 UT
        """
        values = self.logfile(PV_name).history("date time","value",
            time_range=(start_time,end_time))
        return values

channel_archiver = ChannelArchiver()

if __name__ == "__main__": # for testing
    from pdb import pm # for debugging
    self = channel_archiver # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")
    from time import time
    print('channel_archiver.PVs = %r' % channel_archiver.PVs)
    print('channel_archiver.directory = %r' % channel_archiver.directory)
    print('')
    print('channel_archiver.PVs = ["NIH:TEMP.RBV","BNCHI:BunchCurrentAI.VAL"]')
    print('channel_archiver.running = True')
    print('channel_archiver.running = False')
    print('self.history("NIH:TEMP.RBV",time()-1,time())')
