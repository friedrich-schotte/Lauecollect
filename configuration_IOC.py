"""
EPICS Input/Output Controller (IOC)
Author: Friedrich Schotte
Date created: 2021-10-04
Date last modified: 2022-06-16
Revision comment: Based on "IOC" class
"""
__version__ = "2.0"

import logging

from cached_function import cached_function
from IOC import IOC


@cached_function()
def configuration_IOC(name): return Configuration_IOC(name)


class Configuration_IOC(IOC):
    def __init__(self, name):
        domain_name, base_name = name.split(".", 1)
        super().__init__(f"{domain_name}.configuration.{base_name}")


def run(name): configuration_IOC(name).run()


def start(name): configuration_IOC(name).start()


def stop(name): configuration_IOC(name).stop()


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # name = "BioCARS.beamline_configuration"
    # name = "BioCARS.Julich_chopper_modes"
    # name = "BioCARS.heat_load_chopper_modes"
    # name = "BioCARS.timing_modes"
    # name = "BioCARS.sequence_modes"
    # name = "BioCARS.delay_configuration"
    # name = "BioCARS.temperature_configuration"
    # name = "BioCARS.power_configuration"
    # name = "BioCARS.scan_configuration"
    # name = "BioCARS.diagnostics_configuration"
    # name = "BioCARS.detector_configuration"
    name = "BioCARS.method"
    # name = "BioCARS.laser_optics_modes"
    # name = "BioCARS.alio_diffractometer_saved"

    self = configuration_IOC(name)

    from CA import PV

    pv = PV(f"{self.prefix}TITLE")

    print('start(name)')
    # start(name)

    print(f'pv.value')
