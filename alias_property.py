"""
This is to import selected properties from one class object into another,
avoiding the ambiguities and conflicts of multiple inheritance.

Usage:
    
class Camera(object):
    def __init__(name): 
        self.name = name
        self.state = "not connected"

class Camera_IOC(object):
    from GigE_camera import GigE_camera
    camera = GigE_camera("MicroscopeCamera")
    name  = alias_property("camera.name")
    state = alias_property("camera.state")
    
camera_ioc = Camera_IOC()
camera_ioc.name

Author: Friedrich Schotte
Date created: 2020-05-08
Date last modified: 2021-01-09
Revision comment: Cleanup: reference.monitors
"""
__version__ = "1.4.6"

from logging import info, warning


class alias_property(property):
    def __init__(self, name):
        words = name.split(".")
        self.leading_path, self.property_name = words[0:-1], words[-1]
        property.__init__(
            self,
            fget=self.get_property,
            fset=self.set_property,
        )

    def get_property(self, instance):
        return self.original_reference(instance).value

    def set_property(self, instance, value):
        self.original_reference(instance).value = value

    def monitors(self, instance):
        return self.attributes(instance).event_handlers

    def monitor_setup(self, instance):
        self.original_reference(instance).monitors.add(self.handler(instance))

    def monitor_cleanup(self, instance):
        self.original_reference(instance).monitors.remove(self.handler(instance))

    def handler(self, instance):
        from handler import handler
        return handler(self.handle_change, instance)

    def handle_change(self, instance, event=None):
        from event import event as event_object
        from time import time

        if not event:
            warning(f"{self.original_reference(instance)} did not generate an event")
            new_event = event_object(
                time=time(),
                value=self.get_property(instance),
                reference=self.alias_reference(instance),
            )
        elif event.reference != self.original_reference(instance):
            warning("Asked for updates of %r, instead got update of %r" %
                    (self.original_reference(instance), event.reference))
            new_event = event_object(
                time=time(),
                value=self.get_property(instance),
                reference=self.alias_reference(instance),
            )
        else:
            new_event = event_object(
                time=event.time,
                value=event.value,
                reference=self.alias_reference(instance),
            )
        self.monitors(instance).call(event=new_event)

    def original_reference(self, instance):
        from reference import reference
        return reference(self.original_object(instance), self.property_name)

    def alias_reference(self, instance):
        from reference import reference
        return reference(instance, self.get_name(instance))

    def original_object(self, instance):
        obj = instance
        for name in self.leading_path:
            obj = getattr(obj, name)
        return obj

    def attributes(self, instance):
        name = self.get_name(instance)
        attributes_cache = self.attributes_cache(instance)
        if name not in attributes_cache:
            attributes_cache[name] = Attributes(self, instance)
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


class Attributes:
    def __init__(self, alias_property_object, instance):
        from event_handlers import Event_Handlers
        from functools import partial
        self.event_handlers = Event_Handlers(
            setup=partial(alias_property_object.monitor_setup, instance),
            cleanup=partial(alias_property_object.monitor_cleanup, instance),
        )

    def __repr__(self):
        return f"{self.class_name}({self.event_handlers})"

    @property
    def class_name(self):
        return type(self).__name__


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from reference import reference as _reference
    from handler import handler as _handler


    class Camera(object):
        def __init__(self, name):
            self.name = name

        def __repr__(self):
            return f"{type(self).__name__}({self.name!r})"

        from monitored_value_property import monitored_value_property
        state = monitored_value_property(default_value="not connected")


    class Camera_IOC(object):
        def __repr__(self):
            return f"{type(self).__name__}()"

        camera = Camera("MicroscopeCamera")
        name = alias_property("camera.name")
        state = alias_property("camera.state")


    camera_ioc = Camera_IOC()


    @_handler
    def report(event=None):
        info(f"event={event}")


    print(f'camera_ioc.name = {camera_ioc.name!r}')
    print(f'camera_ioc.camera.state = {camera_ioc.camera.state!r}')
    _reference(camera_ioc, "state").monitors.add(report)
    _reference(camera_ioc.camera, "state").monitors.add(report)
