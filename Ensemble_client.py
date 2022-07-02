#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2016-01-31
Date last modified: 2021-10-19
Comment: Cleanup: utf-8
"""

from logging import debug, warning

__version__ = "4.0.4"

verbose_logging = True


class EnsembleClient(object):
    """"""
    __attributes__ = [
        "ip_address_and_port",
        "caching_enabled",
        "connection",
        "integer_registers_", "floating_point_registers_",
        "integer_registers", "floating_point_registers",
        "ip_address", "port",
        "query",
    ]

    name = "Ensemble"
    from persistent_property import persistent_property
    ip_address_and_port = persistent_property("ip_address",
                                              "nih-instrumentation.cars.aps.anl.gov:2000")
    caching_enabled = persistent_property("caching_enabled", True)

    timeout = 5.0
    # This is to make the query method multi-thread safe.
    from threading import Lock
    lock = Lock()

    def __init__(self):
        """ip_address may be given as address:port. If :port is omitted, port
        number 2000 is assumed."""
        self.connection = None  # network connection
        self.integer_registers_ = ArrayWrapper(self, "integer_registers")
        self.floating_point_registers_ = ArrayWrapper(self, "floating_point_registers")
        self.integer_registers = CachedArrayWrapper(self, "integer_registers")
        self.floating_point_registers = CachedArrayWrapper(self, "floating_point_registers")

    def __repr__(self):
        return "EnsembleClient('" + self.ip_address + ":" + str(self.port) + "')"

    def get_ip_address(self):
        return self.ip_address_and_port.split(":")[0]

    def set_ip_address(self, value):
        self.ip_address_and_port = value + ":" + str(self.port)

    ip_address = property(get_ip_address, set_ip_address)

    def get_port(self):
        if ":" not in self.ip_address_and_port:
            return 2000
        return int(self.ip_address_and_port.split(":")[-1])

    def set_port(self, value):
        self.ip_address_and_port = str(self.ip_address) + ":" + str(value)

    port = property(get_port, set_port)

    def query(self, command):
        """To send a command that generates a reply, e.g. "InstrumentID.Value".
        Returns the reply"""
        debug("query %s" % to_repr(command))
        from tcp_client import query
        reply = query(self.ip_address_and_port, command.encode("utf-8")).decode("utf-8")
        if reply:
            debug("reply %s" % to_repr(reply))
        return reply

    def __getattr__(self, name):
        """A property"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute wasn't found the usual ways.
        if name.startswith("__") and name.endswith("__"):
            return object.__getattribute__(self, name)
        # debug("EnsembleWrapper.__getattr__(%r)" % name)
        value = self.query(f"ensemble_driver.{name}")
        # debug("Got reply %s" % to_repr(value))
        if "ArrayWrapper(" in value:
            value = value.replace("ArrayWrapper(", "").replace(")", "")
        try:
            value = eval(value)
        except Exception as x:
            warning(f"ensemble_driver.{name}: {value!r}: {x}")
        return value

    def __setattr__(self, name, value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        if (name.startswith("__") and name.endswith("__")) or \
                name in self.__attributes__:
            object.__setattr__(self, name, value)
        else:
            self.query("ensemble_driver.%s = %r" % (name, value))


class ArrayWrapper(object):
    def __init__(self, obj, name):
        self.object = obj
        self.name = name

    def __getitem__(self, index):
        """Called when [0] is used.
        index: integer or list/array of integers or array of booleans"""
        # debug("ArrayWrapper.__getitem__(%r)" % (index,))
        command = ("ensemble_driver.%s[%r]" % (self.name, index))
        value = self.object.query(command)
        if "ArrayWrapper(" in value:
            value = value.replace("ArrayWrapper(", "").replace(")", "")
        try:
            value = eval(value)
        except Exception as msg:
            debug("%s: %s" % (to_repr(value), msg))
            self.last_reply = value  # for debugging
            value = self.default_value(index)
        if type(value) == str and value == "":
            value = self.default_value(index)
        debug("Ensemble: Value: %s" % to_repr(value))
        return value

    def __setitem__(self, index, value):
        """Called when [0]= is used.
        index: single index, slice or list of indices
        value: single value or array of values"""
        # debug("ArrayWrapper.__setitem__(%r,%r)" % (index,value))
        command = ("ensemble_driver.%s[%r] = %r" % (self.name, index, value))
        self.object.query(command)

    def __len__(self):
        """Length of array. Called when len(x) is used."""
        command = ("len(ensemble_driver.%s)" % self.name)
        value = self.object.query(command)
        try:
            value = eval(value)
        except Exception as msg:
            debug("%s: %s" % (to_repr(value), msg))
            value = 0
        return value

    def default_value(self, index):
        """Return this when a communication error occurs"""
        from numpy import array, nan
        if type(index) != slice and not hasattr(index, "__len__"):
            return nan
        return array([nan] * len(tolist(index)))


class CachedArrayWrapper(ArrayWrapper):
    def __init__(self, obj, name):
        ArrayWrapper.__init__(self, obj, name)
        self.cache = {}

    def __getitem__(self, index):
        """Called when [0] is used.
        index: integer or list/array of integers or array of booleans"""
        # debug("CachedArrayWrapper.__getitem__(%r)" % (index,))
        from numpy import array
        items = tolist(index, len(self))
        cache = dict(self.cache)
        if self.caching_enabled:
            items_to_get = [i for i in items if i not in cache]
        else:
            items_to_get = items
        if len(items_to_get) > 0:
            new_values = ArrayWrapper.__getitem__(self, items_to_get)
            for (i, v) in zip(items_to_get, new_values):
                cache[i] = v
        values = array([cache[i] for i in items])
        if is_scalar(index):
            values = values[0]
        return values

    def __len__(self):
        """Length of array. Called when len(x) is used."""
        if "__len__" not in self.cache or not self.caching_enabled:
            self.cache["__len__"] = ArrayWrapper.__len__(self)
        return self.cache["__len__"]

    def __setitem__(self, index, value):
        """Called when [0]= is used.
        index: single index, slice or list of indices
        value: single value or array of values"""
        # debug("CachedArrayWrapper.__setitem__(%r,%r)" % (index,value))
        from numpy import atleast_1d
        ArrayWrapper.__setitem__(self, index, value)
        items = tolist(index, len(self))
        values = atleast_1d(value)
        for (i, v) in zip(items, values):
            self.cache[i] = v

    def get_caching_enabled(self):
        return self.object.caching_enabled

    def set_caching_enabled(self, value):
        self.object.caching_enabled = value

    caching_enabled = property(get_caching_enabled, set_caching_enabled)


def timestamp():
    """Current date and time as formatted ASCII text, precise to 1 ms"""
    from datetime import datetime
    timestamp = str(datetime.now())
    return timestamp[:-3]  # omit microseconds


def to_repr(x, n_chars=80):
    """limit string length using ellipses (...)"""
    s = repr(x)
    if len(s) > n_chars:
        s = s[0:n_chars - 10 - 3] + "..." + s[-10:]
    return s


def tolist(index, length=1000):
    """Convert index (which may be a slice) to a list"""
    from numpy import atleast_1d, arange
    index_list = list(atleast_1d(arange(0, length)[index]))
    # debug("tolist: converted %s to %s" % (to_repr(index),to_repr(index_list)))
    return index_list


def is_scalar(x):
    if hasattr(x, "__len__") or type(x) == slice:
        return False
    return True


ensemble = EnsembleClient()

if __name__ == "__main__":  # for testing
    import logging
    from tempfile import gettempdir

    logfile = gettempdir() + "/lauecollect_debug.log"
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s: %(message)s")

    self = ensemble  # for debugging
    print('ensemble.ip_address = %r' % ensemble.ip_address)
    print('ensemble.caching_enabled = %r' % ensemble.caching_enabled)
    # print('ensemble.program_filename = "Home (safe).ab"')
    # print('ensemble.program_filename = "PVT_Fly-thru.ab"')
    # print('ensemble.program_filename')
    # print('ensemble.program_running')
    print('ensemble.integer_registers[2]')
    print('ensemble.integer_registers[2] = 0')
