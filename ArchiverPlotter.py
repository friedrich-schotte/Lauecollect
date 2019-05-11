from channel_archiver import channel_archiver
from time import time,sleep
from numpy import asarray, subtract, savetxt
from time import time
import matplotlib.pyplot as plt
from math import floor
from os import getcwd

names = {'NIH:TEMP.P': 'Temperature controller power [W]', 'NIH:DI245.57D81C1303.CH4.temperature': 'Capilary Temp [C]', 'NIH:Ensemble:pumpA': 'pumpA', 'NIH:DI245.56671FE403.ch3.pressure': 'Pressure downstream [V]', 'NIH:ENSEMBLE.pumpA': 'pumpA', 'NIH:TEMP.Power': 'Temperature controller P', 'NIH:TEMP.Current': 'Temperature controller I', 'BNCHI:BunchCurrentAI.VAL': 'Bunch current [mA]', 'NIH:Ensemble.pumpA': 'pumpA', 'NIH:TEMP.I': 'Temperature controller current [A]', 'NIH:DI245.56671FE403.CH4.temperature': 'Oasis chiller cooling water return [C]', '14IDA:DAC1_4.VAL': 'Vertical Mirror Piezo [V]', 'S:SRcurrentAI.VAL': 'Ring current [mA]', 'NIH:DI245.56671FE403.CH1.pressure': 'Pressure upstream [V]', 'NIH:DI245.57D81C13.CH4.temperature': 'Capilary Temp [C]', 'NIH:DI245.56671FE403.CH2.temperature': 'Temperature [C]', 'NIH:ENSEMBLE.PumpA': 'pumpA', 'NIH:DI245.56671FE4.CH2.temperature': 'Temperature [C]', 'NIH:ENSEMBLE:PumpA': 'pumpA', 'NIH:Enseble:pumpA': 'pumpA', 'NIH:pumpA': 'pumpA', 'NIH:TEMP.RBV': 'Temperature controller [C]', 'NIH:CHILLER.I': '', '14IDC:mir2Th.RBV': 'Horizontal Mirror Theta [mrad]', 'NIH:DI245.56671FE403.CH3.pressure': 'Pressure downstream [V]', 'IH:DI245.56671FE403.CH1.pressure': 'Pressure upstream [V]', 'NIH:CHILLER.RBV': 'Oasis chiller temperature [C]'}
known_PVs = ['NIH:TEMP.RBV', 'BNCHI:BunchCurrentAI.VAL', 'NIH:DI245.56671FE403.CH2.temperature', 'NIH:OasisChiller.DL', '14IDC:mir2Th.RBV', '14IDA:DAC1_4.VAL',
             'NIH:DI245.56671FE403.CH1.pressure', 'NIH:DI245.56671FE403.CH3.pressure', 'NIH:CHILLER.RBV', 'NIH:TEMP.P', 'NIH:TEMP.I', 'S:SRcurrentAI.VAL',
             'NIH:DI245.56671FE4.CH2.temperature', 'NIH:DI245.57D81C1303.CH4.temperature', 'NIH:DI245.57D81C13.CH4.temperature', 'NIH:DI245.56671FE403.CH4.temperature']
def get_data(PV,from_t,duration_t):
    return asarray(channel_archiver.history(PV,from_t,from_t+duration_t))

##start_t = time() - 1200 #round(time() -1500,0)
tevent = 1530038031.816
dur_t = 1000
start_t = tevent-1000
data1 = get_data('NIH:TEMP.RBV',from_t = start_t, duration_t = dur_t)
##data1 = get_data('NIH:TEMP.RBV',from_t = start_t, duration_t = dur_t)
##
plt.figure(1)
plt.plot(data1[0,:], data1[1,:],'o')

plt.grid()
##
##
plt.xlabel('time. seconds')
plt.ylabel('Temperature change, K')
plt.draw()
plt.show()
##1516842017


