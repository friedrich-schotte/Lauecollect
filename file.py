#!/usr/bin/env python
"""
Date created: 2020-10-29
Date last modified: 2022-06-30
Revision comment: Fixed: Issue: no event generated when file moved or renamed
"""
__version__ = "1.0.10"

import logging
from cached_function import cached_function


@cached_function()
def file(name):
    return File(name)


class Content_Property(property):
    def __init__(self):
        property.__init__(self, fget=self.get_property, fset=self.set_property)

    def __repr__(self):
        return f"{self.class_name}()"

    def get_property(self, file):
        content = file_content(file.name)
        # debug(f"{file.basename}: {line_count(content)} lines")
        return content

    def set_property(self, file, content):
        if content != file_content(file.name):
            set_file_content(content, file.name)
            # debug(f"{file.basename}: {line_count(content)} lines")
            self.handle_change(file)

    def monitors(self, file):
        attributes_cache = self.attributes_cache(file)
        if "monitors" not in attributes_cache:
            from event_handlers import Event_Handlers
            from functools import partial
            attributes_cache["monitors"] = Event_Handlers(
                setup=partial(self.monitor_setup, file),
                cleanup=partial(self.monitor_cleanup, file),
            )
        return attributes_cache["monitors"]

    def attributes_cache(self, file):
        if not hasattr(file, self.attributes_cache_name):
            setattr(file, self.attributes_cache_name, {})
        attributes_cache = getattr(file, self.attributes_cache_name)
        return attributes_cache

    @property
    def attributes_cache_name(self):
        return f"__{self.class_name}__".lower()

    @property
    def class_name(self):
        return type(self).__name__

    def monitor_setup(self, file):
        # debug(f"Starting monitoring of {file}")
        from file_monitor import file_monitor
        file_monitor(file.name, "created,modified,deleted,moved", self.handle_change, file)

    def monitor_cleanup(self, file):
        # debug(f"Stopping monitoring of {file}")
        from file_monitor import file_monitor_clear
        file_monitor_clear(file.name, "created,modified,deleted,moved", self.handle_change, file)

    def handle_change(self, file):
        import time
        time = file.timestamp if file.timestamp else time.time()
        value = self.get_property(file)
        from reference import reference
        event_reference = reference(file, property_name(file, self))
        from event import event
        event = event(time=time, value=value, reference=event_reference)
        self.monitors(file).call(event=event)


class Timestamp_Property(Content_Property):
    def get_property(self, file):
        return timestamp(file.name)

    def set_property(self, file, time):
        set_timestamp(file.name, time)


class Size_Property(Content_Property):
    def get_property(self, file):
        return size(file.name)

    def set_property(self, file, new_size):
        resize(file.name, new_size)


class File(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    content = Content_Property()
    timestamp = Timestamp_Property()
    size = Size_Property()

    @property
    def basename(self):
        from os.path import basename
        return basename(self.name)


def file_content(filename):
    try:
        return open(filename).read()
    except OSError:
        return ""


def set_file_content(content, filename):
    if content:
        write_file(content, filename)
    else:
        remove_file(filename)


def write_file(content, filename):
    from os.path import exists, dirname
    from os import makedirs
    directory = dirname(filename)
    try:
        makedirs(directory)
    except Exception as x:
        if not exists(directory):
            logging.error("%s: %s" % (directory, x))
    if exists(directory):
        try:
            open(filename, "w").write(content)
        except Exception as x:
            logging.error("%s: %.80r, %s" % (filename, content, x))


def remove_file(filename):
    from os.path import exists
    if exists(filename):
        from os import remove
        try:
            remove(filename)
        except Exception as x:
            logging.error("%s: %s" % (filename, x))


def create_file(filename):
    from os.path import exists, dirname
    from os import makedirs
    directory = dirname(filename)
    try:
        makedirs(directory)
    except Exception as x:
        if not exists(directory):
            logging.error("%s: %s" % (directory, x))
    if exists(directory) and not exists(filename):
        try:
            open(filename, "a")
        except Exception as x:
            logging.error("%s: %s" % (filename, x))


def timestamp(filename):
    from os.path import getmtime
    try:
        time = getmtime(filename)
    except OSError:
        time = 0
    return time


def set_timestamp(filename, time):
    create_file(filename)
    import os
    try:
        os.utime(filename, (-1, time))
    except (ImportError, OSError) as x:
        logging.error("%s: utime: %s" % (filename, x))


def size(filename):
    from os.path import getsize
    try:
        size = getsize(filename)
    except OSError:
        size = 0
    return size


def resize(filename, new_size):
    if new_size != size(filename):
        create_file(filename)
        try:
            open(filename, "a").truncate(new_size)
        except OSError as x:
            logging.error("%s: truncate: %s" % (filename, x))


def property_name(obj, property_object):
    property_name = ""
    for name, value in type(obj).__dict__.items():
        if value is property_object:
            property_name = name
    return property_name


def line_count(text):
    return text.count('\n')


if __name__ == "__main__":
    msg_format = "%(asctime)s: %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
    logging.getLogger("file_monitor").level = logging.DEBUG

    from tempfile import gettempdir
    from handler import handler as _handler
    from reference import reference as _reference
    from os import makedirs
    from os.path import isdir

    temp_dir = gettempdir() + "/test_dir"
    if not isdir(temp_dir):
        makedirs(temp_dir)

    class Example:
        from monitored_value_property import monitored_value_property
        from function_property import function_property
        from attribute_property import attribute_property

        file_name = monitored_value_property(temp_dir + "/test.txt")
        file = function_property(file, "file_name")
        file_content = attribute_property("file", "content")

    example = Example()

    @_handler
    def report(event=None): logging.info(f"event={event!r:.255}")

    @_handler
    def report_length(event=None): logging.info("%r" % event.value.count('\n'))

    # _reference(example, "file_content").monitors.add(report_length)
    # print('_reference(example, "file_content").monitors.remove(report_length)')
    # print('example.file_content = ""')
    # print('example.file_content += "test\\n"')
    # print('for i in range(100): example.file_content += "%d\\n" % i')
    # print('open(example.file_name,"a").write("test\\n")')

    # filename = '/Mirror/femto/C/All Projects/APS/Instrumentation/Software/Lauecollect/settings/test_settings.txt'
    filename = '/tmp/test1/test2/test3.txt'
    self = file(filename)
    _reference(self, "content").monitors.add(report)
