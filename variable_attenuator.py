"""
Motorized variable neutral density filter to control the laser power
for power titration experiments.
This attenuator is controlled by a Thorlabs Z612 actuator. A circular
gradient filter is mounter directly only the lead screw to rotate the
filter. With a screw pitch of 0.5 mm, 0.5 mm of linear translation corresponds
to 360 deg of rotation.

Friedrich Schotte
Date created: 2008-02-22
Date last modified: 2022-07-14
Revision comment: Exact readback_slop
"""
__version__ = "1.7.3"

from math import log10
from numpy import nan, isnan

from alias_property import alias_property
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property


class variable_attenuator(object):
    """Motorized variable neutral density filter for controlling the laser power
    for power titration experiments.
    """
    unit = ""
    OD_range = [0, 2.66]
    motor_range = [15, 345]

    def __init__(self, motor, OD_range=None, motor_range=None,
                 motor_min=None, OD_min=None, motor_max=None, OD_max=None):
        """'motor' is motor controlled by an EPICS motor record
        'motor_range=[15,345]',OD_range=[0,2.66]' means that
        The attenuation varies from 0 to 2.66 (2.7-0.04) over a range of 330 deg,
        which starts at 15 deg."""
        self.motor = motor
        if OD_range is not None:
            self.OD_range = OD_range
        if motor_range is not None:
            self.motor_range = motor_range

        if motor_min is not None:
            self.motor_min = motor_min
        else:
            self.motor_min = motor_range[0]

        if motor_max is not None:
            self.motor_max = motor_max
        else:
            self.motor_max = motor_range[1]

        if OD_min is not None:
            self.OD_min = OD_min
        else:
            self.OD_min = OD_range[0]

        if OD_max is not None:
            self.OD_max = OD_max
        else:
            self.OD_max = OD_range[1]

    def __repr__(self):
        return f"variable_attenuator({self.motor}, OD_range={self.OD_range}, motor_range={self.motor_range}])"

    @monitored_property
    def command_value(self, angle_command_value):
        return self.transmission(angle_command_value)

    @command_value.setter
    def command_value(self, transmission):
        # Rotate the filter to a new orientation, based on the desired
        # transmission.
        angle = self.position_of_transmission(transmission)
        if angle != self.angle_command_value:
            self.angle_command_value = angle

    @monitored_property
    def value(self, angle):
        """Transmission of filter, range 0 to 1"""
        return self.transmission(angle)

    @value.setter
    def value(self, transmission):
        self.command_value = transmission

    readback_slop = monitored_value_property(0.0)

    @monitored_property
    def readback_slop(self, angle, angle_readback_slop):
        return abs(self.transmission(angle) - self.transmission(angle+angle_readback_slop))

    moving = alias_property("motor.moving")

    def transmission(self, angle):
        """Calculates the transmission from the motor angle in deg"""
        if isnan(angle):
            return nan

        if angle == self.motor_max:
            return pow(10, -self.OD_max)
        if angle == self.motor_min:
            return pow(10, -self.OD_min)

        p_min = self.motor_range[0]
        p_max = self.motor_range[1]
        # Assume the transmission is flat outside the angular range
        if angle < min(p_min, p_max):
            angle = min(p_min, p_max)
        if angle > max(p_min, p_max):
            angle = max(p_min, p_max)
        # Inside the angular range, assume that there is a linear gradient of OD 
        OD = self.OD_range[0] + (angle - p_min) / (p_max - p_min) * self.OD_range[1]
        transmission = pow(10, -OD)
        return transmission

    def position_of_transmission(self, transmission):
        """Calculates the motor angle in deg for a desired transmission"""
        if transmission <= 0:
            transmission = 1e-6
        OD = -log10(transmission)

        if OD >= self.OD_max:
            return self.motor_max
        if OD <= self.OD_min:
            return self.motor_min

        p_min = self.motor_range[0]
        p_max = self.motor_range[1]
        angle = p_min + (OD - self.OD_range[0]) / self.OD_range[1] * (p_max - p_min)
        # Assume the transmission is flat outside the angular range
        if angle < min(p_min, p_max):
            angle = min(p_min, p_max)
        if angle > max(p_min, p_max):
            angle = max(p_min, p_max)
        return angle

    angle = alias_property("motor.value")
    angle_command_value = alias_property("motor.command_value")
    angle_readback_slop = alias_property("motor.readback_slop")


if __name__ == "__main__":
    from EPICS_motor import motor
    # Laser beam attenuator wheel in 14ID-B X-ray hutch
    VNFilter2 = motor("14IDB:m32", name="VNFilter2", readback_slop=0.1, min_step=0.050)
    # readback_slop [deg]" otherwise Thorlabs motor gets hung in "Moving" state
    # min_step [deg]" otherwise Thorlabs motor gets hung in "Moving" state"
    # This filter is mounted such that when the motor is homed (at 0) the
    # attenuation is minimal (OD 0.04) and increasing to 2.7 when the motor
    # moves in positive direction.
    # Based on measurements by Hyun Sun Cho and Friedrich Schotte, made 11 Nov 2014
    # Recalibrated by Philip Anfinrud and Hyun Sun Cho 2018-10-28
    trans2 = variable_attenuator(VNFilter2, motor_range=[5, 285], OD_range=[0, 2.66])
    trans2.motor_min = 0
    trans2.OD_min = 0
    trans2.motor_max = 300
    trans2.OD_max = 2.66

    self = trans2
