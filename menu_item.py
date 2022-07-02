"""
Author: Friedrich Schotte
Date created: 2022-06-01
Date last modified: 2022-06-01
Revision comment:
"""
__version__ = "1.0"

import logging


class Menu_Item:
    def __init__(self, label, handler, enabled=True):
        self.label = label
        self.handler = handler
        self.enabled = enabled


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
