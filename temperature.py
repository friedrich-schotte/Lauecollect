"""Client-side interface for Temperature System Level (SL) Server
Capabilities:
- Time-based Temperature ramping

Authors: Valentyn Stadnydskyi, Friedrich Schotte
Date created: 2019-05-08
Date last modified: 2019-07-17
"""
__version__ = "1.1" # prefix = "NIH:TEMP."

from logging import debug,warn,info,error

from EPICS_motor import EPICS_motor
class Temperature(EPICS_motor):
    """Temperature System Level (SL)"""
    from PV_property import PV_property
    time_points = PV_property("time_points",[])
    temp_points = PV_property("temp_points",[])
  
temperature = Temperature(prefix="NIH:TEMP",name="temperature")


if __name__ == "__main__": 
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    from collect import collect
    print('collect.temperature_start()')
    print('collect.temperature_stop()')
    print('')

    from numpy import nan
    print('temperature.VAL = %r' % temperature.VAL)
    print('temperature.RBV = %r' % temperature.RBV)
    print('temperature.time_points = %r' % temperature.time_points)
    print('temperature.temp_points = %r' % temperature.temp_points)
    print('')

    from timing_sequencer import timing_sequencer
    print("timing_sequencer.queue_active = %r" % timing_sequencer.queue_active)
    print("timing_sequencer.queue_active = False # cancel acquistion")
    print("timing_sequencer.queue_repeat_count = 0 # restart acquistion")
    print("timing_sequencer.queue_active = True  # simulate acquistion")
    print ('')



