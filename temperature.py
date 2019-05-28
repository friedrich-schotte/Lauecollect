"""Client-side interface for Temperature System Level (SL) Server
Capabilities:
- Time-based Temperature ramping

Authors: Valentyn Stadnydskyi, Friedrich Schotte
Date created: 2019-05-08
Date last modified: 2019-07-17
"""
__version__ = "1.2" # added multiple new controls

from logging import debug,warn,info,error

from EPICS_motor import EPICS_motor
class Temperature(EPICS_motor):
    """Temperature System Level (SL)"""
    from PV_property_client import PV_property_client
    from PV_property import PV_property
    time_points = PV_property("time_points",[])
    temp_points = PV_property("temp_points",[])

    P_default = PV_property_client("P_default",0.0)
    I_default = PV_property_client("I_default",0.0)
    D_default = PV_property_client("D_default",0.0)
    lightwave_prefix = PV_property_client("lightwave_prefix",'')
    T_threshold = PV_property_client("temperature_oasis_switch",0.0)
    idle_temperature_oasis = PV_property_client("idle_temperature_oasis",0.0)
    temperature_oasis_limit_high = PV_property_client("temperature_oasis_limit_high",0.0)
    oasis_headstart_time = PV_property_client("oasis_headstart_time",0.0)
    oasis_prefix = PV_property_client("oasis_prefix",'')
    oasis_slave = PV_property_client("oasis_slave",0.0)

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
    print('temperature.P_default = %r' % temperature.P_default)
    print('')

    from timing_sequencer import timing_sequencer
    print("timing_sequencer.queue_active = %r" % timing_sequencer.queue_active)
    print("timing_sequencer.queue_active = False # cancel acquistion")
    print("timing_sequencer.queue_repeat_count = 0 # restart acquistion")
    print("timing_sequencer.queue_active = True  # simulate acquistion")
    print ('')
