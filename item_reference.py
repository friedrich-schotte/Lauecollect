"""
This enables values to be passed by reference

Author: Friedrich Schotte
Date created: 2020-12-05
Date last modified: 2022-06-23
Revision Comment: Added: event_history
"""
__version__ = "1.1"

import warnings
from logging import warning
from cached_function import cached_function


def item_reference(obj, index):
    try:
        return item_reference_cached(obj, index)
    except TypeError:
        warning(f"{obj}, {index}: unhashable type")
        return Item_Reference(obj, index)


@cached_function()
def item_reference_cached(obj, index):
    return Item_Reference(obj, index)


class Item_Reference(object):
    def __init__(self, obj, index):
        self.object = obj
        self.index = index

    def __repr__(self):
        class_name = type(self).__name__.lower()
        return f"{class_name}({self.object!r}, {self.index!r})"

    def __str__(self):
        return f"{self.object!r}[{self.index!r}]"

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.object == getattr(other, "object", None),
            self.index == getattr(other, "index", None),
        ])

    def __hash__(self): return hash(repr(self))

    def get_value(self):
        return self.object[self.index]

    def set_value(self, value):
        self.object[self.index] = value

    value = property(get_value, set_value)

    @property
    def monitors_without_check(self):
        if hasattr(type(self.object), "__getitem_monitors__"):
            monitors = self.object.__getitem_monitors__(self.index)
        elif hasattr(type(self.object), "__monitors_item__"):
            warnings.warn(f"{self.object}.__monitors_item__ is deprecated, "
                          f"use __getitem_monitors__", DeprecationWarning)
            monitors = self.object.__monitors_item__(self.index)
        else:
            warning(f"{type(self.object)} has no method __getitem_monitors__")
            monitors = set()
        return monitors

    @property
    def monitors(self):
        monitors = self.monitors_without_check

        import warnings
        if type(monitors) is list:
            message = f"Converting {self}.monitors from type 'list' to 'set'"
            monitors = set(monitors)
            warnings.warn(message, stacklevel=2)

        if type(monitors) is set:
            from event_handlers import Event_Handlers
            message = f'{self}.monitors is of type "set", '\
                      f'not "{Event_Handlers.__name__}"; "add()" will have no effect'
            warnings.warn(message, stacklevel=2)

        return monitors

    @property
    def event_history(self):
        from event_history import event_history
        return event_history(self)
