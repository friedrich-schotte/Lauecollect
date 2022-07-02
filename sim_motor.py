"""Software simulated motor
Author: Friedrich Schotte
Date created: 2015-11-03
Date last modified: 2021-10-10
Revision comment: sim_EPICS_motor: Added option command=
"""
__version__ = "1.4"


class sim_motor(object):
    from persistent_property import persistent_property
    stepsize = persistent_property("stepsize", 0.001)
    target = persistent_property("target", 0.0)
    speed = persistent_property("speed", 10.0)
    acceleration = persistent_property("acceleration", 1.0)
    min_dial = persistent_property("min_dial", 0.0)
    max_dial = persistent_property("max_dial", 100.0)
    sign = persistent_property("sign", 1)
    offset = persistent_property("offset", 0.0)
    unit = persistent_property("unit", "mm")
    enabled = persistent_property("enabled", True)
    description = persistent_property("description", "simulated motor")
    homed = persistent_property("homed", True)

    move_starting_position = 0.0
    move_starting_time = 0.0
    homing = False

    def __init__(self, name="sim_motor"):
        """name: string"""
        self.name = name

    def get_dial(self):
        from time import time
        if self.target > self.move_starting_position:
            direction = 1
        else:
            direction = -1
        dial = self.move_starting_position + \
            (time() - self.move_starting_time) * self.speed * direction
        if direction > 0:
            dial = min(dial, self.target)
        else:
            dial = max(dial, self.target)
        return dial

    def set_dial(self, dial):
        self.command_dial = dial

    dial = property(get_dial, set_dial)

    def get_moving(self):
        from time import time
        from numpy import sign
        direction = sign(self.target - self.move_starting_position)
        dial = self.move_starting_position + \
            (time() - self.move_starting_time) * self.speed * direction
        moving = dial < self.target if direction > 0 else dial > self.target
        return moving

    def set_moving(self, moving):
        if not moving:
            self.target = self.dial

    moving = property(get_moving, set_moving)

    def get_command_dial(self):
        return self.target

    def set_command_dial(self, dial):
        from time import time
        self.move_starting_position = self.dial
        self.move_starting_time = time()
        self.target = dial

    command_dial = property(get_command_dial, set_command_dial)

    def get_value(self):
        return self.user_from_dial(self.dial)

    def set_value(self, value):
        self.dial = self.dial_from_user(value)

    value = property(get_value, set_value)

    def get_command_value(self):
        return self.user_from_dial(self.command_dial)

    def set_command_value(self, value):
        self.command_dial = self.dial_from_user(value)

    command_value = property(get_command_value, set_command_value)

    def get_min(self):
        if self.sign > 0:
            return self.user_from_dial(self.min_dial)
        else:
            return self.user_from_dial(self.max_dial)

    def set_min(self, value):
        if self.sign > 0:
            self.min_dial = self.dial_from_user(value)
        else:
            self.max_dial = self.dial_from_user(value)

    min = property(get_min, set_min)

    def get_max(self):
        if self.sign > 0:
            return self.user_from_dial(self.max_dial)
        else:
            return self.user_from_dial(self.min_dial)

    def set_max(self, value):
        if self.sign > 0:
            self.max_dial = self.dial_from_user(value)
        else:
            self.min_dial = self.dial_from_user(value)

    max = property(get_max, set_max)

    def user_from_dial(self, value):
        return value * self.sign + self.offset

    def dial_from_user(self, value):
        return (value - self.offset) / self.sign

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
    OFF = offset  # User and dial coordinate difference

    def get_DMOV(self):
        """Done moving?"""
        return not self.moving

    def set_DMOV(self, value):
        self.moving = not value

    DMOV = property(get_DMOV, set_DMOV)

    def get_STOP(self):
        return not self.moving

    def set_STOP(self, value):
        self.moving = not value

    STOP = property(get_STOP, set_STOP)

    def get_MSTA(self):
        """Motor status bits:
        8 = home
        11 = moving
        15 = homed"""
        status_bits = self.homing << 8 | self.moving << 11 | self.homed << 15
        return status_bits

    def set_MSTA(self, value):
        pass

    MSTA = property(get_MSTA, set_MSTA)

    def get_DIR(self):
        """User to dial 0=Pos, 1=Neg"""
        return 0 if self.sign == 1 else 1

    def set_DIR(self, value):
        if value == 0:
            self.sign = 1
        if value == 1:
            self.sign = -1

    DIR = property(get_DIR, set_DIR)

    def get_ACCL(self):
        """Acceleration time to full speed in seconds"""
        T = self.speed / self.acceleration
        return T

    def set_ACCL(self, T):
        self.acceleration = self.speed / T

    ACCL = property(get_ACCL, set_ACCL)

    C = value  # needed for slits

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)


