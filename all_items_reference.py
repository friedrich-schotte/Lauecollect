"""
This enables values to be passed by reference

Author: Friedrich Schotte
Date created: 2020-12-11
Date last modified: 2021-10-06
Revision comment: Issue: in item_handle_change:
    values[index] = event.value
    IndexError: list assignment index out of range
"""
__version__ = "1.2.1"

from logging import warning

from cached_function import cached_function


@cached_function()
def all_items_reference(obj):
    return All_Items_Reference(obj)


def valid_index(values, index):
    try:
        _ = values[index]
        valid_index = True
    except IndexError:
        valid_index = False
    return valid_index


class All_Items_Reference(object):
    def __init__(self, obj):
        self.object = obj

        from event_handlers import Event_Handlers
        self.monitors = Event_Handlers(
            setup=self.all_items_monitor_setup,
            cleanup=self.all_items_monitor_cleanup,
        )

    def __repr__(self):
        class_name = type(self).__name__.lower()
        return f"{class_name}({self.object!r})"

    def __str__(self):
        return f"{self.object!r}[:]"

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.object == getattr(other, "object", None),
        ])

    def __hash__(self): return hash(repr(self))

    def get_value(self):
        return self.object[:]

    def set_value(self, value):
        self.object[:] = value

    value = property(get_value, set_value)

    def all_items_monitor_setup(self):
        from handler import handler
        if hasattr(type(self.object), "__all_items_monitors__"):
            self.object.__all_items_monitors__.add(handler(self.all_items_handle_change))
        elif hasattr(type(self.object), "__getitem_monitors__"):
            for index in range(0, len(self.object)):
                self.object.__getitem_monitors__(index).add(handler(self.item_handle_change, index))
        else:
            warning(f"{type(self.object)} has no method __getitem_monitors__")

    def all_items_monitor_cleanup(self):
        from handler import handler
        if hasattr(type(self.object), "__all_items_monitors__"):
            self.object.__all_items_monitors__.remove(handler(self.all_items_handle_change))
        elif hasattr(type(self.object), "__getitem_monitors__"):
            for index in range(0, len(self.object)):
                self.object.__getitem_monitors__(index).remove(handler(self.item_handle_change, index))
        else:
            warning(f"{type(self.object)} has no method __getitem_monitors__")

    def item_handle_change(self, index, event):
        values = list(self.object[:])
        if valid_index(values, index):
            values[index] = event.value
            from event import event as event_object
            new_event = event_object(
                time=event.time,
                value=values,
                reference=self,
            )
            self.monitors.call(event=new_event)

    def all_items_handle_change(self, event):
        from event import event as event_object
        new_event = event_object(
            time=event.time,
            value=event.value,
            reference=self,
        )
        self.monitors.call(event=new_event)
