#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-12-17
Date last modified: 2020-12-22
Revision comment:
"""
__version__ = "1.0"

from logging import warning
from cached_function import cached_function


class indexable_property_from_reference(property):
    def __init__(self, item_reference_function, count_reference_function=None):
        self.item_reference_function = item_reference_function
        self.count_reference_function = count_reference_function
        property.__init__(
            self,
            fget=self.indexable_property_get,
            fset=self.indexable_property_set,
        )
        from threading import Lock
        self.attributes_lock = Lock()

    def count_reference(self, count_reference_function):
        """Intended as decorator"""
        self.count_reference_function = count_reference_function
        return self

    def __repr__(self):
        from func_repr import func_repr
        return f"{self.class_name}({func_repr(self.item_reference_function)}, {func_repr(self.count_reference_function)})"

    def indexable_property_get(self, instance):
        return indexable_object(
            instance,
            self.item_reference_function,
            self.count_reference_function,
        )

    def indexable_property_set(self, instance, value):
        self.indexable_property_get(instance)[:] = value

    def monitors(self, instance):
        return self.attributes(instance).monitors

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

    def monitors_setup(self, instance):
        from handler import handler
        self.reference_to_monitor(instance).monitors.add(handler(self.handle_change, instance))

    def monitors_cleanup(self, instance):
        from handler import handler
        self.reference_to_monitor(instance).monitors.remove(handler(self.handle_change, instance))

    def reference_to_monitor(self, instance):
        from all_items_reference import all_items_reference
        return all_items_reference(self.indexable_property_get(instance))

    def handle_change(self, instance, event):
        from event import event as event_object
        new_event = event_object(
            time=event.time,
            value=event.value,
            reference=self.reference(instance)
        )
        self.monitors(instance).call(event=new_event)

    def reference(self, instance):
        from reference import reference
        return reference(instance, self.get_name(instance))

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


@cached_function()
def indexable_object(motor, item_reference_function, count_reference_function):
    return Indexable_Object(motor, item_reference_function, count_reference_function)


class Indexable_Object:
    def __init__(self, obj, item_reference_function, count_reference_function):
        self.object = obj
        self.item_reference_function = item_reference_function
        self.count_reference_function = count_reference_function

        self.item_monitors = {}

    def __repr__(self):
        from func_repr import func_repr
        return f"{self.class_name}({self.object}, {func_repr(self.item_reference_function)}, {func_repr(self.count_reference_function)})"

    def __getitem__(self, i):
        if type(i) == slice:
            value = [x for x in self]
        else:
            value = self.item_reference(i).value
        return value

    def __setitem__(self, i, value):
        # debug(f"{self}[{i}] = {value}")
        if type(i) == slice:
            for i in range(0, len(value)):
                self[i] = value[i]
        else:
            self.item_reference(i).value = value

    def __getitem_monitors__(self, i):
        from event_handlers import Event_Handlers
        from functools import partial
        if i not in self.item_monitors:
            self.item_monitors[i] = Event_Handlers(
                setup=partial(self.item_monitor_setup, i),
                cleanup=partial(self.item_monitor_cleanup, i),
            )
        return self.item_monitors[i]

    def __len__(self):
        return self.count

    def __iter__(self):
        for i in range(0, len(self)):
            if i < len(self):
                yield self[i]

    def item_reference(self, i):
        return self.item_reference_function(self.object, i)

    def item_monitor_setup(self, i):
        from handler import handler
        self.item_reference(i).monitors.add(handler(self.item_handle_change, i))

    def item_monitor_cleanup(self, i):
        from handler import handler
        self.item_reference(i).monitors.remove(handler(self.item_handle_change, i))

    def item_handle_change(self, i, event):
        from event import event as event_object
        from item_reference import item_reference
        new_event = event_object(
            time=event.time,
            value=event.value,
            reference=item_reference(self, i),
        )
        self.__getitem_monitors__(i).call(event=new_event)

    @property
    def count(self):
        return self.count_reference.value

    @property
    def count_reference(self):
        return self.count_reference_function(self.object)

    @property
    def class_name(self):
        return type(self).__name__

