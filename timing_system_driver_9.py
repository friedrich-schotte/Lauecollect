"""
Author: Friedrich Schotte
Date created: 2007-04-02
Date last modified: 2022-07-29
Revision comment:
"""
__version__ = "9.0"

import logging

from PV_connected_property import PV_connected_property
from PV_info_property import PV_info_property
from alias_property import alias_property
from cached_function import cached_function
from db_property import db_property
from timing_system_variable_property_driver_2 import timing_system_variable_property_driver as variable_property


@cached_function()
def timing_system_driver(domain_name):
    return Timing_System_Driver(domain_name)


class Timing_System_Driver(object):
    """FPGA Timing system"""
    def __init__(self, domain_name="BioCARS"):
        self.domain_name = domain_name

    def __repr__(self):
        return f"{self.class_name}({self.domain_name!r})"

    @property
    def db_name(self):
        return f"domains/{self.domain_name}/timing_system/parameters"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def prefix(self):
        prefix = self.domain_name.upper() + ":TIMING."
        prefix = prefix.replace("BIOCARS", "NIH")
        return prefix

    @property
    def registers(self):
        from timing_system_registers_driver_2 import timing_system_registers_driver
        return timing_system_registers_driver(self)

    @property
    def channels(self):
        from timing_system_channels_driver_2 import timing_system_channels_driver
        return timing_system_channels_driver(self)

    @property
    def clock(self):
        from timing_system_clock_driver_2 import timing_system_clock_driver
        return timing_system_clock_driver(self)

    @property
    def sequencer(self):
        from timing_system_sequencer_driver_9 import timing_system_sequencer_driver
        return timing_system_sequencer_driver(self)

    @property
    def composer(self):
        from timing_system_composer_driver_6 import timing_system_composer_driver
        return timing_system_composer_driver(self)

    @property
    def acquisition(self):
        from timing_system_acquisition_driver_2 import timing_system_acquisition_driver
        return timing_system_acquisition_driver(self)

    @property
    def delay_scan(self):
        from timing_system_delay_scan_driver_2 import timing_system_delay_scan_driver
        return timing_system_delay_scan_driver(self)

    @property
    def laser_on_scan(self):
        from timing_system_laser_on_scan_driver_2 import timing_system_laser_on_scan_driver
        return timing_system_laser_on_scan_driver(self)

    @property
    def directory(self):
        return f"{self.toplevel_directory}/settings/domains/{self.domain_name}/timing_system"

    @property
    def toplevel_directory(self):
        from module_dir import module_dir
        return module_dir(self.__class__)

    ip_address = PV_info_property("registers", "IP_address", upper_case=False)
    online = PV_connected_property("registers", upper_case=False)

    # Needed for sequencer and composer
    delay = variable_property("delay", stepsize=1e-12)  # Ps laser to X-ray delay

    xdet_on = db_property("xdet_on", False)  # Read detector?
    laser_on = db_property("laser_on", False)  # Pump sample?
    ms_on = db_property("ms_on", False)  # Probe sample?
    trans_on = db_property("trans_on", False)  # Translate sample?
    pump_on = db_property("pump_on", False)
    image_number_inc_on = db_property("image_number_inc_on", False)
    pass_number_inc_on = db_property("pass_number_inc_on", False)

    # Needed for Timing_Panel
    p0_shift = alias_property("registers.p0_shift")
    P0t = alias_property("clock.P0t")
    hsct = alias_property("clock.hsct")

    # Needed for Timing_Clock_Configuration_Panel
    clock_period = alias_property("clock.clock_period")
    clock_multiplier = alias_property("clock.clock_multiplier")
    clock_divider = alias_property("clock.clock_divider")
    bct = alias_property("clock.bct")
    clk_shift_stepsize = alias_property("clock.clk_shift_stepsize")
    hlc_nslots = alias_property("clock.hlc_nslots")
    phase_matching_period = alias_property("clock.phase_matching_period")
    hlc_div = alias_property("clock.hlc_div")
    hlct = alias_property("clock.hlct")
    nsl_div = alias_property("clock.nsl_div")
    nslt = alias_property("clock.nslt")


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    self = timing_system_driver(domain_name)
    from IOC import ioc as _ioc
    ioc = _ioc(driver=self)
    print("ioc.running = True")
    # ioc.run()
