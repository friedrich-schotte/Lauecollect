"""Aerotech Ensemble Motion Controller
Communication via the Aerotech C library interface using a proprietary
protocol by Aerotech.
Author: Friedrich Schotte
Date created: 2013-04-12
Date lst modified: 2022-05-01
Revision comment: Cleanup; Corrected typos
"""
__version__ = "4.0.5"

from logging import debug, error

from CA import Record
from array_wrapper import ArrayWrapper
from tcp_server_single_threaded import tcp_server
from EPICS_motor import EPICS_motor


class Ensemble(object):
    from cached_function import cached_function

    handle = None
    max_integer_registers = 50
    max_floating_point_registers = 512

    library_path = r'C:\Program Files (x86)\Aerotech\Ensemble\CLibrary\Bin64'
    library_name = "EnsembleC64.dll"

    @property
    def library_pathname(self):
        return self.library_path+"\\"+self.library_name

    @property
    @cached_function()
    def library(self):
        from os import environ
        environ["PATH"] += ";"+self.library_path
        import ctypes
        try:
            library = ctypes.windll.LoadLibrary(self.library_pathname)
        except Exception as details:
            library = None
            error('ctypes.windll.LoadLibrary(%r): %s' % (self.library_pathname, details))
            error("[This module needs to be running on operating system Windows].")
        return library

    def connect(self):
        """Establish a connection to the controller"""
        if self.library is None:
            return

        if self.handle is not None:
            return

        from ctypes import byref, c_void_p, c_int, POINTER
        if self.library is not None and self.handle is None:
            handles = POINTER(c_void_p)()
            handle_count = c_int()
            success = self.library.EnsembleConnect(byref(handles),
                                                   byref(handle_count))
            if success and handle_count.value >= 1:
                self.handle = handles.contents
            else:
                error("Unable to connect to Ensemble controller")

    def disconnect(self):
        """Undo 'connect'"""
        if self.library is None:
            return
        if self.handle is None:
            return
        from ctypes import c_void_p, POINTER
        handles = POINTER(c_void_p)()
        handles.contents = self.handle
        success = self.library.EnsembleDisconnect(handles)
        if success:
            self.handle = None
        else:
            error("disconnect failed")

    def get_connected(self):
        """Is a communication link with the controller established?"""
        return self.library is not None and self.handle is not None

    def set_connected(self, value):
        if value:
            self.connect()
        else:
            self.disconnect()

    connected = property(get_connected, set_connected)

    @property
    def naxes(self):
        """How many axes does the controller control?"""
        return bin(self.axis_mask).count("1")

    @property
    def axis_mask(self):
        """Bitmask: 1 for every axis that is available in the controller,
        starting from the least significant bit"""
        self.connect()
        if not self.connected:
            return 0
        from ctypes import byref, c_int
        c_value = c_int()
        success = self.library.EnsembleInformationGetAxisMask(self.handle, byref(c_value))
        if not success:
            error("axis mask failed")
        return c_value.value

    def get_fault(self, axis_number):
        """Axis faults as integer with 28 bits
        e.g. bit 0: PositionError, bit 27: VoltageClamp
        0 indicates not fault"""
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        AxisFault = 4  # EnsembleCommonStructures.h, STATUSITEM
        success = self.library.EnsembleStatusGetItem(self.handle, c_int(axis_number),
                                                     c_int(AxisFault), byref(c_value))
        if not success:
            error("get fault failed, axis %r" % axis_number)
        value = int(c_value.value)
        return value

    def get_fault_count(self):
        return self.naxes

    def _get_faults(self):
        return ArrayWrapper(self, "fault", method="single", dtype=int)

    def _set_faults(self, values):
        pass

    faults = property(_get_faults, _set_faults)

    def _get_fault(self):
        """Is any axis on a fault state?"""
        return any(self.faults)

    def set_fault(self, _value):
        self.clear_all_faults()

    fault = property(_get_fault, set_fault)

    def clear_all_faults(self):
        """Clear fault state for all axis.
        (This has the side effect of cancelling all active incomplete moves)."""
        self.connect()
        if not self.connected:
            return
        success = self.library.EnsembleAcknowledgeAll(self.handle)
        if not success:
            error("clear all faults failed")

    def clear_faults(self, axis_numbers):
        """Clear fault state.
        axis_numbers: list of 0-based integers
        """
        self.connect()
        if not self.connected:
            return
        # Attempting to clear faults on currently "active" axes confuses the
        # Ensemble controller.
        # Thus, only clear faults for axis that are currently in "fault" state.
        from numpy import asarray, atleast_1d
        axis_numbers = atleast_1d(axis_numbers)
        axis_numbers = axis_numbers[asarray(self.faults[axis_numbers]) != 0]
        if len(axis_numbers) == 0:
            return

        from ctypes import c_int
        axis_mask = 0
        for i in axis_numbers:
            axis_mask |= (1 << i)
        success = self.library.EnsembleMotionFaultAck(self.handle,
                                                      c_int(axis_mask))
        if not success:
            error("clear faults failed")

    def get_nominal_value(self, axis_number):
        """Target of current or last move"""
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        PositionCommand = 0  # EnsembleCommonStructures.h, STATUSITEM
        self.library.EnsembleStatusGetItem(self.handle, c_int(axis_number),
                                           c_int(PositionCommand), byref(c_value))
        value = c_value.value
        return value

    def get_nominal_value_count(self):
        return self.naxes

    def _get_nominal_values(self):
        return ArrayWrapper(self, "nominal_value", method="single", dtype=float)

    def _set_nominal_values(self, values):
        pass

    nominal_values = property(_get_nominal_values, _set_nominal_values)

    def get_command_value(self, axis_number):
        """Target of current or last move"""
        command_value = \
            self.destination_values[axis_number] if self.moving[axis_number] \
            else self.nominal_values[axis_number]
        return command_value

    def get_command_values(self, axis_numbers):
        """Target of current or last move
        axis_numbers: list of integers"""
        from numpy import where
        moving = self.moving[axis_numbers]
        nominal_values = self.nominal_values[axis_numbers]
        destination_values = self.destination_values[axis_numbers]
        command_values = where(moving, destination_values,
                               nominal_values)
        return command_values

    def set_command_values(self, axis_numbers, values):
        """Move axis
        axis_numbers: list of integers
        values: target positions"""
        # Ignore values that are NaN. 
        from numpy import atleast_1d, isnan
        axis_numbers, values = atleast_1d(axis_numbers), atleast_1d(values)
        valid = ~isnan(values)
        axis_numbers, values = axis_numbers[valid], values[valid]
        # Ignore axis that are already in position.
        old_values = self.command_values[axis_numbers]
        valid = abs(values - old_values) >= 0.001
        axis_numbers, values = axis_numbers[valid], values[valid]
        if len(axis_numbers) == 0:
            return
        self.connect()
        if not self.connected:
            return
        self.clear_faults(axis_numbers)
        # self.clear_faults(axis_numbers[~asarray(self.moving[axis_numbers])]) 
        # Make sure "EnsembleMotionMoveAbs" will not wait for motion to be done.
        from ctypes import c_int, c_double
        waittype = 0  # EnsembleCommonStructures.h, WAITTYPE, WAITTYPE_NoWait
        success = self.library.EnsembleMotionWaitMode(self.handle,
                                                      c_int(waittype))
        if not success:
            error("set wait mode failed")
        # This is needed for compatibility with the "Ensemble-SAXS.ab" program,
        # which uses PLANE and PVT commands.
        plane_number = 0
        success = self.library.EnsembleMotionSetupPlane(self.handle,
                                                        c_int(plane_number))
        if not success:
            error("set plane 0 failed")
        axis_mask = 0
        for i in axis_numbers:
            axis_mask |= (1 << i)
        success = self.library.EnsembleMotionSetupReconcile(self.handle,
                                                            c_int(axis_mask))
        if not success:
            error("reconcile failed")
        # Start the motion.
        c_values = (c_double * len(axis_numbers))(*values)
        speeds = self.speeds[axis_numbers]
        c_speeds = (c_double * len(axis_numbers))(*speeds)
        success = self.library.EnsembleMotionMoveAbs(self.handle,
                                                     c_int(axis_mask), c_values, c_speeds)
        if not success:
            error("set command positions failed")
        # Remember destination values.
        self.destination_values[axis_numbers] = values

    def set_command_values_fast(self, axis_numbers, values):
        """Move axis
        axis_numbers: list of integers
        values: target positions"""
        from ctypes import c_int, c_double
        from numpy import atleast_1d
        axis_numbers, values = atleast_1d(axis_numbers), atleast_1d(values)
        if len(axis_numbers) == 0:
            return
        self.connect()
        if not self.connected:
            return
        # Start the motion.
        axis_mask = 0
        for i in axis_numbers:
            axis_mask |= (1 << i)
        c_values = (c_double * len(axis_numbers))(*values)
        speeds = self.speeds[axis_numbers]
        c_speeds = (c_double * len(axis_numbers))(*speeds)
        success = self.library.EnsembleMotionMoveAbs(self.handle,
                                                     c_int(axis_mask), c_values, c_speeds)
        if not success:
            error("set command positions failed")

    def get_command_values_count(self):
        return self.naxes

    def _get_command_values(self):
        return ArrayWrapper(self, "command_values", method="multiple", dtype=float)

    def _set_command_values(self, values):
        self.command_values[:] = values

    command_values = property(_get_command_values, _set_command_values)

    def get_command_dial_values(self, axis_numbers):
        """Target of current or last move
        axis_numbers: list of integers"""
        values = self.command_values[axis_numbers]
        return self.user_to_dial(axis_numbers, values)

    def set_command_dial_values(self, axis_numbers, dial_values):
        """Move axis
        axis_numbers: list of integers
        values: target positions"""
        values = self.dial_to_user(axis_numbers, dial_values)
        self.command_values[axis_numbers] = values

    def get_command_dial_values_count(self):
        return self.naxes

    def _get_command_dial_values(self):
        return ArrayWrapper(self, "command_dial_values", method="multiple", dtype=float)

    def _set_command_dial_values(self, dial_values):
        self.command_dial_values[:] = dial_values

    command_dial_values = property(_get_command_dial_values,
                                   _set_command_dial_values)

    def get_value(self, axis_number):
        """Actual position based on encoder feedback"""
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        PositionFeedback = 1
        self.library.EnsembleStatusGetItem(self.handle, c_int(axis_number),
                                           c_int(PositionFeedback), byref(c_value))
        value = c_value.value
        return value

    def set_value(self, axis_number, values):
        pass

    def get_value_count(self):
        return self.naxes

    def _get_values(self):
        return ArrayWrapper(self, "value", method="single", dtype=float)

    def _set_values(self, values):
        self.values[:] = values

    values = property(_get_values, _set_values)

    def get_destination_values(self, axis_numbers):
        """The end points of the currently active motions"""
        from numpy import zeros, nan
        if len(self.__destination_values__) != self.naxes:
            self.__destination_values__ = zeros(self.naxes) + nan
        return self.__destination_values__[axis_numbers]

    from numpy import array
    __destination_values__ = array([])

    def set_destination_values(self, axis_numbers, values):
        from numpy import zeros, nan
        if not hasattr(self, "__destination_values__") or \
                len(self.__destination_values__) != self.naxes:
            self.__destination_values__ = zeros(self.naxes) + nan
        self.__destination_values__[axis_numbers] = values

    def get_destination_values_count(self):
        return self.naxes

    def _get_destination_values(self):
        return ArrayWrapper(self, "destination_values", method="multiple", dtype=float)

    def _set_get_destination_values(self, values):
        self.destination_values[:] = values

    destination_values = property(_get_destination_values, _set_get_destination_values)

    def get_dial_values(self, axis_numbers):
        """Target of current or last move
        axis_numbers: list of integers"""
        values = self.values[axis_numbers]
        return self.user_to_dial(axis_numbers, values)

    def set_dial_values(self, axis_numbers, values):
        pass

    def get_dial_values_count(self):
        return self.naxes

    def _get_dial_values(self):
        return ArrayWrapper(self, "dial_values", method="multiple", dtype=float)

    def _set_dial_values(self, dial_values):
        self.dial_values[:] = dial_values

    dial_values = property(_get_dial_values, _set_dial_values)

    def get_moving(self, axis_number):
        """Actual position based on encoder feedback"""
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        if not self.get_enabled(axis_number):
            return False
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        AxisStatus = 3  # EnsembleCommonStructures.h, STATUSITEM
        self.library.EnsembleStatusGetItem(self.handle, c_int(axis_number),
                                           c_int(AxisStatus), byref(c_value))
        value = c_value.value
        # InPositionBit = 2  # EnsembleCommonStructures.h, AXISSTATUSBITS
        MoveActiveBit = 3  # EnsembleCommonStructures.h, AXISSTATUSBITS
        # in_position = (int(value) & 1 << InPositionBit) != 0
        move_active = (int(value) & 1 << MoveActiveBit) != 0
        return move_active  # not in_position

    def set_moving(self, axis_number, value):
        """Stop the motion of the given axis, if value is False"""
        if value:
            return
        # Ignore values that are NaN. 
        from numpy import isnan
        if isnan(value):
            return
        self.connect()
        from ctypes import c_int
        axis_mask = (1 << axis_number)
        self.library.EnsembleMotionAbort(self.handle, c_int(axis_mask))

    def moving_count(self):
        return self.naxes

    def _get_moving(self):
        return ArrayWrapper(self, "moving", method="single", dtype=bool)

    def _set_moving(self, values):
        self.moving[:] = values

    moving = property(_get_moving, _set_moving)

    def get_speed(self, axis_number):
        return self.parameter("DefaultSpeed", axis_number)

    def set_speed(self, axis_number, value):
        # Ignore values that are NaN. 
        from numpy import isnan
        if isnan(value):
            return
        return self.set_parameter("DefaultSpeed", value, axis_number)

    def speed_count(self):
        return self.naxes

    def _get_speeds(self):
        return ArrayWrapper(self, "speed", method="single", dtype=float)

    def _set_speeds(self, values):
        self.speeds[:] = values

    speeds = property(_get_speeds, _set_speeds)

    def get_acceleration(self, axis_number):
        return self.parameter("DefaultRampRate", axis_number)

    def set_acceleration(self, axis_number, value):
        # Ignore values that are NaN. 
        from numpy import isnan
        if isnan(value):
            return
        return self.set_parameter("DefaultRampRate", value, axis_number)

    def acceleration_count(self):
        return self.naxes

    def _get_accelerations(self):
        return ArrayWrapper(self, "acceleration", method="single", dtype=float)

    def _set_accelerations(self, values):
        self.accelerations[:] = values

    accelerations = property(_get_accelerations, _set_accelerations)

    def get_enabled(self, axis_number):
        """Actual position based on encoder feedback"""
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        AxisStatus = 3  # EnsembleCommonStructures.h, STATUSITEM
        self.library.EnsembleStatusGetItem(self.handle, c_int(axis_number),
                                           c_int(AxisStatus), byref(c_value))
        value = c_value.value
        EnabledBit = 0  # EnsembleCommonStructures.h, AXISSTATUSBITS
        value = (int(value) & 1 << EnabledBit) != 0
        return value

    def set_enabled(self, axis_number, value):
        """Turn on the holding current.
        value: if True turn on, if False turn off the holding current"""
        # Ignore values that are NaN.
        from numpy import isnan
        if isnan(value):
            return
        self.connect()
        if not self.connected:
            return
        from ctypes import c_int
        axis_mask = (1 << axis_number)
        if value:
            self.clear_faults([axis_number])
            self.library.EnsembleMotionEnable(self.handle, c_int(axis_mask))
        else:
            self.library.EnsembleMotionDisable(self.handle, c_int(axis_mask))

    def enabled_count(self):
        return self.naxes

    def _get_enabled(self):
        return ArrayWrapper(self, "enabled", method="single", dtype=bool)

    def _set_enabled(self, values):
        self.enabled[:] = values

    enabled = property(_get_enabled, _set_enabled)

    def get_homing(self, axis_number):
        """Actual position based on encoder feedback"""
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        AxisStatus = 3  # EnsembleCommonStructures.h, STATUSITEM
        self.library.EnsembleStatusGetItem(self.handle, c_int(axis_number),
                                           c_int(AxisStatus), byref(c_value))
        value = c_value.value
        HomingBit = 14  # EnsembleCommonStructures.h, AXISSTATUSBITS
        value = (int(value) & 1 << HomingBit) != 0
        return value

    def set_homing(self, axis_number, value):
        """Calibrate the motor by driving it past its home switch.
        value: if True start home run, if False cancel home run"""
        # Ignore values that are NaN.
        from numpy import isnan
        if isnan(value):
            return
        self.connect()
        if not self.connected:
            return

        self.clear_faults([axis_number])
        # Make sure "EnsembleMotionHome" will not wait for motion to be done.
        # (However, the wait mode does not seem to have any effect when using
        # the "EnsembleMotionHome" command.)
        from ctypes import c_int
        waittype = 0  # EnsembleCommonStructures.h, WAITTYPE, WAITTYPE_NoWait
        success = self.library.EnsembleMotionWaitMode(self.handle,
                                                      c_int(waittype))
        if not success:
            error("set wait mode failed")

        axis_mask = (1 << axis_number)
        if value:
            success = self.library.EnsembleMotionHome(self.handle, c_int(axis_mask))
            if not success:
                error("home failed")
        else:
            success = self.library.EnsembleMotionAbort(self.handle, c_int(axis_mask))
            if not success:
                error("abort failed")

    def homing_count(self):
        return self.naxes

    def _get_homing(self):
        return ArrayWrapper(self, "homing", method="single", dtype=bool)

    def _set_homing(self, values):
        self.homing[:] = values

    homing = property(_get_homing, _set_homing)

    def get_homed(self, axis_number):
        """Actual position based on encoder feedback"""
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        AxisStatus = 3  # EnsembleCommonStructures.h, STATUSITEM
        self.library.EnsembleStatusGetItem(self.handle, c_int(axis_number),
                                           c_int(AxisStatus), byref(c_value))
        value = c_value.value
        HomedBit = 1  # EnsembleCommonStructures.h, AXISSTATUSBITS
        value = (int(value) & 1 << HomedBit) != 0
        return value

    def set_homed(self, axis_number, value):
        # Ignore values that are NaN.
        from numpy import isnan
        if isnan(value):
            return
        # If value is True, Home the axis, if not already done.
        if value and not self.homed[axis_number]:
            debug("self.homing[%r] = True..." % axis_number)
            self.homing[axis_number] = True
            debug("self.homing[%r] = %r" % (axis_number, self.homing[2]))

    def homed_count(self):
        return self.naxes

    def _get_homed(self):
        return ArrayWrapper(self, "homed", method="single", dtype=bool)

    def _set_homed(self, values):
        self.homed[:] = values

    homed = property(_get_homed, _set_homed)

    def get_at_low_dial_limits(self, axis_number):
        """Is the stage hitting the end of travel switch?"""
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        AxisStatus = 3  # EnsembleCommonStructures.h, STATUSITEM
        self.library.EnsembleStatusGetItem(self.handle, c_int(axis_number),
                                           c_int(AxisStatus), byref(c_value))
        value = c_value.value
        CCwEndOfTravelLimitInputBit = 23  # EnsembleCommonStructures.h, AXISSTATUSBITS
        value = (int(value) & 1 << CCwEndOfTravelLimitInputBit) != 0
        return value

    def set_at_low_dial_limits(self, axis_number, value):
        pass

    def at_low_dial_limits_count(self):
        return self.naxes

    def _get_at_low_dial_limits(self):
        return ArrayWrapper(self, "at_low_dial_limits", method="single", dtype=bool)

    def _set_at_low_dial_limits(self, values):
        self.at_low_dial_limits[:] = values

    at_low_dial_limits = property(_get_at_low_dial_limits, _set_at_low_dial_limits)

    def get_at_high_dial_limits(self, axis_number):
        """Actual position based on encoder feedback"""
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        AxisStatus = 3  # EnsembleCommonStructures.h, STATUSITEM
        self.library.EnsembleStatusGetItem(self.handle, c_int(axis_number),
                                           c_int(AxisStatus), byref(c_value))
        value = c_value.value
        CwEndOfTravelLimitInputBit = 22  # EnsembleCommonStructures.h, AXISSTATUSBITS
        value = (int(value) & 1 << CwEndOfTravelLimitInputBit) != 0
        return value

    def set_at_high_dial_limits(self, axis_number, value):
        pass

    def at_high_dial_limits_count(self):
        return self.naxes

    def _get_at_high_dial_limits(self):
        return ArrayWrapper(self, "at_high_dial_limits", method="single", dtype=bool)

    def _set_at_high_dial_limits(self, values):
        self.at_high_dial_limits[:] = values

    at_high_dial_limits = property(_get_at_high_dial_limits, _set_at_high_dial_limits)

    def get_at_low_limits(self):
        """Soft limit."""
        from numpy import where
        values = where(self.signs[:] >= 0,
                       self.at_low_dial_limits[:], self.at_high_dial_limits[:])
        return values

    def set_at_low_limits(self, values):
        pass

    def get_at_low_limits_count(self):
        return self.naxes

    def _get_at_low_limits(self):
        return ArrayWrapper(self, "at_low_limits", method="all", dtype=bool)

    def _set_at_low_limits(self, values):
        pass

    at_low_limits = property(_get_at_low_limits, _set_at_low_limits)

    def get_at_high_limits(self):
        """Soft limit."""
        from numpy import where
        values = where(self.signs[:] >= 0,
                       self.at_high_dial_limits[:], self.at_low_dial_limits[:])
        return values

    def set_at_high_limits(self, values):
        pass

    def get_at_high_limits_count(self):
        return self.naxes

    def _get_at_high_limits(self):
        return ArrayWrapper(self, "at_high_limits", method="all", dtype=bool)

    def _set_at_high_limits(self, values):
        pass

    at_high_limits = property(_get_at_high_limits, _set_at_high_limits)

    def parameter(self, parameter_name, axis_number=0):
        """Configuration parameter as floating point number.
        parameter_id: integer. see "parameters_IDs"
        axis_number: 0-based axis number or 0 for a system parameter"""
        parameter_id = self.parameter_ID(parameter_name)
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import byref, c_int, c_double
        c_value = c_double()
        self.library.EnsembleParameterGetValue(self.handle,
                                               c_int(parameter_id), c_int(axis_number), byref(c_value))
        value = c_value.value
        return value

    def set_parameter(self, parameter_name, value, axis_number=0):
        """Change configuration parameter.
        parameter_id: integer. see "parameters_IDs"
        value: floating point number
        axis_number: 0-based axis number or 0 for a system parameter"""
        parameter_id = self.parameter_ID(parameter_name)
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import c_int, c_double
        value = float(value)
        self.library.EnsembleParameterSetValue(self.handle,
                                               c_int(parameter_id), c_int(axis_number), c_double(value))

    def string_parameter(self, parameter_name, axis_number=0):
        """Configuration parameter as string.
        parameter_name: string (see parameterIDs)
        axis_number: 0-based axis number or 0 for a system parameter"""
        parameter_id = self.parameter_ID(parameter_name)
        self.connect()
        if not self.connected:
            return ""
        from ctypes import byref, c_int, create_string_buffer
        c_value = create_string_buffer(81)
        self.library.EnsembleParameterGetValueString(self.handle,
                                                     c_int(parameter_id), c_int(axis_number), c_int(80), byref(c_value))
        value = c_value.value.decode('utf-8')
        return value

    def set_string_parameter(self, parameter_name, value, axis_number=0):
        """Change configuration parameter.
        parameter_name: string (see parameterIDs)
        value: string
        axis_number: 0-based axis number or 0 for a system parameter"""
        parameter_id = self.parameter_ID(parameter_name)
        self.connect()
        if not self.connected:
            from numpy import nan
            return nan
        from ctypes import c_int, c_char_p
        value = str(value).encode("utf-8")
        self.library.EnsembleParameterSetValueString(
            self.handle, c_int(parameter_id), c_int(axis_number), c_char_p(value))

    def parameter_ID(self, name):
        """Translate parameter name to parameter ID"""
        if type(name) == str:
            return self.parameter_IDs[name]
        else:
            return name

    def get_UserInteger0(self):
        return int(self.parameter("UserInteger0"))

    def set_UserInteger0(self, value):
        self.set_parameter("UserInteger0", value)

    UserInteger0 = property(get_UserInteger0, set_UserInteger0)

    def get_UserInteger1(self):
        return int(self.parameter("UserInteger1"))

    def set_UserInteger1(self, value):
        self.set_parameter("UserInteger1", value)

    UserInteger1 = property(get_UserInteger1, set_UserInteger1)

    def get_UserDouble0(self):
        return self.parameter("UserDouble0")

    def set_UserDouble0(self, value):
        self.set_parameter("UserDouble0", value)

    UserDouble0 = property(get_UserDouble0, set_UserDouble0)

    def get_UserDouble1(self):
        return self.parameter("UserDouble1")

    def set_UserDouble1(self, value):
        self.set_parameter("UserDouble1", value)

    UserDouble1 = property(get_UserDouble1, set_UserDouble1)

    def get_UserString0(self):
        return self.string_parameter("UserString0")

    def set_UserString0(self, value):
        self.set_string_parameter("UserString0", value)

    UserString0 = property(get_UserString0, set_UserString0)

    def get_UserString1(self):
        return self.string_parameter("UserString1")

    def set_UserString1(self, value):
        self.set_string_parameter("UserString1", value)

    UserString1 = property(get_UserString1, set_UserString1)

    def get_unit(self, axis_number):
        """Unit name displayed in "Motion Composer" and "Digital Scope"
        Return value: 'mm' or 'deg'"""
        return self.string_parameter("UnitsName", axis_number)

    def set_unit(self, axis_number, value):
        """Value: 'mm' or 'deg'"""
        self.set_string_parameter("UnitsName", value, axis_number)

    def unit_count(self):
        return self.naxes

    def get_units(self):
        return ArrayWrapper(self, "unit", method="single", dtype="S16")

    def set_units(self, values):
        self.units[:] = values

    units = property(get_units, set_units)

    def get_name(self, axis_number):
        """Name of the axis displayed in "Motion Composer" and "Digital Scope" 
        Return value: 'mm' or 'deg'"""
        return self.string_parameter("AxisName", axis_number)

    def set_name(self, axis_number, value):
        """Value: 'mm' or 'deg'"""
        self.set_string_parameter("AxisName", value, axis_number)

    def name_count(self):
        return self.naxes

    def get_names(self):
        return ArrayWrapper(self, "name", method="single", dtype="S16")

    def set_names(self, values):
        self.names[:] = values

    names = property(get_names, set_names)

    def get_floating_point_variable_range(self, start, count):
        """Global register variables
        start: 0-based index
        count: number of variables after start"""
        from numpy import array, nan, zeros
        self.connect()
        if not self.connected:
            return zeros(count) + nan
        from ctypes import c_int, c_double
        c_values = (c_double * count)()
        success = self.library.EnsembleVariableGetGlobalDoubles(self.handle,
                                                                c_int(start), c_values, c_int(count))
        if not success:
            error("get floating point variables failed")
        values = array(c_values[:])
        return values

    def set_floating_point_variable_range(self, start, count, values):
        """Global register variables
        start: 0-based index
        count: number of variables after start
        values: list or array of numbers"""
        self.connect()
        if not self.connected:
            return
        from ctypes import c_int, c_double
        c_values = (c_double * count)(*values)
        success = self.library.EnsembleVariableSetGlobalDoubles(self.handle,
                                                                c_int(start), c_values, c_int(count))
        if not success:
            error("set floating point variables failed")

    def get_floating_point_variables(self, indices):
        """Global register variables
        indices: list of integer variables
        """
        # Organize indices into groups of consecutive indices.
        from numpy import asarray, zeros, nan, argsort, where, roll
        indices = asarray(indices)
        order = argsort(indices)
        indices = indices[order]
        i_start = where(indices != roll(indices, 1) + 1)[0]
        i_end = where(indices != roll(indices, -1) - 1)[0] + 1
        counts = i_end - i_start
        sorted_values = zeros(len(indices)) + nan
        for (i, count) in zip(i_start, counts):
            sorted_values[i:i + count] = \
                self.get_floating_point_variable_range(indices[i], count)
        values = zeros(len(indices)) + nan
        values[order] = sorted_values
        return values

    def set_floating_point_variables(self, indices, values):
        """Global register variables
        indices: list of integer variables
        values: list or array of numbers
        """
        # Organize indices into groups of consecutive indices.
        from numpy import argsort, roll, where, atleast_1d
        indices = atleast_1d(indices)
        values = atleast_1d(values)
        order = argsort(indices)
        indices, values = indices[order], values[order]
        i_start = where(indices != roll(indices, 1) + 1)[0]
        i_end = where(indices != roll(indices, -1) - 1)[0] + 1
        counts = i_end - i_start
        for (i, count) in zip(i_start, counts):
            self.set_floating_point_variable_range(indices[i], count,
                                                   values[i:i + count])

    @property
    def floating_point_variables_count(self):
        count = int(self.parameter("GlobalDoubles"))
        count = min(count, self.max_floating_point_registers)
        return count

    def _get_floating_point_variables(self):
        return ArrayWrapper(self, "floating_point_variables", method="multiple", dtype=float)

    def _set_floating_point_variables(self, values):
        self.floating_point_variables[:] = values

    floating_point_variables = property(_get_floating_point_variables, _set_floating_point_variables)

    floating_point_registers = floating_point_variables
    floating_point_registers_count = floating_point_variables_count

    def get_integer_variable_range(self, start, count):
        """Global register variables
        start: 0-based index
        count: number of variables after start"""
        from numpy import array, nan, zeros
        self.connect()
        if not self.connected:
            return zeros(count) + nan
        from ctypes import c_int
        c_values = (c_int * count)()
        success = self.library.EnsembleVariableGetGlobalIntegers(self.handle,
                                                                 c_int(start), c_values, c_int(count))
        if not success:
            error("get integer variables failed")
        values = array(c_values[:])
        return values

    def set_integer_variable_range(self, start, count, values):
        """Global register variables
        start: 0-based index
        count: number of variables after start
        values: list or array of numbers"""
        from numpy import asarray
        values = asarray(values, dtype=int)
        self.connect()
        if not self.connected:
            return
        from ctypes import c_int
        c_values = (c_int * count)(*values)
        success = self.library.EnsembleVariableSetGlobalIntegers(self.handle,
                                                                 c_int(start), c_values, c_int(count))
        if not success:
            error("set integer variables failed")

    def get_integer_variables(self, indices):
        """Global register variables
        indices: list of 0-based integers"""
        # Organize indices into groups of consecutive indices.
        from numpy import asarray, zeros, nan, argsort, where, roll
        indices = asarray(indices)
        order = argsort(indices)
        indices = indices[order]
        i_start = where(indices != roll(indices, 1) + 1)[0]
        i_end = where(indices != roll(indices, -1) - 1)[0] + 1
        counts = i_end - i_start
        sorted_values = zeros(len(indices)) + nan
        for (i, count) in zip(i_start, counts):
            sorted_values[i:i + count] = \
                self.get_integer_variable_range(indices[i], count)
        values = zeros(len(indices), int)
        values[order] = sorted_values
        return values

    def set_integer_variables(self, indices, values):
        """Global register variables
        indices: list of 0-based integers
        values: list or array of numbers"""
        # Organize indices into groups of consecutive indices.
        from numpy import argsort, roll, where, atleast_1d
        indices = atleast_1d(indices)
        values = atleast_1d(values)
        order = argsort(indices)
        indices, values = indices[order], values[order]
        i_start = where(indices != roll(indices, 1) + 1)[0]
        i_end = where(indices != roll(indices, -1) - 1)[0] + 1
        counts = i_end - i_start
        for (i, count) in zip(i_start, counts):
            self.set_integer_variable_range(indices[i], count,
                                            values[i:i + count])

    @property
    def integer_variables_count(self):
        count = int(self.parameter("GlobalIntegers"))
        count = min(count, self.max_integer_registers)
        return count

    def _get_integer_variables(self):
        return ArrayWrapper(self, "integer_variables", method="multiple", dtype=int)

    def _set_integer_variables(self, values):
        self.integer_variables[:] = values

    integer_variables = property(_get_integer_variables, _set_integer_variables)

    integer_registers = integer_variables
    integer_registers_count = integer_variables_count

    def enable_camming(self):
        """Activates the camming table named 'test.cmx' stored in the
        flash file system of the controller."""
        # Run the program "EnableCamming.bcx" stored in the flash file system
        # on the controller.
        self.run_program("EnableCamming.bcx")

    def disable_camming(self):
        """Undo 'enable_camming'"""
        self.execute("PROGRAM STOP 1")

    def get_camming_enabled(self):
        """Is camming mode currently enabled?"""
        return self.program_running != ""

    def set_camming_enabled(self, value):
        if value:
            self.enable_camming()
        else:
            self.disable_camming()

    camming_enabled = property(get_camming_enabled, set_camming_enabled)

    def get_program_filename(self):
        """Which program is currently running as task 1? Empty sting if none."""
        # By convention each program loads its name into the
        # "UserString0" parameter at startup to identify itself.
        if self.program_running:
            return self.UserString0
        else:
            return ""

    def set_task_program_filename(self, filename, task_number):
        if filename == "":
            self.stop_program(task_number)
            return
        if filename.endswith(".bcx"):
            self.run_program(filename, task_number)
        if filename.endswith(".ab"):
            self.run_local_program(filename, task_number)

    def set_program_filename(self, filename):
        self.set_task_program_filename(filename, 1)

    program_filename = property(get_program_filename, set_program_filename)

    def get_auxiliary_task_filename(self):
        """Which program is currently running? Empty sting if none."""
        # By convention, each program loads its name into the
        # "UserString0" parameter at startup to identify itself.
        if self.auxiliary_task_running:
            return self.UserString1
        else:
            return ""

    def set_auxiliary_task_filename(self, filename):
        self.set_task_program_filename(filename, 5)

    auxiliary_task_filename = property(get_auxiliary_task_filename,
                                       set_auxiliary_task_filename)

    def get_auxiliary_task_running(self):
        """Is there a program running in the auxiliary task?"""
        return self.get_task_program_running(5)

    def set_auxiliary_task_running(self, value):
        """Start/Stop a program in the auxiliary task
        value: True/False"""
        return self.set_task_program_running(value, 5)

    auxiliary_task_running = property(get_auxiliary_task_running)

    def run_program(self, filename, task_number=1):
        """Run a compiled .bcx program stored in the flash file system on the
        controller.
        filename: e.g. 'EnableCamming.bcx'
        task_number: 1 to 5 (5=auxiliary task)"""
        from DB import dbput
        self.execute('PROGRAM RUN %s, "%s"' % (task_number, filename))
        dbput("Ensemble.program_filename", filename)

    def execute(self, command):
        """Executes an AeroBasic command in the immediate task. 
        command: string e.g. 'RET = AXISSTATUS(X) BAND 1'
        A function call that return a value must start with 'RET = '
        Return value: floating point number"""
        self.stop_program()
        self.connect()
        if not self.connected:
            return
        from ctypes import c_double, byref
        c_result = c_double()
        c_command = command.encode("utf-8")
        success = self.library.EnsembleCommandExecute(self.handle,
                                                      c_command, byref(c_result))
        if not success:
            error("command %r: execute failed" % c_command)
            from numpy import nan
            return nan
        result = c_result.value
        return result

    def load_program(self, filename, task_number=1):
        """Loads an Aerobasic program. The given Aerobasic file will be
        compiled, sent to the drive, and associated with the given task number.
        The program is fully loaded and ready to execute.
        filename: local file, full pathname ending with '.ab' in DOS format
        task_number: 1-5 (5=auxiliary task)"""
        from normpath import normpath
        filename = normpath(filename)
        self.connect()
        if not self.connected:
            return
        self.stop_program(task_number)
        from ctypes import c_int
        c_filename = filename.encode("utf-8")
        success = self.library.EnsembleProgramLoad(self.handle,
                                                   c_int(task_number), c_filename)
        if not success:
            error("program %r: load failed" % c_filename)
        from DB import dbput
        dbput("Ensemble.program_filename", filename)

    def run_local_program(self, filename, task_number=1):
        """Runs an Aerobasic program. The given Aerobasic file will be compiled,
        sent to the drive, associated with the given task number, and then
        executed.
        filename: local file, full pathname ending with '.ab' in DOS format
        task_number: 1 to 5 (5=auxiliary task)"""
        from normpath import normpath
        filename = normpath(filename)
        # if isabs(filename): pathname = self.program_directory+"/"+filename
        # else: pathname = filename
        pathname = self.program_directory + "/" + filename
        self.connect()
        if not self.connected:
            return
        self.stop_program(task_number)
        from ctypes import c_int
        c_pathname = pathname.encode("utf-8")
        success = self.library.EnsembleProgramRun(self.handle,
                                                  c_int(task_number), c_pathname)
        if not success:
            error("program %r: run failed" % c_pathname)
        from DB import dbput
        dbput("Ensemble.program_filename", filename)

    @property
    def program_directory(self):
        """Location of Aerobasic programs"""
        from module_dir import module_dir
        return module_dir(Ensemble) + "/Ensemble"

    def start_program(self, task_number=1):
        """Start the execution of an Aerobasic program on a task. The given
        task is started, and the associated Aerobasic program is executed.
        task_number: 1-5 (5=auxiliary task)"""
        self.connect()
        if not self.connected:
            return
        from ctypes import c_int
        success = self.library.EnsembleProgramStart(self.handle, c_int(task_number))
        if not success:
            error("program start failed")

    def get_task_program_running(self, task_number):
        """Is an Aerobasic  program currently running?
        task_number: 1-5 (5=auxiliary task)"""
        self.connect()
        if not self.connected:
            return
        from ctypes import c_int, byref
        c_task_state = c_int()
        success = self.library.EnsembleProgramGetTaskState(self.handle,
                                                           c_int(task_number), byref(c_task_state))
        if not success:
            error("get task state failed")
            return False
        task_state = c_task_state.value
        running = (task_state == 3)
        return running

    def set_task_program_running(self, value, task_number):
        """Start/stop a program
        task_number: 1-5 (5=auxiliary task)"""
        if value:
            self.start_program(task_number)
        else:
            self.stop_program(task_number)

    def get_program_running(self):
        return self.get_task_program_running(1)

    def set_program_running(self, value):
        self.set_task_program_running(value, 1)

    program_running = property(get_program_running, set_program_running)

    def stop_program(self, task_number=1):
        """Stop the execution of an Aerobasic program on a task.
        The given task is stopped immediately, and all motion is aborted.
        task_number: 1 to 5 (5=auxiliary task)"""
        self.connect()
        if not self.connected:
            return
        from ctypes import c_int
        success = self.library.EnsembleProgramStop(self.handle, c_int(task_number))
        if not success:
            error("program stop failed")

    def get_analog_output(self):
        """Voltage (-5..+5 V)"""
        # Using AOUT(X,1) to read-back the voltage does not seem to be supported
        # over the ASCII command interface. "AOUT(X,1)" always generates 
        # "execute failed".
        # return self.execute("AOUT(X,1)")
        from DB import dbget
        value = dbget("Ensemble.AOUT.X.1")
        try:
            value = float(value)
        except ValueError:
            value = 0.0
        return value

    def set_analog_output(self, value):
        # self.execute("AOUT X,1:%g" % value)
        self.connect()
        if not self.connected:
            from numpy import nan
            return
        from ctypes import c_int, c_double
        c_double()
        axis = 0
        channels = [1]
        c_channels = (c_int * 1)(*channels)
        channel_count = 1
        values = [value]
        c_values = (c_double * 1)(*values)
        value_count = 1
        success = self.library.EnsembleIOAnalogOutput(self.handle,
                                                      c_int(axis), c_channels, c_int(channel_count), c_values,
                                                      c_int(value_count))
        if not success:
            error("analog output %r failed" % value)
        from DB import dbput
        dbput("Ensemble.AOUT.X.1", str(value))

    analog_output = property(get_analog_output, set_analog_output)

    def dial_to_user(self, indices, dial_values):
        """Convert user to dial values"""
        return dial_values * self.signs[indices] + self.offsets[indices]

    def user_to_dial(self, indices, user_values):
        """Convert dial to user values"""
        return (user_values - self.offsets[indices]) / self.signs[indices]

    def get_sign(self, axis_number):
        """Is the direction reversed for this axis? +1 or -1"""
        reverse = self.parameter("ReverseMotionDirection", axis_number)
        return -1 if reverse else +1

    def set_sign(self, axis_number, value):
        reverse = 1 if value < 0 else 0
        return self.set_parameter("ReverseMotionDirection", reverse, axis_number)

    def get_sign_count(self):
        return self.naxes

    def get_signs(self):
        return ArrayWrapper(self, "sign", method="single", dtype=int)

    def set_signs(self, values):
        self.signs[:] = values

    signs = property(get_signs, set_signs)

    def get_offsets(self):
        """Dial-to-user conversion sign, maybe either 1 or -1"""
        from DB import dbget
        from numpy import zeros, array, isnan, where
        # noinspection PyBroadException
        try:
            values = array(eval(dbget("Ensemble.offsets")))
        except Exception:
            values = zeros(self.naxes)
        values.resize((self.naxes,), refcheck=False)
        values = where(isnan(values), 0.0, values)
        return values

    def set_offsets(self, values):
        # Ignore values that are NaN. 
        from numpy import asarray, isnan, where
        values = asarray(values)
        old_values = self.get_offsets()
        values = where(~isnan(values), values, old_values)
        from DB import dbput
        dbput("Ensemble.offsets", str(list(values)))

    def get_offsets_count(self):
        return self.naxes

    def _get_offsets(self):
        return ArrayWrapper(self, "offsets", method="all", dtype=float)

    def _set_offsets(self, values):
        self.offsets[:] = values

    offsets = property(_get_offsets, _set_offsets)

    def get_dial_low_limit(self, axis_number):
        return self.parameter("SoftwareLimitLow", axis_number)

    def set_dial_low_limit(self, axis_number, value):
        return self.set_parameter("SoftwareLimitLow", value, axis_number)

    def get_dial_low_limit_count(self):
        return self.naxes

    def get_dial_low_limits(self):
        return ArrayWrapper(self, "dial_low_limit", method="single", dtype=float)

    def set_dial_low_limits(self, values):
        self.dial_low_limits[:] = values

    dial_low_limits = property(get_dial_low_limits, set_dial_low_limits)

    def get_dial_high_limit(self, axis_number):
        return self.parameter("SoftwareLimitHigh", axis_number)

    def set_dial_high_limit(self, axis_number, value):
        return self.set_parameter("SoftwareLimitHigh", value, axis_number)

    def get_dial_high_limit_count(self):
        return self.naxes

    def get_dial_high_limits(self):
        return ArrayWrapper(self, "dial_high_limit", method="single", dtype=float)

    def set_dial_high_limits(self, values):
        self.dial_high_limits[:] = values

    dial_high_limits = property(get_dial_high_limits, set_dial_high_limits)

    def get_low_limit(self, axis_number):
        """Soft limit. Disable soft limits by settings this value to nan"""
        dial_value = \
            self.dial_low_limits[axis_number] if self.signs[axis_number] > 0 \
            else self.dial_high_limits[axis_number]
        value = self.dial_to_user(axis_number, dial_value)
        return value

    def set_low_limit(self, axis_number, value):
        dial_value = self.user_to_dial(axis_number, value)
        if self.signs[axis_number] > 0:
            self.dial_low_limits[axis_number] = dial_value
        else:
            self.dial_high_limits[axis_number] = dial_value

    def get_low_limit_count(self):
        return self.naxes

    def _get_low_limits(self):
        return ArrayWrapper(self, "low_limit", method="single", dtype=float)

    def _set_low_limits(self, values):
        self.low_limits[:] = values

    low_limits = property(_get_low_limits, _set_low_limits)

    def get_high_limit(self, axis_number):
        """Soft limit. Disable soft limits by settings this value to nan"""
        dial_value = \
            self.dial_high_limits[axis_number] if self.signs[axis_number] > 0 \
            else self.dial_low_limits[axis_number]
        value = self.dial_to_user(axis_number, dial_value)
        return value

    def set_high_limit(self, axis_number, value):
        dial_value = self.user_to_dial(axis_number, value)
        if self.signs[axis_number] > 0:
            self.dial_high_limits[axis_number] = dial_value
        else:
            self.dial_low_limits[axis_number] = dial_value

    def get_high_limit_count(self):
        return self.naxes

    def _get_high_limits(self):
        return ArrayWrapper(self, "high_limit", method="single", dtype=float)

    def _set_high_limits(self, values):
        self.high_limits[:] = values

    high_limits = property(_get_high_limits, _set_high_limits)

    def get_has_home(self):
        """Can this motor be homed?"""
        from numpy import ones
        return ones(self.naxes, bool)

    def set_has_home(self, _value):
        pass

    has_home = property(get_has_home, set_has_home)

    # Configuration parameter number. See file
    # C:\Program Files (x86)\Aerotech\Ensemble\CLibrary\Include\EnsembleParameterId.h
    parameter_IDs = {
        "ReverseMotionDirection": 1,
        "SoftwareLimitLow": 37,
        "SoftwareLimitHigh": 38,
        "DefaultSpeed": 71,
        "DefaultRampRate": 72,
        "GlobalIntegers": 124,
        "GlobalDoubles": 125,
        "UnitsName": 129,
        "AxisName": 140,
        "UserInteger0": 141,
        "UserInteger1": 142,
        "UserDouble0": 143,
        "UserDouble1": 144,
        "UserString0": 145,
        "UserString1": 146,
    }


