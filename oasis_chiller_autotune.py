"""
Automatically adjust the set point of the Oasis thermoelectric chiller,
according to the set point of the ILX LightWave LTD-5948 precision temperature
controller. AKA slave the chiller to temperature controller

Authors: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2018-02-22
Date last modified: 2018-05-22

1.1 - changed Tmin to -30 (from -25).
1.2 - if T < 22, keep oasis at 2*C, if above 22C slave linearly
1.3 - The autotune happens only if the new set oasis set temperature is
    - different from the previous one. There is no need to submit new set
    - temperature command if it is equal to the current one.
"""
__version__ = "1.4" # lightwave_temperature_controller
from lightwave_temperature_controller import lightwave_temperature_controller
from oasis_chiller import oasis_chiller
from CAServer import casput,casdel
from time import clock, time, sleep
Told = T = lightwave_temperature_controller.command_value
t= told = oasis_chiller.command_value
tstart = time()
circular_buffer = []
def run():
    from time import sleep
    casput("NIH:CHILLER.AUTOTUNE",1)
    
    while True:
        autotune()
        sleep(5)

def autotune():
    """Adjust the set point of the Oasis chiller.
    autotune only if the new set poitn for the oasis is different
    from the previous one. There is no need to autotune every 5 seconds if
    set temperature for the oasis is the same.
    """
    global Told,T,told,t, circular_buffer
    T = lightwave_temperature_controller.command_value
    if len(circular_buffer) == 0:
        circular_buffer.append(T)
    circular_buffer.append(T)
    if len(circular_buffer) >3:
        circular_buffer.pop(0)
    t = oasis_chiller_set_point(Told,T)
    if t != told:   
        oasis_chiller.command_value = t
        #print('autotune: t new %r, t old %r, time: %r' %(t,told,round(time()-tstart,0)))
    Told = T
    told = t
    
    

def oasis_chiller_set_point(Told,T, mode = '2 states'):
    """Which temperature to set the chiller to?
    T = temperature controller point
    t = oasis temperature point

    default mode:
    keeps oasis temperature(t) at 8*C(oasis_t) if T <=22.0
    and uses linear interpolation if T >22.0.
    
    2 states mode:
    keeps oasis at oasis_t temperature

    If the change in the TEC set temperature is positive
    oasis temperature will be set to 45*C, if negative - 4*C
    If constant, it will use linear interpolation to calculate
    the oasis set temperature

    """
    from numpy import clip
    set_t = oasis_chiller.command_value
    oasis_t_low = oasis_t= 8.0
    oasis_t_high = oasis_t_max = 45.0
    TEC_T = 60.0
    TEC_T_max = 60.0
    T2 = T
    #if len(circular_buffer)>2:
     #   circular_buffer.append()
    #else:
    if mode == '2 states':
        if T>Told and (circular_buffer[1]>circular_buffer[0]):
            t = oasis_t_high
        elif (T < Told) and (circular_buffer[1]<circular_buffer[0]):
            t = oasis_t_low
        else:
            if T < TEC_T:
                t = oasis_t_low
            elif T >= TEC_T:
                t = oasis_t_high
    else: 
        if T>Told and (circular_buffer[1]>circular_buffer[0]):
            t = oasis_t_high
        elif (T < Told) and (circular_buffer[1]<circular_buffer[0]):
            t = oasis_t_low
        else:
            if T < TEC_T:
                t = oasis_t_low
            elif T >= TEC_T_max:
                t = oasis_t_high
            else:
                Tmin,Tmax = TEC_T,TEC_T_max
                tmin,tmax = oasis_t_low,oasis_t_high
                t = (T-Tmin)/(Tmax-Tmin)*(tmax-tmin)+tmin
                t = clip(t,tmin,tmax)
                t = round(t,1)
    return t

if __name__ == "__main__":
    print('oasis_chiller_set_point(%r)' % lightwave_temperature_controller.command_value)
    print('run()')
