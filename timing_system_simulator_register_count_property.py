#!/usr/bin/env python
"""
FPGA Timing System Simulator

Author: Friedrich Schotte
Date created: 2021-08-30
Date last modified: 2021-08-30
Revision comment:
"""
__version__ = "1.0"

from logging import warning


class register_count_property(property):
    from cached_function import cached_function

    def __init__(self, name):
        self.name = name
        super().__init__(
            fget=self.get_property,
            fset=self.set_property,
        )

    def __repr__(self):
        return f"{type(self).__name__}({self.name})"

    def get_property(self, instance):
        return self.reference(instance).value

    def set_property(self, instance, value):
        self.reference(instance).value = value

    def reference(self, instance):
        from reference import reference
        return reference(self.object(instance), "count")

    def object(self, instance):
        return getattr(instance.timing_system.registers, self.name)

    def monitors(self, instance):
        return self.attributes(instance).handlers

    def monitor_setup(self, instance):
        self.reference(instance).monitors.add(self.handler(instance))

    def monitor_cleanup(self, instance):
        self.reference(instance).monitors.remove(self.handler(instance))

    def handler(self, instance):
        from handler import handler
        return handler(self.handle_change, instance)

    def handle_change(self, instance, event):
        from reference import reference
        from event import event as event_object
        new_reference = reference(instance, self.get_name(instance))
        new_event = event_object(time=event.time, value=event.value, reference=new_reference)
        self.monitors(instance).call(event=new_event)

    def attributes(self, instance):
        attributes_cache = self.attributes_cache(instance)
        name = self.get_name(instance)
        if name not in attributes_cache:
            attributes_cache[name] = property_attributes(self, instance)
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


class property_attributes(object):
    def __init__(self, property_object, instance):
        from event_handlers import Event_Handlers
        from functools import partial
        self.handlers = Event_Handlers(
            setup=partial(property_object.monitor_setup, instance),
            cleanup=partial(property_object.monitor_cleanup, instance),
        )

    def __repr__(self):
        name = type(self).__qualname__
        attrs = []
        if self.handlers:
            attrs.append("handlers=%r" % (self.handlers,))
        s = "%s(%s)" % (name, ", ".join(attrs))
        return s
