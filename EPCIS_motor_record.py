"""
Prototype for an EPICS motor record to be used as base class.
Documentation: http://aps.anl.gov/bcda/synApps/motor/R6-7/motorRecord.html

Author: Friedrich Schotte
Date created: 2013-10-29
Date last_modified: 2021-01-08
Revision comment: Cleanup
"""

__version__ = "1.0.1"

from logging import debug


class motor_record(object):
    """Prototype for an EPICS motor record to be used as base class"""

    def __init__(self, record_name=""):
        if record_name != "":
            from CAServer import register_object
            register_object(self, record_name)

    def get_VAL(self):
        """Command position"""
        return self.__VAL__

    def set_VAL(self, value):
        self.__VAL__ = value

    VAL = property(get_VAL, set_VAL)

    __VAL__ = 0.0

    def get_RBV(self):
        """Actual position"""
        return self.VAL

    RBV = property(get_RBV)

    EGU = "mm"
    DESC = "Test"
    PREC = 4  # number of digits
    DIR = 0  # positive or negative user vs dial direction

    def get_DMOV(self):
        """Done moving: Has the motor reached the set point within
        tolerance?
        For scans, to provide feedback whether the temperature 'motor'
        is still 'moving'"""
        return 0

    DMOV = property(get_DMOV)

    def get_STOP(self):
        return 0

    def set_STOP(self, value):
        """If value = True, cancel the current move."""
        if value == 1:
            pass

    STOP = property(get_STOP, set_STOP)

    TWV = 1.0  # Tweak value (step size)

    def get_TWR(self):
        return 0

    def set_TWR(self, value):
        debug(f"{value}")
        if value != 0:
            self.VAL -= self.TWV

    TWR = property(get_TWR, set_TWR)

    def get_TWF(self):
        return 0

    def set_TWF(self, value):
        if value != 0:
            self.VAL += self.TWV

    TWF = property(get_TWF, set_TWF)

    PCOF = 0.0
    ICOF = 0.0
    DCOF = 0.0


if __name__ == "__main__":
    # Control panel: medm -x -attach -macro P=NIH:,M=TEST motorx.adl
    import logging
    logging.getLogger("EPICS_CA").level = logging.DEBUG

    self = motor_record("14IDB:SAMPLEX")
