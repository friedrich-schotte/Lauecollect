"""
Author: Friedrich Schotte
Date created: 2022-06-11
Date last modified: 2022-06-11
Revision comment:
"""
__version__ = "1.0"

import logging
import wx
from cached_function import cached_function


def wx_event_repr(event):
    class_name = type(event).__name__
    event_type = event_type_name(event.EventType)
    event_repr = f"{class_name}(EventType={event_type})"
    return event_repr


def event_type_name(event_type: int):
    if event_type in event_type_dict():
        event_name = event_type_dict()[event_type]
    else:
        event_name = str(event_type)
    return event_name


@cached_function()
def event_type_dict():
    event_type_dict = {}
    for name in dir(wx):
        if name.startswith("EVT_"):
            event = getattr(wx,name)
            if hasattr(event, "evtType"):
                for event_type in event.evtType:
                    event_type_dict[event_type] = f"wx.{name}"
    return event_type_dict


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    print("event_type_name(10072)")
