"""
Author: Friedrich Schotte
Date created: 2021-01-16
Date last modified: 2022-08-17
Revision comment: repr, logging
"""
__version__ = "2.0.1"

import logging
from cached_function import cached_function


@cached_function()
def timing_system_sequencer_fs_driver(timing_system):
    return Timing_System_Sequencer_Fs_Driver(timing_system)


class Timing_System_Sequencer_Fs_Driver:
    event_handlers = {}

    def __init__(self, timing_system):
        self.timing_system = timing_system
        self.event_handlers = {}

    def __repr__(self):
        return f"{self.timing_system!r}.sequencer.fs"

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(f"{self} has no attribute {name!r}")
        pv = self.PV(name)
        pv_value = pv.value
        # logging.debug(f"{name}: {pv}.value: {pv_value!r}")
        value = to_str(pv_value)
        return value

    def __setattr__(self, name, value):
        if name.startswith("__") and name.endswith("__"):
            super().__setattr__(name, value)
        elif name in self.__dict__ or hasattr(type(self), name):
            super().__setattr__(name, value)
        elif name == "timing_system":
            super().__setattr__(name, value)
        else:
            self.PV(name).value = value

    def __getattr_monitors__(self, name):
        if name not in self.event_handlers:
            from event_handlers import Event_Handlers
            from functools import partial
            self.event_handlers[name] = Event_Handlers(
                setup=partial(self.setup, name)
            )
        return self.event_handlers[name]

    def setup(self, name):
        from reference import reference
        from handler import handler
        return reference(self.PV(name), "value").monitors.add(
            handler(self.handle_event, name))

    def handle_event(self, name, event):
        from event import event as event_object
        from reference import reference
        new_event = event_object(
            time=event.time,
            value=to_str(event.value),
            reference=reference(self, name)
        )
        self.__getattr_monitors__(name).call(event=new_event)

    def __dir__(self):
        return sorted(set(self.names + list(super().__dir__()) + list(self.__dict__.keys())))

    def PV(self, name):
        from CA import PV
        return PV(self.PV_name(name))

    def PV_name(self, name):
        return f"{self.timing_system.prefix.strip('.')}.sequencer.fs.{name}"

    @property
    def names(self):
        return [f"{q}_{p}" for q in self.queues for p in self.suffixes]

    queues = "queue1", "queue2", "queue"
    suffixes = "sequence_count", "repeat_count", "max_repeat_count"


def to_str(value):
    if type(value) == str:
        str_value = value
    elif value is None:
        str_value = ""
    else:
        str_value = str(value)
        logging.warning(f"Converted {value!r} to {str_value!r}")
    return str_value


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = 'BioCARS'

    from timing_system_driver_9 import timing_system_driver
    timing_system = timing_system_driver(domain_name)
    self = timing_system_sequencer_fs_driver(timing_system)

    from handler import handler as _handler
    from reference import reference as _reference

    @_handler
    def report(event=None):
        logging.info(f'event = {event}')

    property_names = [
        "queue_sequence_count",
    ]
    for property_name in property_names:
        _reference(self, property_name).monitors.add(report)
