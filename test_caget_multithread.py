"""
Date created: 2020-04-21
Date last modified: 2020-04-21
Revision comment:
"""
__version__ = "1.0"

from logging import info
from threading import Thread
from EPICS_CA.CA import caget

PVs = [
    'NIH:CHILLER.VAL',
    'NIH:CHILLER.VALs',
    'NIH:CHILLER.VAL_choices',
    'NIH:CHILLER.RBV',
    'NIH:CHILLER.faults',
    'NIH:CHILLER.faultss',
    'NIH:CHILLER.faults_choices',
]


def report(PV):
    info(f"{PV} Getting...")
    value = caget(PV)
    info(f"{PV}: {value!r}")


def test():
    for PV in PVs:
        thread = Thread(target=report, args=(PV,))
        thread.start()
        info(f"{PV} Started")


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
    test()
