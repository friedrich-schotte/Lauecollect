#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-12-20
Date last modified: 2020-12-20
Revision comment:
"""
__version__ = "1.0"

from logging import warning

from cached_function import cached_function


class indexable_property_from_class(property):
    def __init__(self, generator_function):
        self.generator_function = generator_function
        property.__init__(self, fget=self.get_value, fset=self.set_value)
        from threading import Lock
        self.attributes_lock = Lock()

    def __repr__(self):
        from func_repr import func_repr
        return f"{self.class_name}({func_repr(self.generator_function)})"

    def get_value(self, instance):
        return self.generator_function(instance)

    def set_value(self, instance, value):
        self.get_value(instance)[:] = value

    def monitors(self, instance):
        return self.attributes(instance).monitors

    def monitors_setup(self, instance):
        from handler import handler
        self.reference_to_monitor(instance).monitors.add(handler(self.handle_change, instance))

    def monitors_cleanup(self, instance):
        from handler import handler
        self.reference_to_monitor(instance).monitors.remove(handler(self.handle_change, instance))

    def reference_to_monitor(self, instance):
        from all_items_reference import all_items_reference
        return all_items_reference(self.get_value(instance))

    def handle_change(self, instance, event):
        from event import event as event_object
        new_event = event_object(
            time=event.time,
            value=event.value,
            reference=self.reference(instance),
        )
        self.monitors(instance).call(event=new_event)

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


class Attributes:
    def __init__(self, indexable_property, instance):
        from event_handlers import Event_Handlers
        from functools import partial
        self.monitors = Event_Handlers(
            setup=partial(indexable_property.monitors_setup, instance),
            cleanup=partial(indexable_property.monitors_cleanup, instance),
        )
