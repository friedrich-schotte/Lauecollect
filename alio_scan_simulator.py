"""
Author: Friedrich Schotte
Date created: 2022-07-09
Date last modified: 2022-07-09
Revision comment:
"""
__version__ = "1.0"

import logging

from cached_function import cached_function

from instance_property import instance_property
from alias_property import alias_property
from db_property import db_property
from monitored_property import monitored_property


@cached_function()
def alio_scan_simulator(domain_name): return Alio_Scan_Simulator(domain_name)


class Alio_Scan_Simulator:
    def __init__(self, domain_name):
        self.domain_name = domain_name

    def __repr__(self):
        return f"{self.class_name}({self.domain_name!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def db_name(self): return f"domains/{self.domain_name}/{self.class_name}"

    ready = db_property("ready", False, local=True)
    wait = db_property("wait", False)

    VAL = db_property("VAL", [0.0, 0.0, 0.0], local=True)

    @monitored_property
    def RBV(self, VAL): return VAL

    @RBV.setter
    def RBV(self, value): self.VAL = value

    command_value = alias_property("VAL")
    value = alias_property("RBV")
    motor_value = alias_property("VAL")
    motor_command_value = alias_property("RBV")

    @monitored_property
    def formatted_value(self, value):
        return self.format(value)

    def format(self, value):
        return str(value).strip("[]")

    @monitored_property
    def formatted_command_value(self, command_value):
        return self.format(command_value)

    @monitored_property
    def formatted_values(self, values):
        return [self.format(value) for value in values]

    values = alias_property("pts.value")

    @instance_property
    class cmd:
        def __init__(self, parent): self.parent = parent

        def __repr__(self): return f"{self.parent}.{self.class_name}"

        @property
        def db_name(self): return f"{self.parent.db_name}/{self.class_name}"

        @property
        def class_name(self):
            return type(self).__name__.lower()

        VAL = db_property("VAL", "", local=True)
        command_value = alias_property("VAL")

        choices = [
            "scan1D_stepping",
            "scan1D_flythru",
            "stepping-24-100",
            "flythru-48-100",
        ]

        @monitored_property
        def RBV(self, VAL): return VAL

        @monitored_property
        def value(self, RBV): return RBV

        @value.setter
        def value(self, value): self.VAL = value

        @instance_property
        class acq:
            def __init__(self, parent): self.parent = parent

            def __repr__(self): return f"{self.parent}.{self.class_name}"

            @property
            def db_name(self): return f"{self.parent.db_name}/{self.class_name}"

            @property
            def class_name(self):
                return type(self).__name__.lower()

            VAL = db_property("VAL", False, local=True)
            command_value = alias_property("VAL")

            @monitored_property
            def RBV(self, VAL): return VAL

            @monitored_property
            def value(self, RBV): return RBV

            @value.setter
            def value(self, value): self.VAL = value

    @instance_property
    class pts:
        def __init__(self, parent): self.parent = parent

        def __repr__(self): return f"{self.parent}.{self.class_name}"

        @property
        def db_name(self): return f"{self.parent.db_name}/{self.class_name}"

        @property
        def class_name(self):
            return type(self).__name__.lower()

        VAL = db_property("VAL", [], local=True)
        DESC = db_property("DESC", [], local=True)
        name = alias_property("DESC")

        @monitored_property
        def value(self, VAL, DESC):
            n_dim = len(DESC)
            n_pts = len(VAL) / n_dim if n_dim != 0 else 0
            from numpy import array
            value = array(VAL[0:n_pts * n_dim]).reshape((n_pts, n_dim))
            return value


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = alio_scan_simulator(domain_name)