ensemble_driver = Ensemble()


class EnsembleMotor(object):
    """Individual axes of the Aerotech Ensemble multi-axis controller"""
    # 'stepsize' is to strip unnecessary digits after the decimal point that
    # arise from float32 to float64 conversion.
    stepsize = 0.0

    def __init__(self, axis_number, **kwargs):
        self.axis_number = axis_number
        for key in kwargs:
            setattr(self, key, kwargs[key])

    def get_command_dial(self):
        """Destination position in dial units"""
        value = ensemble_driver.command_dial_values[self.axis_number]
        value = round_next(value, self.stepsize)
        return value

    def set_command_dial(self, value):
        from numpy import isnan
        if isnan(value):
            return
        ensemble_driver.command_dial_values[self.axis_number] = value

    command_dial = property(get_command_dial, set_command_dial)

    def get_dial(self):
        """Current position in dial units"""
        value = ensemble_driver.dial_values[self.axis_number]
        value = round_next(value, self.stepsize)
        return value

    def set_dial(self, value):
        self.command_dial = value

    dial = property(get_dial, set_dial)

    def get_command_value(self):
        """Destination position in user units"""
        value = ensemble_driver.command_values[self.axis_number]
        value = round_next(value, self.stepsize)
        return value

    def set_command_value(self, value):
        from numpy import isnan
        if isnan(value):
            return
        ensemble_driver.command_values[self.axis_number] = value

    command_value = property(get_command_value, set_command_value)

    def get_value(self):
        """Current position in user units"""
        value = ensemble_driver.values[self.axis_number]
        value = round_next(value, self.stepsize)
        return value

    value = property(get_value, set_command_value)

    def get_moving(self):
        """Target position"""
        return ensemble_driver.moving[self.axis_number]

    def set_moving(self, value):
        ensemble_driver.moving[self.axis_number] = value

    moving = property(get_moving, set_moving)

    def get_enabled(self):
        """Is holding the current turned on?"""
        return ensemble_driver.enabled[self.axis_number]

    def set_enabled(self, value):
        ensemble_driver.enabled[self.axis_number] = value

    enabled = property(get_enabled, set_enabled)

    def enable(self):
        """Turn the holding current on."""
        self.enabled = True

    def disable(self):
        """Turn the holding current off."""
        self.enabled = False

    def get_speed(self):
        """How fast does the motor move?"""
        return ensemble_driver.speeds[self.axis_number]

    def set_speed(self, value):
        ensemble_driver.speeds[self.axis_number] = value

    speed = property(get_speed, set_speed)

    def get_acceleration(self):
        """How fast does the motor move?"""
        return ensemble_driver.accelerations[self.axis_number]

    def set_acceleration(self, value):
        ensemble_driver.accelerations[self.axis_number] = value

    acceleration = property(get_acceleration, set_acceleration)

    def get_homing(self):
        """Currently performing a home run?"""
        return ensemble_driver.homing[self.axis_number]

    def set_homing(self, value):
        ensemble_driver.homing[self.axis_number] = value

    homing = property(get_homing, set_homing)

    def get_homed(self):
        """Has home run been done? Is motor calibrated?"""
        return ensemble_driver.homed[self.axis_number]

    def set_homed(self, value):
        ensemble_driver.homed[self.axis_number] = value

    homed = property(get_homed, set_homed)

    def get_has_home(self):
        """Can this motor be homed?"""
        return ensemble_driver.has_home[self.axis_number]

    def set_has_home(self, value):
        ensemble_driver.has_home[self.axis_number] = value

    has_home = property(get_has_home, set_has_home)

    def get_sign(self):
        """Dial-to-user conversion sign, maybe either 1 or -1"""
        return ensemble_driver.signs[self.axis_number]

    def set_sign(self, value):
        ensemble_driver.signs[self.axis_number] = value

    sign = property(get_sign, set_sign)

    def get_offset(self):
        """Dial-to-user conversion offset, maybe either 1 or -1"""
        return ensemble_driver.offsets[self.axis_number]

    def set_offset(self, value):
        ensemble_driver.offsets[self.axis_number] = value

    offset = property(get_offset, set_offset)

    def get_dial_low_limit(self):
        """Soft limit. Disable soft limits by settings this value to nan"""
        return ensemble_driver.dial_low_limits[self.axis_number]

    def set_dial_low_limit(self, value):
        ensemble_driver.dial_low_limits[self.axis_number] = value

    dial_low_limit = property(get_dial_low_limit, set_dial_low_limit)

    def get_dial_high_limit(self):
        """Soft limit. Disable soft limits by settings this value to nan"""
        return ensemble_driver.dial_high_limits[self.axis_number]

    def set_dial_high_limit(self, value):
        ensemble_driver.dial_high_limits[self.axis_number] = value

    dial_high_limit = property(get_dial_high_limit, set_dial_high_limit)

    def get_low_limit(self):
        """Soft limit. Disable soft limits by settings this value to nan"""
        return ensemble_driver.low_limits[self.axis_number]

    def set_low_limit(self, value):
        ensemble_driver.low_limits[self.axis_number] = value

    low_limit = property(get_low_limit, set_low_limit)

    def get_high_limit(self):
        """Soft limit. Disable soft limits by settings this value to nan"""
        return ensemble_driver.high_limits[self.axis_number]

    def set_high_limit(self, value):
        ensemble_driver.high_limits[self.axis_number] = value

    high_limit = property(get_high_limit, set_high_limit)

    def get_at_low_limit(self):
        """Is the motor at the positive travel end switch currently?"""
        return ensemble_driver.at_low_limits[self.axis_number]

    at_low_limit = property(get_at_low_limit)

    def get_at_high_limit(self):
        """Is the motor at the negative travel end switch currently?"""
        return ensemble_driver.at_high_limits[self.axis_number]

    at_high_limit = property(get_at_high_limit)

    def get_name(self):
        """string"""
        return ensemble_driver.names[self.axis_number]

    def set_name(self, value):
        ensemble_driver.names[self.axis_number] = value

    name = property(get_name, set_name)

    def get_unit(self):
        """'mm' or 'deg'"""
        return ensemble_driver.units[self.axis_number]

    def set_unit(self, value):
        ensemble_driver.units[self.axis_number] = value

    unit = property(get_unit, set_unit)

    # EPICS motor record process variables
    VAL = command_value
    RBV = value
    DVAL = command_dial
    DRBV = dial
    VELO = speed
    CNEN = enabled
    LLM = low_limit
    HLM = high_limit
    DLLM = dial_low_limit
    DHLM = dial_high_limit
    HLS = at_high_limit
    LLS = at_low_limit
    DESC = name
    EGU = unit
    HOMF = homing
    HOMR = homing
    OFF = offset  # User and dial coordinate difference

    def get_DMOV(self):
        """Done moving?"""
        return not self.moving

    def set_DMOV(self, value):
        self.moving = not value

    DMOV = property(get_DMOV, set_DMOV)

    def get_STOP(self):
        return not self.moving

    def set_STOP(self, value):
        self.moving = not value

    STOP = property(get_STOP, set_STOP)

    def get_MSTA(self):
        """Motor status bits:
        8 = home
        11 = moving
        15 = homed"""
        status_bits = self.homing << 8 | self.moving << 11 | self.homed << 15
        return status_bits

    def set_MSTA(self, value):
        pass

    MSTA = property(get_MSTA, set_MSTA)

    def get_DIR(self):
        """User to dial 0=Pos, 1=Neg"""
        return 0 if self.sign == 1 else 1

    def set_DIR(self, value):
        if value == 0:
            self.sign = 1
        if value == 1:
            self.sign = -1

    DIR = property(get_DIR, set_DIR)

    def get_ACCL(self):
        """Acceleration time to full speed in seconds"""
        T = self.speed / self.acceleration
        return T

    def set_ACCL(self, T):
        self.acceleration = self.speed / T

    ACCL = property(get_ACCL, set_ACCL)


