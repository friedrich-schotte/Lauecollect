"""
Remote control of thermoelectric chiller by Solid State Cooling Systems,
www.sscooling.com, via RS-323 interface
Model: Oasis 160

Authors: Friedrich Schotte, Nara Dashdorj, Valentyn Stadnytskyi
Date created: 2009-05-28
Date last modified: 2021-11-29
Revision comment: Issue: command_value is None, if IOC not running
"""
__version__ = "3.0.2"

from EPICS_motor import EPICS_motor


def alias(name):
    """Make property given by name be known under a different name"""

    def fget(self): return getattr(self, name)

    def fset(self, value): setattr(self, name, value)

    return property(fget, fset)


class OasisChiller(EPICS_motor):
    """Thermoelectric water cooler"""
    # command_value = alias("VAL")  # EPICS_motor.command_value not changeable
    port_name = alias("COMM")
    prefix = alias("__prefix__")  # EPICS_motor.prefix not changeable
    nominal_temperature = alias("VAL")  # for backward compatibility
    actual_temperature = alias("RBV")  # for backward compatibility


oasis_chiller = OasisChiller(prefix="NIH:CHILLER", name="oasis_chiller")
chiller = oasis_chiller  # for backward compatibility


if __name__ == "__main__":
    import logging

    # CAServer.DEBUG = True
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=msg_format)

    self = oasis_chiller  # for debugging
    print("self.value")
    print("self.fault_code")
    print("self.faults")
