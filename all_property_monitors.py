#!/usr/bin/env python
"""
Push notifications
Author: Friedrich Schotte
Date created: 2020-12-02
Date last modified: 2020-12-02
Revision comment:
"""
__version__ = "1.0"

import warnings


class All_Property_Monitors:
    def __init__(self, obj):
        self.object = obj

    def __iadd__(self, handler):
        self.add(handler)
        return self

    def __isub__(self, handler):
        self.remove(handler)
        return self

    def __len__(self):
        return len(self.handlers)

    def __iter__(self):
        return self.handlers.__iter__()

    @property
    def handlers(self):
        handlers = set()
        for property_name in dir(type(self.object)):
            property_object = getattr(type(self.object), property_name, None)
            if type(property_object) is not type:
                if hasattr(property_object, "monitors"):
                    handlers |= set(property_object.monitors(self.object))
        if hasattr(type(self.object), "__getitem_monitors__"):
            for i in range(0, len(self.object)):
                handlers |= set(self.object.__getitem_monitors__(i))
        elif hasattr(type(self.object), "__monitors_item__"):
            warnings.warn(f"'__monitors_item__' is deprecated, use '__getitem_monitors__'",
                          DeprecationWarning)
            for i in range(0, len(self.object)):
                handlers |= set(self.object.__monitors_item__(i))
        return handlers

    def add(self, event_handler):
        # for backward-compatibility
        proc = event_handler.procedure
        args = event_handler.args
        kwargs = event_handler.kwargs
        kwargs["new_thread"] = event_handler.new_thread

        for property_name in dir(type(self.object)):
            property_object = getattr(type(self.object), property_name, None)
            if type(property_object) is not type:
                if hasattr(property_object, "monitors"):
                    property_object.monitors(self.object).add(event_handler)
                elif hasattr(property_object, "monitor"):
                    warnings.warn(f"'monitor' is deprecated, use 'monitors'",
                                  DeprecationWarning)
                    property_object.monitor(self.object, proc, *args, **kwargs)
        if hasattr(type(self.object), "__getitem_monitors__"):
            for i in range(0, len(self.object)):
                self.object.__getitem_monitors__(i).add(event_handler)
        elif hasattr(type(self.object), "__monitor_item__"):
            warnings.warn(f"'__monitor_item__' is deprecated, use '__getitem_monitors__'",
                          DeprecationWarning)
            for i in range(0, len(self.object)):
                self.object.__monitor_item__(i, proc, *args, **kwargs)

    def remove(self, event_handler):
        # for backward-compatibility
        proc = event_handler.procedure
        args = event_handler.args
        kwargs = event_handler.kwargs
        kwargs["new_thread"] = event_handler.new_thread

        for property_name in dir(type(self.object)):
            property_object = getattr(type(self.object), property_name, None)
            if type(property_object) is not type:
                if hasattr(property_object, "monitors"):
                    property_object.monitors(self.object).remove(event_handler)
                elif hasattr(property_object, "monitor_clear"):
                    warnings.warn(f"'monitor_clear' is deprecated, use 'monitors'",
                                  DeprecationWarning)
                    property_object.monitor_clear(self.object, proc, *args, **kwargs)
        if hasattr(type(self.object), "__getitem_monitors__"):
            for i in range(0, len(self.object)):
                self.object.__getitem_monitors__(i).remove(event_handler)
        elif hasattr(type(self.object), "__monitor_clear_item__"):
            warnings.warn(f"'__monitor_clear_item__' is deprecated, use '__getitem_monitors__'",
                          DeprecationWarning)
            for i in range(0, len(self.object)):
                self.object.__monitor_clear_item__(i, proc, *args, **kwargs)