def round_next(x, step):
    """Rounds x up or down to the next multiple of step."""
    if step == 0:
        return x
    x = round(x / step) * step
    # Avoid "negative zero" (-0.0), which is different from +0.0 by IEEE standard
    if x == 0:
        x = abs(x)
    return x


SampleX_driver = EnsembleMotor(0)
SampleY_driver = EnsembleMotor(1)
SampleZ_driver = EnsembleMotor(2)
SamplePhi_driver = EnsembleMotor(3)
PumpA_driver = EnsembleMotor(4)
PumpB_driver = EnsembleMotor(5)
msShut_driver = EnsembleMotor(6)

# Ensemble client, using EPICS channel access.

ensemble_client = Record("NIH:ENSEMBLE")

SampleX = EPICS_motor("NIH:SAMPLEX", name="SampleX", readback_slop=0.005)
SampleY = EPICS_motor("NIH:SAMPLEY", name="SampleY", readback_slop=0.005)
SampleZ = EPICS_motor("NIH:SAMPLEZ", name="SampleZ", readback_slop=0.005)
SamplePhi = EPICS_motor("NIH:SAMPLEPHI", name="SamplePhi")
PumpA = EPICS_motor("NIH:PUMPA", name="PumpA", readback_slop=0.02)
PumpB = EPICS_motor("NIH:PUMPB", name="PumpB")
msShut = EPICS_motor("NIH:MSSHUT", name="msshut", readback_slop=0.09)


