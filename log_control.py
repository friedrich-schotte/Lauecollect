#!/usr/bin/env python
"""
For log messages

Authors: Friedrich Schotte
Date created: 2020-10-07
Date last modified: 2020-11-16
Revision comment: Fixed: Issue:
    'Log_Control' object has no attribute 'clear'

"""
__version__ = "1.3.4"

from logging import warning, info

from cached_function import cached_function
from monitored_property import monitored_property
from alias_property import alias_property
from function_property import function_property
from attribute_property import attribute_property
from db_property import db_property
from handler import handler
from monitors import monitors
from reference import reference


@cached_function()
def log_control(name):
    return Log_Control(name)


class Log_Control(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        name = type(self).__name__.lower()
        return "%s(%r)" % (name, self.name)

    levels = ["DEBUG", "INFO", "WARNING", "ERROR", "FATAL"]
    level = db_property("level", "DEBUG")

    @property
    def db_name(self):
        return "Log_Control/%s" % self.name

    def calculate_text(self, filename, _file_timestamp, level):
        max_length = 1000000
        text = read_end(filename, max_length)
        lines = text.splitlines()
        if len(text) == max_length:
            lines = lines[1:]

        words_to_filter_out = []
        if level in self.levels:
            i = self.levels.index(level)
            words_to_filter_out = self.levels[0:i]
        if words_to_filter_out:
            for word in words_to_filter_out:
                lines = [line for line in lines if word not in line]

        max_line_count = 1000
        lines = lines[-max_line_count:]

        text = "\n".join(lines) + "\n"
        return text

    def inputs_text(self):
        return [
            reference(self, "filename"),
            reference(self, "file_timestamp"),
            reference(self, "level"),
        ]

    text = monitored_property(
        calculate=calculate_text,
        inputs=inputs_text,
    )

    filename = alias_property("logger.filename")
    from file import file as file_object
    file = function_property(file_object, "filename")
    file_timestamp = attribute_property("file", "timestamp")
    file_content = attribute_property("file", "content")
    file_size = attribute_property("file", "size")
    clear_enabled = function_property(bool, "file_size")

    def clear(self):
        self.file_size = 0

    @property
    def logger(self):
        from redirect import logger
        return logger(self.name)


def read_end(filename, length):
    """Read the last n=length bytes of a file"""
    value = ""
    from os.path import exists
    if exists(filename):
        try:
            from os.path import getsize
            file_size = getsize(filename)
            start_index = max(file_size - length, 0)
            length = file_size - start_index
            with open(filename) as file:
                file.seek(start_index)
                value = file.read(length)
        except Exception as x:
            warning("%s: %s" % (filename, x))
    return value


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = log_control("LaserLab.acquisition_IOC")

    @handler
    def report(event):
        info("event=%.256r" % event)

    monitors(reference(self, "level")).add(report)
    monitors(reference(self, "filename")).add(report)
    monitors(reference(self, "file_timestamp")).add(report)
    monitors(reference(self, "text")).add(report)
    monitors(reference(self, "clear_enabled")).add(report)
