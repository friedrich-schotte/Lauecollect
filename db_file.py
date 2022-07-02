"""
Author: Friedrich Schotte
Date created: 2022-06-25
Date last modified: 2022-06-25
Revision comment:
"""
__version__ = "1.0"

import logging
from cached_function import cached_function
from alias_property import alias_property
from monitored_property import monitored_property


@cached_function()
def db_file(filename):
    return DB_File(filename)


class DB_File:
    def __init__(self, filename):
        from file import file
        from threading import Lock
        self.file = file(filename)
        self.lock = Lock()

    def __repr__(self):
        return f"{self.class_name}({self.filename!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    content = alias_property("file.content")
    filename = alias_property("file.name")

    @monitored_property
    def dictionary(self, content):
        content = content.replace("\r", "")  # Convert DOS to UNIX
        lines = content.split("\n")
        if len(lines) > 0 and lines[-1] == "":
            lines = lines[0:-1]

        new_dictionary = {}

        def process(entry):
            if "=" in entry:
                i = entry.index("=")
                key = entry[:i].strip(" ")
                value = entry[i + 1:].strip(" ")
                new_dictionary[key] = value

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

        return new_dictionary

    @dictionary.setter
    def dictionary(self, new_dictionary):
        lines = [key + " = " + new_dictionary[key] for key in new_dictionary]
        # lines.sort()
        content = "\n".join(lines)
        self.content = content

    def __getitem__(self, item):
        return self.dictionary[item]

    def __setitem__(self, item, value):
        if item not in self.dictionary or self.dictionary[item] != value:
            with self.lock:
                if item not in self.dictionary or self.dictionary[item] != value:
                    new_dictionary = dict(self.dictionary)
                    new_dictionary[item] = value
                    self.dictionary = new_dictionary

    def keys(self):
        return self.dictionary.keys()


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    filename = '/Mirror/femto/C/All Projects/APS/Instrumentation/Software/Lauecollect/settings/test_settings.txt'
    self = db_file(filename)

    from handler import handler as _handler


    @_handler
    def report(event):
        logging.info(f"{event}")


    from reference import reference
    reference(self, "content").monitors.add(report)
    reference(self, "dictionary").monitors.add(report)
