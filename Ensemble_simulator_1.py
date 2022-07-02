"""Aerotech Ensemble Motion Controller
Author: Friedrich Schotte
Date created: 2019-08-07
Date lst modified: 2019-08-07
"""
__version__ = "1.0"
from logging import debug,info,warn,error

prefix = "SIM:ENSEMBLE"

from DB import db,dbset
from array_wrapper import ArrayWrapper

class Ensemble(object):
    name = "Ensemble_simulator"
    naxes = 6
    
    def get_homed(self,axis_number):
        """Actual position based on encoder feedback"""
        return db("%s.%s.homed" % (self.name,axis_number),False)
    def set_homed(self,axis_number,value):
        dbset("%s.%s.homed" % (self.name,axis_number),value)
    def homed_count(self): return self.naxes

    def _get_homed(self):
        return ArrayWrapper(self,"homed",method="single",dtype=bool)
    def _set_homed(self,values): self.homed[:] = values
    homed = property(_get_homed,_set_homed)

ensemble_driver = Ensemble()

class EnsembleWrapper(object):
    """This is to make sure that NaNs are subsituted when the Ensembe
    driver is offline."""
    naxes = 7
    def __init__(self,name):
        """name: EPICS record name (prefix), e.g. "NIH:ENSEMBLE" """
        from CA import Record
        self.__record__ = Record(name)
        
    def __getattr__(self,name):
        """Called when '.' is used."""
        if name.startswith("__") and name.endswith("__"):
            return object.__getattribute__(self,name)
        ##debug("EnsembleWrapper.__getattr__(%r)" % name)
        from numpy import asarray
        values = getattr(self.__record__,name)
        if values is None: values = self.__default_value__(name)
        if isinstance(values,basestring): return values
        if not hasattr(values,"__len__"): return values
        return asarray(values)

    def __setattr__(self,name,value):
        """Called when '.' is used."""
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self,name,value)
        ##debug("EnsembleWrapper.__setattr__(%r,%r)" % (name,value))
        setattr(self.__record__,name,value)

    def __default_value__(self,name):
        from numpy import zeros,nan
        if name == "program_filename": value = ""
        elif name == "auxiliary_task_filename": value = ""
        elif name == "program_directory": value = ""
        elif name == "program_running": value = nan
        elif name == "auxiliary_task_running": value = nan
        elif name == "fault": value = nan
        elif name == "connected": value = nan
        elif name.startswith("UserInteger"): value = nan
        elif name.startswith("UserDouble"): value = nan
        elif name.startswith("UserString"): value = ""
        else: value = zeros(self.naxes)+nan
        return value

ensemble = EnsembleWrapper(prefix)


def start_server():
    """Start EPCIS IOC and TCP server returing control"""
    start_IOC()

def run_server():
    """Run EPCIS IOC and TCP servers without returing control"""
    start_server()
    wait()

def start_IOC():
    """Serve the Ensemble IPAQ up on the network as EPCIS IOC"""
    import EPICS_CA.EPICS_CA.CAServer as CAServer
    ##CAServer.DEBUG = True
    CAServer.update_interval = 2.0
    CAServer.register_object(ensemble_driver,prefix)

def wait():
    """Halt execution"""
    from time import sleep
    while True: sleep(0.1)


if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=format)
    debug("Started")
    self = ensemble_driver

    import EPICS_CA.EPICS_CA.CAServer as CAServer
    from CA import caget,caput
    ##from CAServer import *
    from CAServer import casget

    PV_name = prefix+".homed"
    print("CAServer.DEBUG = %r" % (not CAServer.DEBUG))
    print("start_IOC()")
    print('casget(%r)' % PV_name)
    print('caget(%r)' % PV_name)
    print('ensemble_driver.homed')
    print('ensemble.homed')
