"""
Automatically adjust the set point of the Oasis thermoelectric chiller,
according to the set point of the ILX LightWave LTD-5948 precision temperature
controller. AKA slave the chiller to temperature controller

Authors: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 22 Feb 2018
Date last modified: 03 July 2018

version 1.1 - changed Tmin to -30 (from -25).
"""
__version__ = "1.1"
from temperature_controller import temperature_controller
from oasis_chiller import oasis_chiller
from CAServer import casput,casdel
from pdb import pm

CAS_prefix = 'NIH:OASIS_DL'
def run():
    from time import sleep
    casput(CAS_prefix+".AUTOTUNE",1)
    while True:
        autotune()
        sleep(10)

def autotune():
    """Adjust the set point of the Oasis chiller"""
    from CA import caput,caget
    from time import time
    T = temperature_controller.command_value
    t = oasis_chiller_set_point(T)
    if caget(CAS_prefix+'.VAL') != t:
        print('Set temperature: %r, new temperature: %r : time:%r' %
              (caget(CAS_prefix+'.VAL'),t,time()))
        caput(CAS_prefix+'.VAL',t) #caput('NIH:OASIS_DL.SET_VAL',t)

def oasis_chiller_set_point(T):
    """Which temperature to set the chiller to?
    T = temperature controller point"""
    from numpy import clip
    Tmin,Tmax = -30.0,120.0
    tmin,tmax = 2.0,45.0
    t = (T-Tmin)/(Tmax-Tmin)*(tmax-tmin)+tmin
    t = clip(t,tmin,tmax)
    t = round(t,1)
    
    return t

if __name__ == "__main__":
    print('oasis_chiller_set_point(%r)' % temperature_controller.command_value)
    print('run()')
