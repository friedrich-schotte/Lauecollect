"""
Author: Friedrich Schotte
Date created: 2022-05-04
Date last modified: 2022-05-04
Revision comment:
"""
__version__ = "1.0"
 
import logging


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)


def list_length(values):
    if type(values) is str:
        length = 1
    else:
        try:
            length = len(values)
        except TypeError:
            length = 1
    return length