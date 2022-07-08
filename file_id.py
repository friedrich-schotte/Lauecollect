"""
Author: Friedrich Schotte
Date created: 2022-07-02
Date last modified: 2022-07-02
Revision comment:
"""
__version__ = "1.0"

import logging


def file_id(filename):
    file_id = 0
    from os import stat
    try:
        s = stat(filename)
    except OSError:
        s = None
    if s:
        file_id = s.st_ino
    return file_id


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    filename = '//femto/C/All Projects/APS/Instrumentation/Software/Lauecollect/settings/test_settings.txt'
    print("file_id(filename)")
