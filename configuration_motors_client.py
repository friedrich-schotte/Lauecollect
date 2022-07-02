"""
Author: Friedrich Schotte
Date created: 2022-06-13
Date last modified: 2022-06-13
Revision comment:
"""
__version__ = "1.0"

from cached_function import cached_function
from PV_record import PV_record


@cached_function()
def configuration_motors_client(timing_system, base_name="motor"):
    return Configuration_Motors_Client(timing_system, base_name)


class Configuration_Motors_Client(PV_record):
    base_name = "motor"

    def __init__(self, configuration, base_name):
        super().__init__(domain_name=configuration.name)
        self.configuration = configuration
        self.base_name = base_name

    def __repr__(self):
        return f"{self.configuration}.{self.base_name}"

    def __hash__(self): return hash(repr(self))

    @property
    def prefix(self):
        return f'{self.configuration.prefix}.{self.base_name}'.upper()

    def __getitem__(self, i):
        from configuration_motor_client import configuration_motor_client
        return configuration_motor_client(self, i)

    def __len__(self):
        return self.configuration.n_motors


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS.method"
    from configuration_client import configuration_client

    configuration = configuration_client(name)
    self = configuration_motors_client(configuration, "motor")

    print("self[0]")
