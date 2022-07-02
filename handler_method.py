"""
Author: Friedrich Schotte
Date created: 2022-05-08
Date last modified: 2022-05-08
Revision comment:
"""
__version__ = "1.0"

import logging


class handler_method(property):
    def __init__(self, method_function):
        self.method_function = method_function
        property.__init__(self, self.get_property)

    def get_property(self, instance):
        from handler import handler
        bound_method = self.method_function.__get__(instance)
        return handler(bound_method)


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