# msShut resolution: 360 deg/4000 counts

class EnsembleWrapper(object):
    """This is to make sure that NaNs are substituted when the Ensemble
    driver is offline."""
    naxes = 7

    def __init__(self, name):
        """name: EPICS record name (prefix), e.g. "NIH:ENSEMBLE" """
        self.__record__ = Record(name)

    def __getattr__(self, name):
        """Called when '.' is used."""
        if name.startswith("__") and name.endswith("__"):
            return object.__getattribute__(self, name)
        # debug("EnsembleWrapper.__getattr__(%r)" % name)
        from numpy import asarray
        values = getattr(self.__record__, name)
        if values is None:
            values = self.__default_value__(name)
        if type(values) == str:
            return values
        if not hasattr(values, "__len__"):
            return values
        return asarray(values)

    def __setattr__(self, name, value):
        """Called when '.' is used."""
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self, name, value)
        # debug("EnsembleWrapper.__setattr__(%r,%r)" % (name,value))
        setattr(self.__record__, name, value)

    def __default_value__(self, name):
        from numpy import zeros, nan
        if name == "program_filename":
            value = ""
        elif name == "auxiliary_task_filename":
            value = ""
        elif name == "program_directory":
            value = ""
        elif name == "program_running":
            value = nan
        elif name == "auxiliary_task_running":
            value = nan
        elif name == "fault":
            value = nan
        elif name == "connected":
            value = nan
        elif name.startswith("UserInteger"):
            value = nan
        elif name.startswith("UserDouble"):
            value = nan
        elif name.startswith("UserString"):
            value = ""
        elif name == "integer_registers":
            value = zeros(Ensemble.max_integer_registers) + nan
        elif name == "floating_point_registers":
            value = zeros(Ensemble.max_floating_point_registers) + nan
        else:
            value = zeros(self.naxes) + nan
        return value


