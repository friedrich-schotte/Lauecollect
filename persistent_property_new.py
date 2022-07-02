"""
A property object to be used inside a class, it value is kept in a permanent
storage in a file.

Usage example:

class Test(object):
    name = "test"
    count = persistent_property("count",0)
    def monitor(self,name,procedure,*args,**kwargs):
        getattr(type(self),name).monitor(self,procedure,*args,**kwargs)
    def __init__(self): self.monitor('count',self.handle_count)
    def handle_count(self): info("count: %r" % self.count)

Author: Friedrich Schotte
Python Version: 2.7 and 3.7
Date created: 2020-05-25
Date last modified: 2021-01-11
Revision comment: Cleanup: reference.monitors
"""
__version__ = "2.0"

from logging import info, warning
from deprecated import deprecated


class persistent_property(property):
    def __init__(self, name, default_value=None):
        property.__init__(self, self.get_property, self.set_property)
        self.name = name
        self.default_value = default_value

    def __repr__(self):
        return f"{self.class_name}({self.name!r}, default_value={self.default_value!r})"

    @property
    def class_name(self):
        return type(self).__name__

    def get_property(self, instance):
        str_value = self.get_str_value(instance)
        value = self.str_to_value(instance, str_value)
        return value

    def set_property(self, instance, value):
        str_value = repr(value)
        self.set_str_value(instance, str_value)

    def monitors(self, instance):
        return self.attributes(instance).event_handlers

    def monitor_setup(self, instance):
        from DB import dbmonitor
        dbmonitor(self.db_name(instance), self.handle_change, instance)

    def monitor_cleanup(self, instance):
        from DB import dbmonitor_clear
        dbmonitor_clear(self.db_name(instance), self.handle_change, instance)

    def handle_change(self, instance):
        import time
        time = time.time()
        value = self.get_property(instance)
        from reference import reference
        event_reference = reference(instance, self.get_name(instance))
        from event import event
        event = event(time=time, value=value, reference=event_reference)
        self.monitors(instance).call(event=event)

    def db_name(self, instance):
        db_name = self.dbname_template.replace("{name}", class_name(instance))
        return db_name

    @property
    def dbname_template(self):
        if "{name}" in self.name:
            template = self.name
        else:
            from DB import db_prefix, db_keyname
            prefix = db_prefix(self.name)
            keyname = db_keyname(self.name)
            if keyname.startswith("."):
                template = prefix + keyname[1:]
            else:
                template = prefix + "{name}" + "." + keyname
        return template

    def filename(self, instance):
        from DB import db_filename
        return db_filename(self.db_name(instance))

    def get_str_value(self, instance):
        from DB import dbget
        str_value = dbget(self.db_name(instance))
        return str_value

    def set_str_value(self, instance, str_value):
        from DB import dbput
        dbput(self.db_name(instance), str_value)

    def str_to_value(self, instance, str_value):
        default_value = self.get_default_value(instance)
        dtype = type(default_value)
        try:
            from numpy import nan, inf, array  # for "eval"
        except ImportError:
            pass
        try:
            import wx  # for "eval"
        except ImportError:
            pass
        try:
            value = dtype(eval(str_value))
        except Exception:
            value = default_value
        return value

    def get_default_value(self, instance):
        if type(self.default_value) == str and self.default_value.startswith("self."):
            property_name = self.default_value[len("self."):]
            default_value = getattr(instance, property_name)
        elif hasattr(self.default_value, "fget"):
            default_value = self.default_value.fget(instance)
        else:
            default_value = self.default_value
        return default_value

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

    @deprecated(use_instead=f'{monitors}')
    def monitor(self, instance, procedure, *args, **kwargs):
        from handler import handler
        self.monitors(instance).add(handler(procedure, *args, **kwargs))

    @deprecated(use_instead=f'{monitors}')
    def monitor_clear(self, instance, procedure, *args, **kwargs):
        from handler import handler
        self.monitors(instance).remove(handler(procedure, *args, **kwargs))


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


def class_name(instance):
    class_name = type(instance).__name__
    if hasattr(instance, "__name__"):
        class_name = getattr(instance, "__name__", "")
    if hasattr(instance, "name"):
        class_name = getattr(instance, "name", "")
    return class_name


if __name__ == "__main__":
    import logging

    level = logging.DEBUG
    msg_format = "%(asctime)s %(levelname)s %(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=level, format=msg_format)

    # import DB; DB.logger.level = level
    # import file_monitor; file_monitor.logger.level = level

    from reference import reference as _reference
    from handler import handler as _handler


    class Test(object):
        count = persistent_property("count", 0)

        def __init__(self, name, comment):
            self.name = name
            self.comment = comment

        def __repr__(self):
            return f'{self.class_name}({self.name}, {self.comment})'

        @property
        def class_name(self):
            return type(self).__name__


    test1 = Test("test", "1")
    test2 = Test("test", "2")


    @_handler
    def report(event=None):
        info(f"event={event}")


    _reference(test1, 'count').monitors.add(report)
    _reference(test2, 'count').monitors.add(report)

    print("_reference(test1, 'count').monitors")
    print("_reference(test1, 'count').monitors.remove(report)")
    print("")
    print("test1.count += 1")
    print("test2.count += 1")
    print("test1.count, test2.count")
