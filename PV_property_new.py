"""EPICS Channel Access Process Variable as class property
Author: Friedrich Schotte
Date created: 2019-05-18
Date last modified: 2022-06-17
Revision comment: Reimplemented based on monitored_property
"""
__version__ = "2.0"

import logging

from monitored_property import monitored_property


class PV_property(monitored_property):
    name = None
    default_value = None
    upper_case = True
    dtype = None

    def __init__(self, name=None, default_value=None, dtype=None, upper_case=None):
        """name: PV name is prefix+name
        default_value: may also be a property object"""
        super().__init__(
            inputs=self.input_references,
            calculate=self.calculate_value,
            fset=self.set_value,
        )
        if name is not None:
            self.name = name
        if default_value is not None:
            self.default_value = default_value
        if dtype is not None:
            self.dtype = dtype
        if upper_case is not None:
            self.upper_case = upper_case

    def input_references(self, instance):
        return [self.PV_value_reference(instance)]

    def calculate_value(self, instance, value):
        return self.PV_value(instance, value)

    def set_value(self, instance, value):
        self.PV(instance).value = value

    def PV_value_reference(self, instance):
        from reference import reference
        return reference(self.PV(instance), "value")

    def PV_value(self, instance, value):
        default_value = self.get_default_value(instance)
        return compatible_value(value, default_value, self.dtype)

    def get_default_value(self, instance):
        if hasattr(self.default_value, "fget"):
            return self.default_value.fget(instance)
        else:
            return self.default_value

    def PV(self, instance):
        from CA import PV
        return PV(self.PV_name(instance))

    def PV_name(self, instance):
        name = self.PV_basename(instance)
        if self.upper_case:
            name = name.upper()
        PV_name = self.prefix(instance) + name
        return PV_name

    def prefix(self, instance):
        prefix = ""
        if hasattr(self, "prefix"):
            prefix = instance.prefix
        if hasattr(self, "__prefix__"):
            prefix = instance.__prefix__
        if prefix and not prefix.endswith("."):
            prefix += "."
        return prefix

    def PV_basename(self, instance):
        if self.name is not None:
            name = self.name
        else:
            name = self.get_name(instance)
        return name


def compatible_value(value, default_value, dtype):
    if default_value is None and dtype is not None:
        s = str(dtype)
        if "float" in s or "int" in s or "bool" in s:
            from numpy import nan
            default_value = nan
        else:
            default_value = dtype()

    if dtype is None and default_value is not None:
        dtype = type(default_value)

    if default_value is not None and dtype is not None:
        if value is None:
            value = default_value
        if type(value) != type(default_value):
            from numpy import ndarray, array
            if type(default_value) == ndarray:
                if not is_array(value):
                    value = [value]
                value = array(value, dtype=default_value.dtype)
            elif not is_array(value) and is_array(default_value):
                value = [value]
            else:
                try:
                    value = dtype(value)
                except (ValueError, TypeError):
                    value = default_value
    return value


def is_array(obj):
    from numpy import ndarray
    return isinstance(obj, (list, tuple, ndarray))


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler
    from reference import reference as _reference

    class Acquisition(object):
        prefix = "BIOCARS:ACQUISITION."

        def __repr__(self):
            return f"{type(self).__name__}(prefix={self.prefix})"

        directory = PV_property(dtype=str)


    self = Acquisition()


    @_handler
    def report(event=None):
        logging.info(f"event={event}")


    _reference(self, "directory").monitors.add(report)
    print(f"self.directory = {self.directory!r}")
