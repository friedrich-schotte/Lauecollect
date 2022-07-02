"""
Client side Python interface for Alio IOC

Authors: Friedrich Schotte, Rob Henning
Date created: 2020-02-05
Date last modified: 2020-11-16
Revision comment: Refactored using monitored_property calculate=
"""
__version__ = "1.0.5"

from logging import info

from monitored_property import monitored_property
from reference import reference


class Alio:
    prefix = "14IDB:ALIO."

    class CMD(object):
        prefix = "14IDB:ALIO.CMD."
        from PV_property import PV_property
        VAL = PV_property("VAL", "")
        RBV = PV_property("RBV", "")
        choices = [
            "scan1D_stepping",
            "scan1D_flythru",
            "stepping-24-100",
            "flythru-48-100",
        ]
        command_value = VAL

        def inputs_value(self): return [reference(self, "RBV")]

        def calculate_value(self, RBV): return RBV

        def set_value(self, value): self.VAL = value

        value = monitored_property(
            inputs=inputs_value,
            calculate=calculate_value,
            fset=set_value,
        )

        def __repr__(self): return "Alio.cmd"

    cmd = CMD()

    class ACQ(object):
        prefix = "14IDB:ALIO.ACQ."
        from PV_property import PV_property
        VAL = PV_property("VAL", False)
        RBV = PV_property("RBV", False)
        command_value = VAL

        def inputs_value(self): return [reference(self, "RBV")]

        def calculate_value(self, RBV): return RBV

        def set_value(self, value): self.VAL = value

        value = monitored_property(
            inputs=inputs_value,
            calculate=calculate_value,
            fset=set_value,
        )

        def __repr__(self): return "Alio.acq"

    acq = ACQ()
    acquiring = acq

    class PTS(object):
        prefix = "14IDB:ALIO.PTS."
        from PV_property import PV_property
        VAL = PV_property("VAL", [])
        DESC = PV_property("DESC", [])

        def inputs_value(self):
            return [
                reference(self, "VAL"),
                reference(self, "DESC"),
            ]

        def calculate_value(self, VAL, DESC):
            n_dim = len(DESC)
            n_pts = len(VAL) / n_dim if n_dim != 0 else 0
            from numpy import array
            value = array(VAL[0:n_pts * n_dim]).reshape((n_pts, n_dim))
            return value

        value = monitored_property(
            inputs=inputs_value,
            calculate=calculate_value,
        )

        name = DESC

        def __repr__(self): return "Alio.pts"

    pts = PTS()
    scan_points = pts


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    # print("cainfo(%r)" % (prefix+'CMD.VAL'))
    # print("cainfo(%r)" % (prefix+'CMD.RBV'))
    print("Alio.cmd.command_value = 'flythru-48-100'")
    print("Alio.cmd.value")
    print("Alio.scan_points.value")
    print("Alio.scan_points.name")
    print("Alio.acq.command_value = True")
    print("Alio.acq.value")
    print("")


    def report(obj, name): info("%r.%s = %r" % (obj, name, getattr(obj, name)))


    print('from monitor import monitor; monitor(Alio.cmd,"value",report,Alio.cmd,"value")')
