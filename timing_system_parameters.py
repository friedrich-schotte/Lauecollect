"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-05
Revision comment:
"""
__version__ = "1.0"


class Parameters(object):
    def __init__(self, timing_system):
        self.__timing_system__ = timing_system

    def __getattr__(self, name):
        """The value of a parameter stored on the timing system"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute wasn't found the usual ways.
        # __members__ is used for auto-completion, browsing and "dir".
        if name == "__members__":
            return self.__timing_system__.parameter_names

        if name.startswith("__") and name.endswith("__"):
            raise RuntimeError("attribute %r not found" % name)
        return self.__timing_system__.parameter(name)

    def __setattr__(self, name, value):
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self, name, value)
        else:
            self.__timing_system__.set_parameter(name, value)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
