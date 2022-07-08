"""
Author: Friedrich Schotte
Date created: 2022-05-24
Date last modified: 2022-05-24
Revision comment:
"""
__version__ = "1.0"

import logging


def start_delayed(delay, proc, *args, **kwargs):
    from threading import Timer
    timer = Timer(delay, proc, args=args, kwargs=kwargs)
    timer.start()


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from time import time
    from date_time import date_time

    start_delayed(3.0, logging.info, f"Scheduled at {date_time(time())}")
