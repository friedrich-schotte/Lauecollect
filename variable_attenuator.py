"""
Motorized variable neutral density filter to control the laser power
for power titration experiments.
This attunator is controlled by a Thorlabs Z612 actuator. A circulator
gardient filter is mounter directly only the lead screw to rotate the
filter. With a screw pitch of 0.5 mm, 0.5 mm of linear translation corresponds
to 360 deg of rotation.

Friedrich Schotte, 22 Feb 2008 - 27 Oct 2016
"""
__version__ = "1.5.1" # motor name

from math import log10

nan = 1e1000/1e1000 # Not a Number
def isnan(x): return x!=x

class variable_attenuator(object):
    """Motorized variable neutral density filter for controling the laser power
    for power titration experiments.
    """
    
    def __init__(self,motor,OD_range=[0,2.66],motor_range=[15,345],
        motor_min=None,OD_min=None,motor_max=None,OD_max=None):
        """'motor' is motor controlled by an EPICS motor record
        'motor_range=[15,345]',OD_range=[0,2.66]' means that
        The attenuation varies from 0 to 2.66 (2.7-0.04) over a range of 330 deg,
        which starts at 15 deg.
        """
        self.motor = motor
        self.unit = ""
        self.motor_range = motor_range
        self.OD_range = OD_range
        if motor_min == None: self.motor_min = motor_range[0]
        if motor_max == None: self.motor_max = motor_range[1]
        if OD_min == None: self.OD_min = OD_range[0]
        if OD_max == None: self.OD_max = OD_range[1]

    def get_value(self):
        """Calculates the transmission from the motor position"""
        return self.transmission(self.motor.value)
      
    def set_value(self,transmission):
        """Rotates the filter to a new orienation, based on the desired
        transmission"""
        position = self.position_of_transmission(transmission)
        if position != self.motor.command_value: self.motor.value = position
      
    value = property(fset=set_value,fget=get_value,
        doc="transmission of filter, range 0 to 1")

    def get_angle(self):
        "Motor position"
        return self.motor.value
      
    def set_angle(self,position):
        "Drives the motor to a new position"
        self.motor.value = position
      
    angle = property(get_angle,set_angle,doc="Orientation of wheel")

    position = property(get_angle,set_angle,doc="same as angle")

    def transmission(self,position):
        """Calculates the transmission from the motor position in mm"""
        if isnan(position): return nan

        if position == self.motor_max: return pow(10,-self.OD_max)
        if position == self.motor_min: return pow(10,-self.OD_min)

        pmin = self.motor_range[0]; pmax = self.motor_range[1]
        # Assume the transmission is flat outside the angular range
        if position < min(pmin,pmax): position = min(pmin,pmax)
        if position > max(pmin,pmax): position = max(pmin,pmax)
        # Inside the angular range, assume that there is a linear gradient of OD 
        OD = self.OD_range[0] + (position-pmin)/(pmax-pmin)*self.OD_range[1]
        transmission = pow(10,-OD)
        return transmission

    def position_of_transmission(self,transmission):
        """Calculates the motor position in mm for a desired transmission"""
        if transmission <= 0: transmission = 1e-6
        OD = -log10(transmission)
        
        if OD >= self.OD_max: return self.motor_max
        if OD <= self.OD_min: return self.motor_min
        
        pmin = self.motor_range[0]; pmax = self.motor_range[1]
        position = pmin + (OD-self.OD_range[0])/self.OD_range[1]*(pmax-pmin)
        # Assume the transmission is flat outside the angular range
        if position < min(pmin,pmax): position = min(pmin,pmax)
        if position > max(pmin,pmax): position = max(pmin,pmax)
        return position

    def set_moving(self,value): self.motor.moving = value

    moving = property(lambda self: self.motor.moving,set_moving,
        doc="Is filter currently moving?")

    def __repr__(self):
        return "variable_attenuator(%r,OD_range=[%g,%g],motor_range=[%g,%g])" \
            % (self.motor,self.OD_range[0],self.OD_range[1],
            self.motor_range[0],self.motor_range[1])

    
if __name__ == "__main__": # for testing - remove when done

    from EPICS_motor import motor # EPICS-controlled motors
    
    # Laser beam attenuator wheel in 14ID-B X-ray hutch
    VNFilter = motor("14IDB:m32",name="VNFilter")
    VNFilter.readback_slop = 0.1 # [deg] otherwise Thorlabs motor gets hung in "Moving" state
    VNFilter.min_step = 0.050 # [deg] otherwise Thorlabs motor gets hung in "Moving" state"
    # This filter is mounted such that when the motor is homed (at 0) the
    # attuation is minimal (OD 0.04) and increasing to 2.7 when the motor
    # moves in positive direction.
    # Based on measurements by Hyun Sun Cho and Friedrich Schotte, made 7 Dec 2009
    trans = variable_attenuator(VNFilter,motor_range=[5,285],OD_range=[0,2.66])
    trans.motor_min=-5
    trans.OD_min=0
    trans.motor_max=300
    trans.OD_max=2.66

    # 14-ID Laser Lab
    VNFilter1 = motor("14IDLL:m8",name="VNFilter1")
    VNFilter1.readback_slop = 0.030 # otherwise Thorlabs motor gets hung in "Moving" state
    VNFilter1.min_step = 0.030 # otherwise Thorlabs motor gets hung in "Moving" state"
    # This filter is mounted such that when the motor is homed (at 0) the
    # attuation is minimal (OD 0.04) and increasing to 2.7 when the motor
    # moves in positive direction.
    trans1 = variable_attenuator(VNFilter1,motor_range=[15,295],OD_range=[0,2.66])
    trans1.motor_min=0
    trans1.OD_min=0
    trans1.motor_max=315
    trans1.OD_max=2.66

