#!/usr/bin/env python
"""
Push notifications
Author: Friedrich Schotte
Date created: 2020-09-05
Date last modified: 2022-06-19
Revision comment: Using module logger to selectively disable debug messages
"""
__version__ = "1.6.2"

import warnings
import logging

from event import Event
from handler import handler
from monitored_property_attributes import Monitored_Property_Attributes
from monitors import monitors
from reference import reference
from time_string import date_time, time_string
from timed_value import Timed_Value
from timestamps import Timestamps

logger = logging.getLogger(__name__)
if not logger.level:
    logger.level = logging.DEBUG


class monitored_property(property):
    parameter_names = ["get", "set", "input_references", "inputs", "calculate"]

    def __init__(self,
                 fget=None,
                 fset=None,
                 input_references=None,  # for backward compatibility
                 inputs=None,
                 dependencies=None,
                 calculate=None,
                 ):

        self.get = fget  # for backward compatibility
        self.set = fset
        self.input_references = input_references
        self.inputs = inputs
        self.dependencies = dependencies
        self.calculate = calculate
        property.__init__(self, self.get_property, self.set_property)

    def __repr__(self):
        return f"{self.class_name}({self.parameters_representation})"

    def setter(self, fset):
        """Usage: decorator"""
        self.set = fset
        return self

    def dependency_references(self, dependencies):
        """Usage: decorator"""
        self.dependencies = dependencies
        return self

    def get_property(self, instance):
        self.set_monitoring(instance, True)
        if self.get_monitoring(instance):
            timed_value = self.get_timed_value_from_cache(instance)
            if not timed_value:
                logger.warning(f"{self.repr(instance)}: Cached timed_value={timed_value}")
            value = timed_value.value
        else:
            value = self.value(instance)
        return value

    def set_property(self, instance, value):
        if self.set:
            self.set(instance, value)
        else:
            # raise AttributeError("Cannot set this attribute")
            logger.warning(f"{self.repr(instance)}: AttributeError: Cannot set this attribute")

    @property
    def class_name(self): return type(self).__name__

    @property
    def parameters_representation(self):
        parameters = []
        for name in self.parameter_names:
            obj = getattr(self, name)
            if obj is not None:
                parameters.append(f"{name}={self.object_representation(obj)}")
        parameters = ", ".join(parameters)
        return parameters

    @staticmethod
    def object_representation(obj):
        if hasattr(obj, "__qualname__"):
            s = getattr(obj, "__qualname__")
        elif hasattr(obj, "__name__"):
            s = getattr(obj, "__name__")
        else:
            s = repr(obj)
        return s

    def input_values(self, instance):
        if self.get_monitoring(instance):
            input_values = self.attributes(instance).cached_input_values
        else:
            input_values = self.attributes(instance).live_input_values
        return input_values

    def monitors(self, instance):
        return self.attributes(instance).handlers

    def monitor(self, instance, proc, *args, **kwargs):
        warnings.warn("monitor() is deprecated, use monitors()",
                      DeprecationWarning, stacklevel=2)
        self.monitors(instance).add(handler(proc, *args, **kwargs))

    def monitor_clear(self, instance, proc, *args, **kwargs):
        warnings.warn("monitor_clear() is deprecated, use monitors()",
                      DeprecationWarning, stacklevel=2)
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
        self.set_monitoring(instance, True)

    def monitor_cleanup(self, instance):
        self.set_monitoring(instance, False)

    def set_monitoring(self, instance, value):
        with self.attributes(instance).lock:
            if value != self.get_monitoring(instance):
                if value:
                    self.attributes(instance).update_cached_input_values()
                    self.attributes(instance).update_cached_value(self.value(instance))
                    self.monitor_inputs(instance)
                else:
                    self.unmonitor_inputs(instance)
                    self.attributes(instance).clear_cached_inputs_values()
                    self.attributes(instance).clear_cached_value()

    def get_monitoring(self, instance):
        return all([
            self.attributes(instance).monitoring_inputs,
            self.attributes(instance).input_values_are_cached,
            self.attributes(instance).value_is_cached,
        ])

    def monitor_inputs(self, instance):
        for i, input_reference in enumerate(self.attributes(instance).cached_input_references):
            input_handler = self.input_handler(instance, i)
            monitors(input_reference).add(input_handler)
        for dependency_reference in self.attributes(instance).cached_dependency_references:
            dependency_handler = self.dependency_handler(instance)
            monitors(dependency_reference).add(dependency_handler)
        self.attributes(instance).monitoring_inputs = True

    def unmonitor_inputs(self, instance):
        self.attributes(instance).monitoring_inputs = False
        for i, input_reference in enumerate(self.attributes(instance).cached_input_references):
            input_handler = self.input_handler(instance, i)
            if input_handler in monitors(input_reference):
                # logger.debug("remove_monitor(%r, %r)" % (input_reference, event_handler))
                monitors(input_reference).remove(input_handler)
        for dependency_reference in self.attributes(instance).cached_dependency_references:
            dependency_handler = self.dependency_handler(instance)
            monitors(dependency_reference).remove(dependency_handler)

    def input_handler(self, instance, input_count: int):
        return handler(self.handle_input_change, instance, input_count)

    def dependency_handler(self, instance):
        return handler(self.handle_dependency_change, instance)

    def handle_dependency_change(self, instance, event=None):
        logger.debug(f"{self.repr(instance)}: event={event}")

        from time import time as now
        input_values = self.input_values(instance)
        value = self.value_from_input_values(instance, input_values)

        if event:
            time = event.time
        else:
            time = now()
        self.generate_event(instance, value, time)

    def handle_input_change(self, instance, input_count, event):
        from same import same
        with self.attributes(instance).lock:
            # logger.debug(f"{self.repr(instance)}: input_count={input_count}, event={event}")
            self.check_event(instance, event, input_count)

            new_event = None

            old = self.attributes(instance).get_cached_timed_input_value(input_count)

            if event.time < old.time:
                logger.debug(f"{self.repr(instance)}, input_count={input_count}: Events out of order: Ignoring {event.value!r}, {time_string(old.time - event.time)} older than {old.value!r}: {date_time(event.time)} vs {date_time(old.time)}")
            if event.time == old.time and not same(event.value, old.value):
                logger.warning(f"{self.repr(instance)}, input_count={input_count}: Conflict {event.value!r} vs {old.value!r} at {date_time(event.time)}")
            # if event.time == old.time and same(event.value, old.value):
            #     logger.debug(f"{self.repr(instance)}, input_count={input_count}: Duplicate event {event.value!r} at {date_time(event.time)}")

            if event.time >= old.time or not same(event.value, old.value):
                input_updated = True
            else:
                input_updated = False

            if input_updated:
                self.attributes(instance).set_cached_timed_input_value(input_count, Timed_Value(event.value, event.time))
                timed_input_values = self.attributes(instance).cached_timed_input_values
                input_values = [x.value for x in timed_input_values]
                input_timestamps = Timestamps([x.time for x in timed_input_values])
                old_timestamps = self.attributes(instance).cached_timed_value.timestamps

                # if input_timestamps == old_timestamps:
                #     logger.debug(f"{self.repr(instance)}: Duplicate input timestamps {input_timestamps}")

                if input_timestamps >= old_timestamps:
                    # To do: Skip calculation if input values have not changed, only timestamps
                    value = self.value_from_input_values(instance, input_values)
                    old_value = self.attributes(instance).cached_timed_value.value
                    if not same(value, old_value):
                        self.attributes(instance).cached_timed_value.value = value
                        self.attributes(instance).cached_timed_value.timestamps = input_timestamps
                        new_event = Event(
                            value=self.attributes(instance).cached_timed_value.value,
                            time=self.attributes(instance).cached_timed_value.timestamps.last,
                            reference=self.reference(instance),
                        )
                        new_event_time = self.attributes(instance).cached_timed_value.timestamps.last
                        if new_event.time == self.attributes(instance).last_event_time:
                            last_event = self.attributes(instance).last_event
                            fake_event_time = last_event.time + 1e-6
                            new_event.time = fake_event_time
                            logger.debug(f"{self.repr(instance)}: Overriding {last_event} with {new_event}")
                        self.attributes(instance).last_event = new_event
                        self.attributes(instance).last_event_time = new_event_time

        if new_event:
            self.call_monitors(instance, new_event)

    def check_event(self, instance, event, input_count):
        input_references = self.attributes(instance).cached_input_references
        if event and event.reference != input_references[input_count]:
            logger.warning("Asked for updates of %r, instead got update of %r" %
                           (input_references[input_count], event.reference))

    def generate_event(self, instance, value, time):
        logger.debug(f"{self.repr(instance)}, value={value!r:.80}, time={date_time(time)}")
        old_value = self.attributes(instance).cached_timed_value.value
        from same import same
        if not same(value, old_value):
            self.attributes(instance).cached_timed_value.value = value
            self.attributes(instance).cached_timed_value.timestamps = Timestamps([time])
            event = self.event(instance)
            self.call_monitors(instance, event)

    def event(self, instance):
        new_event = Event(
            value=self.attributes(instance).cached_timed_value.value,
            time=self.attributes(instance).cached_timed_value.time,
            reference=self.reference(instance),
        )
        return new_event

    def call_monitors(self, instance, event):
        for monitor in list(self.monitors(instance)):
            monitor(event=event)

    def value(self, instance):
        if self.calculate_function:
            input_values = self.input_values(instance)
            value = call(self.calculate_function, instance, *input_values)
        elif self.get:  # for backward compatibility
            value = self.get(instance)
        else:
            # raise AttributeError("unreadable attribute")
            logger.warning(f"{self.repr(instance)}: AttributeError: unreadable attribute.")
            value = None
        return value

    def value_from_input_values(self, instance, input_values):
        if self.calculate_function:
            value = call(self.calculate_function, instance, *input_values)
        elif self.get:  # for backward compatibility
            value = self.get(instance)
        else:
            # raise AttributeError("unreadable attribute")
            logger.warning(f"{self.repr(instance)}: AttributeError: unreadable attribute.")
            value = None
        return value

    def reference(self, instance):
        return reference(instance, self.get_name(instance))

    def get_timed_value_from_cache(self, instance):
        from time import time as now
        timed_value = self.get_cached_timed_value(instance)
        if not timed_value:
            timed_value.value = self.value(instance)
            timed_value.time = now()
            logger.warning(f"{self.repr(instance)}: Value is not cached. Using live value {timed_value} instead")
        return timed_value

    def get_cached_timed_value(self, instance):
        timed_value = self.attributes(instance).cached_timed_value
        from copy import copy
        timed_value = copy(timed_value)
        return timed_value

    def get_input_references(self, instance):
        if self.input_references:  # for backward compatibility
            input_references = self.input_references(instance)
        elif self.inputs:
            input_references = self.inputs(instance)
        else:
            input_references = self.auto_input_references(instance)
        return input_references

    def cached_input_references(self, instance):
        return self.attributes(instance).cached_input_references

    def auto_input_references(self, instance):
        from function_argument_names import function_argument_names
        f = self.calculate_function
        if f:
            argument_names = function_argument_names(f)
        else:
            argument_names = []
        input_references = [reference(instance, name) for name in argument_names]
        return input_references

    @property
    def calculate_function(self):
        from function_argument_names import function_argument_names
        if self.calculate:
            f = self.calculate
        elif self.get:
            if function_argument_names(self.get):
                f = self.get
            else:
                f = None
        else:
            f = None
        return f

    def get_dependency_references(self, instance):
        if self.dependencies:
            references = self.dependencies(instance)
        else:
            references = []
        return references

    def attributes(self, instance) -> Monitored_Property_Attributes:
        if not hasattr(instance, "__monitored_property_lock__"):
            from threading import Lock
            instance.__monitored_property_lock__ = Lock()
        attributes_lock = instance.__monitored_property_lock__
        if not hasattr(instance, "__monitored_property__"):
            with attributes_lock:
                if not hasattr(instance, "__monitored_property__"):
                    instance.__monitored_property__ = {}
        all_attributes = instance.__monitored_property__
        name = self.get_name(instance)
        if name not in all_attributes:
            attributes = Monitored_Property_Attributes(self, instance)
            with attributes_lock:
                if name not in all_attributes:
                    all_attributes[name] = attributes
        attributes = all_attributes[name]
        return attributes

    def get_name(self, instance):
        if not self.__property_name__:
            class_object = type(instance)
            for name in dir(class_object):
                if getattr(class_object, name) == self:
                    break
            else:
                logger.warning(f"Could not find {self} in {class_object}")
                name = "unknown"
            self.__property_name__ = name
        return self.__property_name__

    __property_name__ = ""

    def repr(self, instance):
        property_name = self.get_name(instance)
        return f"{instance}.{property_name}"


