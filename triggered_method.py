#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-02-04
Date last modified: 2022-07-17
Revision comment: Enable by "object.method = True"
"""
__version__ = "2.0"

import logging


class triggered:
    def __init__(self):
        self.arm()

    def arm(self):
        object_type = type(self)
        for attribute_name in dir(object_type):
            class_attribute = getattr(object_type, attribute_name)
            if isinstance(class_attribute, triggered_method):
                setattr(self, attribute_name, True)


class triggered_method(property):
    def __init__(self, procedure):
        self.procedure = procedure
        property.__init__(self, self.get_property, self.set_property)

    def __repr__(self):
        return f"{self.class_name}({self.procedure.__qualname__})"

    def get_property(self, instance):
        return self.get_monitoring_inputs(instance)

    def set_property(self, instance, value):
        self.set_monitoring_inputs(instance, value)

    def set_monitoring_inputs(self, instance, monitoring):
        if monitoring != self.get_monitoring_inputs(instance):
            if monitoring:
                self.cache_input_values(instance)
                for i, reference in enumerate(self.input_references(instance)):
                    reference.monitors.add(self.event_handler(instance, i))
            else:
                for i, reference in enumerate(self.input_references(instance)):
                    reference.monitors.remove(self.event_handler(instance, i))

    def get_monitoring_inputs(self, instance):
        are_monitoring = []
        for i, reference in enumerate(self.input_references(instance)):
            is_monitoring = self.event_handler(instance, i) in reference.monitors
            are_monitoring.append(is_monitoring)
        monitoring = all(are_monitoring)
        return monitoring

    def input_references(self, instance):
        from reference import reference
        return [reference(instance, input_name) for input_name in self.input_names]

    def cache_input_values(self, instance):
        from reference import reference
        input_values = []
        for input_name in self.input_names:
            input_value = reference(instance, input_name).value
            input_values.append(input_value)
        self.attributes(instance).cached_input_values = input_values

    def event_handler(self, instance, input_count):
        from handler import handler
        return handler(self.handle_change, instance, input_count)

    def handle_change(self, instance, input_count, event):
        # logging.debug(f"instance {instance}, input_count {input_count}, event {event}")
        from same import same
        cached_input_values = self.attributes(instance).cached_input_values
        if not same(event.value, cached_input_values[input_count]):
            cached_input_values[input_count] = event.value
            self.attributes(instance).cached_input_values = cached_input_values
            self.procedure(instance, *cached_input_values)

    @property
    def input_names(self):
        from function_argument_names import function_argument_names
        return function_argument_names(self.procedure)

    def attributes(self, instance):
        name = self.get_name(instance)
        attributes_cache = self.attributes_cache(instance)
        if name not in attributes_cache:
            attributes_cache[name] = Attributes()
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

    def get_name(self, instance):
        if not self.__property_name__:
            class_object = type(instance)
            for name in dir(class_object):
                if getattr(class_object, name) == self:
                    break
            else:
                logging.warning(f"Could not find {self} in {class_object}")
                name = "unknown"
            self.__property_name__ = name
        return self.__property_name__

    __property_name__ = ""


class Attributes:
    def __init__(self):
        self.cached_input_values = []

    def __repr__(self):
        return f"{self.class_name}()"

    @property
    def class_name(self):
        return type(self).__name__


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from monitored_value_property import monitored_value_property


    class Example(triggered):
        def __repr__(self):
            return f"{type(self).__name__}()"

        value = monitored_value_property(0)

        @triggered_method
        def report_value(self, value):
            logging.info(f"value = {value}")

    self = Example.report_value
    instance = Example()

    print("instance.value += 1")
