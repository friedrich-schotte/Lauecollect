"""
Author: Friedrich Schotte
Date created: 2022-03-28
Date last modified: 2022-05-04
Revision comment:
"""
__version__ = "1.0"

from alias_property import alias_property
from cached_function import cached_function
from PV_record import PV_record
from PV_property import PV_property


@cached_function()
def timing_system_composer_client(timing_system, base_name="composer"):
    return Timing_System_Composer_Client(timing_system, base_name)


class Timing_System_Composer_Client(PV_record):
    base_name = "composer"

    def __init__(self, timing_system, base_name):
        super().__init__(domain_name=timing_system.name)
        self.timing_system = timing_system
        self.base_name = base_name

    def __repr__(self):
        return f"{self.timing_system}.{self.base_name}"

    @property
    def prefix(self):
        return f'{self.timing_system.prefix}.{self.base_name}'.upper()

    delay = PV_property(dtype=float)
    nom_delay = PV_property(dtype=float)
    mode = PV_property(dtype=str)
    modes = PV_property(dtype=list)
    trigger_period_in_1kHz_cycles = PV_property(dtype=int)
    xdet_on = PV_property(dtype=bool)
    laser_on = PV_property(dtype=bool)
    ms_on = PV_property(dtype=bool)
    trans_on = PV_property(dtype=bool)
    pump_on = PV_property(dtype=bool)
    transc = PV_property(dtype=int)
    image_number_inc = PV_property(dtype=bool)
    pass_number_inc = PV_property(dtype=bool)
    generator = PV_property(dtype=str)
    generator_version = PV_property(dtype=str)
    timing_sequence_version = PV_property(dtype=str)
    xd = PV_property(dtype=float)

    mode_number = PV_property(dtype=int)
    period = PV_property(dtype=int)
    N = PV_property(dtype=int)
    dt = PV_property(dtype=int)
    t0 = PV_property(dtype=int)
    transd = PV_property(dtype=int)
    z = PV_property(dtype=int)

    acquisition_sequence = PV_property(dtype=str)
    sequence = PV_property(dtype=str)

    scan_point_acquisition_time = PV_property(dtype=float)
    sequence_acquisition_time = PV_property(dtype=float)
    sequences_per_scan_point = PV_property(dtype=int)

    update_later = PV_property(dtype=bool)

    timing_modes_configuration_name = PV_property(dtype=str)

    def update(self): self.update_later = True

    sequencer = alias_property("timing_system.sequencer")


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system_client import timing_system_client

    timing_system = timing_system_client(domain_name)
    self = timing_system_composer_client(timing_system, "composer")

    print("self.delay")
