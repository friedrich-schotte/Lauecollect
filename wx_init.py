#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2008-02-31
Date last modified: 2021-05-31
Revision comment: Cleanup
"""
__version__ = "1.0"

from logging import info


def wx_init():
    try:
        import ctypes

        ctypes.cdll.LoadLibrary("libX11.so").XInitThreads()
        info("XInitThreads called")
    except Exception:
        pass


if __name__ == "__main__":  # for testing
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
