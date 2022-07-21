"""
Client side Python interface for Alio IOC

Authors: Friedrich Schotte, Rob Henning
Date created: 2020-02-05
Date last modified: 2022-07-15
Revision comment: Added: VAL, RBV,
    motor_value, motor_command_value,
    formatted_value, formatted_command_value, formatted_values,
    values, ready, wait
"""
__version__ = "1.1"

import logging

from cached_function import cached_function
from PV_record import PV_record
from alias_property import alias_property
from monitored_property import monitored_property
from PV_property import PV_property
from monitored_value_property import monitored_value_property
from numpy import nan


@cached_function()
def alio_scan_client(domain_name): return Alio_Scan_Client(domain_name)


class Alio_Scan_Client(PV_record):
    prefix = "BIOCARS:ALIO_SCAN."

    VAL = PV_property(default_value=[nan, nan, nan])
    RBV = PV_property(default_value=[nan, nan, nan])

    motor_value = alias_property("VAL")
    motor_command_value = alias_property("RBV")

    ready = PV_property(dtype=bool)
    wait = PV_property(dtype=bool)

    values = PV_property(dtype=list)
    formatted_values = PV_property(dtype=list)
    formatted_command_value = PV_property(dtype=str)
    formatted_value = PV_property(dtype=str)

    class CMD:
        prefix = "BIOCARS:ALIO_SCAN.CMD."
        VAL = PV_property("VAL", "")
        RBV = PV_property("RBV", "")
        choices = [
            "scan1D_stepping",
            "scan1D_flythru",
            "stepping-24-100",
            "flythru-48-100",
        ]
        values = monitored_value_property(choices)
        command_value = alias_property("VAL")

        @monitored_property
        def value(self, RBV): return RBV

        @value.setter
        def value(self, value): self.VAL = value

        def __repr__(self): return "Alio.cmd"

    cmd = CMD()

    class ACQ:
        prefix = "BIOCARS:ALIO_SCAN.ACQ."
        VAL = PV_property("VAL", False)
        RBV = PV_property("RBV", False)
        command_value = VAL

        @monitored_property
        def value(self, RBV): return RBV

        @value.setter
        def value(self, value): self.VAL = value

        def __repr__(self): return "Alio.acq"

    acq = ACQ()
    acquiring = acq

    class PTS:
        prefix = "BIOCARS:ALIO_SCAN.PTS."
        VAL = PV_property("VAL", [])
        DESC = PV_property("DESC", [])

        @monitored_property
        def value(self, VAL, DESC):
            n_dim = len(DESC)
            n_pts = len(VAL) / n_dim if n_dim != 0 else 0
            from numpy import array
            value = array(VAL[0:n_pts * n_dim]).reshape((n_pts, n_dim))
            return value

        name = DESC

        def __repr__(self): return "Alio.pts"

    pts = PTS()
    scan_points = pts


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    domain_name = "BioCARS"
    self = alio_scan_client(domain_name)

    from handler import handler as _handler

    @_handler
    def report(event):
        logging.info(f"{event}")
