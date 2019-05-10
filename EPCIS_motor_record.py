"""Prototype for an EPICS motor record to be used as base class.
Documentation: aps.anl.gov/bcda/synApps/motor/R6-7/motorRecord.html
"""

__version__ = "1.0"

class motor_record(object):
    """Prototype for an EPICS motor record to be used as base class"""

    def __init__(self,record_name=""):
        if record_name != "":
            from CAServer_new import register_object
            register_object(self,record_name)
        
    def get_VAL(self):
        """Command position"""
        return getattr(self,"__VAL__",0.0)
    def set_VAL(self,value):
        self.__VAL__ = value
    VAL = property(get_VAL,set_VAL)

    def get_RBV(self):
        """Actual position"""
        return self.VAL
    RBV = property(get_RBV)

    EGU = "mm"
    DESC = "Test"
    PREC = 4 # number of digits
    DIR = 0 # positive or negative user vs dial direction
            
    def get_DMOV(self):
        """Done moving: Has the motor reached the set point within
        tolerance?
        For scans, to provide feedback whether the temperature 'motor'
        is still 'moving'"""
        return 0
    DMOV = property(get_DMOV)

    def get_STOP(self): return 0
    def set_STOP(self,value):
        """If value = True, cancel the current move."""
        if value == 1: pass
    STOP = property(get_STOP,set_STOP)

    TWV = 1.0 # Tweak value (step size)

    def get_TWR(self): return 0 
    def set_TWR(self,value):
        print value
        if value != 0: self.VAL -= self.TWV 
    TWR = property(get_TWR,set_TWR)

    def get_TWF(self): return 0 
    def set_TWF(self,value):
        if value != 0: self.VAL += self.TWV 
    TWF = property(get_TWF,set_TWF)

    PCOF = 0.0
    ICOF = 0.0
    DCOF = 0.0
    
if __name__ == "__main__":
    """for testing"""
    motor = motor_record("14IDB:SAMPLEX")
    # Control panel: medm -x -attach -macro P=NIH:,M=TEST motorx.adl
    import CAServer_new; CAServer_new.verbose_logging = True
    self = motor
