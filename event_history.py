"""Caching of Channel Access
Author: Friedrich Schotte
Date created: 2022-03-22
Date last modified: 2022-07-14
Revision comment: Storing event history in the class object that generates it
"""
__version__ = "3.0"

import logging

from date_time import date_time
from same import same
from thread_property_2 import thread_property


def event_history(reference, max_count=None):
    from reference_info import reference_info
    event_history = reference_info(reference, Event_History, reference)

    if max_count is not None and event_history.max_count < max_count:
        event_history.max_count = max_count

    return event_history


class Event_History:
    max_count = 25

    def __init__(self, reference):
        from threading import Lock

        self.reference = reference

        self.all_events = []
        self.events_lock = Lock()
        self.initialize_lock = Lock()

        # For pylint "Instance attribute initializing defined outside __init__"
        self.initializing = False

        # self.recording = True

    def __repr__(self):
        return f"{self.class_name}({self.reference})"

    @property
    def events(self):
        events = []
        all_events = self.all_events
        for i in range(0, len(all_events) - 1):
            event = all_events[i]
            next_event = all_events[i + 1]
            if event.real_time < next_event.real_time:
                events.append(event)
        if len(all_events) > 0:
            events.append(all_events[len(all_events) - 1])
        return events

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
        return self.recording and self.initialized

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
        self.add(event, versioning=False)

    def add(self, event, versioning=True):
        with self.events_lock:
            # if new_event in self.events:
            #    logging.debug(f"Ignoring duplicate event {new_event}")

            events = self.all_events
            if event not in events:
                # logging.debug(f"{new_event}")
                if versioning:
                    event = self.event_with_version(event)

                if event in events:
                    logging.debug(f"Ignoring duplicate event {event}")

                if event not in events:
                    have_newer_version = any([self.is_newer_version(ev, event) for ev in events])
                    if not have_newer_version:
                        pos = len(events)
                        while pos > 0 and event < events[pos - 1]:
                            pos -= 1
                        events.insert(pos, event)

                    while len(events) > self.max_count:
                        events.pop(0)

                    if not sorted(events) == events:
                        logging.warning("Sorting all events")
                        events.sort()

    @staticmethod
    def is_older_version(ev, event):
        is_outdated = ev.real_time == event.real_time and ev.version < event.version
        if is_outdated:
            logging.debug(f"{ev} is older version of {event}")
        conflicts = ev.real_time == event.real_time and ev.version == event.version and not same(ev.value, event.value)
        if conflicts:
            logging.debug(f"{ev} conflicts with {event}")
        return is_outdated or conflicts

    @staticmethod
    def is_newer_version(ev, event):
        is_more_recent = ev.real_time == event.real_time and ev.version > event.version
        if is_more_recent:
            logging.debug(f"{ev} is newer version of {event}")
        conflicts = ev.real_time == event.real_time and ev.version == event.version and not same(ev.value, event.value)
        if conflicts:
            logging.debug(f"{ev} conflicts with {event}")
        return is_more_recent

    def event_with_version(self, event):
        version = self.event_version(event)
        if version != 0:
            # logging.debug(f"Assigning version={version} to {event}")
            from event import Event
            event_with_version = Event(
                timestamps=event.timestamps,
                version=version,
                value=event.value,
                reference=event.reference,
            )
        else:
            event_with_version = event
        return event_with_version

    def event_version(self, event):
        version = 0
        events_at_same_time = self.all_events_at_time(event.real_time)
        identical_events = [ev for ev in events_at_same_time if self.are_identical(ev, event)]
        conflicting_events = [ev for ev in events_at_same_time if self.are_conflicting(ev, event)]
        for ev in conflicting_events:
            if ev.real_time:
                logging.debug(f"{ev} conflicts with {event}")
        if identical_events:
            version = max([ev.version for ev in identical_events])
        elif events_at_same_time:
            is_newest_event = all([event.timestamps >= ev.timestamps for ev in events_at_same_time])
            if is_newest_event:
                version = max([ev.version for ev in events_at_same_time]) + 1
        return version

    @staticmethod
    def are_identical(ev, event):
        are_identical = ev.timestamps == event.timestamps and same(ev.value, event.value)
        if are_identical:
            if ev == event:
                logging.debug(f"{ev} and {event} are identical.")
            else:
                differences = []
                for attribute_name in ["real_time", "version", "sent_time"]:
                    if getattr(ev, attribute_name) != getattr(event, attribute_name):
                        differences.append(attribute_name)
                differences = ", ".join(differences)
                logging.debug(f"{ev} and {event} are the same, except for: {differences}")
        return are_identical

    @staticmethod
    def are_conflicting(ev, event):
        are_conflicting = ev.timestamps == event.timestamps and not same(ev.value, event.value)
        if are_conflicting and ev.real_time and event.real_time:
            logging.debug(f"{ev} and {event} are conflicting.")
        return are_conflicting

    def clear(self):
        with self.events_lock:
            self.events.clear()

    def time(self, value):
        from numpy import nan
        time = nan
        for event in self.events[::-1]:
            if same(event.value, value):
                time = event.real_time
                break
        return time

    def value_before_or_at(self, time):
        """time: seconds elapsed since 1970-01-01T00:00:00+0000"""
        if not self.initialized:
            logging.warning(f"{self} is not initialized yet")
        value = None
        for event in self.events[::-1]:
            if event.real_time <= time:
                value = event.value
                break
        else:
            logging.warning(f"{self} has no value before or at {date_time(time)}")
        return value

    value = value_before_or_at

    def has_value_before_or_at(self, time):
        """time: seconds elapsed since 1970-01-01T00:00:00+0000"""
        has_value = False
        for event in self.events[::-1]:
            if event.real_time <= time:
                has_value = True
                break
        return has_value

    has_value = has_value_before_or_at

    def max_value(self, time1, time2):
        """timestamp1, timestamp2: seconds elapsed since 1970-01-01T00:00:00+0000"""
        return max(self.values(time1, time2))

    def min_value(self, time1, time2):
        """timestamp1, timestamp2: seconds elapsed since 1970-01-01T00:00:00+0000"""
        return min(self.values(time1, time2))

    def values(self, time1, time2):
        last_event_before_time1 = None

        values = []
        for event in self.events:
            if event.real_time < time1:
                last_event_before_time1 = event
            if time1 <= event.real_time <= time2:
                values.append(event.value)
                if event.real_time == time1:
                    last_event_before_time1 = None

        if last_event_before_time1:
            values.insert(0, last_event_before_time1.value)

        return values

    def last_event_time_before_or_at(self, time):
        """time: seconds elapsed since 1970-01-01T00:00:00+0000"""
        from numpy import nan
        event_time = nan
        for event in self.events:
            if event.real_time <= time:
                event_time = event.real_time
        return event_time

    def event_times_after_or_at(self, time):
        """time: seconds elapsed since 1970-01-01T00:00:00+0000"""
        event_times = []
        for event in self.events:
            if event.real_time >= time:
                event_times.append(event.real_time)
        return event_times

    def event_times_after(self, time):
        """time: seconds elapsed since 1970-01-01T00:00:00+0000"""
        event_times = []
        for event in self.events:
            if event.real_time > time:
                event_times.append(event.real_time)
        return event_times

    def last_event_timestamps_before_or_at(self, time):
        """time: seconds elapsed since 1970-01-01T00:00:00+0000"""
        from timestamps import Timestamps
        timestamps = Timestamps()
        for event in self.events:
            if event.real_time <= time:
                timestamps = event.timestamps
        return timestamps

    def closest_event_time(self, time):
        """time: seconds elapsed since 1970-01-01T00:00:00+0000"""
        from numpy import nan, abs, argmin
        t = self.event_times
        if len(t) > 0:
            dt = abs(time - t)
            event_time = t[argmin(dt)]
        else:
            event_time = nan
        return event_time

    @property
    def event_times(self):
        return [event.real_time for event in self.events]

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

    def all_events_at_time(self, time):
        return [event for event in self.all_events if event.real_time == time]

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

    @property
    def events_to_be_sent_old(self):
        events_to_be_sent = []
        events = self.events
        if len(events) == 1 and not events[0].sent_time:
            events_to_be_sent.append(events[0])
        for i in range(1, len(events)):
            event = events[i]
            previous_event = events[i-1]
            if not event.sent_time and not same(event.value, previous_event.value):
                events_to_be_sent.append(event)
        return events_to_be_sent

    @property
    def events_to_be_sent(self):
        events_to_be_sent = []

        events = self.all_events

        if len(events) == 1:
            event = events[0]
            if not event.sent_time:
                events_to_be_sent.append(event)

        if events:
            previous_sent_value = events[0].value
        else:
            previous_sent_value = None

        for i in range(1, len(events)):
            event = events[i]
            if i+1 < len(events):
                event_is_valid = event.real_time < events[i+1].real_time
            else:
                event_is_valid = True
            if event_is_valid:
                if not same(event.value, previous_sent_value):
                    if not event.sent_time:
                        events_to_be_sent.append(event)
            if event.sent_time or event in events_to_be_sent:
                previous_sent_value = event.value

        return events_to_be_sent


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
    reference = item_reference(configuration.motors_in_position, 0)

    self = event_history(reference)
    self.recording = True

    print('self.recording = True')
    print('self.reference.value')
    print('self.events')
    print('from time import time as time')
    print('self.value_before_or_at(time())')
