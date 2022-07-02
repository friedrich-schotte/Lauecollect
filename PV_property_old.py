"""EPICS Channel Access Process Variable as class property
Author: Friedrich Schotte
Date created: 2019-05-18
Date last modified: 2022-06-08
Revision comment: Added: update
"""
__version__ = "1.9"

import logging
import warnings

from CA import PV
from cached_function import cached_function


class PV_property(property):
    name = None
    default_value = None
    upper_case = True
    dtype = None
    update = False  # always generate event even if PV keeps the same value

    def __init__(self, name=None, default_value=None, dtype=None, upper_case=None, update=None):
        """name: PV name is prefix+name
        default_value: may also be a property object"""
        property.__init__(self, fget=self.get_property, fset=self.set_property)
        if name is not None:
            self.name = name
        if default_value is not None:
            self.default_value = default_value
        if dtype is not None:
            self.dtype = dtype
        if upper_case is not None:
            self.upper_case = upper_case
        if update is not None:
            self.update = update

    def __repr__(self):
        return f"{self.class_name}(name={self.name!r}, default_value={self.default_value!r})"

    def get_property(self, instance):
        value = self.value(instance, self.PV(instance).value)
        return value

    def set_property(self, instance, value):
        self.PV(instance).value = value

    def monitors(self, instance):
        return self.attributes(instance).handlers

    def monitor(self, instance, proc, *args, **kwargs):
        warnings.warn("monitor() is deprecated, use monitors()",
                      DeprecationWarning, stacklevel=2)
        from handler import handler
        self.monitors(instance).add(handler(proc, *args, **kwargs))

    def monitor_clear(self, instance, proc, *args, **kwargs):
        warnings.warn("monitor_clear() is deprecated, use monitors()",
                      DeprecationWarning, stacklevel=2)
        from handler import handler
        self.monitors(instance).remove(handler(proc, *args, **kwargs))

    def add_monitor(self, instance, event_handler):
        warnings.warn("add_monitor() is deprecated, use monitors()",
                      DeprecationWarning, stacklevel=2)
        self.monitors(instance).add(event_handler)

    def remove_monitor(self, instance, event_handler):
        warnings.warn("remove_monitor() is deprecated, use monitors()",
                      DeprecationWarning, stacklevel=2)
        self.monitors(instance).remove(event_handler)

    def monitor_setup(self, instance):
        value = self.value(instance, self.PV(instance).value)
        self.set_cached_value(instance, value)
        self.PV_value_reference(instance).monitors.add(self.handler(instance))

    def monitor_cleanup(self, instance):
        self.PV_value_reference(instance).monitors.remove(self.handler(instance))
        self.set_cached_value(instance, None)

    def PV_value_reference(self, instance):
        from reference import reference
        return reference(self.PV(instance), "value")

    def handler(self, instance):
        from handler import handler
        return handler(self.handle_change, instance)

    def handle_change(self, instance, event):
        from reference import reference
        from event import event as event_object
        from same import same

        # logging.debug(f"{self}: {instance}: {event}")
        value = self.value(instance, event.value)
        if self.update or not same(value, self.get_cached_value(instance)):
            new_reference = reference(instance, self.get_name(instance))
            new_event = event_object(time=event.time, value=value, reference=new_reference)
            self.monitors(instance).call(event=new_event)
        self.set_cached_value(instance, value)

    def PV(self, instance):
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

    def attributes(self, instance):
        attributes_cache = self.attributes_cache(instance)
        name = self.get_name(instance)
        if name not in attributes_cache:
            attributes_cache[name] = self.Attributes(self, instance)
        attributes = attributes_cache[name]
        return attributes

    def attributes_cache(self, instance):
        if not hasattr(instance, self.attributes_cache_name):
            setattr(instance, self.attributes_cache_name, {})
        attributes_cache = getattr(instance, self.attributes_cache_name)
        return attributes_cache

    @property
    def attributes_cache_name(self):
        return f"__{self.class_name}__".lower()

    @property
    def class_name(self):
        class_name = type(self).__name__
        return class_name

    def PV_basename(self, instance):
        if self.name is not None:
            name = self.name
        else:
            name = self.get_name(instance)
        return name

    @cached_function()
    def get_name(self, instance):
        class_object = type(instance)
        for name in dir(class_object):
            if getattr(class_object, name) == self:
                break
        else:
            logging.warning(f"Could not find {self} in {class_object}")
            name = "unknown"
        return name

    def value(self, instance, value):
        default_value = self.get_default_value(instance)
        return compatible_value(value, default_value, self.dtype)

    def get_default_value(self, instance):
        if hasattr(self.default_value, "fget"):
            return self.default_value.fget(instance)
        else:
            return self.default_value

    def set_cached_value(self, instance, value):
        if hasattr(value, "copy"):
            value = value.copy()
        self.attributes(instance).cached_value = value

    def get_cached_value(self, instance):
        value = self.attributes(instance).cached_value
        if hasattr(value, "copy"):
            value = value.copy()
        return value

    class Attributes(object):
        def __init__(self, PV_property_object, instance):
            from event_handlers import Event_Handlers
            from functools import partial
            self.handlers = Event_Handlers(
                setup=partial(PV_property_object.monitor_setup, instance),
                cleanup=partial(PV_property_object.monitor_cleanup, instance),
            )
            self.cached_value = None

        def __repr__(self):
            name = type(self).__qualname__
            attrs = []
            if self.handlers:
                attrs.append("handlers=%r" % (self.handlers,))
            s = "%s(%s)" % (name, ", ".join(attrs))
            return s


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

        directory = PV_property(dtype=str, update=True)


    self = Acquisition()


    @_handler
    def report(event=None):
        logging.info(f"event={event}")


    _reference(self, "directory").monitors.add(report)
    print(f"self.directory = {self.directory!r}")