def call(function, instance, *input_values):
    # logger.debug(f"type({function}) is staticmethod: {type(function) is staticmethod}")
    if type(function) is staticmethod:
        value = function.__func__(*input_values)
    else:
        value = function(instance, *input_values)
    return value


def to_references(references):
    return [to_reference(x) for x in references]


def to_reference(x):
    if type(x) == tuple:
        logger.warning(f"Converting {x} to reference")
        x = reference(*x)
    return x


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    class Example(object):
        from monitored_value_property import monitored_value_property
        count0 = monitored_value_property(default_value=9)

        @monitored_property
        def base_count0(self, count0): return count0 % 10

        @base_count0.setter
        def base_count0(self, base_count0):
            self.count0 = self.base_count1 * 10 + base_count0

        @monitored_property
        def base_count1(self, count0): return count0 // 10

        @base_count1.setter
        def base_count1(self, base_count1):
            self.count0 = base_count1 * 10 + self.base_count0

        @monitored_property
        def count(self, base_count0, base_count1):
            return base_count1 * 10 + base_count0

        @count.setter
        def count(self, count):
            self.base_count0 = count % 10
            self.base_count1 = count // 10

        def __repr__(self): return f"{type(self).__name__}()"

    self = Example.count
    instance = Example()

    @handler
    def report(event=None):
        logging.info(f"event={event}")

    monitors(reference(instance, "count0")).add(report)
    monitors(reference(instance, "base_count0")).add(report)
    monitors(reference(instance, "base_count1")).add(report)
    monitors(reference(instance, "count")).add(report)
    print("instance.count0 += 1")
