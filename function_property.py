#!/usr/bin/env python
"""
Date created: 2020-11-12
Date last modified: 2020-08-02
Revision comment: calculate_property: Using "self" is first argument
"""
__version__ = "1.0.2"

import logging
from logging import info


def function_property(function, property_name):
    from monitored_property import monitored_property

    def inputs_property(self):
        from reference import reference
        return [reference(self, property_name)]

    def calculate_property(self, filename):  # noqa - Parameter 'self' value is not used
        return function(filename)

    property_object = monitored_property(
        inputs=inputs_property,
        calculate=calculate_property,
    )
    return property_object


if __name__ == "__main__":
    # from pdb import pm
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    from attribute_property import attribute_property
    from reference import reference
    from handler import handler
    from monitors import monitors

    class Test_Object:
        from db_property import db_property
        from file import file as file_object
        filename = db_property("filename", "/tmp/test.txt")
        file = function_property(file_object, "filename")
        file_timestamp = attribute_property("file", "timestamp")
        file_content = attribute_property("file", "content")
        file_size = attribute_property("file", "size")

        def __repr__(self):
            return "self"


    self = Test_Object()

    @handler
    def report(event=None):
        info(f"event={event}")

    monitors(reference(self, "filename")).add(report)
    monitors(reference(self, "file")).add(report)
    monitors(reference(self, "file_timestamp")).add(report)
    monitors(reference(self, "file_content")).add(report)
    monitors(reference(self, "file_size")).add(report)
    print(f"self.filename = {self.filename!r}")
    print(f"self.file_content = {self.file_content!r}")
