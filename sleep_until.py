"""
Author: Friedrich Schotte
Date created: 2022-05-24
Date last modified: 2022-05-24
Revision comment:
"""
__version__ = "1.0"

import logging


def sleep_until(time):
    from time import time as now, sleep
    delay = time - now()
    if delay > 0:
        sleep(delay)


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from time import time
    print("Started...")
    sleep_until(time()+1)
    print("Done.")
