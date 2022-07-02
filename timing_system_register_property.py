"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-05
Revision comment:
"""
__version__ = "1.0"

from timing_system_property import Property


class Register_Property(Property):
    from numpy import nan
    default_value = nan
    dtype = None

    def __init__(self, name, default_value=None, dtype=None):
        """name: 'count', 'address, 'bits', 'bit_offset'"""
        super().__init__(name=name)
        if default_value is not None:
            self.default_value = default_value
        if dtype is not None:
            self.dtype = dtype

    def __repr__(self):
        name = type(self).__name__
        return "%s(%r, default_value=%r, dtype=%s)" % \
               (name, self.name, self.default_value, self.dtype.__name__)

    def property_name(self, instance):
        return "registers.%s.%s" % (instance.name, self.name)

    def calculate(self, instance, value):
        from timing_system import register_property_value
        return register_property_value(value, self.default_value, self.dtype,
                                       report_name=self.PV(instance).name)

    def set_value(self, instance, value):
        from numpy import isnan
        if not isnan(value):
            self.PV(instance).value = value


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
