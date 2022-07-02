"""
Author: Friedrich Schotte
Date created: 2022-04-29
Date last modified: 2022-04-29
Revision comment:
"""
__version__ = "1.0"

import logging


class type_property(property):
    def __init__(self, property_type):
        self.property_type = property_type
        property.__init__(self, self.get_property)

    def get_property(self, instance):
        return self.property_type(instance)


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
