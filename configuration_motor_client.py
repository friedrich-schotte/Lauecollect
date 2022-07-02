"""
Author: Friedrich Schotte
Date created: 2022-06-13
Date last modified: 2022-06-26
Revision comment: Cleanup: Removed properties no longer used
"""
__version__ = "2.2.2"

from PV_connected_property import PV_connected_property
from PV_record import PV_record
from array_PV_property import array_PV_property
from cached_function import cached_function
from PV_property import PV_property


@cached_function()
def configuration_motor_client(channels, motor_num):
    return Configuration_Motor_Client(channels, motor_num)


class Configuration_Motor_Client(PV_record):
    base_name = "motor"

    def __init__(self, motors, motor_num):
        super().__init__(domain_name=motors.name)
        self.motors = motors
        self.motor_num = motor_num

    def __repr__(self):
        return f"{self.motors}[{self.motor_num}]"

    @property
    def prefix(self):
        return f'{self.motors.prefix}{self.motor_num + 1}'.upper()

    motor_name = PV_property(dtype=str)
    name = PV_property(dtype=str)
    configuration_name = PV_property(dtype=str)
    format_string = PV_property(dtype=str)
    tolerance = PV_property(dtype=float)

    in_position = PV_property(dtype=bool)
    formatted_position = PV_property(dtype=str)
    choices = PV_property(dtype=list)

    positions = array_PV_property("positions", "")

    nominal_position = PV_property()
    current_position = PV_property()
    position = PV_property()

    is_numeric = PV_property(dtype=bool)

    online = PV_connected_property("motor_name")


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS.method"
    from configuration_client import configuration_client

    configuration = configuration_client(name)
    self = configuration_motor_client(configuration.motor, 0)

    print("self.formatted_position")
    print("self.in_position")
