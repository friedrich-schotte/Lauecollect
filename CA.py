"""
Date created: 2019-09-17
Date last modified: 2020-10-28
Revision comment: Issue: pylint: Cannot find reference 'camonitors' in "CA.py"
"""
__version__ = "2.2.1"

from logging import error

from EPICS_CA.CA import (
    PV, pv, caget, caput, cainfo, camonitor, camonitor_clear, camonitors,
    Record, cawait,
    camonitor_handler, camonitor_handlers, camonitor_clear_handler,
)


def use(package):
    global PV, pv, caget, caput, cainfo, camonitor, camonitor_clear
    global Record, cawait
    global camonitor_handler, camonitor_handlers, camonitor_clear_handler
    global package_name

    if package == "EPICS_CA":
        from EPICS_CA.CA import (
            PV, pv, caget, caput, cainfo, camonitor, camonitor_clear, camonitors,
            Record, cawait,
            camonitor_handler, camonitor_handlers, camonitor_clear_handler,
        )
    elif package == "pyepics":
        from epics import camonitor, camonitor_clear, cainfo, PV

        def caget(PV_name, timeout=1.0):
            import epics
            return epics.caget(PV_name, timeout)

        def caput(PV_name, value, wait=False, timeout=1):
            import epics
            return epics.caput(PV_name, value, wait=wait, timeout=timeout)
    elif package == "caproto":
        def caget(PV_name, timeout=1):
            import caproto.sync.client
            try:
                value = caproto.sync.client.read(PV_name, timeout=timeout).data
            except caproto.CaprotoTimeoutError:
                value = None
            else:
                if len(value) == 1:
                    value = value[0]
            return value

        def caput(PV_name, value, wait=False, timeout=1):
            import caproto.sync.client
            try:
                caproto.sync.client.write(PV_name, value, timeout=timeout, notify=wait)
            except caproto.CaprotoTimeoutError:
                pass
    else:
        error("expecting one of 'EPICS_CA', 'pyepics', 'caproto'")

    package_name = package


use("EPICS_CA")
# use("pyepics")
# use("caproto")
