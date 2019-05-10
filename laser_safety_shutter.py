"""BioCARS 14ID-B LaserShutter
Author: Friedrich Schotte
Date created: 2013-11-29
Date last modified: 2019-03-01
"""
__version__ = "1.2" # nan to indicate offline state

class LaserShutterOpen(object):
    def get_command_value(self):
        """Is the laser shutter told to open?"""
        from CA import caget
        return (caget("14IDB:lshutter.VAL") == 1)
    def set_command_value(self,value):
        from CA import caput
        if value != self.command_value or value != self.value:
            caput("14IDB:lshutter.VAL",1 if value else 0)
    command_value = property(get_command_value,set_command_value)

    def get_value(self):
        """Is the laser shutter open?"""
        from CA import caget
        PV_state = caget("14IDB:B1Bi0.VAL")
        from numpy import nan
        if PV_state == 0: state = True
        elif PV_state == 1: state = False
        elif PV_state is None: state = nan
        else: state = False
        return state
    value = property(get_value,set_command_value)

    def get_moving(self):
        """There is a five second delay before opening the laser shutter
        Is the opening of the shutter currently pending?"""
        if self.command_value != self.value: return True
        return False
    moving = property(get_moving)

    auto_PV_name = "14IDB:lshutter_auto.VAL"
    def get_auto(self):
        from CA import caget
        from numpy import nan
        PV_state = caget(self.auto_PV_name)
        state = nan
        if PV_state == 0: state = False
        if PV_state == 1: state = True
        return state
    def set_auto(self,value):
        from CA import caput
        if bool(value) == True:  caput(self.auto_PV_name,1) 
        if bool(value) == False: caput(self.auto_PV_name,0) 
    auto = property(get_auto,set_auto)

laser_safety_shutter_open = LaserShutterOpen()

class LaserSafetyShutterAutoOpen(object):
    PV_name = "14IDB:lshutter_auto.VAL"
    def get_value(self): return laser_safety_shutter_open.auto
    def set_value(self,value): laser_safety_shutter_open.auto = value
    value = property(get_value,set_value)

laser_safety_shutter_auto_open = LaserSafetyShutterAutoOpen()

# Auto mode: 14IDB:lshutter_auto

if __name__ == "__main__":
    print("laser_safety_shutter_open.value")
    print("laser_safety_shutter_open.value = True")
    print("laser_safety_shutter_open.value = False")
    print("")
    print("laser_safety_shutter_open.auto")
    print("laser_safety_shutter_open.auto = True")
    print("laser_safety_shutter_open.auto = False")
    print("")
    print("laser_safety_shutter_auto_open.value")
    print("laser_safety_shutter_auto_open.value = True")
    print("laser_safety_shutter_auto_open.value = False")

