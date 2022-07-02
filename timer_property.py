#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-12-22
Date last modified: 2020-12-22
Revision comment:
"""
__version__ = "1.0"

from logging import warning

from cached_function import cached_function


class timer_property(property):
    def __init__(self, period=1.0):
        self.period = period
        property.__init__(self, fget=self.get_property)
        from threading import Lock
        self.attributes_lock = Lock()

    def get_property(self, _instance):
        from time import time
        return time()

    def monitors(self, instance):
        return self.attributes(instance).monitors

    def monitors_setup(self, instance):
        if not self.attributes(instance).timer.is_alive():
            self.restart_timer(instance)

    def monitors_cleanup(self, instance):
        self.attributes(instance).timer.cancel()

    def handle_timer(self, instance):
        self.restart_timer(instance)

        from event import event as event_object
        from time import time
        new_event = event_object(
            time=time(),
            value=time(),
            reference=self.reference(instance),
        )
        self.monitors(instance).call(event=new_event)

    def restart_timer(self, instance):
        from time import time
        dt = self.period - (time() % self.period)
        self.attributes(instance).timer = self.new_timer(instance, dt)
        self.attributes(instance).timer.start()

    def reference(self, instance):
        from reference import reference
        return reference(instance, self.get_name(instance))

    def attributes(self, instance):
        if not hasattr(instance, self.attributes_name):
            with self.attributes_lock:
                if not hasattr(instance, self.attributes_name):
                    setattr(instance, self.attributes_name, {})
        all_attributes = getattr(instance, self.attributes_name)
        name = self.get_name(instance)
        if name not in all_attributes:
            with self.attributes_lock:
                if name not in all_attributes:
                    all_attributes[name] = Attributes(self, instance)
        attributes = all_attributes[name]
        return attributes

    @property
    def attributes_name(self):
        return f"__{self.class_name}__"

    @property
    def class_name(self):
        return type(self).__name__

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

    def new_timer(self, instance, interval=None):
        if interval is None:
            interval = self.period
        from threading import Timer
        timer = Timer(
            interval=interval,
            function=self.handle_timer,
            args=(instance,),
        )
        timer.daemon = True
        return timer


class Attributes:
    def __init__(self, timer_property, instance):
        from event_handlers import Event_Handlers
        from functools import partial
        self.monitors = Event_Handlers(
            setup=partial(timer_property.monitors_setup, instance),
            cleanup=partial(timer_property.monitors_cleanup, instance),
        )
        self.timer = timer_property.new_timer(instance)
