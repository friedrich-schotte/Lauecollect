"""
Author: Friedrich Schotte
Date created: 2021-01-16
Date last modified: 2022-03-28
Revision comment: Cleanup: Renamed: timing_system_sequencer_fs
"""
__version__ = "1.0.2"

from logging import warning
from cached_function import cached_function


@cached_function()
def timing_system_sequencer_fs(name):
    return Timing_System_Sequencer_FS(name)


class Timing_System_Sequencer_FS:
    name = "BioCARS"
    event_handlers = {}

    def __init__(self, name=None):
        if name is not None:
            self.name = name
            self.event_handlers = {}

    def __repr__(self):
        return "%r.sequencer_fs" % self.timing_system

    @property
    def timing_system(self):
        from timing_system import timing_system
        return timing_system(self.name)

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError(f"{self} has no attribute {name!r}")
        return to_str(self.PV(name).value)

    def __setattr__(self, name, value):
        if name.startswith("__") and name.endswith("__"):
            super().__setattr__(name, value)
        if name in self.__dict__ or hasattr(type(self), name):
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
        return self.timing_system.property_PV(f"sequencer.fs.{name}")

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
        warning(f"Converted {value!r} to {str_value!r}")
    return str_value


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from reference import reference as _reference
    from handler import handler as _handler

    # self = timing_system_sequencer_fs('BioCARS')
    self = timing_system_sequencer_fs('LaserLab')
    # self = timing_system_sequencer_fs('TestBench')

    @_handler
    def report(event=None):
        logging.info(f'event = {event}')

    print(f"self.queue1_repeat_count = {self.queue1_repeat_count!r}")
    _reference(self, 'queue1_repeat_count').monitors.add(report)
    print("_reference(self, 'queue1_repeat_count').monitors.remove(report)")
