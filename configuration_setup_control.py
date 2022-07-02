#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-01-01
Date last modified: 2022-06-24
Revision comment: Cleanup: Removed properties no longer used
"""
__version__ = "1.3.1"

import logging

from alias_property import alias_property
from cached_function import cached_function
from monitored_property import monitored_property


@cached_function()
def configuration_setup_control(name):
    return Configuration_Setup_Control(name)


class Configuration_Setup_Control:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @monitored_property
    def window_title(self, configuration_title, online):
        window_title = f"{configuration_title}"
        window_title += f" [{self.domain_name}]"
        if not online:
            window_title += f" (Offline)"
        return window_title

    @property
    def parameters(self):
        return [
            Item(label="Title", obj=self.configuration, attribute_name="title", type_name="str", show=True),
        ]

    online = alias_property("configuration.online")
    configuration_title = alias_property("configuration.title")
    domain_name = alias_property("configuration.domain_name")

    @property
    def configuration(self):
        from configuration_client import configuration_client
        return configuration_client(self.name)

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

    name = "BioCARS.method"

    self = configuration_setup_control(name)
