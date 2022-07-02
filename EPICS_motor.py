"""
EPICS-controlled motors
Author: Friedrich Schotte
Date created: 2007-11-07
Date last modified: 2021-10-13
Revision comment: Cleanup: moving
"""
__version__ = "3.3.2"

import logging
from logging import info, warning
from time import time

from numpy import nan, isnan

from CA import Record


class EPICS_motor(Record):
    """EPICS-controlled motor
    Using the following process variables:
    VAL - nominal position
    DVAL - dial value
    RBV - read back value
    DRBV - dial read back value
    HLM - high limit
    LLM - low limit
    DESC - description
    EGU - unit
    DMOV - 0 if currently moving, 1 if done
    STOP - set to 1 momentarily to stop ?
    VELO - speed in mm/s
    ACCL - acceleration
    CNEN - enabled
    DIR - user to dial sign
    OFF - user to dial offset
    HLS - at high limit switch
    LLS - at low limit switch
    HOMF - home in forward direction
    """
    from monitored_property import monitored_property
    from monitored_value_property import monitored_value_property
    from timed_out_property import timed_out_property

    def __init__(
            self,
            prefix,
            name=None,
            command="VAL",
            readback="RBV",
            readback_slop=0.001,
            timeout=20.0,
            min_step=0,
    ):
        """prefix = EPICS motor record
        If is assumed that command value process variable is named 'VAL'
        and the readback process variable 'RBV', unless specified otherwise
        by the optional 'command' and 'readback' keywords.

        readback slop: A motion is considered finished when the difference
        between the command value and the readback value is smaller than this
        amount.

        timeout: The motion is considered finished when the readback value has
        not changed within the readback slop for this amount of time.

        min_step: only if the new position deviates from the current position by
        at least this amount will a command to move to motor be sent to the
        IOC.
        """
        Record.__init__(self, prefix)

        if name is not None:
            self.__db_name__ = name

        self.__command__ = command
        self.__readback__ = readback

        self.__readback_slop__ = readback_slop
        self.__timeout__ = timeout
        self.__min_step__ = min_step

    move_timed_out = timed_out_property("__timeout__")

    __last_command_value__ = monitored_value_property(nan)
    __new_command_value__ = monitored_value_property(nan)
    __motion_started__ = monitored_value_property(0)
    __move_done__ = monitored_value_property(True)
    __last_moving__ = monitored_value_property(0)

    def get_prefix(self):
        from DB import dbget

        dbname = getattr(self, "__db_name__", "")
        try:
            prefix = eval(dbget("EPICS_motor/" + dbname + ".prefix"))
        except Exception:
            prefix = ""
        if not prefix:
            prefix = getattr(self, "__my_prefix__", "")
        return prefix

    def set_prefix(self, value):
        # debug("EPICS_motor.prefix = %r" % value)
        from DB import dbput

        dbname = getattr(self, "__db_name__", "")
        if dbname:
            # debug("EPICS_motor/"+dbname+".prefix: "+repr(value))
            dbput("EPICS_motor/" + dbname + ".prefix", repr(value))
        else:
            # debug("EPCIS_motor.__my_prefix__ = %r" % value)
            self.__my_prefix__ = value

    prefix = property(get_prefix, set_prefix)
    __prefix__ = prefix

    @property
    def command_PV_name(self):
        """Process variable value for the motor target position.
        Usually the value of the VAL process variable, but may me overridden."""
        if ":" not in self.__command__:
            PV_name = self.__prefix__ + "." + self.__command__
        else:
            PV_name = self.__command__
        return PV_name

    @property
    def readback_PV_name(self):
        """Process variable value for the actual position as measured.
        Usually the value of the RBV process variable, but may me overridden."""
        if ":" not in self.__readback__:
            PV_name = self.__prefix__ + "." + self.__readback__
        else:
            PV_name = self.__readback__
        return PV_name

    def inputs_command_value(self):
        from reference import reference
        from CA import PV
        return [reference(PV(self.command_PV_name), "value")]

    def calculate_command_value(self, command_PV_value):
        """Position of motor (user value)."""
        # Found that the Aerotech "Ensemble" EPICS driver is slow updating
        # the command value. Make that not an old command value is returned.
        # Wait 0.05 s from the command value to update.
        # debug(f"command_PV_value={command_PV_value}")
        if time() - self.__motion_started__ < 0.05 and not isnan(self.__new_command_value__):
            value = self.__new_command_value__
        else:
            value = command_PV_value
        value = as_float(value)
        # debug(f"value={value}")
        return value

    def set_command_value(self, value):
        # debug("value = %r" % value)
        try:
            value = float(value)
        except (ValueError, TypeError):
            return
        if isnan(value):
            return
        if abs(value - self.value) < self.__min_step__:
            return
        # Found that the Aerotech "Ensemble" EPICS driver is slow updating
        # the command value.
        # Cache the new command value for a short period.
        self.__new_command_value__ = value
        # Record the time the last motion was initiated.
        self.__motion_started__ = time()
        # Enable the motor (in case it was disabled)
        # self.CNEN = 1
        # Initiate the motion by setting a new command value.
        # debug("caget(self.command_PV_name, %r)" % value)
        from CA import caput
        caput(self.command_PV_name, value)
        self.move_timed_out = False
        self.__last_command_value__ = value
        self.__move_done__ = False

    command_value = monitored_property(
        inputs=inputs_command_value,
        calculate=calculate_command_value,
        fset=set_command_value,
    )

    def inputs_value(self):
        from reference import reference
        from CA import PV
        return [reference(PV(self.readback_PV_name), "value")]

    def calculate_value(self, readback_PV_value):
        """Position of motor (user value)."""
        return as_float(readback_PV_value)

    def set_value(self, value):
        self.command_value = value

    value = monitored_property(
        inputs=inputs_value,
        calculate=calculate_value,
        fset=set_value,
    )

    @monitored_property
    def command_dial(self, DVAL):
        """Target position as unscaled dial value."""
        return as_float(DVAL)

    @command_dial.setter
    def command_dial(self, value):
        value = as_float(value)
        if not isnan(value):
            self.__motion_started__ = time()
            self.DVAL = value

    @monitored_property
    def dial(self, DRBV):
        """Position of motor as reported by the encoder (dial value)."""
        return as_float(DRBV)

    @dial.setter
    def dial(self, value):
        value = as_float(value)
        if not isnan(value):
            self.__motion_started__ = time()
            self.DVAL = value

    def get_min(self):
        """Low limit in user units"""
        return as_float(self.LLM)

    def set_min(self, value):
        self.LLM = value

    min = property(get_min, set_min)
    low_limit = min

    def get_max(self):
        """Positive and of travel in user units"""
        return as_float(self.HLM)

    def set_max(self, value):
        self.HLM = value

    max = property(get_max, set_max)
    high_limit = max

    def get_at_low_limit(self):
        """Is motor at end switch?"""
        return as_bool(self.LLS)

    at_low_limit = property(get_at_low_limit)

    def get_at_high_limit(self):
        """Is motor at end switch?"""
        return as_bool(self.HLS)

    at_high_limit = property(get_at_high_limit)

    def get_name(self):
        """Description"""
        name = self.DESC
        if name is None:
            name = ""
        return name

    def set_name(self, value):
        self.DESC = value

    name = property(get_name, set_name)

    def get_unit(self):
        """mm,deg or mrad"""
        unit = self.EGU
        if unit is None:
            unit = ""
        unit = unit.strip("()")  # Sometimes the unit is included in parentheses.
        return unit

    def set_unit(self, value):
        self.EGU = value

    unit = property(get_unit, set_unit)

    @monitored_property
    def _moving(self, DMOV):
        return not DMOV

    @monitored_property
    def moving(self, _moving, value, command_value, move_timed_out):
        if move_timed_out:
            # if abs(value - command_value) > self.__readback_slop__ and not _moving:
            #    logging.warning(f"{self}: Move to {command_value} timed out at {value} out after {self.__timeout__} s")
            moving = _moving
            # logging.debug(f"move_timed_out = {move_timed_out}: moving = {moving}")
        elif _moving:
            moving = _moving
            # logging.debug(f"_moving == {_moving}: moving = _moving = {moving}")
        elif abs(value - command_value) > self.__readback_slop__:
            moving = True
            # logging.debug(f"abs(value - command_value) = {abs(value - command_value)} > {self.__readback_slop__}: moving = {moving}")
        else:
            moving = _moving
            # logging.debug(f"moving = _moving = {moving}")
        return moving

    @moving.setter
    def moving(self, moving):
        if not moving:
            self.stop()

    def get_speed(self):
        """Velocity in mm/s or deg/s"""
        return as_float(self.VELO)

    def set_speed(self, value):
        try:
            value = float(value)
        except (ValueError, TypeError):
            return
        self.VELO = value

    speed = property(get_speed, set_speed)

    def get_acceleration(self):
        """Acceleration in mm/s^2 or deg/s^2"""
        T = as_float(self.ACCL)  # acceleration time
        acceleration = self.speed / T
        return acceleration

    def set_acceleration(self, acceleration):
        try:
            acceleration = float(acceleration)
        except (ValueError, TypeError):
            return
        T = self.speed / acceleration
        self.ACCL = T

    acceleration = property(get_acceleration, set_acceleration)

    @monitored_property
    def enabled(self, CNEN):
        value = CNEN if CNEN is not None else nan
        return value

    @enabled.setter
    def enabled(self, value):
        self.CNEN = value

    def get_homing(self):
        """Current executing a home calibration? If set execute the home
        calibration."""
        if self.HOMR:
            value = True
        elif self.HOMF:
            value = True
        else:
            value = False
        return value

    def set_homing(self, value):
        self.HOMF = value

    homing = property(get_homing, set_homing)

    def get_homed(self):
        """Current executing a home calibration? If set execute the home
        calibration."""
        status_bits = self.MSTA
        if status_bits is None:
            homed = nan
        else:
            homed = bool((status_bits >> 15) & 1)
        return homed

    def set_homed(self, value):
        pass

    homed = property(get_homed, set_homed)

    def get_sign(self):
        """Dial to user direction: +1 or -1"""
        value = self.DIR
        if value == 0:
            return 1
        elif value == 1:
            return -1
        else:
            return nan

    def set_sign(self, sign):
        self.DIR = 0 if sign >= 0 else 1

    sign = property(get_sign, set_sign)

    def get_offset(self):
        """Dial to user direction: +1 or -1"""
        return as_float(self.OFF)

    def set_offset(self, value):
        self.OFF = value

    offset = property(get_offset, set_offset)

    def define_value(self, value):
        """modifies the user to dial offset such that the new user value is 'value'"""
        self.offset = value - self.dial * self.sign
        # user = dial*sign + offset; offset = user - dial*sign

    def get_readback_slop(self):
        """Maximum allowed difference between readback value and command value
        for the motion to be considered complete."""
        return self.__readback_slop__

    def set_readback_slop(self, value):
        self.__readback_slop__ = value

    readback_slop = property(get_readback_slop, set_readback_slop)

    def wait(self):
        """If the motor is moving, returns control after current move move is
        complete."""
        from time import sleep
        while self.moving:
            sleep(0.01)

    def stop(self):
        self.STOP = 1

    def __repr__(self):
        return f"{type(self).__name__}({self.__prefix__!r})"


motor = EPICS_motor


def as_float(x):
    """Convert x to a floating point number without raising an exception.
    Return nan instead if conversion fails"""
    try:
        return float(x)
    except (ValueError, TypeError):
        return nan


def as_bool(x):
    """Convert x to a boolean without raising an exception.
    Return False instead if conversion fails"""
    try:
        return bool(int(x))
    except (ValueError, TypeError, ArithmeticError):
        return False


if __name__ == "__main__":  # for testing
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler
    from reference import reference as _reference

    self = motor("14IDB:m7", name="HuberPhi")

    @_handler
    def report(event):
        info(f"event={event}")

    _reference(self, "command_value").monitors.add(report)
    _reference(self, "value").monitors.add(report)
    # _reference(self, "RBV").monitors.add(report)
    # _reference(self, "VAL").monitors.add(report)
    # _reference(self, "DMOV").monitors.add(report)
    _reference(self, "_moving").monitors.add(report)
    _reference(self, "moving").monitors.add(report)

    print(f"self = {self}")
    print(f"self.value = {self.command_value}")
    print(f"self.value += 4")
