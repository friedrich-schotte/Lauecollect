"""Software simulated motor
Author: Friedrich Schotte
Date created: 2015-11-03
Date last modified: 2019-05-26
"""
__version__ = "1.2" # sim_EPICS_motor: readback

class sim_motor(object):
    from persistent_property import persistent_property
    from numpy import inf
    stepsize = persistent_property("stepsize",0.001)
    target = persistent_property("target",0.0)
    speed = persistent_property("speed",10.0)
    min_dial = persistent_property("min_dial",0.0)
    max_dial = persistent_property("max_dial",100.0)
    sign = persistent_property("sign",1)
    offset = persistent_property("offset",0.0)
    unit = persistent_property("unit","mm")
    enabled = persistent_property("enabled",True)
    description = persistent_property("description","simulated motor")
    
    move_starting_position = 0.0
    move_starting_time = 0.0

    def __init__(self,name="sim_motor"):
        """name: string"""
        self.name = name

    def get_dial(self):
        from time import time
        if self.target > self.move_starting_position:
            direction = 1
        else: direction = -1
        dial = self.move_starting_position + \
            (time() - self.move_starting_time)*self.speed*direction
        if direction > 0: dial = min(dial,self.target)
        else: dial = max(dial,self.target)
        return dial
    def set_dial(self,dial): self.command_dial = dial
    dial = property(get_dial,set_dial)

    def get_moving(self):
        from time import time
        from numpy import sign
        direction = sign(self.target - self.move_starting_position)
        dial = self.move_starting_position + \
            (time() - self.move_starting_time)*self.speed*direction
        moving = dial < self.target if direction > 0 else dial > self.target
        return moving
    def set_moving(self,value):
        if bool(value) == False: self.target = self.dial
    moving = property(get_moving,set_moving)

    def get_command_dial(self): return self.target
    def set_command_dial(self,dial):
        from time import time
        self.move_starting_position = self.dial
        self.move_starting_time = time()
        self.target = dial
    command_dial = property(get_command_dial,set_command_dial)

    def get_value(self): return self.user_from_dial(self.dial)
    def set_value(self,value): self.dial = self.dial_from_user(value)
    value = property(get_value,set_value)

    def get_command_value(self): return self.user_from_dial(self.command_dial)
    def set_command_value(self,value): self.command_dial = self.dial_from_user(value)
    command_value = property(get_command_value,set_command_value)

    def get_min(self):
        if self.sign>0: return self.user_from_dial(self.min_dial)
        else: return self.user_from_dial(self.max_dial)
    def set_min(self,value):
        if self.sign>0: self.min_dial = self.dial_from_user(value)
        else: self.max_dial = self.dial_from_user(value)
    min = property(get_min,set_min)
    
    def get_max(self):
        if self.sign>0: return self.user_from_dial(self.max_dial)
        else: return self.user_from_dial(self.min_dial)
    def set_max(self,value):
        if self.sign>0: self.max_dial = self.dial_from_user(value)
        else: self.min_dial = self.dial_from_user(value)
    max = property(get_max,set_max)

    def user_from_dial(self,value): return value * self.sign + self.offset  
    def dial_from_user(self,value): return (value - self.offset) / self.sign

    # EPICS motor record process variables
    VAL = command_value
    RBV = value
    DVAL = command_dial
    DRBV = dial
    VELO = speed
    CNEN = enabled
    LLM = min
    HLM = max
    DLLM = min_dial
    DHLM = max_dial
    HLS = False
    LLS = False
    DESC = description
    EGU = unit
    HOMF = False
    HOMR = False
    OFF = offset # User and dial coordinate difference
    def get_DMOV(self):
        """Done moving?"""
        return not self.moving
    def set_DMOV(self,value): self.moving = not value
    DMOV = property(get_DMOV,set_DMOV)
    def get_STOP(self): return not self.moving
    def set_STOP(self,value): self.moving = not value
    STOP = property(get_STOP,set_STOP)
    def get_MSTA(self):
        """Motor status bits:
        8 = home
        11 = moving
        15 = homed"""
        status_bits = self.homing<<8|self.moving<<11|self.homed<<15
        return status_bits
    def set_MSTA(self,value): pass
    MSTA = property(get_MSTA,set_MSTA)
    def get_DIR(self):
        """User to dial 0=Pos, 1=Neg"""
        return 0 if self.sign == 1 else 1
    def set_DIR(self,value):
        if value == 0: self.sign = 1
        if value == 1: self.sign = -1
    DIR = property(get_DIR,set_DIR)
    def get_ACCL(self):
        """Acceleration time to full speed in seconds"""
        T = self.speed/self.acceleration
        return T
    def set_ACCL(self,T):
        self.acceleration = self.speed/T
    ACCL = property(get_ACCL,set_ACCL)

    C = value # needed for slits 


class sim_EPICS_motor(sim_motor):
    """Simulated EPICS motor"""
    from persistent_property import persistent_property
    __prefix__ = persistent_property("prefix","SIM:MOTOR")
    __EPICS_enabled__ = persistent_property("EPICS_enabled",True)
    
    def __init__(self,prefix="SIM:MOTOR",name="sim_motor",
        description="simulated motor",unit=None,readback=None):
        """prefix: default name of motor record
        name: mnemonic name
        readback: PV name for readback value (RBV)
        """
        sim_motor.__init__(self,prefix)
        self.name = name
        if self.__prefix__ == "SIM:MOTOR": self.__prefix__ = prefix
        if self.description == "simulated motor": self.description = description
        if unit is not None and self.unit == "mm": self.unit = unit
        self.readback = readback
        self.EPICS_enabled = self.EPICS_enabled

    def get_prefix(self):
        return self.__prefix__
    def set_prefix(self,value):
        from CAServer import register_object,unregister_object
        self.__prefix__ = value
        unregister_object(object=self)
        self.name = value
        register_object(self,value)
    prefix = property(get_prefix,set_prefix)
    
    def get_EPICS_enabled(self):
        return self.__EPICS_enabled__
    def set_EPICS_enabled(self,value):
        self.__EPICS_enabled__ = value
        if self.__EPICS_enabled__:
            from CAServer import register_object,register_property
            register_object(self,self.__prefix__)
            if self.readback: register_property(self,"RBV",self.readback)
        else:
            from CAServer import unregister_object,unregister_property
            unregister_object(object=self)
            if self.readback: unregister_property(self,"RBV",self.readback)
    EPICS_enabled = property(get_EPICS_enabled,set_EPICS_enabled)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime): %(message)s")
    motor = sim_EPICS_motor
    Slit1H = motor("14IDA:Slit1Hsize",name="Slit1H",description="White beam slits H gap",
      readback="14IDA:Slit1Ht2.C")
    from CA import caget,caput
    print('Slit1H.prefix = %r' % Slit1H.prefix)
    print('Slit1H.readback = %r' % Slit1H.readback)
    print('Slit1H.EPICS_enabled = %r' % Slit1H.EPICS_enabled)
    print('caget(Slit1H.prefix+".VAL")')
    print('caget(Slit1H.readback)')
    print('caput(Slit1H.readback,Slit1H.VAL)')
    print('Slit1H.value += 0.001')
    print('Slit1H.value')
