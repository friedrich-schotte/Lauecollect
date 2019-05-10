"""Nov 5, 2015"""

from temperature_controller import temperature_controller
from numpy import nan,array

print temperature_controller.setT.values
print len(temperature_controller.readT.values)
##setTs = temperature_controller.setT.values
##setT = setTs[-1] if len(setTs) > 0 else nan
##Ts = array(temperature_controller.readT.values)
##all(abs(Ts[-3:0]-setT)) < temperature_controller.setT.stabilization_RMS
