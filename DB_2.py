"""
Simple database
Author: Friedrich Schotte
Date created: 2010-12-10
Date last modified: 2022-06-30
Revision comment:
"""
__version__ = "2.0"

import logging

from alias_property import alias_property
from cached_function import cached_function
from monitored_property import monitored_property

logger = logging.getLogger(__name__)


def db(key, default_value):
    return db_entry(key, default_value).value


def dbset(key, value):
    db_entry(key, None).value = value


def dbget(key):
    return db_entry(key, None).string_value


def dbput(key, string_value):
    db_entry(key, None).string_value = string_value


@cached_function()
def db_entry(key, default_value):
    return DB_Entry(key, default_value)


class DB_Entry:
    def __init__(self, key, default_value):
        self.key = key
        self.default_value = default_value

    def __repr__(self):
        return f"{self.class_name}({self.key!r}, {self.default_value!r})"

    @property
    def class_name(self):
        return type(self).__name__

    @monitored_property
    def value(self, string_value):
        """Retrieve a value from the database
        Return value: any built-in Python data type"""
        return value_from_string(string_value, self.default_value)

    @value.setter
    def value(self, value):
        self.string_value = repr(value)

    @monitored_property
    def string_value(self, dictionary):
        return dictionary.get(self.dictionary_key, "")

    @string_value.setter
    def string_value(self, string_value):
        if string_value != self.string_value:
            with self.file.lock:
                if string_value != self.string_value:
                    new_dictionary = dict(self.dictionary)
                    new_dictionary[self.dictionary_key] = string_value
                    self.dictionary = new_dictionary

    dictionary = alias_property("file.dictionary")

    @property
    def file(self):
        from db_file import db_file
        return db_file(self.filename)

    @property
    def filename(self):
        filename = f"{self.dirname}/{self.key_basename}_settings.txt"
        filename = normpath(filename)
        return filename

    @property
    def dictionary_key(self):
        return self.key[len(self.prefix + self.key_basename) + 1:]

    @property
    def key_basename(self):
        return self.key_without_prefix.split(".")[0]

    @property
    def key_without_prefix(self):
        return self.key[len(self.prefix):]

    @property
    def prefix(self):
        prefix = ""
        if self.key.startswith("local."):
            prefix = "local."
        return prefix

    @property
    def dirname(self):
        """Pathname of the file used to store persistent parameters"""
        if self.prefix == "local.":
            path = local_settings_dir()
        else:
            path = global_settings_dir()
        return path


def value_from_string(string_value, default_value):
    from numpy import nan, inf, array  # noqa - for "eval"
    from collections import OrderedDict  # noqa - for "eval"
    try:
        import wx  # for "eval"
    except ImportError:
        pass
    if default_value is not None:
        dtype = type(default_value)
        # noinspection PyBroadException
        try:
            value = dtype(eval(string_value))
        except Exception:
            value = default_value
    else:
        # noinspection PyBroadException
        try:
            value = eval(string_value)
        except Exception:
            value = None
    return value


@cached_function()
def global_settings_dir():
    from module_dir import module_dir
    path = module_dir(global_settings_dir) + "/settings"
    return path


@cached_function()
def local_settings_dir():
    from os import environ
    if "APPDATA" in environ:
        settings_dir = environ["APPDATA"] + "/Python"
    elif "HOMEPATH" in environ:
        settings_dir = environ["HOMEPATH"] + "/Python"
    elif "USERPROFILE" in environ:
        settings_dir = environ["USERPROFILE"] + "/Python"
    elif "HOME" in environ:
        home = environ["HOME"]
        settings_dir = home + "/.python"
        from os.path import exists
        if exists(home + "/Library/Preferences"):
            settings_dir = home + "/Library/Preferences/Python"
    else:
        from tempfile import gettempdir
        settings_dir = gettempdir() + "/python"
    return settings_dir


def normpath(pathname):
    """Make sure no illegal characters are contained in the file name."""
    from sys import platform
    illegal_chars = ":?*"
    for c in illegal_chars:
        # Colon may in the path after the drive letter.
        if platform == "win32" and c == ":" and pathname[1:2] == ":":
            pathname = pathname[0:2] + pathname[2:].replace(c, "")
        else:
            pathname = pathname.replace(c, ".")
    return pathname


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = db_entry("test.test1", "")

    from handler import handler as _handler


    @_handler
    def report(event):
        logging.info(f"{event}")


    from reference import reference
    reference(self, "string_value").monitors.add(report)
    reference(self, "value").monitors.add(report)

    print("self.value += '.'")
