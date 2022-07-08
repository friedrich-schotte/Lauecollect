"""
Author: Friedrich Schotte
Date created: 2022-05-24
Date last modified: 2022-05-24
Revision comment:
"""
__version__ = "1.0"

import logging


def start_thread(proc, *args, **kwargs):
    from threading import Thread
    timer = Thread(target=proc, args=args, kwargs=kwargs, daemon=True)
    timer.start()


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    start_thread(logging.info, f"hello")
