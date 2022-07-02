"""
EPICS Channel Access Process Variable as class property
Author: Friedrich Schotte
Date created: 2021-01-09
Date last modified: 2022-04-08
Revision comment: Cleanup: Using only keyword parameters for superclass constructor
"""
__version__ = "1.1.1"

from PV_property import PV_property


class PV_info_property(PV_property):
    def __init__(self, name, property_name, upper_case=True):
        """property_name: e.g. "IP_address" """
        super().__init__(name=name, default_value=None, upper_case=upper_case)
        self.property_name = property_name

    def get_property(self, instance):
        return self.value(instance)

    def set_property(self, instance, value):
        pass

    def value(self, instance, _value=None):
        from CA import cainfo
        value = cainfo(self.PV_name(instance), self.property_name)
        return value


if __name__ == "__main__":
    import logging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler
    from reference import reference as _reference

    class IOC(object):
        prefix = "NIH:CAMERA.LASERLABCAMERA."

        def __repr__(self):
            return f"{type(self).__name__}(prefix={self.prefix})"

        server_ip_address = PV_info_property("pixel_format", "IP_address")


    self = IOC()


    @_handler
    def report(event=None):
        logging.info(f"event={event}")


    _reference(self, "server_ip_address").monitors.add(report)
    print("self.server_ip_address")
