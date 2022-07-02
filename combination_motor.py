"""Combination motor for slit gap and center, based on motor for individual
blades
Author: Friedrich Schotte
Date created: 2010-12-14
Date last modified: 2020-11-16
Revision comment: Using monitored_property calculate=
"""
__version__ = "1.1.2"

from logging import info

from reference import reference


class gap(object):
    """Combination motor for slit"""

    def __init__(self, blade1, blade2):
        self.blade1 = blade1
        self.blade2 = blade2

    def get_value(self):
        return self.blade1.value - self.blade2.value

    value = property(get_value)


class center(object):
    """Combination motor"""

    def __init__(self, blade1, blade2):
        self.blade1 = blade1
        self.blade2 = blade2

    def get_value(self):
        return (self.blade1.value + self.blade2.value) / 2

    value = property(get_value)


class tilt(object):
    """Combination motor"""
    name = "tilt"
    from persistent_property import persistent_property
    offset = persistent_property("offset", 0.0)
    sign = persistent_property("sign", +1)
    unit = persistent_property("unit", "mrad")

    def __init__(self, m1, m2, distance=1.0, name=None, unit=None):
        self.m1 = m1
        self.m2 = m2
        self.distance = distance
        if name is not None:
            self.name = name
        if unit is not None:
            self.unit = unit

    from monitored_property import monitored_property

    def get_dial(self):
        """Readback value, in dial units"""
        return self.theta(self.m1.dial, self.m2.dial)

    def set_dial(self, value):
        self.m1.dial, self.m2.dial = \
            self.x1_x2(self.m1.dial, self.m2.dial, value)

    def inputs_dial(self):
        return [
            reference(self.m1, "dial"),
            reference(self.m2, "dial"),
        ]

    dial = monitored_property(
        fget=get_dial,
        fset=set_dial,
        inputs=inputs_dial,
    )

    def get_command_dial(self):
        """Target value, in dial units"""
        return self.theta(self.m1.command_dial, self.m2.command_dial)

    def set_command_dial(self, value):
        self.m1.command_dial, self.m2.command_dial = \
            self.x1_x2(self.m1.command_dial, self.m2.command_dial, value)

    def inputs_command_dial(self):
        return [
            reference(self.m1, "command_dial"),
            reference(self.m2, "command_dial"),
        ]

    command_dial = monitored_property(
        fget=get_command_dial,
        fset=set_command_dial,
        inputs=inputs_command_dial,
    )

    def get_value(self):
        """Readback value, in user units, taking into account offset"""
        return self.user_from_dial(self.dial)

    def set_value(self, value):
        self.dial = self.dial_from_user(value)

    def inputs_value(self):
        return [
            reference(self, "dial"),
            reference(self, "offset"),
            reference(self, "sign"),
        ]

    value = monitored_property(
        fget=get_value,
        fset=set_value,
        inputs=inputs_value,
    )

    def get_command_value(self):
        """Target value, in user units, taking into account offset"""
        return self.user_from_dial(self.command_dial)

    def set_command_value(self, command_value):
        self.command_dial = self.dial_from_user(command_value)

    def inputs_command_value(self):
        return [
            reference(self, "command_dial"),
            reference(self, "offset"),
            reference(self, "sign"),
        ]

    command_value = monitored_property(
        fget=get_command_value,
        fset=set_command_value,
        inputs=inputs_command_value,
    )

    def theta(self, x1, x2):
        """Tilt angle in mrad as function of jack positions in mm"""
        return (x1 - x2) / self.distance

    def x1_x2(self, x1, x2, theta):
        """New positions for new tilt angle in mm"""
        # Keep the center constant
        d_theta = theta - self.theta(x1, x2)
        dx = d_theta * self.distance
        x1, x2 = x1 + dx / 2, x2 - dx / 2
        return x1, x2

    def user_from_dial(self, value):
        return value * self.sign + self.offset

    def dial_from_user(self, value):
        return (value - self.offset) / self.sign


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from instrumentation import mir2X1, mir2X2
    from handler import handler as _handler
    from reference import reference as _reference

    self = tilt(mir2X1, mir2X2, distance=1.045, name="mir2Th", unit="mrad")
    print("mir2X1.value = %.6f" % mir2X1.value)
    print("mir2X2.value = %.6f" % mir2X2.value)
    print('')
    print("self.offset = %r" % self.offset)
    print("self.value = %.6f" % self.value)
    print('')

    @_handler
    def report(event):
        info(f"event={event}")

    _reference(self, "value").monitors.add(report)
    print('_reference(self, "value").monitors')
    print("self.value += 0.0001")
    print('_reference(self, "value").monitors.remove(report)')
