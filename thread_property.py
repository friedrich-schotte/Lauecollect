"""
A property object to be used inside a class
Author: Friedrich Schotte
Date created: 2020-11-13
Revision comment: Issue:
    line 26: monitors = self.monitors,
    monitor_property' is deprecated (use 'monitored_property' instead)

"""
__version__ = "1.2"

from logging import info, warning, error
from traceback import format_exc


class thread_property(property):
    """A property object to be used inside a class"""

    def __init__(self, procedure_name):
        self.procedure_name = procedure_name
        super().__init__(
            fget=self.get_property,
            fset=self.set_property,
        )

    def __repr__(self):
        return "%s(%r)" % (
            type(self).__name__,
            self.procedure_name,
        )

    def run(self, instance):
        self.attributes(instance).running = True
        self.notify(instance, running=True)
        procedure = getattr(instance, self.procedure_name)
        try:
            procedure()
        except Exception:
            error("%r.%s: %s" % (instance, self.procedure_name, format_exc()))
        self.attributes(instance).running = False
        self.notify(instance, running=False)

    def notify(self, instance, running):
        from event import event as event_object
        from time import time
        from reference import reference
        event = event_object(
            time=time(),
            value=running,
            reference=reference(instance, self.get_name(instance)),
        )
        self.monitors(instance).call(event=event)

    def get_property(self, instance):
        return self.attributes(instance).running

    def set_property(self, instance, value):
        if value != self.get_property(instance):
            if value:
                from threading import Thread
                thread = Thread(target=self.run, args=(instance,))
                self.attributes(instance).thread = thread
                thread.daemon = True
                instance.cancelled = False
                thread.start()
            else:
                instance.cancelled = True

    def monitors(self, instance):
        return self.attributes(instance).event_handlers

    def attributes(self, instance):
        name = self.get_name(instance)
        attributes_cache = self.attributes_cache(instance)
        if name not in attributes_cache:
            attributes_cache[name] = thread_attributes()
        attributes = attributes_cache[name]
        return attributes

    def attributes_cache(self, instance):
        name = self.attributes_cache_base_name
        if not hasattr(instance, name):
            setattr(instance, name, {})
        attributes_cache = getattr(instance, name)
        return attributes_cache

    @property
    def attributes_cache_base_name(self):
        return f"__{self.class_name}__".lower()

    @property
    def class_name(self):
        return type(self).__name__

    from cached_function import cached_function

    @cached_function()
    def get_name(self, instance):
        class_object = type(instance)
        for name in dir(class_object):
            if getattr(class_object, name) == self:
                break
        else:
            warning(f"Could not find {self} in {class_object}")
            name = "unknown"
        return name

    from deprecated import deprecated

    @deprecated(use_instead="monitors")
    def monitor(self, instance, proc, *args, **kwargs):
        from handler import handler
        self.monitors(instance).add(handler(proc, *args, **kwargs))

    @deprecated(use_instead="monitors")
    def monitor_clear(self, instance, proc, *args, **kwargs):
        from handler import handler
        self.monitors(instance).remove(handler(proc, *args, **kwargs))


class thread_attributes:
    def __init__(self):
        self.running = False
        from threading import Thread
        self.thread = Thread()
        from event_handlers import Event_Handlers
        self.event_handlers = Event_Handlers()


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

    from handler import handler
    from reference import reference

    class Test(object):
        cancelled = False

        def procedure(self):
            from time import time, sleep
            t0 = time()
            while time() - t0 < 10 and not self.cancelled:
                sleep(0.1)

        procedure_running = thread_property("procedure")

        def __repr__(self): return "%s()" % type(self).__name__

    instance = Test()

    @handler
    def report(event=None):
        info(f"event={event}")

    reference(instance, "procedure_running").monitors.add(report)
    print("instance.procedure_running = True")
    print("instance.cancelled = True")
