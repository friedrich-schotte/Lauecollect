"""EPICS Channel Access Process Variable as class property
Author: Friedrich Schotte
Date created: 2020-11-12
Date last modified: 2022-07-31
Revision comment: Added: option: upper_case
"""
__version__ = "1.2"

import logging
from PV_property import PV_property


class PV_connected_property(PV_property):
    def __init__(self, name, upper_case=True):
        super().__init__(name, default_value=None, upper_case=upper_case)

    def PV_value(self, instance, value):
        return value is not None


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler
    from reference import reference as _reference

    class Example(object):
        prefix = "BIOCARS:ACQUISITION."

        def __repr__(self):
            return f"{type(self).__name__}(prefix={self.prefix})"

        directory = PV_property(dtype=str)
        online = PV_connected_property("directory")


    self = Example()


    @_handler
    def report(event=None):
        logging.info(f"event={event}")


    _reference(self, "online").monitors.add(report)
    print(f"self.online = {self.online!r}")
