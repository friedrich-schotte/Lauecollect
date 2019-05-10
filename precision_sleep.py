"""
Precision Sleep
author: Valentyn Stadnytskyi
data: 2017 - June 09 2018

The precision sleep class.
functiob:
psleep - sleep specified amount of time with sub milisecond precision
test_sleep - for testing purposes. will print how much time the code waited.
This is important for the Windows platform programs if precise wait is required.
The Windows OS has ~15-17 ms latenct - the shortest time between attentions from OS.
"""
__vesrion__ = '1.0.0'
from time import clock, time, sleep
import platform
        
class precision_sleep_class(object):
    def __init__(self):
        from time import clock, time, sleep
        import platform
        self.min_time = 0.017
        
    
    def psleep(self, t = 0.02, min_time = 0.017):
        """
        sleep for t seconds.
        """
        from time import clock, time, sleep
        import platform
        self.min_time = min_time
        
        time_start = clock()
        if platform.system() == 'Linux':
            sleep(t)
        else:
            if t>self.min_time:
                sleep(t-min_time)
                time_left = t - (clock() - time_start)
                time_while_start = clock()
                while clock() - time_while_start <= time_left:
                    pass
            else:
                time_left = t - (clock() - time_start)
                time_while_start = clock()
                while clock() - time_while_start <= time_left:
                    pass
            
    def test_sleep(self,t = 0.01):
        """
        test_sleep t = 0.01 in seconds
        """
        from time import clock, time, sleep
        t1 =  clock()
        self.psleep(t)
        t2 = clock()
        dt = t2-t1
        print(dt)
    
precision_sleep = precision_sleep_class()
self = precision_sleep
if __name__ == '__main__':
    print('self.test_sleep(0.010) # in seconds')

