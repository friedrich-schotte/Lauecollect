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
Date created: 2015-03-07
Date last modified: 2020-12-23
Python Version: 2.7 and 3.7
Revision comment: Cleanup
"""
__version__ = "1.7.2"

from logging import info


def persistent_property(name, default_value=0.0):
    """A property object to be used inside a class"""

    def get(self): return get_persistent_property(self, name, default_value)

    def set(self, value): set_persistent_property(self, name, value)

    def monitor(self, procedure, *args, **kwargs):
        monitor_persistent_property(self, name, procedure, *args, **kwargs)

    def monitor_clear(self, procedure, *args, **kwargs):
        monitor_clear_persistent_property(self, name, procedure, *args, **kwargs)

    def monitors(self):
        return monitors_persistent_property(self, name)

    def _dbname(self): return dbname(self, name)

    property_object = Persistent_Property(get, set)
    property_object.monitor = monitor
    property_object.monitor_clear = monitor_clear
    property_object.monitors = monitors
    property_object.name = name
    property_object.dbname = _dbname
    property_object.default_value = default_value
    return property_object


class Persistent_Property(property):
    def __repr__(self):
        return "%s(%s,%s,monitor=%s,name=%r,default_value=%r)" % (
            type(self).__name__,
            self.fget.__name__,
            self.fset.__name__,
            getattr(getattr(self, "monitor", None), "__name__", ""),
            getattr(self, "name", None),
            getattr(self, "default_value", None),
        )

    @property
    def dbname_template(self):
        return dbname_template(self.name)

    def dbname(self, instance):
        return dbname(instance, self.name)

    def filename(self, instance):
        from DB import db_filename
        return db_filename(self.dbname(instance))


def get_persistent_property(self, name, default_value=0.0):
    from DB import dbget
    t = dbget(dbname(self, name))
    if type(default_value) == str and default_value.startswith("self."):
        def_val = getattr(self, default_value[len("self."):])
    elif type(default_value) == property:
        def_val = default_value.fget(self)
    else:
        def_val = default_value
    dtype = type(def_val)
    try:
        from numpy import nan, inf, array  # for "eval"
    except ImportError:
        pass
    try:
        import wx  # for "eval"
    except ImportError:
        pass
    try:
        t = dtype(eval(t))
    except Exception:
        t = def_val
    return t


def set_persistent_property(self, name, value):
    from DB import dbput
    dbput(dbname(self, name), repr(value))


def monitor_persistent_property(self, name, procedure, *args, **kwargs):
    from DB import dbmonitor
    dbmonitor(dbname(self, name), procedure, *args, **kwargs)


def monitor_clear_persistent_property(self, name, procedure, *args, **kwargs):
    from DB import dbmonitor_clear
    dbmonitor_clear(dbname(self, name), procedure, *args, **kwargs)


def monitors_persistent_property(self, name):
    from DB import dbmonitors
    return dbmonitors(dbname(self, name))


def dbname(self, name):
    dbname = dbname_template(name).replace("{name}", class_name(self))
    return dbname


def dbname_template(name):
    if "{name}" in name:
        template = name
    else:
        from DB import db_prefix, db_keyname
        prefix = db_prefix(name)
        keyname = db_keyname(name)
        if keyname.startswith("."):
            template = prefix + keyname[1:]
        else:
            template = prefix + "{name}" + "." + keyname
    return template


def class_name(self):
    class_name = type(self).__name__
    if hasattr(self, "__name__"):
        class_name = getattr(self, "__name__", "")
    if hasattr(self, "name"):
        class_name = getattr(self, "name", "")
    return class_name


if __name__ == "__main__":
    import logging

    level = logging.DEBUG
    msg_format = "%(asctime)s %(levelname)s %(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=level, format=msg_format)

    # import DB; DB.logger.level = level
    # import file_monitor; file_monitor.logger.level = level

    class Test(object):
        name = "test"
        count = persistent_property("count", 0)

        def monitor(self, name, procedure, *args, **kwargs):
            getattr(type(self), name).monitor(self, procedure, *args, **kwargs)

        def __init__(self): self.monitor('count', self.handle_count)

        def handle_count(self): info("count: %r" % self.count)


    self = Test()

    print("self.count += 1")
