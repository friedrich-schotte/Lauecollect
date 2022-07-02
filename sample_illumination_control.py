#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-05-31
Date last modified: 2021-05-31
Revision comment: Using timing system server
"""
__version__ = "1.1"

from logging import info

from cached_function import cached_function


@cached_function()
def sample_illumination_control(domain_name):
    return Sample_Illumination_Control(domain_name)


class Sample_Illumination_Control(object):
    from db_property import db_property
    from alias_property import alias_property
    from monitored_property import monitored_property

    @property
    def db_name(self): return f"{self.domain_name}.sample_illumination"

    channel_number = db_property("channel_number", 9)

    def __init__(self, domain_name="BioCARS"):
        self.domain_name = domain_name

    def __repr__(self):
        return f"{self.class_name}({self.domain_name})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def timing_system(self):
        from timing_system_client import timing_system_client
        return timing_system_client(self.domain_name)

    @property
    def channel(self):
        return self.timing_system.channels[self.channel_number]

    override = alias_property("channel.override.count")
    state = alias_property("channel.override_state.count")
    online = alias_property("timing_system.online")

    @monitored_property
    def PP_controlled(self, online, override):
        if online:
            value = not override
        else:
            value = False
        return value

    @PP_controlled.setter
    def PP_controlled(self, value):
        self.override = not value

    @monitored_property
    def enabled(self, online, PP_controlled):
        if online:
            value = not PP_controlled
        else:
            value = False
        return value

    @monitored_property
    def label(self, online, state):
        if online:
            value = "On" if state else "Off"
        else:
            value = "Offline"
        return value


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from reference import reference
    from handler import handler
    self = sample_illumination_control("BioCARS")

    @handler
    def report(event): info(f"{event}")

    reference(self, "override").monitors.add(report)
    reference(self, "PP_controlled").monitors.add(report)
    reference(self, "state").monitors.add(report)
    reference(self, "enabled").monitors.add(report)
    reference(self, "label").monitors.add(report)

    print(f"self.PP_controlled = {self.PP_controlled}")
    print(f"self.state = {self.state}")
