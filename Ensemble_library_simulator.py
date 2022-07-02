"""Aerotech  Motion Controller
Communication via Aeroch's C library interface using a proprietary
protocol by Aerotech.
Author: Friedrich Schotte
Date created: 2019-08-15
Date lst modified: 2019-08-15
"""
__version__ = "1.0" 
from logging import debug,info,warn,error

class Ensemble_Library(object):
    # EnsembleCommonStructures.h, STATUSITEM
    PositionCommand = 0
    PositionFeedback = 1
    AxisStatus = 3
    AxisFault = 4

    @staticmethod
    def EnsembleConnect(ref_handles,ref_handle_count):
        from ctypes import cast,c_void_p,c_int,POINTER
        ##debug("ref_handles=%r, ref_handles=%r" % (ref_handles,ref_handle_count))
        handles_ = cast(ref_handles,POINTER(POINTER(c_void_p))).contents
        x = c_void_p(0xFFFFFFFF)
        handles_.contents = POINTER(c_void_p)(x)
        handle_count_ = cast(ref_handle_count,POINTER(c_int)).contents
        handle_count_.value = 1
        return 1
    
    @staticmethod
    def EnsembleStatusGetItem(handle,c_axis_number,c_code,ref_value):
        ##debug("handle=%r, c_axis_number=%r, c_code=%r, ref_value=%r" % (handle,c_axis_number,c_code,ref_value))
        from ctypes import cast,c_double,c_int,POINTER
        axis_number = c_axis_number.value
        code = c_code.value
        c_value_ = cast(ref_value,POINTER(c_double)).contents
        from Ensemble_simulator import ensemble_simulator
        ensemble_simulator.axes[axis_number].value
        if code == Ensemble_Library.PositionFeedback:
            c_value_.value = ensemble_simulator.axes[axis_number].value
        if code == Ensemble_Library.PositionCommand:
            c_value_.value = ensemble_simulator.axes[axis_number].command_value
        return 1

    @staticmethod
    def EnsembleMotionMoveAbs(handle,c_axis_mask,c_values,c_speeds):
        ##debug("handle=%r, c_axis_mask=%r, c_values=%r, c_speeds=%r" % (handle,c_axis_mask,c_values,c_speeds))
        from ctypes import cast,c_double,c_int,POINTER
        axis_mask = c_axis_mask.value
        from Ensemble_simulator import ensemble_simulator
        axis_numbers = []
        for axis_number in range(0,ensemble_simulator.naxes):
            if (axis_mask & (1 << axis_number)) != 0: axis_numbers.append(axis_number)
        for i,axis_number in enumerate(axis_numbers):
            value = c_values[i]
            speed = c_speeds[i]
            debug("Simulating move of axis %r to %g at speed %r." % (axis_number+1,value,speed))
            ensemble_simulator.axes[axis_number].speed = speed
            ensemble_simulator.axes[axis_number].command_value = value
        return 1
        

ensemble_library = Ensemble_Library()

if __name__ == "__main__":
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s: %(levelname)s %(message)s")

    self = ensemble_library
    from ctypes import byref,c_void_p,c_int,c_double,POINTER,cast
    handles = POINTER(c_void_p)()
    handle_count = c_int()
    ref_handles = byref(handles)
    ref_handle_count = byref(handle_count)
    print('success = self.EnsembleConnect(byref(handles),byref(handle_count))')
    ##print('success,handles.contents,handle_count.value')
    handle = c_void_p(4444307616)
    print('handle = handles.contents')
    PositionFeedback = 1
    axis_number = 0
    c_value = c_double()
    code = PositionFeedback
    c_axis_number = c_int(axis_number)
    c_code = c_int(code)
    print('success = self.EnsembleStatusGetItem(handle,c_int(axis_number),c_int(code),byref(c_value))')
    print('c_value.value')
