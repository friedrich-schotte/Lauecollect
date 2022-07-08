"""
Author: Friedrich Schotte
Date created: 2022-06-19
Date last modified: 2022-06-19
Revision comment:
"""
__version__ = "1.0"
 
import logging

from timestamps import Timestamps

if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)


class Timed_Value:
    value = None

    def __init__(self, value=None, time=None):
        self.timestamps = Timestamps()
        if value is not None:
            self.value = value
        if time is not None:
            self.time = time

    @property
    def time(self):
        return self.timestamps.last

    @time.setter
    def time(self, value):
        if value is not None:
            self.timestamps.values = [value]
        else:
            self.timestamps.values = []

    def __repr__(self):
        name = type(self).__name__
        attrs = []
        if self.value is not None:
            attrs.append("value=%.80r" % (self.value,))
        if self.time is not None:
            from date_time import date_time
            attrs.append("time=%s" % (date_time(self.time),))
        s = "%s(%s)" % (name, ", ".join(attrs))
        return s

    def __eq__(self, other):
        from same import same
        return all([
            same(self.value, getattr(other, "value", None)),
            same(self.time, getattr(other, "time", None)),
        ])

    def __bool__(self):
        return self.value is not None or self.time is not None
