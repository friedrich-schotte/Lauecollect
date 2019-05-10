"""
ILX Lightwave LDT-5948 Precision Temperature Controller
EPICS client
Friedrich Schotte, 14 Dec 2009 - 5 Jul 2017
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
class Temperature_Controller(EPICS_motor):
    """ILX Lightwave LDT-5948 Precision Temperature Controller"""
    command_value = alias("VAL") # EPICS_motor.command_value not changable
    enabled = alias("CNEN") # EPICS_motor.enabled not changable
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
    prefix = alias("__prefix__") # EPICS_motor.prefix not changable
  
temperature_controller = Temperature_Controller(prefix="NIH:TEMP",name="temperature_controller")

if __name__ == "__main__":
    print('temperature_controller.prefix = %r' % temperature_controller.prefix)
    print('temperature_controller.port_name = %r' % temperature_controller.port_name)
    print('temperature_controller.command_value = %r' % temperature_controller.command_value)
