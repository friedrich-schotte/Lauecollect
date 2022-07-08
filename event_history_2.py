"""Caching of Channel Access
Author: Friedrich Schotte
Date created: 2022-03-22
Date last modified: 2022-07-06
Revision comment: Renamed: time(...)
"""
__version__ = "2.6"

import logging

from thread_property_2 import thread_property

from cached_function import cached_function


@cached_function()
def event_history(reference, max_count=None):
    return Event_History(reference, max_count=max_count)


class Event_History:
    def __init__(self, reference, max_count=None):
        from threading import Lock

        self.reference = reference
        if max_count is not None:
            self.max_count = max_count

        self.lock = Lock()
        self.initial_value = None
        self.data = [], []
        self.recording = True
        self.initializing = True

    @thread_property
    def initializing(self):
        self.initial_value = self.reference.value

    @property
    def recording(self):
        return self.update in self.reference.monitors

    @recording.setter
    def recording(self, recording):
        if recording:
            self.reference.monitors.add(self.update)
        else:
            self.reference.monitors.remove(self.update)

    def __repr__(self):
        return f"{self.class_name}({self.reference}, max_count={self.max_count})"

    @property
    def class_name(self): return type(self).__name__.lower()

    max_count = 100

    def update(self, event):
        with self.lock:
            t, v = self.data
            t = (t + [event.time])[-self.max_count:]
            v = (v + [event.value])[-self.max_count:]
            self.data = t, v

    def clear(self):
        with self.lock:
            self.data = [], []

    def time(self, value):
        from numpy import nan
        timestamp = nan
        for (t, v) in zip(*self.data):
            if v == value:
                timestamp = t
        return timestamp

    def value_before_or_at(self, timestamp):
        """
        timestamp: seconds elapsed since 1970-01-01T00:00:00+0000
        """
        value = self.initial_value
        for (t, v) in zip(*self.data):
            if t <= timestamp:
                value = v
        return value

    value = value_before_or_at

    def max_value(self, timestamp1, timestamp2):
        """timestamp1, timestamp2: seconds elapsed since 1970-01-01T00:00:00+0000"""
        return max(self.values(timestamp1, timestamp2))

    def min_value(self, timestamp1, timestamp2):
        """timestamp1, timestamp2: seconds elapsed since 1970-01-01T00:00:00+0000"""
        return min(self.values(timestamp1, timestamp2))

    def values(self, timestamp1, timestamp2):
        last_value = self.initial_value
        values = []
        for (t, v) in zip(*self.data):
            if t < timestamp1:
                last_value = v
            if timestamp1 <= t <= timestamp2:
                values.append(v)
                if t == timestamp1:
                    last_value = None
        if last_value is not None:
            values.insert(0, last_value)
        return values

    def last_event_time_before_or_at(self, timestamp):
        """timestamp: seconds elapsed since 1970-01-01T00:00:00+0000
        return value: None if PV was not connect4ed before the given timestamp
        """
        from numpy import nan
        time = nan
        for (t, v) in zip(*self.data):
            if t <= timestamp:
                time = t
        return time

    def closest_event_time(self, timestamp):
        """timestamp: seconds elapsed since 1970-01-01T00:00:00+0000"""
        from numpy import nan, array, abs, argmin
        t = array(self.data[0])
        if len(t) > 0:
            dt = abs(timestamp - t)
            event_time = t[argmin(dt)]
        else:
            event_time = nan
        return event_time


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from timing_system_client import timing_system_client
    from reference import reference as _reference
    from time import time as time

    domain_name = "BioCARS"
    timing_system = timing_system_client(domain_name)
    reference = _reference(timing_system.channels.xdet.trig_count, "count")
    self = event_history(reference)
    t = time()

    print('self.reference.value')
    print('self.data')
    print('self.value_before_or_at(time())')