ensemble = EnsembleWrapper("NIH:ENSEMBLE")


class EnsembleMotors(EnsembleWrapper):
    """Multi-axis coordinated motion"""

    def axes_numbers(self, axes_names):
        from numpy import where
        return [where(self.names == name)[0][0] for name in axes_names]

    def move(self, axes_names, positions):
        """Perform a coordinated move, on multiple axs simultaneously.
        names: list of strings
        positions: list of real numbers"""
        values = self.command_values
        values[self.axes_numbers(axes_names)] = positions
        self.command_values = values

    def positions(self, axes_names):
        """Not yet at destination?"""
        return self.values[self.axes_numbers(axes_names)]

    def are_moving(self, axes_names):
        """Not yet at destination?"""
        return self.moving[self.axes_numbers(axes_names)]


ensemble_motors = EnsembleMotors("NIH:ENSEMBLE")


def program_directory():
    """Location of Aerobasic programs"""
    from module_dir import module_dir
    return module_dir(Ensemble) + "/Ensemble"


def start_IOC():
    """Serve the Ensemble EPAQ up on the network as EPICS IOC"""
    import CAServer
    # CAServer.verbose_logging = True
    # CAServer.verbose = True
    CAServer.update_interval = 0.25
    # CAServer.DEBUG = True
    # CAServer.LOG = True
    ensemble_driver.connect()
    CAServer.register_object(ensemble_driver, "NIH:ENSEMBLE")
    CAServer.register_object(SampleX_driver, "NIH:SAMPLEX")
    CAServer.register_object(SampleY_driver, "NIH:SAMPLEY")
    CAServer.register_object(SampleZ_driver, "NIH:SAMPLEZ")
    CAServer.register_object(SamplePhi_driver, "NIH:SAMPLEPHI")
    CAServer.register_object(PumpA_driver, "NIH:PUMPA")
    CAServer.register_object(PumpB_driver, "NIH:PUMPB")
    CAServer.register_object(msShut_driver, "NIH:MSSHUT")


server = tcp_server(globals=globals(), locals=locals())
server.ip_address_and_port_db = "Ensemble.ip_address"


def start_TCP_server(): server.start()


def run_TCP_server(): server.run()


def start_server():
    """Start EPICS IOC and TCP server returning control"""
    start_IOC()
    start_TCP_server()


def run_server():
    """Run EPICS IOC and TCP servers without returning control"""
    start_server()
    wait()


def wait():
    """Halt execution"""
    from time import sleep
    while True:
        sleep(0.1)


if __name__ == "__main__":
    # Output error messages to console and file at te same time.
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # for debugging
    self = ensemble_driver
    print('start_server()')

    filename = "Home (safe).ab"
    print('ensemble_driver.program_filename = %r' % filename)
    print('ensemble_driver.run_local_program(%r)' % filename)
    print('ensemble_driver.program_running')
    # print('ensemble_driver.auxiliary_task_running')
    print('ensemble_driver.UserString1')
    print('ensemble.program_filename = %r' % filename)
    print('ensemble.program_running')
    print('ensemble.UserString1')
    # print('ensemble.auxiliary_task_running')
