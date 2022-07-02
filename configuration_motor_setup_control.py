#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-12-30
Date last modified: 2022-06-26
Revision comment: Cleanup: Removed property no longer needed
"""
__version__ = "1.4.5"

import logging

from alias_property import alias_property
from cached_function import cached_function
from monitored_property import monitored_property


@cached_function()
def configuration_motor_setup_control(domain_name):
    return Configuration_Setup_Motor_Control(domain_name)


class Configuration_Setup_Motor_Control:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @monitored_property
    def window_title(self, configuration_title, name, online):
        title = f"{configuration_title}, {name}"
        title += f" [{self.domain_name}]"
        if not online:
            title += f" (Offline)"
        return title

    @property
    def parameters(self):
        return [
            Item(label="Python code", obj=self.motor, attribute_name="motor_name", type_name="str", show=True),
            Item(label="Mnemonic", obj=self.motor, attribute_name="name", type_name="str", show=True),
            Item(label="Format", obj=self.motor, attribute_name="format_string", type_name="str", show=True),
            Item(label="Tolerance", obj=self.motor, attribute_name="tolerance", type_name="float", show=True),
        ]

    @property
    def motor(self):
        return self.configuration.motor[self.motor_num]

    @property
    def configuration(self):
        from configuration import configuration
        return configuration(self.configuration_name)

    @property
    def configuration_name(self):
        return ".".join(self.name.split(".")[0:-1])

    @property
    def motor_num(self):
        name = self.name
        name = name.replace(self.configuration_name, "")
        name = name.strip(".")
        name = name.replace("motor", "")
        try:
            motor_num = int(name) - 1
        except ValueError:
            motor_num = 0
        return motor_num

    online = alias_property("motor.online")
    motor_name = alias_property("motor.name")
    domain_name = alias_property("configuration.domain_name")
    configuration_title = alias_property("configuration.title")

    @property
    def class_name(self): return type(self).__name__.lower()


class Item:
    def __init__(self, label, obj, attribute_name, type_name, show=True):
        self.label = label
        self.object = obj
        self.attribute_name = attribute_name
        self.type_name = type_name
        self.show = show

    def __repr__(self):
        parameters = [
            f"label={self.label!r}",
            f"object={self.object!r}",
            f"attribute_name={self.attribute_name!r}",
            f"type_name={self.type_name!r}",
            f"show={self.show!r}",
        ]
        parameter_list = ",".join(parameters)
        return f"{self.class_name}({parameter_list})"

    @property
    def class_name(self): return type(self).__name__


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS.method.motor1"

    self = configuration_motor_setup_control(name)
