"""
Author: Friedrich Schotte
Date created: 2022-04-25
Date last modified: 2022-06-30
Revision comment: Simplified Scan_Driver.init
"""
__version__ = "1.3.7"

import logging

from monitored_value_property import monitored_value_property
from scan_driver import Scan_Driver
from alias_property import alias_property
from cached_function import cached_function
from monitored_property import monitored_property


@cached_function()
def timing_system_laser_on_scan(timing_system):
    return Timing_System_Laser_On_Scan(timing_system)


class Timing_System_Laser_On_Scan(Scan_Driver):
    def __init__(self, timing_system):
        super().__init__(domain_name=timing_system.domain_name)
        self.timing_system = timing_system

    def __repr__(self):
        return f"{self.timing_system}.laser_on_scan"

    @property
    def db_name(self):
        return f"{self.timing_system.db_name}/laser_on_scan"

    # PVs to be hosted
    @monitored_property
    def values_string(self, collection_variables_with_options):
        values_string = ""
        for variable in collection_variables_with_options:
            if variable.startswith("Laser_on="):
                values_string = variable.split("=")[-1]
        return values_string

    wait = monitored_value_property(False)
    return_value = alias_property("timing_system.laser_on")
    ready = monitored_value_property(True)

    @monitored_property
    def values(self, values_string):
        values = [1]
        try:
            values = eval(values_string)
        except Exception as x:
            if values_string:
                logging.error(f"{values_string}: {x}: expecting list, e.g. 0,1")
        return values

    # Imported PVs
    enabled = alias_property("acquisition_client.scanning.laser_on")
    scan_point_divider = alias_property("acquisition_client.scan_point_dividers.laser_on")

    # Diagnostics PVs to be hosted
    motor_value = alias_property("timing_system.composer.laser_on")
    motor_command_value = alias_property("motor_value")
    motor_moving = monitored_value_property(False)

    @staticmethod
    def format(value):
        text = "on" if value else "off"
        return text

    def handle_values_index_change(self, values_index, time):
        logging.debug(f"[Ignoring values_index={values_index}]")

    def handle_collecting_dataset_change(self, collecting_dataset):
        logging.debug(f"[Ignoring collecting_dataset={collecting_dataset}]")

    collection_variables_with_options = alias_property("acquisition_driver.collection_variables_with_options")

    acquisition_client = alias_property("domain.acquisition_client")
    acquisition_driver = alias_property("domain.acquisition_driver")


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS"
    # name = "LaserLab"

    from timing_system import timing_system

    self = timing_system_laser_on_scan(timing_system(name))
