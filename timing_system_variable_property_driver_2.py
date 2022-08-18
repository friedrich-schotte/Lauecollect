"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-07-31
Revision comment:
"""
__version__ = "2.0"


def timing_system_variable_property_driver(name, *args, **kwargs):
    """A property object that is a timing register"""

    def get(self):
        from timing_system_variable_driver_2 import Timing_System_Variable
        return Timing_System_Variable(self, name, *args, **kwargs)

    return property(get)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
