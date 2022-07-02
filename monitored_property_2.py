#!/usr/bin/env python
"""
Push notifications
Author: Friedrich Schotte
Date created: 2020-09-05
Date last modified: 2022-06-24
Revision comment: Using module logger to selectively disable debug messages
"""
__version__ = "2.0"

import warnings
import logging

from event import Event
from handler import handler
from monitors import monitors
from reference import reference
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
            value = self.reference(instance).event_history.last_value
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
        values = []
        input_references = self.cache(instance).input_references
        for input_reference in input_references:
            if input_reference.event_history.recording:
                value = input_reference.event_history.last_value
            else:
                value = input_reference.value
            values.append(value)
        return values

    def monitors(self, instance):
        from reference_info import reference_info
        reference = self.reference(instance)
        from event_handlers import Event_Handlers
        from functools import partial
        setup = partial(self.monitor_setup, instance)
        cleanup = partial(self.monitor_cleanup, instance)
        monitors = reference_info(reference, Event_Handlers, setup=setup, cleanup=cleanup)
        return monitors

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

    def set_monitoring(self, instance, monitoring):
        with self.cache(instance).lock:
            if monitoring != self.get_monitoring(instance):
                if monitoring:
                    self.set_monitoring_inputs(instance, True)
                    self.set_inputs_recording_started(instance, True),
                    self.reference(instance).event_history.default_value = self.value(instance)
                else:
                    self.set_monitoring_inputs(instance, False)

    def get_monitoring(self, instance):
        return all([
            self.get_inputs_recording_started(instance),
            self.get_monitoring_inputs(instance)
        ])

    def get_monitoring_inputs(self, instance):
        return self.cache(instance).monitoring_inputs

    def set_monitoring_inputs(self, instance, monitoring):
        if monitoring:
            input_references = self.cache(instance).input_references
            for i, input_reference in enumerate(input_references):
                input_handler = self.input_handler(instance, i)
                monitors(input_reference).add(input_handler)
            for dependency_reference in self.cache(instance).dependency_references:
                dependency_handler = self.dependency_handler(instance)
                monitors(dependency_reference).add(dependency_handler)
            self.cache(instance).monitoring_inputs = True
        else:
            self.cache(instance).monitoring_inputs = False
            for i, input_reference in enumerate(self.cache(instance).input_references):
                input_handler = self.input_handler(instance, i)
                if input_handler in monitors(input_reference):
                    # logger.debug("remove_monitor(%r, %r)" % (input_reference, event_handler))
                    monitors(input_reference).remove(input_handler)
            for dependency_reference in self.cache(instance).dependency_references:
                dependency_handler = self.dependency_handler(instance)
                monitors(dependency_reference).remove(dependency_handler)

    def get_inputs_recording_started(self, instance):
        input_references = self.cache(instance).input_references
        recording = all([input_reference.event_history.recording_started for input_reference in input_references])
        return recording

    def set_inputs_recording_started(self, instance, recording_started):
        input_references = self.cache(instance).input_references
        for input_reference in input_references:
            input_reference.event_history.recording_started = recording_started

    def get_input_last_values(self, instance):
        input_references = self.cache(instance).input_references
        last_values = [input_reference.event_history.last_value for input_reference in input_references]
        return last_values

    def input_handler(self, instance, input_count: int):
        return handler(self.handle_input_change, instance, input_count)

    def dependency_handler(self, instance):
        return handler(self.handle_dependency_change, instance)

    def handle_dependency_change(self, instance, event=None):
        logger.debug(f"{self.repr(instance)}: event={event}")
        self.generate_new_event(instance, event.time)

    def handle_input_change(self, instance, input_count, event):
        self.check_event(instance, event, input_count)

        input_references = self.cache(instance).input_references
        input_references[input_count].event_history.add(event)

        self.generate_new_event(instance, event.time)

    def generate_new_event(self, instance, time):
        input_references = self.cache(instance).input_references
        input_values = [ref.event_history.value(time) for ref in input_references]
        input_timestamps = Timestamps([ref.event_history.last_event_time_before_or_at(time) for ref in input_references])
        value = self.value_from_input_values(instance, input_values)
        new_event = Event(
            value=value,
            time=time,
            timestamps=input_timestamps,
            reference=self.reference(instance),
        )
        event_history = self.reference(instance).event_history
        competing_events = event_history.events_at_time(time)
        is_new_event = all([new_event.timestamps >= ev.timestamps for ev in competing_events])
        if is_new_event:
            if competing_events:
                new_event.version = max([ev.version for ev in competing_events]) + 1
            event_history.add(new_event)
            self.call_monitors(instance, new_event)

    def check_event(self, instance, event, input_count):
        input_references = self.cache(instance).input_references
        if event and event.reference != input_references[input_count]:
            logger.warning("Asked for updates of %r, instead got update of %r" %
                           (input_references[input_count], event.reference))

    def call_monitors(self, instance, event):
        for monitor in list(self.monitors(instance)):
            monitor(event=event)

    def value(self, instance):
        input_values = self.input_values(instance)
        value = self.value_from_input_values(instance, input_values)
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

    def get_input_references(self, instance):
        if self.input_references:  # for backward compatibility
            input_references = self.input_references(instance)
        elif self.inputs:
            input_references = self.inputs(instance)
        else:
            input_references = self.auto_input_references(instance)
        return input_references

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

    def cache(self, instance):
        from reference_info import reference_info
        reference = self.reference(instance)
        attributes = reference_info(reference, Monitored_Property_Cache, self, instance)
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


class Monitored_Property_Cache(object):
    def __init__(self, monitored_property_object, instance):
        from threading import Lock
        self.lock = Lock()
        self.monitoring_inputs = False
        self.input_references = monitored_property_object.get_input_references(instance)
        self.dependency_references = monitored_property_object.get_dependency_references(instance)

    def __repr__(self):
        attrs = []
        if self.monitoring_inputs:
            attrs.append(f"monitoring_inputs={self.monitoring_inputs}")
        if self.input_references:
            attrs.append(f"input_references={self.input_references}")
        if self.dependency_references:
            attrs.append(f"dependency_references={self.dependency_references}")
        attrs = ", ".join(attrs)
        s = f"{self.class_name}({attrs})"
        return s

    @property
    def class_name(self):
        class_name = type(self).__name__
        return class_name


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
            try:
                count = base_count1 * 10 + base_count0
            except Exception as x:
                logging.error(f"{x}")
                from numpy import nan
                count = nan
            return count

        @count.setter
        def count(self, count):
            self.base_count0 = count % 10
            self.base_count1 = count // 10

        def __repr__(self): return f"{type(self).__name__}()"

    self = Example.base_count0
    instance = Example()

    @handler
    def report(event=None):
        logging.info(f"event={event}")

    reference(instance, "count0").monitors.add(report)
    reference(instance, "base_count0").monitors.add(report)
    reference(instance, "base_count1").monitors.add(report)
    reference(instance, "count").monitors.add(report)
    print("instance.count0 += 1")
