"""
ILX Lightwave LDT-5948 Precision Temperature Controller
EPICS client
Author: Friedrich Schotte
Date created: 14 Dec 2009
Date last modified: 2019-02-21
"""
__version__ = "4.5" # id

from pdb import pm # stabilization number of samples: stabilization_nsamples
import logging
##logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")

def alias(name):
    """Make property given by name be known under a different name"""
    def get(self): return getattr(self,name)
    def set(self,value): setattr(self,name,value)
    return property(get,set)

from EPICS_motor import EPICS_motor
class Lightwave_Temperature_Controller(EPICS_motor):
    """ILX Lightwave LDT-5948 Precision Temperature Controller"""
    port_name = alias("COMM")
    stabilization_threshold = alias("RDBD")
    stabilization_nsamples = alias("NSAM")
    current_low_limit = alias("ILLM")
    current_high_limit = alias("IHLM")
    trigger_enabled = alias("TENA")
    trigger_start = alias("P1SP")
    trigger_stop = alias("P1EP")
    trigger_stepsize = alias("P1SI")
    id = alias("ID")
    setT = alias("command_value") # for backward compatbility with lauecollect
    readT = alias("value") # for backward compatbility with lauecollect
  
lightwave_temperature_controller = Lightwave_Temperature_Controller(prefix="NIH:LIGHTWAVE",
    name="lightwave_temperature_controller")

if __name__ == "__main__":
    print('lightwave_temperature_controller.prefix = %r' % lightwave_temperature_controller.prefix)
    print('lightwave_temperature_controller.port_name = %r' % lightwave_temperature_controller.port_name)
    print('lightwave_temperature_controller.command_value = %r' % lightwave_temperature_controller.command_value)
