"""Software simulated motor
Author: Friedrich Schotte
Date created: 2019-02-28
Date last modified: 2019-04-26
"""
__version__ = "1.0.1" # IOC_Wrapper.transform_functions initialization

from logging import debug,info,warn,error

class sim_safety_shutter(object):
    from persistent_property import persistent_property
    from numpy import inf
    __command_value__ = persistent_property("command_value",0.0)
    speed = persistent_property("speed",0.2)
    __auto_open__ = persistent_property("auto_open",1)
    description = persistent_property("description","")
    
    move_starting_position = 0.0
    move_starting_time = 0.0

    def __init__(self,name="sim_shutter",description=""):
        """name: string"""
        self.name = name
        if description != "" and self.description == "": self.description = description

    def get_command_value(self):
        value = self.__command_value__
        if self.auto_open: value = 1.0
        return value
    def set_command_value(self,value):
        from time import time
        self.move_starting_position = self.value
        self.move_starting_time = time()
        self.__command_value__ = value
    command_value = property(get_command_value,set_command_value)

    def get_value(self):
        from time import time
        if self.command_value > self.move_starting_position: direction = 1
        else: direction = -1
        value = self.move_starting_position + \
            (time() - self.move_starting_time)*self.speed*direction
        if direction > 0: value = min(value,self.command_value)
        else: value = max(value,self.command_value)
        return value
    def set_value(self,value): self.command_value = value
    value = property(get_value,set_value)

    def get_auto_open(self): return self.__auto_open__
    def set_auto_open(self,value):
        from time import time
        self.move_starting_position = self.value
        self.move_starting_time = time()
        if bool(value) == True: self.__command_value__ = 1
        self.__auto_open__ = value
    auto_open = property(get_auto_open,set_auto_open)

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__,self.name)


class sim_EPICS_safety_shutter(sim_safety_shutter):
    """Simulated EPICS motor"""    
    def __init__(self,name,description,command_value,value,auto_open):
        """command_value: PV name
        value: PV name
        auto_open: PV name
        """
        sim_safety_shutter.__init__(self,name,description)
        self.IOC = IOC_Wrapper(self,
            command_value=command_value,
            value=value,
            auto_open=auto_open,
        )

    def get_EPICS_enabled(self): return self.IOC.EPICS_enabled
    def set_EPICS_enabled(self,value): self.IOC.EPICS_enabled = value
    EPICS_enabled = property(get_EPICS_enabled,set_EPICS_enabled)

    def get_prefix(self): return self.IOC.PV_names["value"]
    def set_prefix(self,value): self.IOC.PV_names["value"] = value
    prefix = property(get_prefix,set_prefix)
    

