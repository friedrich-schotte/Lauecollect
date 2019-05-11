"""Monitor temperature
Author: Friedrich Schotte, Apr 7, 2016 - Apr 29, 2016
"""
__version__ = "3.0" # thermocouple reader

from temperature_controller import temperature_controller
from time import time
from sleep import sleep
from numpy import nan
from omega_thermocouple import thermocouple
thermocouple.logging = True

def run():
    t0 = time()
    T0 = nan
    f = file("logfiles/temperature_controller.log","wb")
    s = "#time[s]\tT[C]\tI[A]\tU[V]\tTC[C]"
    print(s)
    f.write(s+"\n")
    try:
        while True:
            TC = thermocouple.T
            TIU = temperature_controller.TIU
            if TIU is not None and TC is not None:
                T,I,U = TIU
                t = time()
                if T != T0:
                    s = "%s\t%g\t%g\t%g\t%g" % (t-t0,T,I,U,TC)
                    print(s)
                    f.write(s+"\n")
                T0 = T
            sleep(0.2)
    except KeyboardInterrupt: pass

print('run()')
