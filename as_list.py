"""
Author: Friedrich Schotte
Date created: 2022-04-26
Date last modified: 2022-04-26
Revision comment:
"""
__version__ = "1.0"


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)


def as_list(x):
    if not hasattr(x, "__len__") or isinstance(x, str):
        x = [x]
    return x