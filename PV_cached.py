"""
Caching of Channel Access
Author: Friedrich Schotte
Date created: 2020-11-27
Date last modified: 2021-05-28
Revision comment: Do not update cache as "None" if PV disconnects
"""
__version__ = "1.0.3"

from logging import debug, warning
import warnings

from cached_function import cached_function


@cached_function()
def PV_cached(name): return _PV_cached(name)


class PV_cached_property(property):
    def __init__(
            self,
            fget=None,
            fset=None,
            add_monitor=None,
            remove_monitor=None,
            monitors=None,
    ):
        property.__init__(self, fget, fset)
        self.add_monitor = add_monitor
        self.remove_monitor = remove_monitor
        self.monitors = monitors


class _PV_cached:
    from cache import Cache
    cache = Cache("PV")

    def __init__(self, name):
        self.name = name
        from event_handlers import Event_Handlers
        self.event_handlers_value = Event_Handlers(
            setup=self.monitor_setup_value,
        )

    def __repr__(self):
        return f"PV_cached({self.name!r})"

    def __eq__(self, other):
        return all([
            type(self) == type(other),
            self.name == getattr(other, "name", None),
        ])

    def __hash__(self): return hash(repr(self))

    def get_value(self):
        self.monitor_setup_value()
        from CA import caget
        value = caget(self.name, timeout=0)
        if value is None:
            if self.cache_exists:
                value = self.cached_value
            else:
                value = caget(self.name)
                if value is None:
                    warning(f"Failed to get PV {self.name!r}")
                self.update_cached_value(value)
        return value

    def set_value(self, value):
        from CA import caput
        caput(self.name, value)

    def monitors_value(self):
        return self.event_handlers_value

    def add_monitor_value(self, event_handler):
        warnings.warn("add_monitor() is deprecated, use monitors()",
                      DeprecationWarning, stacklevel=2)
        self.monitors_value().add(event_handler)

    def remove_monitor_value(self, event_handler):
        warnings.warn("remove_monitor() is deprecated, use monitors()",
                      DeprecationWarning, stacklevel=2)
        self.monitors_value().remove(event_handler)

    value = PV_cached_property(
        fget=get_value,
        fset=set_value,
        monitors=monitors_value,
        add_monitor=add_monitor_value,
        remove_monitor=remove_monitor_value,
    )

    def monitor_setup_value(self):
        from reference import reference
        event_handlers = reference(self.PV, "value").monitors
        if self.update_handler_value not in event_handlers:
            # debug(f"Monitoring {self.PV}")
            event_handlers.add(self.update_handler_value)

    @property
    def PV(self):
        from CA import PV
        return PV(self.name)

    @property
    def update_handler_value(self):
        from handler import handler
        return handler(self.handle_update_value)

    def handle_update_value(self, event):
        # debug(f"event={event}")
        if event.value is not None:
            self.update_cached_value(event.value)

            from event import event as generate_event
            from reference import reference
            new_event = generate_event(
                value=event.value,
                time=event.time,
                reference=reference(self, "value"),
            )
            self.event_handlers_value.call(event=new_event)

    def update_cached_value(self, value):
        from same import same
        if not self.cache_exists or not same(value, self.cached_value):
            # debug("%s=%s" % (self.name, value))
            self.cached_value = value

    def get_cached_value(self):
        cache_value = self.cache.get(self.name + ".py")
        # Needed for eval:
        try:
            value = eval(cache_value)
        except Exception:
            value = None
        return value

    def set_cached_value(self, value):
        self.cache.set(self.name + ".py", repr(value).encode("utf-8"))

    cached_value = property(get_cached_value, set_cached_value)

    @property
    def cache_exists(self):
        return self.cache.exists(self.name + ".py")


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # PV = PV_cached("LASERLAB:TIMING.registers.image_number.count")
    PV = PV_cached("NIH:TIMING.registers.image_number.count")
    print('PV.value')
