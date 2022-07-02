"""
A property object to be used inside a class, its value is kept in a permanent
storage in a file.

Usage example:

class Test(object):
    name = "test"
    count = db_property("count",0)
    def monitor(self,name,procedure,*args,**kwargs):
        getattr(type(self),name).monitor(self,procedure,*args,**kwargs)
    def __init__(self): self.monitor('count',self.handle_count)
    def handle_count(self): logging.info("count: {self.count}")

Author: Friedrich Schotte
Python Version: 2.7 and 3.7
Date created: 2020-05-25
Date last modified: 2022-06-26
Revision comment: Cleanup: docstring
"""
__version__ = "1.3.8"

import logging
from deprecated import deprecated


class db_property(property):
    def __init__(self, name, default_value=None, local=False, private=False):
        property.__init__(self, self.get_property, self.set_property)
        self.name = name
        self.default_value = default_value
        self.local = local
        self.private = private
        if self.private:
            self.private_str_value = {}

    def __repr__(self):
        return "%s(name=%r,default_value=%r,local=%r,private=%r)" % (
            type(self).__name__,
            self.name,
            self.default_value,
            self.local,
            self.private,
        )

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
        db_name = self.db_prefix + instance_dbname(instance) + "." + self.name
        return db_name

    @property
    def db_prefix(self):
        return "local." if self.local else ""

    def filename(self, instance):
        from DB import db_filename
        return db_filename(self.db_name(instance))

    def get_str_value(self, instance):
        from DB import dbget
        if self.private:
            if instance not in self.private_str_value:
                self.private_str_value[instance] = dbget(self.db_name(instance))
            str_value = self.private_str_value[instance]
        else:
            str_value = dbget(self.db_name(instance))
        return str_value

    def set_str_value(self, instance, str_value):
        from DB import dbput
        dbput(self.db_name(instance), str_value)
        if self.private:
            self.private_str_value[instance] = str_value

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
        # noinspection PyBroadException
        try:
            value = dtype(eval(str_value))
        except Exception:
            value = default_value
        return value

    def get_default_value(self, instance):
        if hasattr(self.default_value, "fget"):
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
            logging.warning(f"Could not find {self} in {class_object}")
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


def instance_dbname(instance):
    if hasattr(type(instance), "db_name"):
        db_name = getattr(instance, "db_name")
    else:
        db_name = default_instance_dbname(instance)
    return db_name


def default_instance_dbname(instance):
    class_name = type(instance).__name__
    name = getattr(instance, "name", "")
    if name:
        db_name = class_name + "." + name
    else:
        db_name = class_name
    return db_name


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # import DB; DB.logger.level = level
    # import file_monitor; file_monitor.logger.level = level

    from reference import reference as _reference
    from handler import handler as _handler


    class Test(object):
        count = db_property("count", 0)

        def __init__(self, name, comment):
            self.name = name
            self.comment = comment

        def __repr__(self):
            return f'{self.class_name}({self.name!r}, {self.comment!r})'

        @property
        def class_name(self):
            return type(self).__name__

        @property
        def db_name(self):
            return self.name


    test1 = Test("test", "Example 1")
    test2 = Test("test", "Example 2")


    @_handler
    def report(event=None):
        logging.info(f"event={event}")


    _reference(test1, 'count').monitors.add(report)
    _reference(test2, 'count').monitors.add(report)

    print("_reference(test1, 'count').monitors")
    print("_reference(test1, 'count').monitors.remove(report)")
    print("")
    print("test1.count += 1")
    print("test2.count += 1")
    print("test1.count, test2.count")