class IOC_Wrapper(object):
    """Server a Python oject on the network as an EPICS Inpup/Output controller,
    using Channel Access protocol"""
    
    def __init__(self,object,prefix="",**kwargs):
        """command_value: PV name
        value: PV name
        auto_open: PV name
        """
        self.transform_functions = {}
        self.object = object
        self.name = self.object.name # for EPICS_enabled
        self.prefix = prefix
        self.PV_names = {}
        for name in kwargs:
            self.PV_names[name] = kwargs[name]
        self.running = self.EPICS_enabled

    def PV_name(self,name):
        return self.prefix+self.PV_names[name]

    def transform(self,name,value):
        if name in self.transform_functions:
            transform_function = self.transform_functions[name][0]
            value = transform_function(value)
        return value

    def back_transform(self,name,value):
        if name in self.transform_functions:
            back_transform_function = self.transform_functions[name][1]
            value = back_transform_function(value)
        return value
    
    def get_EPICS_enabled(self):
        return self.__EPICS_enabled__
    def set_EPICS_enabled(self,value):
        self.__EPICS_enabled__ = value
        self.running = value
    EPICS_enabled = property(get_EPICS_enabled,set_EPICS_enabled)

    from persistent_property import persistent_property
    __EPICS_enabled__ = persistent_property("EPICS_enabled",True)

    from thread_property_2 import thread_property
    @thread_property
    def running(self):
        info("Starting IOC...")
        from CAServer import casget,casput,casdel,casmonitor
        from time import time
        from sleep import sleep

        for name in self.PV_names:
            PV_name = self.PV_name(name)
            casmonitor(PV_name,callback=self.monitor)
        
        while not self.running_cancelled:
            t = time()
            for name in self.PV_names:
                if time() - self.last_updated(name) > self.update_period(name):
                    PV_name = self.PV_name(name)
                    value = getattr(self.object,name)
                    ##info("%s=%r" % (PV_name,value))
                    casput(PV_name,self.transform(name,value),update=False)
                    self.set_update_time(name)
            if not self.running_cancelled: sleep(t+self.min_update_period-time())

        for name in self.names:
            PV_name = self.PV_name(name)
            casdel(PV_name)

    min_update_period = 0.024

    def monitor(self,PV_name,value,char_value):
        """Handle PV change requests"""
        info("%s = %r" % (PV_name,value))
        from CAServer import casput
        for name in self.PV_names:
            if PV_name == self.PV_name(name):
                info("%s.%s=%r" % (self.object,name,value))
                setattr(self.object,name,self.back_transform(name,value))
                value = getattr(self.object,name)
                casput(PV_name,self.transform(name,value))

    last_updated_dict = {}
    def set_update_time(self,name):
        from time import time
        self.last_updated_dict[name] = time()
    def last_updated(self,name): return self.last_updated_dict.get(name,0)
    
    def update_period(self,name):
        period = 0.25
        return period


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    ID14A_shutter = sim_EPICS_safety_shutter(
        name="ID14A_shutter",
        description="Shutter 14IDA",
        command_value="14IDA:shutter_in1.VAL",
        value="PA:14ID:STA_A_FES_OPEN_PL.VAL",
        auto_open="14IDA:shutter_auto_enable1.VAL",
    )
    ID14A_shutter.IOC.transform_functions["command_value"] = lambda x:1-x,lambda x:1-x

    ID14C_shutter = sim_EPICS_safety_shutter(
        name="ID14C_shutter",
        description="ID14C Shutter",
        command_value="14IDA:shutter_in2.VAL",
        value="PA:14ID:STA_B_SCS_OPEN_PL.VAL",
        auto_open="14IDA:shutter_auto_enable2.VAL",
    )
    ID14C_shutter.IOC.transform_functions["command_value"] = lambda x:1-x,lambda x:1-x

    laser_safety_shutter = sim_EPICS_safety_shutter(
        name="laser_safety_shutter",
        description="Laser Safety Shutter",
        command_value="14IDB:lshutter.VAL",
        value="14IDB:B1Bi0.VAL",
        auto_open="14IDB:lshutter_auto.VAL",
    )
    laser_safety_shutter.IOC.transform_functions["value"] = lambda x:1-x,lambda x:1-x
    self = laser_safety_shutter

    from CA import caget,caput
    from xray_safety_shutters import ID14A_shutter_open
    from xray_safety_shutters import ID14C_shutter_open
    from xray_safety_shutters import xray_safety_shutters_open
    from laser_safety_shutter import laser_safety_shutter_open
    from time import sleep
    sleep(0.5)
    print('caget("14IDB:lshutter.VAL"): %r' % caget("14IDB:lshutter.VAL"))
    print('caput("14IDB:lshutter.VAL",0)')
    print('caput("14IDB:lshutter.VAL",1)')
    print('caget("14IDB:B1Bi0.VAL"): %r' % caget("14IDB:B1Bi0.VAL"))
    print('')
    print("laser_safety_shutter.value = %r" % laser_safety_shutter.value)
    print("laser_safety_shutter.auto_open = %r" % laser_safety_shutter.auto_open)
    print("laser_safety_shutter.auto_open")
    print("laser_safety_shutter.value")
