"""Simple database
Author: Friedrich Schotte
Date created: 2010-12-10
Date last modified: 2022-07-01
Python Version: 2.7 and 3.7
Revision comment: Updated example
"""
__version__ = "1.12.5"

import logging
from threading import Lock
from typing import Any
from cached_function import cached_function

logger = logging.getLogger(__name__)
logger.level = logging.INFO
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error

db_file_extension = "_settings.txt"


def dbset(key, value):
    """Store a value in the database
    value: any python built-in data type"""
    dbput(key, repr(value))


def db(key, default_value: Any = ""):
    """Retrieve a value from the database
    Return value: any built-in Python data type"""
    value = dbget(key)
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
            value = dtype(eval(value))
        except Exception:
            value = default_value
    else:
        # noinspection PyBroadException
        try:
            value = eval(value)
        except Exception:
            value = None
    return value


def dbval(key, default_value=None):
    """Retrieve a value from the database
    Return value: any built-in Python data type"""
    value = dbget(key)
    from numpy import nan, inf, array  # noqa - for "eval"
    from collections import OrderedDict  # noqa - for "eval"
    # noinspection PyBroadException
    try:
        value = eval(value)
    except Exception:
        value = default_value
    if default_value is not None:
        dtype = type(default_value)
        # noinspection PyBroadException
        try:
            value = dtype(value)
        except Exception:
            value = default_value
    return value


def dbput(key, value):
    """Store a value in the database
    value: string"""
    with lock_of_key(key):
        key_basename = db_basename(key)
        dbread_with_callbacks(key_basename)
        changed = db_get_cache(key) != value
        if changed:
            db_put_cache(key, value)
            dbsave(key_basename)
    if changed:
        handle_key_change(key)


def dbget(key):
    """Retrieve a value from the database
    Return value: string, if not found: empty string"""
    with lock_of_key(key):
        key_basename = db_basename(key)
        dbread_with_callbacks(key_basename)
        value = db_get_cache(key)
    return value


def dbdir(key_starting_name):
    """List of entries names starting with 'key_starting_name'"""
    with lock_of_key(key_starting_name):
        from os.path import isdir
        keys = []
        key_basename = db_basename(key_starting_name)
        pathname = db_file_basename_of_key_basename(key_basename)
        file_basenames = sorted(listdir(pathname)) if isdir(pathname) else []
        file_basenames = [name.replace(db_file_extension, "") for name in file_basenames]
        keys += file_basenames
        dbread_with_callbacks(key_basename)
        prefix = key_starting_name[len(key_basename + "."):]
        if prefix:
            prefix += "."
        subkeys = list(DB[key_basename].keys())
        subkeys = [key for key in subkeys if key.startswith(prefix)]
        subkeys = [key[len(prefix):] for key in subkeys]
        subkeys = [key.split(".")[0] for key in subkeys]
        subkeys = list(set(subkeys))
        keys += subkeys
        keys = sorted(keys)
        return keys


def lock_of_key(key):
    return lock_of_filename(db_filename(key))


def lock_of_filename(filename):
    if filename not in locks:
        with locks_lock:
            if filename not in locks:
                locks[filename] = Lock()
    return locks[filename]


locks = {}
locks_lock = Lock()


def dbmonitor(key, procedure, *args, **kwargs):
    if key not in callbacks:
        callbacks[key] = []
    from handler import Handler
    callback = Handler(procedure, *args, **kwargs)
    if callback not in callbacks[key]:
        callbacks[key].append(callback)
    filename = db_filename(key)
    key_basename = db_basename(key)
    from file_monitor import file_monitor
    file_monitor(filename, "created,modified,deleted,moved", handle_file_change, key_basename)


def dbmonitor_clear(key, procedure, *args, **kwargs):
    if key in callbacks:
        from handler import Handler
        callback = Handler(procedure, *args, **kwargs)
        while callback in callbacks[key]:
            callbacks[key].remove(callback)
        if len(callbacks[key]) == 0:
            del callbacks[key]
    filename = db_filename(key)
    if not any([db_filename(n) == filename for n in list(callbacks)]):
        key_basename = db_basename(key)
        from file_monitor import file_monitor_clear
        file_monitor_clear(filename, "created,modified", handle_file_change, key_basename)


def dbmonitors(key):
    monitors = callbacks.get(key, [])
    return monitors


def handle_file_change(key_basename):
    dbread_with_callbacks(key_basename)


def dbread_with_callbacks(key_basename):
    affected_keys = [key for key in list(callbacks) if db_basename(key) == key_basename]
    # debug("affected_keys = %r" % affected_keys)

    old_values = dict([(key, db_get_cache(key)) for key in affected_keys])
    # debug("old_values = %r" % old_values)

    dbread(key_basename)

    new_values = dict([(key, db_get_cache(key)) for key in affected_keys])
    # debug("new_values = %r" % new_values)

    changed_keys = [key for key in affected_keys if new_values[key] != old_values[key]]
    if changed_keys:
        debug("changed_keys = %r" % changed_keys)

    for key in changed_keys:
        handle_key_change(key)


def handle_key_change(key):
    if key in callbacks:
        for callback in callbacks[key]:
            callback()


callbacks = {}


def listdir(pathname):
    """Directory content, minus "hidden" files"""
    from os import listdir
    filenames = listdir(pathname)
    # Exclude "hidden" files.
    filenames = [f for f in filenames if not f.startswith(".")]
    return filenames


def db_get_cache(key):
    key_basename = db_basename(key)
    resname = db_resname(key)
    value = DB.get(key_basename, {}).get(resname, "")
    return value