class sim_EPICS_motor(sim_motor):
    """Simulated EPICS motor"""
    from persistent_property import persistent_property
    __prefix__ = persistent_property("prefix", "SIM:MOTOR")
    EPICS_autostart = persistent_property("EPICS_autostart", True)
    readback = None
    command = None

    def __init__(
        self,
        prefix="SIM:MOTOR",
        name="sim_motor",
        description="simulated motor",
        unit=None,
        command=None,
        readback=None,
    ):
        """prefix: default name of motor record
        name: mnemonic name
        readback: PV name for readback value (RBV)
        """
        sim_motor.__init__(self, prefix)
        self.name = name
        if self.__prefix__ == "SIM:MOTOR":
            self.__prefix__ = prefix
        if self.description == "simulated motor":
            self.description = description
        if unit is not None and self.unit == "mm":
            self.unit = unit
        if command is not None:
            self.command = command
        if readback is not None:
            self.readback = readback

    @property
    def command_PV_name(self):
        if self.command:
            if ":" not in self.command:
                PV_name = self.__prefix__ + "." + self.command
            else:
                PV_name = self.command
        else:
            PV_name = None
        return PV_name

    @property
    def readback_PV_name(self):
        if self.readback:
            if ":" not in self.readback:
                PV_name = self.__prefix__ + "." + self.readback
            else:
                PV_name = self.readback
        else:
            PV_name = None
        return PV_name

    def get_prefix(self):
        return self.__prefix__

    def set_prefix(self, value):
        from CAServer import register_object, unregister_object
        self.__prefix__ = value
        unregister_object(object=self)
        self.name = value
        register_object(self, value)

    prefix = property(get_prefix, set_prefix)

    def get_EPICS_enabled(self):
        from CAServer import registered_objects
        return self in registered_objects()

    def set_EPICS_enabled(self, enabled):
        if enabled:
            from CAServer import register_object, register_property
            register_object(self, self.__prefix__)
            if self.readback_PV_name:
                register_property(self, "RBV", self.readback_PV_name)
            if self.command_PV_name:
                register_property(self, "RBV", self.command_PV_name)
        else:
            from CAServer import unregister_object, unregister_property
            unregister_object(object=self)
            if self.readback_PV_name:
                unregister_property(self, "RBV", self.readback_PV_name)
            if self.command_PV_name:
                unregister_property(self, "RBV", self.command_PV_name)

    EPICS_enabled = property(get_EPICS_enabled, set_EPICS_enabled)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s: %(levelname)s %(module)s %(message)s")
    motor = sim_EPICS_motor
    self = motor("14IDC:table2", name="Table2X", command="X", readback="EX", description="DS Table horiz.")
    # print('import EPICS_CA.CA; EPICS_CA.CA.DEBUG = True')
    # print('EPICS_CA.CAServer; EPICS_CA.CAServer.DEBUG = True')
    print('self.EPICS_enabled = True')
    print('')
    # print('from CAServer import casget, casput, casdel')
    # print('casget(self.prefix+".VAL")')
    # print('casdel(self.prefix+".VAL")')
    print('from CA import caget, caput, cainfo')
    # print('caget(self.prefix+".VAL")')
    print('cainfo(self.command_PV_name)')
    print('cainfo(self.readback_PV_name)')
    # print('self.value += 0.001')
    # print('self.value')
