"""Caching of Channel Access
Author: Friedrich Schotte
Date created: 2018-10-24
Date last modified: 2019-05-27
Revision comment: Added: CA_history_clear, CA_history_initialized
"""
__version__ = "1.2"

from logging import debug, info, warn, error

from threading import Lock

PV_history = {}
default_max_count = 100


def caget_history(PV_name, timestamp):
    """Value of Channel Access (CA) Process Variable (PV) as a given
    time.
    timestamp: seconds elapsed since 1970-01-01T00:00:00+0000
    return value: None if PV was not connect4ed before the given timestamp
    """
    value = None
    history = CA_history(PV_name)
    for (t, v) in zip(*history):
        if t <= timestamp: value = v
    return value


def caget_timestamp(PV_name, value):
    from numpy import nan
    timestamp = nan
    history = CA_history(PV_name)
    for (t, v) in zip(*history):
        if v == value: timestamp = t
    return timestamp


def CA_history(PV_name):
    """Value of Channel Access (CA) Process Variable (PV)"""
    CA_history_init(PV_name)
    history = PV_history.get(PV_name, ([], []))
    return history


def CA_history_init(PV_name, max_count=None):
    if max_count is not None:
        set_max_count(PV_name, max_count)

    from CA import camonitor
    camonitor(PV_name, callback=update)


def CA_history_initialized(PV_name):
    from CA import camonitors
    return update in camonitors(PV_name)


def CA_history_unsetup(PV_name):
    from CA import camonitor_clear
    camonitor_clear(PV_name, callback=update)


def CA_history_clear(PV_name):
    try:
        del PV_history[PV_name]
    except KeyError:
        pass


def update(PV_name, value, formatted_value, timestamp):
    """Handle Process Variable (PV) update"""
    with PV_history_lock(PV_name):
        max_count = get_max_count(PV_name)
        t, v = PV_history.get(PV_name, ([], []))
        t = (t + [timestamp])[-max_count:]
        v = (v + [value])[-max_count:]
        PV_history[PV_name] = t, v


def get_max_count(PV_name):
    max_count = max_counts.get(PV_name, default_max_count)
    return max_count


def set_max_count(PV_name, max_count):
    max_counts[PV_name] = max_count


max_counts = {}


def PV_history_lock(PV_name):
    if not PV_name in PV_history_locks:
        with PV_history_locks_lock:
            if not PV_name in PV_history_locks:
                PV_history_locks[PV_name] = Lock()
    return PV_history_locks[PV_name]


PV_history_locks = {}
PV_history_locks_lock = Lock()


if __name__ == "__main__":
    from pdb import pm  # for debugging
    import logging  # for debugging
    from time import time  # for timing

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    PV_name = "LASERLAB:TIMING.registers.ch4_trig_count.count"
    from time import time
    from CA import caget

    print('caget(PV_name)')
    print('CA_history_init(PV_name)')
    print('CA_history(PV_name)')
    print('caget_history(PV_name,time())')
