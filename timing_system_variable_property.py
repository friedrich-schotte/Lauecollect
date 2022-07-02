"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-05
Revision comment:
"""
__version__ = "1.0"


def variable_property(name, *args, **kwargs):
    """A property object that is a timing register"""

    def get(self):
        from timing_system_variable import Variable
        return Variable(self, name, *args, **kwargs)

    return property(get)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
