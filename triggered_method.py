#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-02-04
Date last modified: 2022-05-01
Revision comment: Moved: function_argument_names
"""
__version__ = "1.0.1"

from logging import warning


class triggered:
    def __init__(self):
        self.arm()

    def arm(self):
        class_object = type(self)
        for name in dir(class_object):
            attribute = getattr(class_object, name)
            if hasattr(attribute, "arm"):
                attribute.arm(self)


class triggered_method:
    def __init__(self, procedure):
        self.procedure = procedure

    def __repr__(self):
        return f"{self.class_name}({self.procedure.__qualname__})"

    def arm(self, instance):
        from reference import reference
        from handler import handler

        input_values = []
        for input_name in self.input_names:
            input_value = reference(instance, input_name).value
            input_values.append(input_value)
        self.attributes(instance).cached_input_values = input_values

        for input_count, input_name in enumerate(self.input_names):
            reference(instance, input_name).monitors.add(
                handler(self.handle_change, instance, input_count)
            )

    def handle_change(self, instance, input_count, event):
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
                warning(f"Could not find {self} in {class_object}")
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
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    class Example(triggered):
        from monitored_value_property import monitored_value_property
        value = monitored_value_property(0)

        @triggered_method
        def report_value(self, value):
            logging.info(f"value = {value}")

    example = Example()
    print("example.value += 1")
