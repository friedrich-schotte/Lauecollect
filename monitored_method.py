#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-10-27
Date last modified: 2021-07-23
Revision comment: Refactored
"""
__version__ = "1.0.4"

from logging import info, warning


class monitored_method(property):
    def __init__(self, method):
        self.method = method
        property.__init__(self, fget=self.get_method)
        self.f_dependencies = None

        from threading import Lock
        self.attributes_lock = Lock()

    def __repr__(self):
        class_name = type(self).__name__
        method_name = self.method.__qualname__
        return f"{class_name}({method_name})"

    def monitors(self, instance):
        return self.attributes(instance).handlers

    def add_monitor(self, instance, event_handler):
        # For backward compatibility with monitor.add_monitor
        self.monitors(instance).add(event_handler)

    def remove_monitor(self, instance, event_handler):
        # For backward compatibility with monitor.remove_monitor
        self.monitors(instance).remove(event_handler)

    def get_method(self, instance):
        from types import MethodType
        return MethodType(self.method, instance)

    def dependencies(self, f_dependencies):
        self.f_dependencies = f_dependencies
        return self

    def monitor_setup(self, instance):
        for reference in self.get_dependencies(instance):
            reference.monitors.add(self.handler(instance))

    def monitor_cleanup(self, instance):
        for reference in self.get_dependencies(instance):
            reference.monitors.remove(self.handler(instance))

    def get_dependencies(self, instance):
        if self.f_dependencies:
            dependencies = self.f_dependencies(instance)
        else:
            dependencies = []
        return dependencies

    def handler(self, instance):
        from handler import handler
        return handler(self.handle_change, instance)

    def handle_change(self, instance, event=None):
        self.monitors(instance).call(event=self.event(instance, event))

    def event(self, instance, event):
        from reference import reference
        value = self.get_method(instance)
        event_reference = reference(instance, self.method.__name__)
        if event:
            time = event.time
        else:
            from time import time
            time = time()
        from event import event
        return event(value=value, reference=event_reference, time=time)

    def attributes(self, instance):
        if not hasattr(instance, "__monitored_method__"):
            with self.attributes_lock:
                if not hasattr(instance, "__monitored_method__"):
                    instance.__monitored_method__ = {}
        all_attributes = instance.__monitored_method__
        name = self.get_name(instance)
        if name not in all_attributes:
            with self.attributes_lock:
                if name not in all_attributes:
                    all_attributes[name] = Attributes(self, instance)
        attributes = all_attributes[name]
        return attributes

    def get_name(self, instance):
        if not self.__property_name__:
            class_object = type(instance)
            for name in dir(class_object):
                if getattr(class_object, name) == self:
                    break
            else:
                warning(f"Could not find {self} in {class_object}")
                name = "unknown"
            self.__property_name__ = name
        return self.__property_name__

    __property_name__ = ""


class Attributes(object):
    def __init__(self, monitored_method_object: monitored_method, instance):
        self.monitored_method = monitored_method_object
        self.instance = instance
        from event_handlers import Event_Handlers
        from functools import partial
        self.handlers = Event_Handlers(
            setup=partial(monitored_method_object.monitor_setup, instance),
            cleanup=partial(monitored_method_object.monitor_cleanup, instance),
        )

    def __repr__(self):
        name = type(self).__name__
        attrs = []
        if self.handlers:
            attrs.append("event_handlers=%r" % (self.handlers,))
        s = "%s(%s)" % (name, ", ".join(attrs))
        return s


if __name__ == "__main__":
    import logging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from reference import reference
    from handler import handler as _handler

    class Test:
        from monitored_value_property import monitored_value_property
        from monitored_property import monitored_property

        def __repr__(self):
            return "Test()"

        y = monitored_value_property(default_value=1)

        @monitored_method
        def f(self, x):
            return x + self.y

        @f.dependencies
        def f(self):
            return [reference(self, "y")]

        def dependencies_z(self):
            return [reference(self, "f")]

        def calculate_z(self):
            return self.f(0) + 1

        z = monitored_property(
            dependencies=dependencies_z,
            calculate=calculate_z,
        )

    test = Test()

    @_handler
    def report(event=None):
        info(f'event={event}')

    reference(test, 'y').monitors.add(report)
    reference(test, 'f').monitors.add(report)
    reference(test, 'z').monitors.add(report)
    print("test.z")
    # print("_reference(test, 'z').monitors")
