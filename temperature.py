"""Client-side interface for Temperature System Level (SL) Server
Capabilities:
- Time-based Temperature ramping

Authors: Valentyn Stadnytskyi, Friedrich Schotte
Date created: 2019-05-08
Date last modified: 2022-03-28
Revision comment: Cleanup: Tests
"""
__version__ = "1.3.6"

from logging import info

from EPICS_motor import EPICS_motor


class Temperature(EPICS_motor):
    """Temperature System Level (SL)"""
    from PV_property_client import PV_property_client
    from PV_property import PV_property
    time_points = PV_property("time_points", [])
    temp_points = PV_property("temp_points", [])
    P_default = PV_property_client("P_default", 0.0)
    I_default = PV_property_client("I_default", 0.0)
    D_default = PV_property_client("D_default", 0.0)
    lightwave_prefix = PV_property_client("lightwave_prefix", '')
    T_threshold = PV_property_client("temperature_oasis_switch", 0.0)
    idle_temperature_oasis = PV_property_client("idle_temperature_oasis", 0.0)
    temperature_oasis_limit_high = PV_property_client("temperature_oasis_limit_high", 0.0)
    oasis_headstart_time = PV_property_client("oasis_headstart_time", 0.0)
    oasis_prefix = PV_property_client("oasis_prefix", '')
    oasis_slave = PV_property_client("oasis_slave", 0.0)

    def __init__(self, prefix, name):
        from numpy import inf
        super().__init__(prefix=prefix, name=name, timeout=inf, readback_slop=0.050)

    def monitor(self, callback, new_thread=True):
        """Have the routine 'callback' be called every the time value
        of the PV changes.
        callback: function that takes three parameters:
        PV_name, value, char_value
        """
        from CA import camonitor
        camonitor(self.prefix + ".RBV", callback=callback, new_thread=new_thread)

    def monitor_clear(self, callback=None):
        """Undo 'monitor'."""
        from CA import camonitor_clear
        camonitor_clear(self.prefix + ".RBV", callback=callback)

    @property
    def name(self): return self.prefix + ".RBV"


temperature = Temperature(prefix="NIH:TEMP", name="temperature")

if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
                        )

    print('acquisition.temperature_start()')
    print('acquisition.temperature_stop()')
    print('')

    print('temperature.VAL = %r' % temperature.VAL)
    print('temperature.RBV = %r' % temperature.RBV)
    print('temperature.time_points = %r' % temperature.time_points)
    print('temperature.temp_points = %r' % temperature.temp_points)
    print('')
    print('temperature.P_default = %r' % temperature.P_default)
    print('temperature.I_default = %r' % temperature.I_default)
    print('temperature.D_default = %r' % temperature.D_default)
    print('')

    # from instrumentation import BioCARS
    # timing_system_sequencer = BioCARS.timing_system.sequencer
    # print("timing_system_sequencer.queue_active = %r" % timing_system_sequencer.queue_active)
    # print("timing_system_sequencer.queue_active = False # cancel acquisition")
    # print("timing_system_sequencer.queue_repeat_count = 0 # restart acquisition")
    # print("timing_system_sequencer.queue_active = True  # simulate acquisition")
    # print ('')

    def callback(PV_name, value, _string_value): info("%s=%r" % (PV_name, value))


    print('temperature.monitor(callback)')
    self = temperature  # for debugging
