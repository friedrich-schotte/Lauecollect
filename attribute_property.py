#!/usr/bin/env python
"""
Date created: 2020-11-12
Date last modified: 2021-08-14
Revision comment: Fixed: Issue: monitor_cleanup not called
"""
__version__ = "1.1.2"

import logging
from logging import info, warning


class attribute_property(property):
    from cached_function import cached_function

    def __init__(self, property_name, attribute_name):
        self.property_name = property_name
        self.attribute_name = attribute_name
        property.__init__(self, fget=self.get_property, fset=self.set_property)

    def __repr__(self):
        return f"{self.class_name}({self.property_name}, {self.attribute_name})"

    def get_property(self, instance):
        return self.attribute_reference(instance).value

    def set_property(self, instance, value):
        self.attribute_reference(instance).value = value

    def monitors(self, file):
        return self.attributes(file).monitors

    def monitor_setup(self, instance):
        self.attribute_reference(instance).monitors.add(self.event_handler(instance))

    def monitor_cleanup(self, instance):
        self.attribute_reference(instance).monitors.remove(self.event_handler(instance))

    def event_handler(self, instance):
        from handler import handler
        return handler(self.handle_change, instance)

    def handle_change(self, instance, event):
        from event import event as event_object
        new_event = event_object(
            time=event.time,
            value=event.value,
            reference=self.reference(instance),
        )
        self.monitors(instance).call(event=new_event)

    @cached_function()
    def reference(self, instance):
        from reference import reference
        return reference(instance, self.get_name(instance))

    @cached_function()
    def attribute_reference(self, instance):
        from dynamic_reference import dynamic_reference
        from reference import reference
        return dynamic_reference(reference(instance, self.property_name), self.attribute_name)

    def attributes(self, instance):
        attributes_cache = self.attributes_cache(instance)
        name = self.get_name(instance)
        if name not in attributes_cache:
            attributes_cache[name] = Attributes(self, instance)
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
        return type(self).__name__

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


class Attributes:
    def __init__(self, attribute_property_object, instance):
        from event_handlers import Event_Handlers
        from functools import partial
        self.monitors = Event_Handlers(
            setup=partial(attribute_property_object.monitor_setup, instance),
            cleanup=partial(attribute_property_object.monitor_cleanup, instance),
        )


if __name__ == "__main__":
    # from pdb import pm
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    from handler import handler as _handler
    from reference import reference as _reference

    class Example:
        from db_property import db_property
        from file import file as file_object
        from function_property import function_property

        file_name = db_property("file_name", "/tmp/test.txt")
        file = function_property(file_object, "file_name")
        file_timestamp = attribute_property("file", "timestamp")
        file_content = attribute_property("file", "content")
        file_size = attribute_property("file", "size")

        def __repr__(self):
            return "example"


    example = Example()

    @_handler
    def report(event=None): info(f"event={event}")

    @_handler
    def report_length(event=None): info("%r" % event.value.count('\n'))

    _reference(example, "file_name").monitors.add(report)
    _reference(example, "file").monitors.add(report)
    _reference(example, "file_timestamp").monitors.add(report)
    _reference(example, "file_content").monitors.add(report)
    _reference(example, "file_size").monitors.add(report)
    print(f"example.file_name = {example.file_name!r}")
    print(f"example.file_content = {example.file_content!r}")
    print(r'example.file_content = ""')
    print(r'example.file_content += "test\n"')
    print(r'for i in range(100): example.file_content += "%d\n" % i')
    print(r'open(example.file_name,"a").write("test\n")')
