"""
Author: Friedrich Schotte
Date created: 2021-11-30
Date last modified: 2022-07-20
Revision comment: Added: motor_names
"""
__version__ = "1.9"

from PV_record import PV_record
from cached_function import cached_function
from monitored_property import monitored_property
from PV_property import PV_property
from PV_connected_property import PV_connected_property


@cached_function()
def scan_client(domain_name=None, base_name=None, prefix=None):
    return Scan_Client(domain_name=domain_name, base_name=base_name, prefix=prefix)


class Scan_Client(PV_record):
    motor_name = PV_property(dtype=str)
    motor_names = PV_property(dtype=list)
    values_string = PV_property(dtype=str)
    wait = PV_property(dtype=bool)
    return_value = PV_property(dtype=float)
    scan_point_divider = PV_property(dtype=int)

    ready = PV_property(dtype=bool)
    formatted_values = PV_property(dtype=list)
    formatted_command_value = PV_property(dtype=str)
    formatted_value = PV_property(dtype=str)

    values = PV_property(dtype=list)

    # Diagnostics
    scan_point_number = PV_property(dtype=float)
    value_count = PV_property(dtype=int)
    values_index = PV_property(dtype=int)

    motor_command_value = PV_property(dtype=float)
    motor_value = PV_property(dtype=float)
    motor_moving = PV_property(dtype=bool)

    enabled = PV_property(dtype=bool)
    collecting_dataset = PV_property(dtype=bool)
    acquiring = PV_property(dtype=bool)
    scanning = PV_property(dtype=bool)

    slewing = PV_property(dtype=bool)
    start_time = PV_property(dtype=float)
    scan_point_acquisition_time = PV_property(dtype=float)

    trajectory_array = PV_property(dtype=list)

    @monitored_property
    def trajectory_times_values(self, trajectory_array):
        from numpy import array
        n = len(trajectory_array) // 2
        return array(trajectory_array)[0:2*n].reshape(2, n)

    online = PV_connected_property("values_string")

    # Diagnostics for debugging
    running = PV_property(dtype=bool)
    handling_value_index = PV_property(dtype=bool)
    handling_collecting_dataset = PV_property(dtype=bool)


if __name__ == "__main__":  # for debugging
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # self = scan_client(domain_name="BioCARS")
    self = scan_client(prefix="BIOCARS:TIMING_SYSTEM.DELAY_SCAN")

    print("self.values_string")
