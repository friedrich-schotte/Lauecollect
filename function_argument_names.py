"""
Author: Friedrich Schotte
Date created: 2022-05-01
Date last modified: 2022-05-01
Revision comment:
"""
__version__ = "1.0"
 
import logging


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)


def function_argument_names(f):
    from inspect import signature
    names = list(signature(f).parameters)
    if names[0:1] == ["self"]:
        names = names[1:]
    return names