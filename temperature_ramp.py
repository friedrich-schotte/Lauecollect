"""Ramp temperature as fast as possible for data collection
F. Schotte 4 Jun 2015 - 5 Jun 2015"""

from temperature_controller import temperature_controller
from sleep import sleep
from numpy import ceil

setT,readT = temperature_controller.setT,temperature_controller.readT

T_repeat = 3
Time_array = [10,62,50,80,30]   # -20 to 60 Celsius; Mar 1, 2016
Temp_array = [22,-15,55]        # -20 to 60 Celsius

Time_array = [10,70,80,105,30]  # -15 to 100 Celsius; Mar 1, 2016
Temp_array = [22,-15,100]       # -15 to 100 Celsius

#Time_array = [60,90,90,125,60]  # -15 to 100 Celsius; Apr 11, 2016
#Temp_array = [22,-15,100]       # -15 to 100 Celsius

#Time_array = [60,40,80,100,60]  # 0 to 100 Celsius; Apr 30, 2016
#Temp_array = [22,0,100]       # 0 to 100 Celsius

#Time_array = [20,20,40,55,60]  # 0 to 100 Celsius; Apr 30, 2016
#Temp_array = [22,0,100]       # 0 to 100 Celsius



#Time_array = [10,40,28,56,30]   # -17 to 52 Celsius; Jun 22, 2016
#Temp_array = [22,-20,60]        # -17 to 52 Celsius

#Time_array = [10,40,33,61,30]   # -17 to 60 Celsius; Jun 22, 2016
#Temp_array = [22,-20,70]        # -17 to 60 Celsius

Time_array = [10,40,60,70,30]   # -15 to 100 Celsius; Jun 22, 2016
Temp_array = [22,-20,105]        # -15 to 100 Celsius

T_image = 0.238995  #time per stroke in fly-thru mode.
N_images = (sum(Time_array)+sum(Time_array[2:4])*(T_repeat-1))/T_image    

def run():
    setT.value = Temp_array[0]
    sleep(Time_array[0])
    setT.value = Temp_array[1]
    sleep(Time_array[1])
    for i in range(0,T_repeat):
        setT.value = Temp_array[2]
        sleep(Time_array[2])
        setT.value = Temp_array[1]
        sleep(Time_array[3])
    setT.value = Temp_array[0]
    sleep(Time_array[4])
    
print 'N_images=',int(ceil(N_images))
print 'run()'

