"""
This is a utility to test the scan software without using any hardware.

Friedrich Schotte, NIH 13 Mar 2008

Run simuation:
app=wx.App(False)
data=rscan(sim_mot,-0.2,0.2,50,sim_det,plot=True)
COM(data)
FWHM(data),RMSD(data),CFWHM(data),COM(data)
"""

from scan import *

class simulated_motor(object):
    "Simulates a motor in software without moving anything"
    def __init__(self,name="dummy",speed=Inf,value=0):
        object.__init__(self)
        self.name  = name
        self.speed = speed
        self.target_value = value
        self.starting_value = value
        self.move_started = time()

    def get_value(self):
        dt = time() - self.move_started
        if isinf(self.speed): return self.target_value
        if self.target_value >= self.starting_value:
            return min(self.starting_value + dt*self.speed, self.target_value)
        else:
            return max(self.starting_value - dt*self.speed, self.target_value)
    def set_value(self,value):
        self.starting_value = self.value
        self.target_value = value
        self.move_started = time() # Record the time the last move was initiated.
    value = property(get_value,set_value,doc="""Position of motor (user value)""")

    def get_moving(self):
        return (self.value != self.target_value)
    moving = property(get_moving,doc="True if currently moving, False if done")

    def wait(self):
        "If the motor is moving, returns control after current move move is complete."
        while self.moving: sleep(0.01)


class simulated_detector(object):
    """Simulates a detector. The detector reading is dependent on the
    position of a simulates motor.
    """
    def __init__(self,name="dummy",motor=simulated_motor(),center=0,FWHM=0.1):
        object.__init__(self)
        self.name  = name
        self.motor = motor
        self.center = center
        self.FWHM = FWHM

    def get_value(self):
        x = self.motor.value
        cx = self.center
        sx = self.FWHM / (2*sqrt(2*log(2)))
        y = exp(-0.5*((x-cx)/sx)**2)
        return y
    value = property(fget=get_value,doc="simulates a measurement")

#sim_mot = simulated_motor("sim_mot",speed=0.2,value=69.0286)
sim_mot = simulated_motor("sim_mot",speed=Inf,value=0)
sim_det = simulated_detector("sim_det",motor=sim_mot,center=sim_mot.value,
    FWHM=0.1)

# This is for testing, remove when done

# Needed for plot window:
if not "app" in globals(): app = wx.App(0)

