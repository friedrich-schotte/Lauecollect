"""Friedrich Schotte, Oct 21, 2015 - Oct 29, 2015
"""
__version__ = "1.1.2"

from pdb import pm # for debugging
from Ensemble_SAXS_pp import Ensemble_SAXS
from timing_system import *
from time import sleep
##import logging; logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")

delays = [
    100*ps,178*ps,316*ps,562*ps,
    1*ns,1.78*ns,3.16*ns,5.62*ns,
    10*ns,17.8*ns,31.6*ns,56.2*ns,
    100*ns,178*ns,316*ns,562*ns,
    1*us,1.78*us,3.16*us,5.62*us,
    10*us,17.8*us,31.6*us,56.2*us,
    100*us,178*us,316*us,562*us,
    1*ms,1.78*ms,3.16*ms,5.62*ms,
    10*ms,17.8*ms,31.6*ms,
    32/hscf,64/hscf,128/hscf
]
laser_modes = [0,1]

all_delays = [t for t in delays for l in laser_modes]
all_laser_modes = [l for t in delays for l in laser_modes]

def test():
    while True:
        Ensemble_SAXS.add_sequences(all_delays,all_laser_modes)
        while len(Ensemble_SAXS.queue) > 10: sleep(1)

print("timing_system.ip_address = %r" % timing_system.ip_address)
print("Ensemble_SAXS.delay = 10e-3")
print("Ensemble_SAXS.queue")
print("Ensemble_SAXS.abort()")
print("Ensemble_SAXS.start()")
print("Ensemble_SAXS.add_sequences(all_delays,all_laser_modes)")
print("test()")
