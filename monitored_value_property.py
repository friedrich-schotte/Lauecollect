#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-11-16
Date last modified: 2020-11-16
Revision comment:
"""
__version__ = "1.0"

from logging import warning, info


class monitored_value_property(property):
    def __init__(self, default_value):
        self.default_value = default_value
        property.__init__(self, self.get_property, self.set_property)

    def __repr__(self):
        return f'{self.class_name}({self.default_value})'

    def get_property(self, instance):
        return self.attributes(instance).value.value

    def set_property(self, instance, value):
        old_value = self.get_property(instance)
        from same import same
        if not same(value, old_value):
            from time import time
            time = time()
            self.attributes(instance).value.value = value
            self.attributes(instance).value.time = time
            from event import event
            new_event = event(
                time=time,
                value=value,
                reference=self.reference(instance)
            )
            self.monitors(instance).call(event=new_event)

    def monitors(self, instance):
        return self.attributes(instance).event_handlers

    def attributes(self, instance):
        name = self.get_name(instance)
        attributes_cache = self.attributes_cache(instance)
        if name not in attributes_cache:
            attributes_cache[name] = Attributes(self, instance)
        attributes = attributes_cache[name]
        return attributes

    def attributes_cache(self, instance):
        name = self.attributes_cache_base_name
        if not hasattr(instance, name):
            setattr(instance, name, {})
        attributes_cache = getattr(instance, name)
        return attributes_cache

    @property
    def attributes_cache_base_name(self):
        return f"__{self.class_name}__".lower()

    @property
    def class_name(self):
        return type(self).__name__

    def reference(self, instance):
        from reference import reference
        return reference(instance, self.get_name(instance))

    from cached_function import cached_function

    @cached_function()
    def get_name(self, instance):
        instance = type(instance)
        for name in dir(instance):
            if getattr(instance, name) == self:
                break
        else:
            warning(f"Could not find {self} in {instance}")
            name = "unknown"
        return name

    from deprecated import deprecated

    @deprecated(use_instead=f"{monitors}")
    def monitor(self, instance, proc, *args, **kwargs):
        from handler import handler
        self.monitors(instance).add(handler(proc, *args, **kwargs))

    @deprecated(use_instead=f"{monitors}")
    def monitor_clear(self, instance, proc, *args, **kwargs):
        from handler import handler
        self.monitors(instance).remove(handler(proc, *args, **kwargs))

    @deprecated(use_instead=f"{monitors}")
    def add_monitor(self, instance, event_handler):
        self.monitors(instance).add(event_handler)

    @deprecated(use_instead=f"{monitors}")
    def remove_monitor(self, instance, event_handler):
        self.monitors(instance).remove(event_handler)


class Attributes(object):
    def __init__(self, property_object, _instance):
        from time import time
        self.value = timed_value(
            value=property_object.default_value,
            time=time()
        )
        from event_handlers import Event_Handlers
        self.event_handlers = Event_Handlers()

    def __repr__(self):
        attrs = []
        if self.value:
            attrs.append("value=%r" % self.value)
        if self.event_handlers:
            attrs.append("event_handlers=%r" % self.event_handlers)
        attrs = ", ".join(attrs)
        return f"{self.class_name}({attrs})"

    @property
    def class_name(self):
        return type(self).__name__


class timed_value(object):
    value = None
    time = None

    def __init__(self, value=None, time=None):
        if value is not None:
            self.value = value
        if time is not None:
            self.time = time

    def __repr__(self):
        name = type(self).__name__
        attrs = []
        if self.value is not None:
            attrs.append("value=%r" % (self.value,))
        if self.time is not None:
            from date_time import date_time
            attrs.append("time=%s" % (date_time(self.time),))
        s = "%s(%s)" % (name, ", ".join(attrs))
        return s

    def __eq__(self, other):
        from same import same
        return all([
            same(self.value, getattr(other, "value", None)),
            same(self.time, getattr(other, "time", None)),
        ])

    def __bool__(self):
        return self.value is not None or self.time is not None


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from reference import reference as _reference
    from handler import handler as _handler

    class Example(object):
        count = monitored_value_property(default_value=0)

    self = Example.count
    instance = Example()

    @_handler
    def report(event=None):
        info(f"event={event}")

    _reference(instance, "count").monitors.add(report)
    print("instance.count += 1")
