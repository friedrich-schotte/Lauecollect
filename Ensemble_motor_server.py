"""Aerotech  Motion Controller
Communication via Aeroch's C library interface using a proprietary
protocol by Aerotech.
Author: Friedrich Schotte
Date created: 2019-08-15
Date lst modified: 2019-08-15
"""
__version__ = "1.0" 
from logging import debug,info,warn,error

class Ensemble_Server(object):
    name = "ensemble_server"
    
    def __init__(self):
        from EPICS_motor_record import EPICS_Motor_Record
        self.motors = [EPICS_Motor_Record(self.prefix+name.upper())
            for name in self.motor_names]
        for axis_number,motor in enumerate(self.motors):
            motor.monitor("VAL",self.on_VAL,axis_number)

    motor_names = "SampleX","SampleY","SampleZ","SamplePhi","PumpA","PumpB",##"msshut"

    from persistent_property import persistent_property
    prefix = persistent_property("prefix","TESTBENCH:")
            
    def get_EPCIS_enabled(self):
        return all([motor.EPICS_enabled for motor in self.motors])
    def set_EPCIS_enabled(self,value):
        for motor in self.motors: motor.EPICS_enabled = value
    EPICS_enabled = property(get_EPCIS_enabled,set_EPCIS_enabled)

    from thread_property_2 import thread_property
    @thread_property
    def running(self):
        self.initialize()
        from time import sleep
        while not self.running_cancelled:
            self.update_once()
            sleep(0.1)

    def initialize(self):
        """To be done once a startup"""
        for axis_number,motor in enumerate(self.motors):
            pass
            ##motor.VAL = self.status(axis_number,self.PositionFeedback)
            ##motor.VAL = self.status(axis_number,self.PositionCommand)
                
    def update_once(self):
        for axis_number,motor in enumerate(self.motors):
            motor.RBV = self.status(axis_number,self.PositionFeedback)

    # EnsembleCommonStructures.h, STATUSITEM
    PositionCommand = 0
    PositionFeedback = 1
    AxisStatus = 3
    AxisFault = 4

    def on_VAL(self,axis_number):
        value = self.motors[axis_number].VAL
        self.MoveAbs(axis_number,value)

    def MoveAbs(self,axis_number,value):
        self.connect()
        if self.connected:
            info("Moving axis %r to %r" % (axis_number,value))
            speed = self.motors[axis_number].VELO
            axis_mask = (1 << axis_number)
            from ctypes import ARRAY,c_int,c_double
            c_values = ARRAY(c_double,1)(value)
            c_speeds = ARRAY(c_double,1)(speed)
            success = self.library.EnsembleMotionMoveAbs(self.handle,
                c_int(axis_mask),c_values,c_speeds)
            if success != True:
                error("EnsembleMotionMoveAbs(axis_mask=%s,pos=%r,speed=%r) failed"
                    % (bin(axis_mask),value,speed))

    def status(self,axis_number,code):
        """A floating point value
        axis_number: 0-based index
        code: e.g. 1 = PositionFeedback"""
        from numpy import nan
        status = nan
        self.connect()
        if self.connected:
            from ctypes import byref,c_int,c_double
            c_value = c_double()
            success = self.library.EnsembleStatusGetItem(self.handle,
                c_int(axis_number),c_int(code),byref(c_value))
            if success != True:
                error("EnsembleStatusGetItem(%r,%r) failed" % (axis_number,code))
            status = c_value.value
        return status
        
    def get_connected(self):
        """Is a communication link with the controller established?"""
        return self.handle is not None
    def set_connected(self,value):
        if value: self.connect()
        else: self.disconnect()
    connected = property(get_connected,set_connected)

    def connect(self):
        """Establish a connection to the controller"""
        if not hasattr(self.library,"EnsembleConnect"): return
        
        if self.handle is not None: return
        
        from ctypes import byref,c_void_p,c_int,POINTER
        if self.library is not None and self.handle is None:
            handles = POINTER(c_void_p)()
            handle_count = c_int()
            success = self.library.EnsembleConnect(byref(handles),
                byref(handle_count))
            if success and handle_count.value >= 1:
                self.handle = handles.contents
            else: error("Unable to connect to Ensemble controller")

    def disconnect(self):
        """Undo 'connect'"""
        if self.library is None: return
        if self.handle is None: return
        from ctypes import c_void_p,POINTER
        handles = POINTER(c_void_p)()
        handles.contents = self.handle
        success = self.library.EnsembleDisconnect(handles)
        if success == True: self.handle = None
        else: error("disconnect failed")

    handle = None

    @property
    def library(self):
        from Ensemble_library import ensemble_library as library
        return library

ensemble_server = Ensemble_Server()


def run_server():
    ensemble_server.EPICS_enabled = True
    ensemble_server.running = True
    from time import sleep
    try:
        while True: sleep(0.1)
    except KeyboardInterrupt: pass


if __name__ == "__main__":
    from pdb import pm
    import logging
    format="%(asctime)s: %(levelname)s %(module)s.%(funcName)s %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=format)

    self = ensemble_server

    def monitor_object(object):
        for name in dir(object):
            if name.isupper(): object.monitor(name,report,object,name)
    def report(object,name): info("%s.%s = %r" % (object.__name__,name,getattr(object,name)))
    def monitor(self):
        for motor in self.motors: monitor_object(motor)

    print('self.prefix = %r' % self.prefix)
    print('')
    print('self.prefix = "TESTBENCH:"')
    print('self.prefix = "NIH:"')
    print('')
    print('run_server()')
    print('')
    ##self.EPICS_enabled = True
    print('self.EPICS_enabled = True')
    print('self.running = True')
    print('self.update_once()')
    print('monitor(self)')
    print('self.motors[0].DVAL += 0.001')
    from CA import caget,caput,camonitor
    print('camonitor("TESTBENCH:SAMPLEX.VAL")')
    print('camonitor("TESTBENCH:SAMPLEX.RBV")')
    print('camonitor("TESTBENCH:SAMPLEX.DMOV")')
