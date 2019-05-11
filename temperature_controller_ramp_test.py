from temperature_controller import temperature_controller
from numpy import arange
from time import time,sleep

def one_ramp():
    t_start = time()
    for temp in temp_up:
        print('Setting temperature to %r, time = %r' % (temp, round(time() - t_start,2)))
        temperature_controller.command_value = temp
        sleep(time_step)
    sleep(time_step*18)
    for temp in temp_down:
        print('Setting temperature to %r, time = %r' % (temp, round(time() - t_start,2)))
        temperature_controller.command_value = temp
        sleep(time_step)
    sleep(time_step*18)    
   
    
def ramp_test(number):
    for i in range(number):
        print('cycle = '+str(i))
        one_ramp()
        
temp_up = arange(-15.0,120.5,0.5)
temp_down = arange(120.0,-15.5,-0.5)
time_step = 1.33
temperature_controller.command_value = temp_up[0]
print('sleeping .....')
sleep(10)
print('ramp_test(1)')
#ramp_test(36)
