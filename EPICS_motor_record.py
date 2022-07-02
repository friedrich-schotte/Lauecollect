"""
EPICS-controlled motor
Using the following process variables:
VAL - nominal position
RBV - read back value
DVAL - dial nominal position
DRBV - dial read back value
HLM - high limit
LLM - low limit
DESC - description
EGU - unit
DMOV - 0 if currently moving, 1 if done
SPDB - Set point deadband: acceptable difference between DRBV and DVAL
STOP - set to 1 momentarily to stop ?
VELO - speed in mm/s
CNEN - enabled
DIR - user to dial sign
OFF - user to dial offset
HLS - at high limit switch
LLS - at low limit switch
HOMF - homing
HOMR - homing
MSTA - motor status bits: bit 8 = home, bit 11 = moving, bit 15 = homed
ACCL - acceleration time to full speed in seconds

Documentation:
"Motor Record and related software"
https://epics.anl.gov/bcda/synApps/motor/motorRecord.html#Fields_motion

Author: Friedrich Schotte
Date created: 2019-08-13
Date last modified: 2019-08-15
"""
__version__ = "1.0"

from logging import debug,info,warning,error
from traceback import format_exc

from EPICS_record import EPICS_Record

class EPICS_Motor_Record(EPICS_Record):
    from persistent_property import persistent_property
    from record import depends_on,invoke_on,always_invoke_on
    from numpy import inf

    def __init__(self,*args,**kwargs):
        EPICS_Record.__init__(self,*args,**kwargs)

    DVAL = persistent_property("DVAL",0.0) # dial nominal position
    DRBV = persistent_property("DRBV",0.0)
    OFF  = persistent_property("OFF",0.0)
    DIR  = persistent_property("DIR",1)
    DHLM = persistent_property("DHLM",inf)
    DLLM = persistent_property("DLLM",-inf)
    DESC = persistent_property("DESC","Motor")
    EGU  = persistent_property("EGU","mm")
    DMOV = 1   # 0 if currently moving, 1 if done
    SPDB = persistent_property("SPDB",0.0) # Set point deadband
    STOP = 0   # set to 1 momentarily to stop ?
    VELO = persistent_property("VELO",1.0) # speed in mm/s
    CNEN = 1   # enabled
    HLS  = 0   # at high limit switch
    LLS  = 0   # at low limit switch

    @depends_on("DVAL","dial_to_user")
    def get_VAL(self): return self.dial_to_user(self.DVAL)
    def set_VAL(self,value): self.DVAL = self.dial_to_user(value)
    VAL = property(get_VAL,set_VAL)

    @depends_on("DRBV","dial_to_user")
    def get_RBV(self): return self.dial_to_user(self.DRBV)
    def set_RBV(self,value): self.DRBV = self.dial_to_user(value)
    RBV = property(get_RBV,set_RBV)
    
    @always_invoke_on("VAL","DVAL")
    def reset_DMOV(self):
        ##debug("reset_DMOV called")
        # DMOV is guaranteed to execute and post a 1/0/1 pulse when the motor
        # is commanded to move--even if no motion actually occurs because the
        # motor was commanded to move to its current position.
        if self.DMOV != 0: self.DMOV = 0
        if abs(self.DRBV - self.DVAL) <= self.SPDB: self.DMOV = 1

    @invoke_on("DRBV","DVAL","SPDB")
    def assert_DMOV(self):
        if abs(self.DRBV - self.DVAL) <= self.SPDB: self.DMOV = 1

    @depends_on("DHLM","DLLM","DIR","dial_to_user")
    def get_HLM(self):
        return self.dial_to_user(self.DHLM if self.DIR > 0 else self.DLLM)
    def set_HLM(self,value):
        if self.DIR > 0: self.DHLM = self.dial_to_user(value)
        if self.DIR < 0: self.DLLM = self.dial_to_user(value)
    HLM = property(get_HLM,set_HLM)

    @depends_on("DHLM","DLLM","DIR","dial_to_user")
    def get_LLM(self):
        return self.dial_to_user(self.DLLM if self.DIR > 0 else self.DHLM)
    def set_LLM(self,value):
        if self.DIR > 0: self.DLLM = self.dial_to_user(value)
        if self.DIR < 0: self.DHLM = self.dial_to_user(value)
    LLM = property(get_LLM,set_LLM)

    @depends_on("OFF","DIR")
    def dial_to_user(self,DVAL): return DVAL*self.DIR + self.OFF

    @depends_on("OFF","DIR")
    def user_to_dial(self,VAL): return (VAL-self.OFF) / self.DIR


if __name__ == "__main__":
    from pdb import pm
    import logging
    format="%(asctime)s: %(levelname)s %(module)s.%(funcName)s %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=format)
    
    self = EPICS_Motor_Record("TESTBENCH:TEST")

    def report(object,name): info("%s = %r" % (name,getattr(object,name)))
    def monitor(object):
        for name in dir(object):
            if name.isupper(): object.monitor(name,report,object,name)
    ##monitor(self)
    print('monitor(self)')
    self.EPICS_enabled = True
    from CA import caget,caput,camonitor
    print('camonitor("TESTBENCH:TEST.VAL")')
    print('camonitor("TESTBENCH:TEST.RBV")')
    print('camonitor("TESTBENCH:TEST.DMOV")')
    print('caput("TESTBENCH:TEST.VAL",caget("TESTBENCH:TEST.VAL")+0.001)')
    print('')
    print("self.VAL += 0.001 # start move")
    print("self.DRBV = self.DVAL # finish move")
    print("self.VAL += 0 # move to current position")
