"""
Author: Friedrich Schotte
Date created: 2022-08-17
Date last modified: 2022-08-17
Revision comment:
"""
__version__ = "1.0"

import logging
from threading import Lock


def retry_setattr(obj, name, value):
    from time import sleep

    max_write_attempts = 10
    max_read_attempts = 2
    read_wait_time = 0.25

    with lock(obj, name):
        write_attempt = 0
        read_attempt = 0

        read_back_value = getattr(obj, name)
        if read_back_value != value:
            # logging.debug(f"{obj}.{name} = {value!r}")
            setattr(obj, name, value)
            write_attempt += 1
            read_back_value = getattr(obj, name)
            read_attempt += 1
            while read_back_value != value and write_attempt < max_write_attempts:
                while read_back_value != value and read_attempt < max_read_attempts:
                    logging.debug(f"Write {write_attempt}/{max_write_attempts}, read {read_attempt}/{max_read_attempts}: {obj}.{name}: {read_back_value!r} instead of {value!r}")
                    sleep(read_wait_time)
                    read_back_value = getattr(obj, name)
                    read_attempt += 1
                if read_back_value != value:
                    logging.debug(f"Write {write_attempt}/{max_write_attempts}, read {read_attempt}/{max_read_attempts}: {obj}.{name}: {read_back_value!r} instead of {value!r}")
                    logging.debug(f"Write {write_attempt}/{max_write_attempts}: {obj}.{name} = {value!r}")
                    setattr(obj, name, value)
                    write_attempt += 1
                    read_attempt = 0
                read_back_value = getattr(obj, name)
                read_attempt += 1
            if read_back_value == value:
                if write_attempt > 1 or read_attempt > 1:
                    logging.debug(f"Succeeded at write {write_attempt}/{max_write_attempts}, read {read_attempt}/{max_read_attempts}: {obj}.{name} = {read_back_value!r} (expecting {value!r})")
            else:
                logging.debug(f"Giving up at write {write_attempt}/{max_write_attempts}, read {read_attempt}/{max_read_attempts}: {obj}.{name} = {read_back_value!r} instead of {value!r}")


def lock(obj, name):
    if not (obj, name) in locks:
        with global_lock:
            if not (obj, name) in locks:
                locks[obj, name] = Lock()
    lock = locks[obj, name]
    return lock


global_lock = Lock()
locks = {}


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
