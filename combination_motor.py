"""Combination motor for slit gap and center, based on motor for individual
blades
Friedrich Schotte, 14 Dec 2010 - Jun 28, 2017
"""

__version__ = "1.0.1"

class gap(object):
    """Combination motor for slit"""
    def __init__(self,blade1,blade2):
        self.blade1 = blade1
        self.blade2 = blade2

    def get_value(self):
        return self.blade1.value-self.blade2.value
    value = property(get_value)
    

class center(object):
    """Combination motor"""
    def __init__(self,blade1,blade2):
        self.blade1 = blade1
        self.blade2 = blade2

    def get_value(self):
        return (self.blade1.value+self.blade2.value)/2
    value = property(get_value)

class tilt(object):
    """Combination motor"""
    name = "tilt"
    from persistent_property import persistent_property
    offset = persistent_property("offset",0.0)
    sign = persistent_property("sign",+1)
    unit = persistent_property("unit","mrad")

    def __init__(self,m1,m2,distance=1.0,name=None,unit=None):
        self.m1 = m1
        self.m2 = m2
        self.distance = distance
        if name is not None: self.name = name
        if unit is not None: self.unit = unit

    def get_dial(self):
        """Readback value, in dial units"""
        return self.theta(self.m1.dial,self.m2.dial)
    def set_dial(self,value):
        self.m1.dial,self.m2.dial = \
            self.x1_x2(self.m1.dial,self.m2.dial,value)
    dial = property(get_dial,set_dial)

    def get_command_dial(self):
        """Target value, in dial units"""
        return self.theta(self.m1.command_dial,self.m2.command_dial)
    def set_command_dial(self,value):
        self.m1.command_dial,self.m2.command_dial = \
            self.x1_x2(self.m1.command_dial,self.m2.command_dial,value)
    command_dial = property(get_command_dial,set_command_dial)

    def get_value(self):
        """Readback value, in user units, taking into account offset"""
        return self.user_from_dial(self.dial)
    def set_value(self,value):
        self.dial = self.dial_from_user(value)
    value = property(get_value,set_value)

    def get_command_value(self):
        """Target value, in user units, taking into account offset"""
        return self.user_from_dial(self.dial)
    def set_command_value(self,command_value):
        self.dial = self.dial_from_user(command_value)
    command_value = property(get_command_value,set_command_value)

    def theta(self,x1,x2):
        """Tilt angle in mrad as function of jack positions in mm"""
        return (x1-x2)/self.distance

    def x1_x2(self,x1,x2,theta):
        """New positions for new tilt angle in mm"""
        # Keep the center constant
        dtheta = theta - self.theta(x1,x2)
        dx = dtheta*self.distance
        x1,x2 = x1 + dx/2,x2 - dx/2
        return x1,x2

    def user_from_dial(self,value): return value * self.sign + self.offset  
    def dial_from_user(self,value): return (value - self.offset) / self.sign


if __name__ == "__main__":
    from EPICS_motor import motor
    print('motor("14IDC:m12").value = %.6f # mir2X1' % motor("14IDC:m12").value)
    print('motor("14IDC:m13").value = %.6f # mir2X2' % motor("14IDC:m13").value)
    print('motor("14IDC:mir2Th").value = %.6f' % motor("14IDC:mir2Th").value)
    mir2X1 = motor("14IDC:m12",name="mir2X1") # H mirror X1-upstream
    mir2X2 = motor("14IDC:m13",name="mir2X2") # H mirror X1-downstream
    print("mir2X1.__prefix__ = %r" % mir2X1.__prefix__)
    print("mir2X2.__prefix__ = %r" % mir2X2.__prefix__)
    print("mir2X1.value = %.6f" % mir2X1.value)
    print("mir2X2.value = %.6f" % mir2X2.value)
    mir2Th = tilt(mir2X1,mir2X2,distance=1.045,name="mir2Th")
    print("mir2Th.offset = %r" % mir2Th.offset)
    print("mir2Th.value = %.6f" % mir2Th.value)
    stepsize = 0.000416*2/1.045
    print("mir2Th.value += %.6f" % (stepsize*3))
    self = mir2Th
    

