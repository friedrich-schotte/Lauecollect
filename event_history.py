"""Caching of Channel Access
Author: Friedrich Schotte
Date created: 2022-03-22
Date last modified: 2022-05-24
Revision comment: Storing event history in the class object that generates it
"""
__version__ = "3.0"

import logging

from thread_property_2 import thread_property


def event_history(reference, max_count=None):
    from reference_info import reference_info
    event_history = reference_info(reference, Event_History, reference)

    if max_count is not None and event_history.max_count < max_count:
        event_history.max_count = max_count

    return event_history


class Event_History:
    max_count = 5

    def __init__(self, reference):
        from threading import Lock

        self.reference = reference

        self.events = []
        self.events_lock = Lock()
        self.initialize_lock = Lock()

        # For pylint "Instance attribute initializing defined outside __init__"
        self.initializing = False

        # self.recording = True

    def __repr__(self):
        return f"{self.class_name}({self.reference})"

    @property
    def initialized(self):
        return len(self.events) > 0

    @initialized.setter
    def initialized(self, do_initialize):
        if do_initialize and not self.initialized:
            self.initializing = True

    @thread_property
    def initializing(self):
        self.initialize()

    def initialize(self):
        if not self.initialized:
            with self.initialize_lock:
                if not self.initialized:
                    # logging.debug(f"{self}")
                    default_value = self.reference.value
                    if not self.initialized:
                        self.default_value = default_value
                        # logging.debug(f"{self}.default_value = {self.default_value!r:.80}")
                    # logging.debug(f"{self}.last_value = {self.last_value!r:.80}")

    @property
    def recording(self):
        return self.update in self.reference.monitors

    @recording.setter
    def recording(self, recording):
        if recording != self.recording:
            if recording:
                self.reference.monitors.add(self.update)
                self.initialized = True
            else:
                self.reference.monitors.remove(self.update)

    @property
    def recording_started(self):
        return self.update in self.reference.monitors and self.initialized

    @recording_started.setter
    def recording_started(self, recording):
        if recording != self.recording:
            if recording:
                self.reference.monitors.add(self.update)
                self.initialize()
            else:
                self.reference.monitors.remove(self.update)

    def start_recording(self):
        if not self.recording:
            self.reference.monitors.add(self.update)
            self.initialize()

    @property
    def class_name(self): return type(self).__name__.lower()

    def update(self, event):
        # logging.debug(f"{event}")
        self.add(event)

    @staticmethod
    def is_outdated(event, new_event):
        is_outdated = event.real_time == new_event.real_time and event.version <= new_event.version
        if is_outdated:
            logging.debug(f"{event} is outdated with respect to {new_event}")
        return is_outdated

    @staticmethod
    def is_more_recent(event, new_event):
        is_more_recent = event.real_time == new_event.real_time and event.version > new_event.version
        if is_more_recent:
            logging.debug(f"{event} is more recent than {new_event}")
        return is_more_recent

    def add(self, new_event):
        with self.events_lock:
            # if new_event in self.events:
            #    logging.debug(f"Ignoring duplicate event {new_event}")

            if new_event not in self.events:
                self.events = [event for event in self.events if not self.is_outdated(event, new_event)]
                has_a_more_recent_event = any([self.is_more_recent(event, new_event) for event in self.events])

                if not has_a_more_recent_event:
                    pos = len(self.events)
                    while pos > 0 and new_event.time < self.events[pos - 1].time:
                        pos -= 1
                    self.events.insert(pos, new_event)

            while len(self.events) > self.max_count:
                self.events.pop(0)

    def clear(self):
        with self.events_lock:
            self.events.clear()

    def timestamp(self, value):
        from numpy import nan
        from same import same
        timestamp = nan
        for event in self.events[::-1]:
            if same(event.value, value):
                timestamp = event.time
                break
        return timestamp

    def value_before_or_at(self, timestamp):
        """
        timestamp: seconds elapsed since 1970-01-01T00:00:00+0000
        """
        value = None
        for event in self.events[::-1]:
            if event.time <= timestamp:
                value = event.value
                break
        return value

    value = value_before_or_at

    def max_value(self, timestamp1, timestamp2):
        """timestamp1, timestamp2: seconds elapsed since 1970-01-01T00:00:00+0000"""
        return max(self.values(timestamp1, timestamp2))

    def min_value(self, timestamp1, timestamp2):
        """timestamp1, timestamp2: seconds elapsed since 1970-01-01T00:00:00+0000"""
        return min(self.values(timestamp1, timestamp2))

    def values(self, timestamp1, timestamp2):
        last_event_before_timestamp1 = None

        values = []
        for event in self.events:
            if event.time < timestamp1:
                last_event_before_timestamp1 = event
            if timestamp1 <= event.time <= timestamp2:
                values.append(event.value)
                if event.time == timestamp1:
                    last_event_before_timestamp1 = None

        if last_event_before_timestamp1:
            values.insert(0, last_event_before_timestamp1.value)

        return values

    def last_event_time_before_or_at(self, timestamp):
        """timestamp: seconds elapsed since 1970-01-01T00:00:00+0000
        return value: None if PV was not connect4ed before the given timestamp
        """
        from numpy import nan
        time = nan
        for event in self.events:
            if event.time <= timestamp:
                time = event.time
        return time

    def closest_event_time(self, timestamp):
        """timestamp: seconds elapsed since 1970-01-01T00:00:00+0000"""
        from numpy import nan, abs, argmin
        t = self.event_times
        if len(t) > 0:
            dt = abs(timestamp - t)
            event_time = t[argmin(dt)]
        else:
            event_time = nan
        return event_time

    @property
    def event_times(self):
        return [event.time for event in self.events]

    @property
    def last_value(self):
        value = None
        last_event = self.last_event
        if last_event:
            value = last_event.value
        return value

    @last_value.setter
    def last_value(self, value):
        from event import Event
        from time import time
        event = Event(
            time=time(),
            value=value,
            reference=self.reference,
        )
        self.add(event)

    @property
    def last_event(self):
        try:
            last_event = self.events[-1]
        except IndexError:
            last_event = None
        return last_event

    def events_at_time(self, time):
        return [event for event in self.events if event.real_time == time]

    @property
    def default_value(self):
        return self.value(0)

    @default_value.setter
    def default_value(self, value):
        from event import Event
        event = Event(
            time=0,
            value=value,
            reference=self.reference,
        )
        self.add(event)


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from timing_system_client import timing_system_client
    from configuration_client import configuration_client
    from reference import reference as _reference
    from item_reference import item_reference

    timing_system = timing_system_client("BioCARS")
    reference1 = _reference(timing_system.channels.xdet.trig_count, "count")

    configuration = configuration_client("BioCARS.method")
    reference = item_reference(configuration.motors_in_position_old, 0)

    self = event_history(reference)
    self.recording = True

    print('self.recording = True')
    print('self.reference.value')
    print('self.events')
    print('from time import time as time')
    print('self.value_before_or_at(time())')
