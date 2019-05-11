"""
Boxer perstaltic pump, controlled by a stpper motor, controller by Aerotech
Ensemble EPAQ motion controller.
Friedrich Schotte, Jun 27, 2014 - 19 Jun 2015
"""
from logging import debug

__version__ = "1.1.5"

from Ensemble import PumpA,PumpB,ensemble_motors

class LinearCombinationMotor(object):
    """Linear combinations of motor positions
    (average,difference)"""
    def __init__(self,coefficients,number,**kwargs):
        """
        coefficients: [[1,0],[0,1]],
        number 0: first motor, 1: second motor
        coefficients: [[0.5,0.5],[-1,1]],
        number 0: average, number 1: difference
        """
        from numpy import asarray
        self.coefficients = asarray(coefficients)
        self.number = number

        for key in kwargs: setattr(self,key,kwargs[key])

    @property
    def axis_numbers(self):
        """0-based axis numbers of the motor controllers for the pumps inside
        the Ensemble controller."""
        return ensemble_motors.axes_numbers(["PumpA","PumpB"])
    
    def combined_values(self,hardware_values):
        from numpy import asarray,dot      
        x = asarray(hardware_values)
        T = self.coefficients
        y = dot(T,x)
        return y

    def hardware_values(self,combined_values):
        from numpy import asarray,dot
        from numpy.linalg import inv
        y = asarray(combined_values)
        T = self.coefficients
        x = dot(inv(T),y)
        return x
    
    def get_command_value(self):
        from numpy import asarray
        v = asarray(ensemble_motors.command_values)[self.axis_numbers]    
        combined_values = self.combined_values(v)
        value = combined_values[self.number]
        return value
    def set_command_value(self,value):
        from numpy import asarray
        all_Vs = asarray(ensemble_motors.command_values)
        debug("command_values %r" % all_Vs)
        v = all_Vs[self.axis_numbers]
        combined_values = self.combined_values(v)
        combined_values[self.number] = value
        all_Vs[self.axis_numbers] = self.hardware_values(combined_values)
        debug("command_values %r" % all_Vs)
        ensemble_motors.command_values = all_Vs
    command_value = property(get_command_value,set_command_value)
        
    def get_value(self):
        from numpy import asarray
        v = asarray(ensemble_motors.values)[self.axis_numbers]    
        return self.combined_values(v)[self.number]
    value = property(get_value,set_command_value)

    unit = "deg"

    def get_moving(self):
        from numpy import asarray
        return any(asarray(ensemble_motors.moving)[self.axis_numbers])
    def set_moving(self,value):
        from numpy import asarray
        moving = asarray(ensemble_motors.moving)
        moving[self.axis_numbers] = value
        ensemble_motors.moving = moving
    moving = property(get_moving,set_moving)

    def wait(self):
        """Do not return until current motion has stopped"""
        from time import sleep
        while self.moving: sleep(0.05)

    def get_speed(self):
        from numpy import asarray
        return max(asarray(ensemble_motors.speeds)[self.axis_numbers])
    def set_speed(self,value):
        from numpy import asarray
        speeds = asarray(ensemble_motors.speeds)
        speeds[self.axis_numbers] = value
        ensemble_motors.speeds = speeds
    speed = property(get_speed,set_speed)


class PeristalticPump(object):
    """"""
    V1 = LinearCombinationMotor([[1,0],[0,1]],0,name="PumpA")
    V2 = LinearCombinationMotor([[1,0],[0,1]],1,name="PumpB")
    V  = LinearCombinationMotor([[0.5,0.5],[0.5,-0.5]],0,name="PumpA+B+")
    dV = LinearCombinationMotor([[0.5,0.5],[0.5,-0.5]],1,name="PumpA-B+")

peristaltic_pump = PeristalticPump()
# Shortcuts:
p = peristaltic_pump

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    self = p.V # for debugging
    print 'p.V1.value'
    print 'p.V2.value'
    print 'p.V.value'
    print 'p.dV.value'

