"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-07-31
Revision comment: Cleanup: docstring formatting; logging; f-string; Added Example
"""
__version__ = "1.0.1"

import logging

from timing_system_parameter import Parameter


class Variable(object):
    """Software-defined parameter controlling the timing,
    not associated with any hardware register in the FPGA"""

    def __init__(self, timing_system, name, stepsize=None, sign=1):
        """name: common base name for registers
        sign: user to dial scale factor
        stepsize: e.g. 1 or "hlct"
        """
        self.timing_system = timing_system
        self.name = name
        self.stepsize_ref = "parameters." + self.name + ".stepsize"
        if stepsize is not None:
            self.stepsize_ref = stepsize
        self.sign = sign
        self.timing_system.add_variable(self)

    def get_stepsize(self):
        if type(self.stepsize_ref) == str:
            expr = f"self.timing_system.{self.stepsize_ref}"
            try:
                stepsize = eval(expr)
            except Exception as msg:
                logging.warning(f"{self.name}.stepsize: {expr}: {msg}")
                stepsize = 1
        else:
            stepsize = self.stepsize_ref  # numeric value
        return stepsize

    def set_stepsize(self, value):
        if type(self.stepsize_ref) == str:
            cmd = f"self.timing_system.{self.stepsize_ref}={value!r}"
            try:
                exec(cmd)
            except Exception as msg:
                logging.warning(f"{self.name}.stepsize: {cmd}: {msg}")
        else:
            self.stepsize_ref = value

    stepsize = property(get_stepsize, set_stepsize)

    def get_dial(self):
        """Delay controlled by the register in units of seconds"""
        return self.count * self.stepsize

    def set_dial(self, value):
        self.count = int(round(value / self.stepsize))

    dial = property(get_dial, set_dial)

    def next(self, value):
        """Round user value to the next possible value, given the step size"""
        dial_value = self.dial_from_user(value)
        count = int(round(dial_value / self.stepsize))
        dial_value = count * self.stepsize
        value = self.user_from_dial(dial_value)
        return value

    def get_value(self):
        """User value of the delay in units of seconds"""
        return self.user_from_dial(self.dial)

    def set_value(self, value):
        self.dial = self.dial_from_user(value)

    value = property(get_value, set_value)

    count = Parameter("count", 0)
    offset = Parameter("offset", 0.0)

    def user_from_dial(self, value):
        return value * self.sign + self.offset

    def dial_from_user(self, value):
        return (value - self.offset) / self.sign

    from numpy import inf

    min = -inf
    max = inf

    def __repr__(self):
        return self.name


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from timing_system_driver import timing_system_driver

    timing_system = timing_system_driver(domain_name)
    self = Variable(timing_system, "delay", stepsize=1e-12)
