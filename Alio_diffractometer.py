"""
Alio Diffractometer: Serialize motor moves:
- Move Z to retracted position (-50 mm)
- Then move X, Y, Phi
- Finally, move Z to target

Setup:
self.Phi.low_limit, self.Phi.high_limit = -360.0, 360.0
self.X.low_limit, self.X.high_limit = -5.5, 6.0
self.Y.low_limit, self.Y.high_limit = -7.8, 5.0
self.Z.low_limit, self.Z.high_limit = -60.0, 10.0
self.Phi.speed = 50.0
self.X.speed = 5.0
self.Y.speed = 5.0
self.Z.speed = 100.0

Date created: 2022-01-28
Date last modified: 2022-02-03
Authors: Philip Anfinrud, Friedrich Schotte
Revision comment: Issue: Not aborting sequence of motions if one motor times outs
"""
__version__ = "1.0.1"

import logging
from cached_function import cached_function


@cached_function()
def alio_diffractometer(domain_name): return Alio_Diffractometer(domain_name)


class Alio_Diffractometer:
    from db_property import db_property
    from thread_property_2 import thread_property
    from EPICS_motor import motor

    def __init__(self, domain_name):
        self.domain_name = domain_name

    def __repr__(self):
        return f"{self.class_name}({self.domain_name!r})"

    real_Phi = motor("14IDB:m151", name="Phi")
    real_X = motor("14IDB:m152", name="X")
    real_Y = motor("14IDB:m153", name="Y")
    real_Z = motor("14IDB:m150", name="Z")

    Z_retracted_position = db_property("Z_retracted_position", -50.0)
    delay = db_property("delay", 0.5)

    @thread_property
    def motion_scheduled(self):
        from time import sleep
        sleep(self.delay)
        self.move_motors()

    def move_motors(self):
        from numpy import isnan, nan

        try:
            if self.motors_to_move:
                if self.normal_move:
                    for motor in self.motors_to_move:
                        move(motor.real_motor, motor.target)
                        motor.target = nan
                else:
                    if not isnan(self.Z.target):
                        Z_target = self.Z.target
                    else:
                        Z_target = self.Z.VAL
                    move(self.Z.real_motor, self.Z_retracted_position)
                    for motor in self.motors_to_move:
                        if motor != self.Z:
                            move(motor.real_motor, motor.target)
                            motor.target = nan
                    move(self.Z.real_motor, Z_target)
                    self.Z.target = nan
        except TimeoutError as x:
            logging.error(f"{x}")

    @property
    def normal_move(self):
        if self.motors_to_move == [self.Z]:
            normal_move = True
        else:
            normal_move = False
        return normal_move

    @property
    def motors_to_move(self):
        motors = [motor for motor in self.motors if need_move(motor.real_motor, motor.target)]
        return motors

    @property
    def Phi(self):
        return motor_wrapper(self, self.real_Phi)

    @property
    def X(self):
        return motor_wrapper(self, self.real_X)

    @property
    def Y(self):
        return motor_wrapper(self, self.real_Y)

    @property
    def Z(self):
        return motor_wrapper(self, self.real_Z)

    @property
    def motors(self):
        return self.Phi, self.X, self.Y, self.Z

    @property
    def db_name(self):
        return f"{self.domain_name}/{self.class_name}"

    @property
    def class_name(self):
        return type(self).__name__.lower()


def need_move(motor, target):
    from numpy import isnan
    if isnan(target):
        need_move = False
    else:
        need_move = abs(motor.value - target) > motor.readback_slop
    return need_move


def move(motor, target):
    from time import sleep, time
    initial_value = motor.value
    logging.debug(f"{motor.name}: {initial_value} -> {target}")
    motor.command_value = target
    start_time = time()
    start_timeout = 2.0

    while abs(motor.value - target) > motor.readback_slop:
        logging.debug(f"{motor.name}: {motor.value}")
        dt = time() - start_time
        if dt > start_timeout and not motor.moving:
            message = f"{motor.name}: Move {initial_value} -> {target} timed out at {motor.value} after {dt} s"
            logging.error(message)
            raise TimeoutError(message)
        sleep(0.1)

    logging.debug(f"{motor.name}: {motor.value}")


@cached_function()
def motor_wrapper(group, motor): return Motor_Wrapper(group, motor)


class Motor_Wrapper:
    from db_property import db_property
    from monitored_property import monitored_property
    from alias_property import alias_property
    from numpy import nan

    def __init__(self, group, real_motor):
        self.group = group
        self.real_motor = real_motor

    def __repr__(self):
        return f"{self.class_name}({self.group},{self.real_motor})"

    @property
    def db_name(self):
        motor_name = self.name.replace(' ', '_')
        return f"{self.group.db_name}/{motor_name}"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    target = db_property("target", nan, local=True)

    @monitored_property
    def VAL(self, real_motor_VAL, target):
        from numpy import isnan
        if not isnan(target):
            value = target
        else:
            value = real_motor_VAL
        return value

    @VAL.setter
    def VAL(self, value):
        self.target = value
        self.group.motion_scheduled = True

    command_value = alias_property("VAL")

    @monitored_property
    def value(self, RBV):
        return RBV

    @value.setter
    def value(self, value):
        self.VAL = value

    real_motor_VAL = alias_property("real_motor.VAL")

    name = alias_property("real_motor.name")
    RBV = alias_property("real_motor.RBV")
    DMOV = alias_property("real_motor.DMOV")
    moving = alias_property("real_motor.moving")
    low_limit = alias_property("real_motor.low_limit")
    high_limit = alias_property("real_motor.high_limit")
    speed = alias_property("real_motor.speed")
    readback_slop = alias_property("real_motor.readback_slop")


if __name__ == "__main__":
    from reference import reference
    from handler import handler

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.INFO, format=msg_format)

    domain_name = "BioCARS"
    self = alio_diffractometer(domain_name)
    Phi = self.Phi
    GonX = self.X
    GonY = self.Y
    GonZ = self.Z


    @handler
    def report(event): logging.info(f"{event}")


    print('Phi.value, GonX.value, GonY.value, GonZ.value =  -15.000, +0.640, +0.411, +3.332')
    print('Phi.value, GonX.value, GonY.value, GonZ.value = -105.000, -3.184, -0.589, -3.468')

    reference(Phi, "RBV").monitors.add(report)
    reference(GonX, "RBV").monitors.add(report)
    reference(GonY, "RBV").monitors.add(report)
    reference(GonZ, "RBV").monitors.add(report)
