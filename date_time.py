"""
Author: Friedrich Schotte
Date created: 2022-07-03
Date last modified: 2022-07-05
Revision comment:
"""
__version__ = "1.0"
 
import logging

from cached_function import cached_function


def date_time(seconds):
    """Date and time as formatted ASCII text, precise to 1 us
    seconds: time elapsed since 1 Jan 1970 00:00:00 UTC
    e.g. '2016-02-01 19:14:31.707016-0800' """
    from datetime import datetime
    try:
        date_time = datetime.fromtimestamp(seconds, timezone()).strftime("%Y-%m-%d %H:%M:%S.%f%z")
    except ValueError:
        date_time = ""
    return date_time


@cached_function()
def timezone():
    from tzlocal import get_localzone
    return get_localzone()


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
