"""
Author: Friedrich Schotte
Date created: 2022-06-19
Date last modified: 2022-06-19
Revision comment:
"""
__version__ = "1.0"
 
import logging

from event_handlers import Event_Handlers

from event import Event

from timed_value import Timed_Value
from timestamps import Timestamps


class Monitored_Property_Attributes(object):
    def __init__(self, monitored_property_object, instance):
        from threading import Lock
        self.lock = Lock()
        self.cached_timed_value = Timed_Value()
        self.last_event = Event(time=0)
        self.last_event_time = 0
        n = len(monitored_property_object.get_input_references(instance))
        self.input_timed_values = [Timed_Value() for _ in range(n)]
        from functools import partial
        self.handlers = Event_Handlers(
            setup=partial(monitored_property_object.monitor_setup, instance),
            cleanup=partial(monitored_property_object.monitor_cleanup, instance),
        )
        self.monitoring_inputs = False
        self.cached_input_references = monitored_property_object.get_input_references(instance)
        self.cached_dependency_references = monitored_property_object.get_dependency_references(instance)
        self.name = monitored_property_object.get_name(instance)

    def __repr__(self):
        class_name = type(self).__name__
        attrs = [f"name={self.name!r}"]
        if self.cached_timed_value:
            attrs.append(f"cached_timed_value={self.cached_timed_value}")
        if self.input_timed_values:
            attrs.append(f"input_timed_values={self.input_timed_values}")
        if self.handlers:
            attrs.append(f"handlers={self.handlers}")
        attrs = ", ".join(attrs)
        s = f"{class_name}({attrs})"
        return s

    @property
    def cached_timed_input_values(self):
        n = len(self.cached_input_references)
        return [self.get_cached_timed_input_value(i) for i in range(n)]

    @property
    def cached_input_values(self):
        input_values = [x.value for x in self.cached_timed_input_values]
        if any([value is None for value in input_values]):
            logging.debug(f"{self}: cached input_values={input_values}")
        return input_values

    @property
    def live_input_values(self):
        input_references = self.cached_input_references
        input_values = [input_reference.value for input_reference in input_references]
        return input_values

    def get_cached_timed_input_value(self, input_count):
        timed_value = self.input_timed_values[input_count]
        from copy import copy
        timed_value = copy(timed_value)
        return timed_value

    def set_cached_timed_input_value(self, input_count, input_value):
        from copy import copy
        input_value = copy(input_value)
        self.input_timed_values[input_count] = input_value

    def update_cached_input_values(self):
        n = len(self.cached_input_references)
        for input_count in range(n):
            self.update_cached_input_value(input_count)
        # logging.debug(f"{self}: input_values_are_cached={self.attributes(instance).input_values_are_cached}")

    def update_cached_input_value(self, input_count):
        from time import time as now
        input_reference = self.cached_input_references[input_count]
        timed_input_value = Timed_Value(input_reference.value, now())
        old_timed_input_value = self.get_cached_timed_input_value(input_count)
        from same import same
        if not same(timed_input_value.value, old_timed_input_value.value):
            # logging.debug(f"{self}, input_count={input_count}: {input_reference} updated as {timed_input_value}")
            self.set_cached_timed_input_value(input_count, timed_input_value)
        else:
            # logging.debug(f"{self}, input_count={input_count}: {input_reference} left unchanged as {old_timed_input_value}")
            pass

    def update_cached_value(self, value):
        timed_input_values = self.cached_timed_input_values
        input_timestamps = Timestamps([x.time for x in timed_input_values])
        # logging.debug(f"{self}: input_timestamps: {input_timestamps}")

        old_value = self.cached_timed_value.value
        from same import same
        if not same(value, old_value):
            self.cached_timed_value.timestamps = input_timestamps
            self.cached_timed_value.value = value

    @property
    def input_values_are_cached(self):
        return all([v for v in self.cached_timed_input_values])

    @property
    def value_is_cached(self):
        return bool(self.cached_timed_value)

    def clear_cached_inputs_values(self):
        for time_valued in self.input_timed_values:
            time_valued.time = None
            time_valued.value = None

    def clear_cached_value(self):
        self.cached_timed_value.timestamps = Timestamps()
        self.cached_timed_value.value = None



if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
