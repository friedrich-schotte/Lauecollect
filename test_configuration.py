#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-06-25
Date last modified: 2022-06-28
Revision comment: Renamed: configuration_tables_driver
"""
__version__ = "1.1.1"

from configuration_tables_driver import configuration_tables_driver


def test(domain_name):
    for configuration in configuration_tables_driver(domain_name):
        for i in range(0, configuration.n_motors):
            motor = configuration.motor[i]
            motor_object_name = motor.object_name
            motor_object = motor.motor_object
            print(f"{configuration}[{i}]: {motor_object_name}: {motor_object}")


if __name__ == '__main__':
    import logging

    for h in logging.root.handlers[:]:
        logging.root.removeHandler(h)

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    print(f"test({domain_name!r})")
