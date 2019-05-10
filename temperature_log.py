"""
This is to log the tempeature of the
ILX Lightwave LDT-5948 Precision Temperature Controller
Friedrich Schotte, APS, 4 Dec 2009
"""

from temperature_controller import temperature_controller
from CA import PV
from scan import timescan

temperature = temperature_controller.temperature
power = temperature_controller.power
chillerT = PV("14Keithley1:DMM1Ch3_raw.VAL")

logfile = "//id14bxf/data/anfinrud_1004/Scans/2010.04.14-01 Temperature.log"
##logfile = None
timescan([temperature,power,chillerT],waiting_time=1,logfile=logfile)
