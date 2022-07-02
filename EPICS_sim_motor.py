"""EPICS IOC interface for software simulated motor
Author: Friedrich Schotte
Date created: 2015-12-08
Date last modified: 2021-11-23
Revision comment: Cleanup
"""
__version__ = "1.0.1"

from sim_motor import sim_motor


class EPICS_sim_motor(sim_motor):
    """"""
    VAL = sim_motor.command_value
    RBV = sim_motor.value
    DVAL = sim_motor.command_dial
    DRBV = sim_motor.dial
    HLM = sim_motor.max
    LLM = sim_motor.min
    DHLM = sim_motor.max_dial
    DLLM = sim_motor.min_dial

    def get_DESC(self): return self.name

    def set_DESC(self, value): self.name = value

    DESC = property(get_DESC, set_DESC)

    EGU = sim_motor.unit

    def get_DMOV(self): return not self.moving

    def set_DMOV(self, value): self.moving = not value

    DMOV = property(get_DMOV, set_DMOV)

    def get_STOP(self): return not self.moving

    def set_STOP(self, value): self.moving = not value

    STOP = property(get_STOP, set_STOP)

    VELO = sim_motor.speed
    DIR = sim_motor.sign
    OFF = sim_motor.offset

    def get_CNEN(self): return True

    def set_CNEN(self, value): pass

    CNEN = property(get_CNEN, set_CNEN)

    def get_HOMF(self): return False

    def set_HOMF(self, value): pass

    HOMF = property(get_HOMF, set_HOMF)

    def get_HOMR(self): return False

    def set_HOMR(self, value): pass

    HOMR = property(get_HOMR, set_HOMR)

    def get_MSTA(self):
        homed = True
        status = homed << 15
        return status

    def set_MSTA(self, value):
        pass

    MSTA = property(get_MSTA, set_MSTA)


if __name__ == "__main__":
    from CAServer import register_object
    # from CA import caget, caput, Record
    from EPICS_motor import EPICS_motor

    # import logging
    # logging.basicConfig(level=logging.DEBUG,format="%(asctime): %(message)s")
    m = EPICS_sim_motor()
    self = m  # for debugging
    register_object(m, "NIH:m")
    M = EPICS_motor("NIH:m")
