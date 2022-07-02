#!/usr/bin/env python
"""
Database save and recall motor positions
Author: Friedrich Schotte
Date created: 2022-06-16
Date last modified: 2022-06-27
Revision comment: Using configuration.n_motors
"""
__version__ = "1.0.2"

from cached_function import cached_function


@cached_function()
def motors(configuration): return Motors(configuration)


class Motors:
    def __init__(self, configuration):
        self.configuration = configuration

    def __repr__(self):
        return f"{self.configuration}.motor"

    def __getitem__(self, index):
        from configuration_table_motor_driver import configuration_table_motor_driver
        return configuration_table_motor_driver(self.configuration, index)

    def __len__(self):
        return self.configuration.n_motors

    def __iter__(self):
        for i in range(0, len(self)):
            if i < len(self):
                yield self[i]

    @property
    def count(self):
        """How many motors are there?"""
        return len(self)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler

    from configuration_table_driver import configuration_table_driver
    configuration = configuration_table_driver("BioCARS.method")
    self = motors(configuration)


    @_handler
    def report(event): logging.info(f"{event}")


    print('len(self.count)')
    print('self[0]')
    print('[motor for motor in self]')
