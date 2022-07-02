"""
Author: Friedrich Schotte
Date created: 2022-05-24
Date last modified: 2022-05-24
Revision comment:
"""
__version__ = "1.0"

import logging


def schedule(time, proc, *args, **kwargs):
    from time import time as now
    from threading import Timer
    delay = max(time - now(), 0)
    timer = Timer(delay, proc, args=args, kwargs=kwargs)
    timer.start()


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from time import time
    from time_string import date_time
    schedule(time()+3, logging.info, f"Scheduled at {date_time(time())}")
