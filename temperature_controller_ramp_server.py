"""
Timed temperature ramps by changing the set point of the ILX LightWave LTD-5948
precision temperature controller in a timer.

Authors: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 22 Feb 2018
Date last modified: 23 Feb 2018
"""
__version__ = "1.0"
from temperature_controller import temperature_controller
from CAServer import casput,casdel

def run():
    from time import sleep
    casput("NIH:TEMP.RAMP",1)
        while True:
            set_temperature()
            sleep(5)

def set_temperature():
    """Adjust the set point of the temperature controller as function of time"""
    from time import time
    t = time()
    T = temperature(T)
    temperature_controller.command_value = T

def temperature(t):
    """Which temperature as function of time?
    t = time in seconds since 1970-01-01T00:00:00+00"""
    from scipy import interpolate
    T = inerp(timepoints,temperatures,t)
    return T

if __name__ == "__main__":
    print('oasis_chiller_set_point(%r)' % temperature_controller.command_value)
    print('run()')
