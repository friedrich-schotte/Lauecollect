"""EPICS Channel Access Process Variable
Author: Friedrich Schotte
Date created: 2020-12-16
Date last modified: 2022-06-15
Revision comment: Updated examples
"""
__version__ = "1.1.6"

import logging

from cached_function import cached_function


@cached_function()
def array_PV(PV_name, default_value=None):
    return Array_PV(PV_name, default_value)


class Array_PV(object):
    default_value = ""

    def __init__(self, PV_name, default_value=None):
        self.PV_name = PV_name
        if default_value is not None:
            self.default_value = default_value
        from event_handlers import Event_Handlers
        self.all_item_monitors = Event_Handlers(
            setup=self.monitor_setup,
            cleanup=self.monitor_cleanup,
        )
        self.item_monitors = {}
        self._cached_values = []

    def __repr__(self):
        return f"{self.class_name}({self.PV_name!r}, value={self.default_value!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower().replace("pv", "PV")

    def __getitem__(self, i):
        if type(i) == slice:
            value = self.array[i]
        else:
            try:
                value = self.array[i]
            except IndexError:
                value = self.default_value
        return value

    def __setitem__(self, i, value):
        if type(i) == slice:
            self.array = value
        else:
            array = self.array
            if len(array) < i+1:
                array = resize(array, i+1, self.default_value)
            array[i] = value
            self.array = array

    def __len__(self):
        return len(self.array)

    def __iter__(self):
        for i in range(0, len(self)):
            if i < len(self):
                yield self[i]

    def index(self, value):
        return self.array.index(value)

    def __eq__(self, array):
        if not hasattr(array, "__len__"):
            return False
        if len(self) != len(array):
            return False
        return all([self[i] == array[i] for i in range(0, len(self))])

    def __ne__(self, array):
        return not self == array

    def __hash__(self):
        return hash(repr(self))

    def __getitem_monitors__(self, i):
        if type(i) == slice:
            monitors = self.all_item_monitors
        else:
            monitors = self.get_item_monitors(i)
        return monitors

    def get_item_monitors(self, i):
        from event_handlers import Event_Handlers
        if i not in self.item_monitors:
            self.item_monitors[i] = Event_Handlers(
                setup=self.monitor_setup,
                cleanup=self.monitor_cleanup,
            )
        monitors = self.item_monitors[i]
        return monitors

    def monitor_setup(self):
        self.caching_values = True
        self.monitoring_PV = True

    def monitor_cleanup(self):
        self.monitoring_PV = False
        self.caching_values = False

    @property
    def monitoring_PV(self):
        return self.PV_handler in self.array_reference.monitors

    @monitoring_PV.setter
    def monitoring_PV(self, monitoring):
        if monitoring:
            self.array_reference.monitors.add(self.PV_handler)
        else:
            self.array_reference.monitors.remove(self.PV_handler)

    @property
    def PV_handler(self):
        from handler import handler
        return handler(self.handle_PV_update)

    def handle_PV_update(self, event):
        from same import same
        from event import event as event_object
        from item_reference import item_reference
        from all_items_reference import all_items_reference

        # logging.debug(f"{self}: {event}")
        for i in self.item_monitors:
            try:
                new_value = event.value[i]
            except IndexError:
                new_value = self.default_value
            if not same(new_value, self.get_cached_item(i)):
                new_event = event_object(
                    time=event.time,
                    value=new_value,
                    reference=item_reference(self, i),
                )
                self.item_monitors[i].call(event=new_event)

        if self.all_item_monitors:
            if not same(event.value, self.cached_values):
                new_event = event_object(
                    time=event.time,
                    value=event.value,
                    reference=all_items_reference(self),
                )
                # debug(f"new_event={new_event}")
                self.all_item_monitors.call(event=new_event)

        self.cached_values = event.value

    @property
    def array(self):
        from as_array import as_array
        return as_array(self.array_reference.value).copy()

    @array.setter
    def array(self, value):
        self.array_reference.value = value

    @property
    def array_reference(self):
        from reference import reference
        return reference(self.PV, "value")

    @property
    def PV(self):
        from CA import PV
        return PV(self.PV_name)

    def get_cached_item(self, i):
        try:
            value = self.cached_values[i]
        except IndexError:
            value = self.default_value
        return value

    @property
    def caching_values(self):
        return self.is_cached_values

    @caching_values.setter
    def caching_values(self, caching_values):
        if caching_values != self.caching_values:
            if caching_values:
                self.cached_values = self.array
            else:
                self.clear_cached_values()

    @property
    def cached_values(self):
        from as_array import as_array
        return as_array(self._cached_values).copy()

    @cached_values.setter
    def cached_values(self, values):
        from as_array import as_array
        self._cached_values = as_array(values).copy()

    def clear_cached_values(self):
        self._cached_values = []

    @property
    def is_cached_values(self):
        return len(self._cached_values) > 0


def resize(array, new_size, default_value):
    if type(array) is list:
        if new_size > len(array):
            new_array = array + [default_value] * (new_size - len(array))
        elif new_size < len(array):
            new_array = array[0:new_size]
        else:
            new_array = array.copy()
    else:
        from numpy import resize
        new_array = resize(array, new_size)
        if new_size > len(array):
            new_array[len(array):] = convert(default_value, new_array.dtype.type)
    return new_array


def convert(value, data_type):
    from numpy import nan
    try:
        value = data_type(value)
    except ValueError:
        if issubclass(data_type, float):
            value = nan
        if issubclass(data_type, int):
            value = 0
    return value


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from item_reference import item_reference
    from all_items_reference import all_items_reference
    from handler import handler as _handler

    PV_name = "BIOCARS:CONFIGURATION.METHOD.WIDTHS"
    self = array_PV(PV_name, 200)

    @_handler
    def report(event=None):
        logging.info(f"event={event}")

    item_reference(self, 0).monitors.add(report)
    all_items_reference(self).monitors.add(report)
    print("self[0] += 1")
