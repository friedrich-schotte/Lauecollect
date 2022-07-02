"""
Author: Friedrich Schotte
Date created: 2021-09-27
Date last modified: 2022-06-15
Revision comment: Updated examples
"""
__version__ = "1.0.3"

import logging
from cached_function import cached_function


@cached_function()
def PV_array(PV_name_template, count, default_value=None):
    return PV_Array(PV_name_template, count, default_value)


class PV_Array:
    default_value = ""

    def __init__(self, PV_name_template, count, default_value=None):
        """PV_name_template: e.g. "BIOCARS:CONFIGURATION.METHOD.MOTOR{i+1}.CURRENT_POSITION"
        count: e.g. BIOCARS:CONFIGURATION.METHOD.N_MOTORS
        default_value: e.g. 0.0, "", () """
        from threading import Lock
        from event_handlers import Event_Handlers

        self.PV_name_template = PV_name_template
        self.length_PV_name = count
        if default_value is not None:
            self.default_value = default_value

        self.lock = Lock()
        self.all_item_monitors = Event_Handlers(
            setup=self.all_items_monitor_setup,
            cleanup=self.all_items_monitor_cleanup,
        )
        self.item_monitors = {}
        self._cached_items = {}
        self._cached_item_locks = {}
        self._cached_all_items = []

    def __repr__(self):
        return f"{self.class_name}({self.PV_name_template!r}, count={self.length_PV_name!r}, default_value={self.default_value!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower().replace("pv", "PV")

    def __getitem__(self, i):
        from is_array import is_array
        from array_PV import array_PV

        if type(i) == slice:
            value = [x for x in self]
        else:
            if is_array(self.default_value):
                value = array_PV(self.PV_name(i))
            else:
                value = self.PV_value(i)
        return value

    def __setitem__(self, i, value):
        if type(i) == slice:
            for j in range(0, len(value)):
                self[j] = value[j]
        else:
            self.set_PV_value(i, value)

    def __len__(self):
        length = self.length_PV.value
        if length is None:
            length = 0
        return length

    def __iter__(self):
        for i in range(0, len(self)):
            if i < len(self):
                yield self[i]

    def __getitem_monitors__(self, i):
        if type(i) == slice:
            monitors = self.all_item_monitors
        else:
            monitors = self.get_item_monitors(i)
        return monitors

    def get_item_monitors(self, i):
        from event_handlers import Event_Handlers
        from functools import partial

        if i not in self.item_monitors:
            self.item_monitors[i] = Event_Handlers(
                setup=partial(self.monitor_setup, i),
                cleanup=partial(self.monitor_cleanup, i),
            )
        monitors = self.item_monitors[i]
        return monitors

    def monitor_setup(self, i):
        self.set_caching_item(i, True)
        self.PV_value_reference(i).monitors.add(self.update_handler(i))

    def monitor_cleanup(self, i):
        self.PV_value_reference(i).monitors.remove(self.update_handler(i))
        self.set_caching_item(i, False)

    def all_items_monitor_setup(self):
        self.caching_all_items = True
        for i in range(0, len(self)):
            self.PV_value_reference(i).monitors.add(self.all_items_update_handler(i))

    def all_items_monitor_cleanup(self):
        for i in range(0, len(self)):
            self.PV_value_reference(i).monitors.remove(self.all_items_update_handler(i))
        self.caching_all_items = False

    def PV_value_reference(self, i):
        from reference import reference
        return reference(self.PV(i), "value")

    def update_handler(self, i):
        from handler import handler
        return handler(self.handle_PV_update, i)

    def all_items_update_handler(self, i):
        from handler import handler
        return handler(self.handle_PV_update_all_items, i)

    def handle_PV_update(self, i, event):
        from same import same
        from item_reference import item_reference
        from event import event as event_object

        # logging.debug(f"{self}: {i}: {event}")
        with self.cached_item_lock(i):
            if not same(event.value, self.get_cached_item(i)):
                self.set_cached_item(i, event.value)
                changed = True
            else:
                changed = False

        if changed:
            new_event = event_object(time=event.time, value=event.value, reference=item_reference(self, i))
            self.item_monitors[i].call(event=new_event)

    def handle_PV_update_all_items(self, i, event):
        from same import same
        from event import event as event_object
        from all_items_reference import all_items_reference

        logging.debug(f"{self}: {i}: {event}")
        all_items = self.cached_all_items
        try:
            all_items[i] = event.value
        except IndexError:
            pass
        if not same(all_items, self.cached_all_items):
            new_event = event_object(time=event.time, value=all_items, reference=all_items_reference(self))
            self.all_item_monitors.call(event=new_event)
        self.cached_all_items = all_items

    @property
    def all_items(self):
        from is_array import is_array
        from as_array import as_array
        if is_array(self.default_value):
            value = [as_array(v[:]).copy() for v in self]
        else:
            value = self[:]
        return value

    def PV_value(self, i):
        from is_array import is_array
        from as_array import as_array

        value = self.PV(i).value
        if value is None:
            value = self.default_value
        if is_array(self.default_value):
            value = as_array(value)

        return value

    def set_PV_value(self, i, value):
        self.PV(i).value = value

    def PV(self, i):
        from CA import PV
        return PV(self.PV_name(i))

    @property
    def length_PV(self):
        from CA import PV
        return PV(self.length_PV_name)

    def PV_name(self, i):
        # PV_name_template: e.g. "BIOCARS:CONFIGURATION.METHOD.MOTOR{i+1}.CURRENT_POSITION"
        PV_name = eval(f"f'{self.PV_name_template}'", dict(i=i, I=i))
        return PV_name

    def set_caching_item(self, i, caching):
        if caching != self.is_cached_item(i):
            if caching:
                self.set_cached_item(i, self.PV_value(i))
            else:
                self.clear_cached_item(i)

    def get_cached_item(self, i):
        try:
            value = self._cached_items[i]
        except KeyError:
            value = None
        if hasattr(value, "copy"):
            value = value.copy()
        return value

    def set_cached_item(self, i, value):
        if hasattr(value, "copy"):
            value = value.copy()
        self._cached_items[i] = value

    def clear_cached_item(self, i):
        try:
            del self._cached_items[i]
        except KeyError:
            pass

    def is_cached_item(self, i):
        return i in self._cached_items

    def cached_item_lock(self, i):
        from threading import Lock
        with self.lock:
            try:
                lock = self._cached_item_locks[i]
            except KeyError:
                lock = self._cached_item_locks[i] = Lock()
            return lock

    @property
    def caching_all_items(self):
        return self.is_cached_all_items

    @caching_all_items.setter
    def caching_all_items(self, caching):
        if caching != self.caching_all_items:
            if caching:
                self.cached_all_items = self.all_items
            else:
                self.clear_cached_all_items()

    @property
    def cached_all_items(self):
        value = self._cached_all_items
        value = [v.copy() for v in value]
        return value

    @cached_all_items.setter
    def cached_all_items(self, all_items):
        all_items = [v.copy() for v in all_items]
        self._cached_all_items = all_items

    def clear_cached_all_items(self):
        self._cached_all_items = []

    @property
    def is_cached_all_items(self):
        return len(self._cached_all_items) > 0


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from item_reference import item_reference as _item_reference
    from all_items_reference import all_items_reference as _all_items_reference
    from handler import handler as _handler

    # self = PV_array('BIOCARS:CONFIGURATION.METHOD.MOTOR{I+1}.CURRENT_POSITION', 'BIOCARS:CONFIGURATION.METHOD.N_MOTORS', default_value="")
    self = PV_array('BIOCARS:CONFIGURATION.METHOD.MOTOR{I+1}.POSITIONS', 'BIOCARS:CONFIGURATION.METHOD.N_MOTORS', default_value=())

    @_handler
    def report(event=None):
        logging.info(f"event={event}")

    print(f"self = {self}")
    print(f"self[0] = {self[0]}")
    print(f"self[:] = {self[:]}")
    _item_reference(self, 0).monitors.add(report)
    _all_items_reference(self).monitors.add(report)
