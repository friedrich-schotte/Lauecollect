"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-05
Revision comment:
"""
__version__ = "1.0"

from logging import warning

from cached_function import cached_function

from timing_system_register import Register


@cached_function()
def timing_register(
        timing_system,
        name,
        stepsize=1.0,
        min=None,
        max=None,
        sign=1,
        unit="s",
        min_count=None,
        max_count=None,
):
    return Timing_Register(
        timing_system,
        name,
        stepsize=stepsize,
        min=min,
        max=max,
        sign=sign,
        unit=unit,
        min_count=min_count,
        max_count=max_count,
    )


class Timing_Register(Register):
    """A register representing a time delay, with a scale factor, converting count to a
  delay value in units of seconds"""

    def __init__(
            self,
            timing_system,
            name,
            stepsize=1.0,
            min=None,
            max=None,
            sign=1,
            unit="s",
            min_count=None,
            max_count=None,
    ):
        """
        name = mnemonic or hexadecimal address as string
        stepsize = resolution in units of seconds
        min = minimum dial value
        max = maximum dial value
        min_count = minimum count
        max_count = maximum count
        sign = +1 or -1, for dial to user value conversion
        offset = for dial to user value conversion
        """
        Register.__init__(self, timing_system, name)

        self.stepsize_ref = "parameters." + self.name + ".stepsize"
        if stepsize is not None:
            self.stepsize_ref = stepsize
        self.sign = sign
        self.unit = unit
        if min is not None:
            self.min_dial = min
        if max is not None:
            self.max_dial = max
        if min_count is not None:
            self.min_count = min_count
        if max_count is not None:
            self.max_count = max_count

    min = Register.min_value
    max = Register.max_value

    def get_stepsize(self):
        if type(self.stepsize_ref) == str:
            expr = "self.timing_system." + self.stepsize_ref
            try:
                stepsize = eval(expr)
            except Exception as msg:
                warning("%s.stepsize: %s: %s" % (self.name, expr, msg))
                stepsize = 1
        else:
            stepsize = self.stepsize_ref  # numeric value
        return stepsize

    def set_stepsize(self, value):
        if type(self.stepsize_ref) == str:
            cmd = "self.timing_system.%s=%r" % (self.stepsize_ref, value)
            try:
                exec(cmd)
            except Exception as msg:
                warning("%s.stepsize: %s: %s" % (self.name, cmd, msg))
        else:
            self.stepsize_ref = value

    stepsize = property(get_stepsize, set_stepsize)

    def define_value(self, value):
        """Modifies the user to dial offset such that the new user value is 'value'"""
        self.offset = value - self.dial * self.sign
        # user = dial*sign + offset; offset = user - dial*sign

    def next(self, value):
        """What is the closest possible value to the given user value the register
        can hold?
        value: user value
        """
        count = self.count_from_value(value)
        value = self.value_from_count(count)
        return value
