#!/usr/bin/env python
"""
Push notifications
Author: Friedrich Schotte
Date created: 2020-06-27
Date last modified: 2021-01-09
Revision comment: Cleanup: Deprecation message
"""
__version__ = "1.5.7"

import warnings
from logging import info

warnings.warn(f"Module 'monitor' is deprecated, use 'monitors'",
              DeprecationWarning, stacklevel=2)


def add_monitor(reference, event_handler):
    warnings.warn("add_monitor() is deprecated, use monitors.monitors()",
                  DeprecationWarning, stacklevel=2)
    reference.monitors.add(event_handler)


def remove_monitor(reference, event_handler):
    warnings.warn("remove_monitor() is deprecated, use monitors.monitors()",
                  DeprecationWarning, stacklevel=2)
    reference.monitors.remove(event_handler)


def get_monitors(reference):
    warnings.warn("get_monitors() is deprecated, use monitors.monitors()",
                  DeprecationWarning, stacklevel=2)
    return reference.monitors


def monitor(obj, property_name, proc, *args, **kwargs):
    warnings.warn("monitor() is deprecated, use monitors.monitors()",
                  DeprecationWarning, stacklevel=2)
    from reference import reference
    from handler import handler
    reference(obj, property_name).monitors.add(handler(proc, *args, **kwargs))


def monitor_clear(obj, property_name, proc, *args, **kwargs):
    warnings.warn("monitor_clear() is deprecated, use monitors.monitors()",
                  DeprecationWarning, stacklevel=2)
    from reference import reference
    from handler import handler
    reference(obj, property_name).monitors.remove(handler(proc, *args, **kwargs))


def monitors(obj, property_name):
    warnings.warn("monitors() is deprecated, use monitors.monitors()",
                  DeprecationWarning, stacklevel=2)
    from reference import reference
    return reference(obj, property_name).monitors


def monitoring(obj, property_name, proc, *args, **kwargs):
    warnings.warn("monitoring() is deprecated, use monitors.monitors()",
                  DeprecationWarning, stacklevel=2)
    from handler import handler
    event_handler = handler(proc, *args, **kwargs)
    monitoring = event_handler in reference(obj, property_name).monitors
    return monitoring


def monitor_all(obj, proc, *args, **kwargs):
    for property_name in dir(type(obj)):
        property_object = getattr(type(obj), property_name, None)
        if type(property_object) is not type:
            if hasattr(property_object, "monitor"):
                monitor = getattr(property_object, "monitor")
                monitor(obj, proc, *args, **kwargs)
    if hasattr(obj, "__monitor_item__"):
        for i in range(0, len(obj)):
            obj.__monitor_item__(i, proc, *args, **kwargs)


def monitor_clear_all(obj, proc, *args, **kwargs):
    for property_name in dir(type(obj)):
        property_object = getattr(type(obj), property_name, None)
        if type(property_object) is not type:
            if hasattr(property_object, "monitor_clear"):
                monitor_clear = getattr(property_object, "monitor_clear")
                monitor_clear(obj, proc, *args, **kwargs)
    if hasattr(obj, "__monitor_clear_item__"):
        for i in range(0, len(obj)):
            obj.__monitor_clear_item__(i, proc, *args, **kwargs)


def monitors_all(obj):
    handlers = []
    for property_name in dir(type(obj)):
        property_object = getattr(type(obj), property_name, None)
        if type(property_object) is not type:
            if hasattr(property_object, "monitors"):
                monitors = getattr(property_object, "monitors")
                handlers += monitors(obj)
    if hasattr(obj, "__monitors_item__"):
        for i in range(0, len(obj)):
            handlers += obj.__monitors_item__(i)

    handlers = list(set(handlers))
    return handlers


def monitor_property_names(obj):
    property_names = []
    for property_name in dir(type(obj)):
        property_object = getattr(type(obj), property_name, None)
        if hasattr(property_object, "monitor"):
            property_names.append(property_name)
    return property_names


def all_monitors():
    monitors = {}
    from polling_monitor import polling_monitors
    add_dict(monitors, polling_monitors.monitors)
    import DB
    add_dict(monitors, DB.callbacks)
    from CA import camonitors
    add_dict(monitors, camonitors())
    from CA import camonitor_handlers
    add_dict(monitors, camonitor_handlers())
    return monitors


def add_dict(original_dict, dict_to_add):
    for key in dict_to_add:
        if key not in original_dict:
            original_dict[key] = set()
        for x in dict_to_add[key]:
            original_dict[key].add(x)


if __name__ == "__main__":
    import logging

    for h in logging.root.handlers:
        logging.root.removeHandler(h)
    logging_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=logging_format)
    logging.getLogger('EPICS_CA.event_handler').level = logging.DEBUG
    logging.getLogger('EPICS_CA').level = logging.INFO

    from CA import pv
    from handler import handler
    from reference import reference

    PV = pv('LASERLAB:TIMING.registers.ch4_trig_count.count')
    reference = reference(PV, "value")


    def report(event=None):
        info(f'event = {event}')


    event_handler = handler(report)

    print("add_monitor(reference, event_handler)")
    print("get_monitors(reference)")
    print("remove_monitor(reference, event_handler)")

    print("add_monitor(reference, event_handler); sleep(0.25); remove_monitor(reference, event_handler)")
