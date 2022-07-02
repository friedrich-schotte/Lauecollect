#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-10-13
Date last modified: 2020-10-13
Revision comment:
"""
__version__ = "1.0"

import logging
from logging import warning

from cached_function import cached_function


class timed_out_property(property):
    def __init__(self, period):
        self._period = period
        property.__init__(self, fget=self.get_property, fset=self.set_property)
        from threading import Lock
        self.attributes_lock = Lock()

    def get_property(self, instance):
        from time import time
        start_time = self.attributes(instance).start_time
        timed_out = time() - start_time > self.period(instance)
        return timed_out

    def set_property(self, instance, timed_out):
        from time import time

        new_value = timed_out
        old_value = self.get_property(instance)

        if timed_out:
            self.attributes(instance).start_time = 0.0
            self.attributes(instance).timer.cancel()
        else:
            self.attributes(instance).start_time = time()
            if self.monitors(instance):
                self.restart_timer(instance)

        if new_value != old_value:
            from event import event as event_object
            from time import time
            new_event = event_object(
                time=time(),
                value=new_value,
                reference=self.reference(instance),
            )
            self.monitors(instance).call(event=new_event)

    def monitors(self, instance):
        return self.attributes(instance).monitors

    def period(self, instance):
        if type(self._period) == str:
            period = getattr(instance, self._period)
        else:
            period = self._period
        return period

    def monitors_setup(self, instance):
        if not self.attributes(instance).timer.is_alive():
            self.restart_timer(instance)

    def monitors_cleanup(self, instance):
        self.attributes(instance).timer.cancel()

    def handle_timer(self, instance):
        from event import event as event_object
        from time import time
        value = self.get_property(instance)
        new_event = event_object(
            time=time(),
            value=value,
            reference=self.reference(instance),
        )
        self.monitors(instance).call(event=new_event)

    def restart_timer(self, instance):
        from time import time
        dt = self.attributes(instance).start_time + self.period(instance) - time()
        self.attributes(instance).timer.cancel()
        if dt > 0:
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
            interval = self.period(instance)
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
        self.start_time = 0.0


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler
    from reference import reference as _reference

    class Test:
        time_out = 10
        timed_out = timed_out_property("time_out")

    instance = Test()
    self = Test.timed_out

    @_handler
    def report(event):
        logging.info(f"event={event}")

    _reference(instance, "timed_out").monitors.add(report)
    print(f"instance.timed_out = {instance.timed_out}")