def db_put_cache(key, value):
    key_basename = db_basename(key)
    resname = db_resname(key)
    from collections import OrderedDict
    if key_basename not in DB:
        DB[key_basename] = OrderedDict()
    DB[key_basename][resname] = value


def dbread(key_basename):
    from os.path import exists, getmtime
    from time import time
    from collections import OrderedDict
    if key_basename not in DB:
        DB[key_basename] = OrderedDict()
    settings_file = db_filename_of_key_basename(key_basename)
    # Check only every N seconds to avoid excessive system load.
    if settings_file in last_checked and \
            time() - last_checked[settings_file] < 1.0:
        return
    last_checked[settings_file] = time()

    if not exists(settings_file):
        return
    if settings_file in timestamps and \
            getmtime(settings_file) == timestamps[settings_file]:
        return
    try:
        settings = open(settings_file).read()
    except IOError:
        settings = ""
    settings = settings.replace("\r", "")  # Convert DOS to UNIX

    DB[key_basename] = OrderedDict()
    lines = settings.split("\n")
    if len(lines) > 0 and lines[-1] == "":
        lines = lines[0:-1]

    def process(entry):
        if "=" in entry:
            i = entry.index("=")
            resname = entry[:i].strip(" ")
            DB[key_basename][resname] = entry[i + 1:].strip(" ")

    entry = ""
    for line in lines:
        # Continuation of previous entry?
        if entry == "":
            entry = line
        elif entry.endswith("\\"):
            entry += "\n" + line
        elif line.startswith(" "):
            entry += "\n" + line
        elif line.startswith("\t"):
            entry += "\n" + line
        elif "=" not in line:
            entry += "\n" + line
        else:
            process(entry)
            entry = line
    process(entry)

    timestamps[settings_file] = getmtime(settings_file)


def dbsave(key_basename):
    from os.path import exists, getmtime, dirname, basename
    from os import makedirs, umask, chmod, remove, rename
    from tempfile import NamedTemporaryFile
    from time import time
    if key_basename in DB:
        lines = [key + " = " + DB[key_basename][key] for key in DB[key_basename]]
        # lines.sort()
        text = "\n".join(lines)
        umask(0)  # Make sure files and directories are writable to all users.
        settings_file = db_filename_of_key_basename(key_basename)
        settings_directory = dirname(settings_file)
        if not exists(settings_directory):
            try:
                makedirs(settings_directory)
            except Exception as x:
                warning("makedirs(%r): %s" % (settings_directory, x))
        if exists(settings_directory):
            # Make sure that is a non-writeable file already exists, is will be
            # replaced by a writeable file.
            tempfile = NamedTemporaryFile(delete=False, dir=settings_directory,
                                          prefix=basename(settings_file), mode="w+")
            # debug("Writing %r" % tempfile.name)
            tempfile.write(text)
            tempfile.close()
            chmod(tempfile.name, 0o666)
            if exists(settings_file):
                # debug("Removing %r" % settings_file)
                try:
                    remove(settings_file)
                except Exception as x:
                    warning("remove(%r): %s" % (settings_file, x))
            if not exists(settings_file):
                # debug("Renaming %r to %r" % (tempfile.name,settings_file))
                try:
                    rename(tempfile.name, settings_file)
                except Exception as x:
                    warning("rename(%r,%r): %s" % (tempfile.name, settings_file, x))
            if exists(tempfile.name):
                # debug("Removing %r" % tempfile.name)
                try:
                    remove(tempfile.name)
                except Exception as x:
                    warning("remove(%r): %s" % (tempfile.name, x))
        timestamps[settings_file] = getmtime(settings_file)
        last_checked[settings_file] = time()


@cached_function()
def db_filename(key):
    return db_filename_of_key_basename(db_basename(key))


@cached_function()
def db_basename(key):
    keyname = db_keyname(key)
    prefix = db_prefix(key)
    key_basename = prefix + keyname.split(".")[0]
    return key_basename


def db_resname(key):
    key_basename = db_basename(key)
    resname = key[len(key_basename) + 1:]
    return resname


def db_filename_of_key_basename(key_basename):
    return db_file_basename_of_key_basename(key_basename) + db_file_extension


@cached_function()
def db_file_basename_of_key_basename(key_basename):
    basename = normpath(db_dirname(key_basename) + "/" + db_keyname(key_basename))
    return basename


def db_prefix(key):
    prefix = ""
    if key.startswith("local."):
        prefix = "local."
    return prefix


@cached_function()
def db_keyname(key):
    prefix = db_prefix(key)
    keyname = key[len(prefix):]
    return keyname


@cached_function()
def db_dirname(key_basename):
    """Pathname of the file used to store persistent parameters"""
    if db_prefix(key_basename) == "local.":
        path = db_local_settings_dir()
    else:
        path = db_global_settings_dir()
    return path


@cached_function()
def db_global_settings_dir():
    from module_dir import module_dir
    path = module_dir(db_global_settings_dir) + "/settings"
    return path


def db_local_settings_dir():
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


# Needed by "dbread" and "dbsave"
DB = {}
timestamps = {}
last_checked = {}


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
    import logging

    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
    logger.level = logging.DEBUG

    key = "test.test1"
    default_value = ""

    def report():
        logging.info(f"db({key}, {default_value}): {db(key, default_value)!r}")

    dbmonitor(key, report)

    print(f"db({key!r}, {default_value!r})")
    print(f"dbset({key!r}, 'test')")
    print("dbset('test.test1', db('test.test1', '')+'.')")
