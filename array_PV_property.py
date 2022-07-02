"""EPICS Channel Access Process Variable as class property
Author: Friedrich Schotte
Date created: 2020-12-16
Date last modified: 2022-06-15
Revision comment: Updated examples
"""
__version__ = "1.1.5"

import warnings
from logging import warning


class array_PV_property(property):
    def __init__(self, name, default_value):
        """name: PV name is instance.prefix+name
        """
        property.__init__(self, fget=self.get_property, fset=self.set_property)
        self.name = name
        self.default_value = default_value

    def __repr__(self):
        return "%s(%r)" % (self.class_name, self.name)

    def get_property(self, instance):
        from array_PV import array_PV
        return array_PV(self.PV_name(instance), self.default_value)

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
        value = self.get_property(instance)[:]
        self.set_cached_value(instance, value)
        self.PV_value_reference(instance).monitors.add(self.handler(instance))

    def monitor_cleanup(self, instance):
        self.PV_value_reference(instance).monitors.remove(self.handler(instance))
        self.set_cached_value(instance, None)

    def PV_monitors(self, instance):
        from reference import reference
        return reference(self.PV(instance), "value").monitors

    def PV_value_reference(self, instance):
        from reference import reference
        return reference(self.PV(instance), "value")

    def handler(self, instance):
        from handler import handler
        return handler(self.handle_change, instance)

    def handle_change(self, instance, event):
        from as_array import as_array
        from reference import reference
        from event import event as event_object
        from same import same

        # logging.debug(f"{self}: {instance}: {event}")
        value = as_array(event.value)
        if not same(value, self.get_cached_value(instance)):
            new_reference = reference(instance, self.get_name(instance))
            new_event = event_object(time=event.time, value=value, reference=new_reference)
            self.monitors(instance).call(event=new_event)
        self.set_cached_value(instance, value)

    def PV(self, instance):
        from CA import PV
        return PV(self.PV_name(instance))

    def PV_name(self, instance):
        return self.prefix(instance) + self.name.upper()

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

    from cached_function import cached_function

    @cached_function()
    def get_name(self, instance):
        class_object = type(instance)
        for name in dir(class_object):
            if getattr(class_object, name) == self:
                break
        else:
            warning(f"Could not find {self} in {class_object}")
            name = "unknown"
        return name

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

        def __repr__(self):
            name = type(self).__qualname__
            attrs = []
            if self.handlers:
                attrs.append("handlers=%r" % (self.handlers,))
            s = "%s(%s)" % (name, ", ".join(attrs))
            return s


if __name__ == "__main__":
    import logging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from reference import reference as _reference
    from item_reference import item_reference
    from handler import handler as _handler

    class Configuration(object):
        prefix = "BIOCARS:CONFIGURATION.METHOD"

        def __repr__(self):
            return "%s(prefix=%r)" % (type(self).__name__, self.prefix)

        widths = array_PV_property("widths", 200)


    self = Configuration()

    @_handler
    def report(event=None):
        logging.info(f"event={event}")

    _reference(self, "widths").monitors.add(report)
    item_reference(self.widths, 0).monitors.add(report)
    print(f"self.widths = {self.widths[:]}")
    print(f"self.widths[0] = {self.widths[0]}")
