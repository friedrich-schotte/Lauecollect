"""Base class for event-based device drivers
Author: Friedrich Schotte
Date created: 2019-08-12
Date last modified: 2022-07-02
Revision comment: Cleanup: pylint
"""
__version__ = "1.0.2"

import logging
from logging import error
from traceback import format_exc


class Record(object):
    __name__ = "record"

    def __init__(self, name=None):
        if name is not None:
            self.__name__ = name
        self.__callbacks__ = {}

    def __setattr__(self, name, value):
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self, name, value)
        else:
            old_value = getattr(self, name)
            if not self.__equal__(old_value, value):
                deps = self.__dependent_properties__(name)
                old_values = [getattr(self, dep) for dep in deps]
                object.__setattr__(self, name, value)
                new_values = [getattr(self, dep) for dep in deps]
                for (dep, old_value, new_value) in zip(deps, old_values, new_values):
                    changed = not self.__equal__(old_value, new_value)
                    if changed:
                        self.__notify__(dep)
            self.__notify_always__(name)

    def __notify__(self, name):
        if name in self.__callbacks__:
            for callback in self.__callbacks__[name]:
                callback.start()
        for method_name in self.__methods_names_to_invoke__(name):
            self.__call_method__(method_name)

    def __notify_always__(self, name):
        for method_name in self.__methods_names_to_invoke_always__(name):
            self.__call_method__(method_name)

    def __dependent_properties__(self, name):
        names = self.__dependencies__(name)
        names = [name for name in names if self.__is_property__(name)]
        return names

    def __dependencies__(self, name):
        deps = [name]
        dep_dict = self.__dep_dict__
        for dep in deps:
            for prop in dep_dict:
                if dep in dep_dict[prop]:
                    if prop not in deps:
                        deps.append(prop)
        return deps

    @property
    def __dep_dict__(self):
        dep_dict = {}
        for name in self.__property_names__:
            dep_dict[name] = []
            prop = getattr(type(self), name)
            dep_dict[name] += getattr(prop, "depends_on", [])
            fget = getattr(prop, "fget", None)
            dep_dict[name] += getattr(fget, "depends_on", [])
            if len(dep_dict[name]) == 0:
                del dep_dict[name]
        return dep_dict

    def __methods_names_to_invoke__(self, name):
        """name: a class property"""
        names = []
        for methods_name in self.__method_names__:
            method = getattr(type(self), methods_name, None)
            property_names = getattr(method, "invoke_on", [])
            if name in property_names:
                names.append(methods_name)
        return names

    def __methods_names_to_invoke_always__(self, name):
        """name: a class property"""
        names = []
        for methods_name in self.__method_names__:
            method = getattr(type(self), methods_name, None)
            property_names = getattr(method, "always_invoke_on", [])
            if name in property_names:
                names.append(methods_name)
        return names

    def __call_method__(self, method_name):
        method = getattr(self, method_name)
        from threading import Thread
        thread = Thread(target=method)
        thread.daemon = True
        thread.start()

    @property
    def __method_names__(self):
        names = self.__property_names__
        names = [name for name in names if self.__is_method__(name)]
        return names

    @property
    def __property_names__(self):
        base_class_property_names = dir(Record)
        names = dir(type(self))
        names = [name for name in names if name not in base_class_property_names]
        names = [name for name in names if not self.__is_private__(name)]
        return names

    def __is_property__(self, name):
        attr = getattr(type(self), name, None)
        return not hasattr(attr, "__call__")

    def __is_method__(self, name):
        attr = getattr(type(self), name, None)
        return hasattr(attr, "__call__")

    @staticmethod
    def __is_private__(name):
        return name.startswith("__") and name.endswith("__")

    @staticmethod
    def __equal__(current_value, value):
        return repr(current_value) == repr(value)

    def monitor(self, name, function, *args, **kwargs):
        if name not in self.__callbacks__:
            self.__callbacks__[name] = []
        self.__callbacks__[name] += [callback(function, *args, **kwargs)]

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.__name__)


def depends_on(*args):
    """Decorator for a method of a record-derived class
    args: property names as list of strings"""

    def decorate(method):
        property_names = getattr(method, "depends_on", [])
        for arg in args:
            if arg not in property_names:
                property_names.append(arg)
        method.depends_on = property_names
        return method

    return decorate


def invoke_on(*args):
    """"Decorator for a method of a record-derived class
    automatically call a method if one or more properties change
    args: property names as list of strings"""

    def decorate(method):
        property_names = getattr(method, "invoke_on", [])
        for arg in args:
            if arg not in property_names:
                property_names.append(arg)
        method.invoke_on = property_names
        return method

    return decorate


def always_invoke_on(*args):
    """"Decorator for a method of a record-derived class
    automatically call a method if one or more properties change
    args: property names as list of strings"""

    def decorate(method):
        property_names = getattr(method, "always_invoke_on", [])
        for arg in args:
            if arg not in property_names:
                property_names.append(arg)
        method.always_invoke_on = property_names
        return method

    return decorate


class callback(object):
    def __init__(self, function, *args, **kwargs):
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def call(self):
        try:
            self.function(*self.args, **self.kwargs)
        except Exception as x:
            error("%r: %s\n%s" % (self, x, format_exc()))

    def start(self):
        from threading import Thread
        thread = Thread(target=self.call)
        thread.daemon = True
        thread.start()

    def __repr__(self):
        args = ",".join([repr(v) for v in self.args])
        kwargs = ",".join(["%s=%r" % (k, self.kwargs[k]) for k in self.kwargs])
        arg_list = ",".join([args, kwargs])
        return "%s(%s)" % (self.function.__name__, arg_list)


if __name__ == "__main__":
    msg_format = "%(asctime)s: %(levelname)s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = Record()
