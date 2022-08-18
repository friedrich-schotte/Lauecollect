# !/usr/bin/env python
"""Support module for SAXS/WAXS control panel.
Author: Friedrich Schotte, Valentyn Stadnydskyi
Date created: 2017-06-12
Date last modified: 2022-07-25
Revision comment: Issue: using domain
"""
__version__ = "2.3.12"

import logging
from logging import debug, warning


class SAXS_WAXS_Control(object):
    from persistent_property import persistent_property
    from action_property import action_property
    from alias_property import alias_property
    from numpy import nan

    name = "SAXS_WAXS_control"

    cancelled = persistent_property("cancelled", False)

    environment_choices = ['0 (NIH)', '1 (APS)', '2 (LCLS)']

    def get_environment(self):
        """'0 (NIH)','1 (APS)','2 (LCLS)'"""
        from numpy import isnan
        i = self.environment_index
        if 0 <= i < len(self.environment_choices):
            value = self.environment_choices[i]
        elif isnan(i):
            value = 'offline'
        else:
            value = str(i)
        return value

    def set_environment(self, value):
        if value in self.environment_choices:
            i = self.environment_choices.index(value)
        else:
            i = 0
        self.environment_index = i

    environment = property(get_environment, set_environment)

    def get_environment_index(self):
        """0=NIH, 1=APS, 2=LCLS"""
        return self.domain.ensemble.UserInteger0

    def set_environment_index(self, value):
        self.domain.ensemble.UserInteger0 = value

    environment_index = property(get_environment_index, set_environment_index)

    det_inserted_pos = 186.9
    det_retracted_pos = 486.9

    def get_det_inserted(self):
        from numpy import isnan, nan
        value = abs(self.domain.DetZ.value - self.det_inserted_pos) < 0.01 \
            if not isnan(self.domain.DetZ.value) else nan
        return value

    def set_det_inserted(self, value):
        if self.domain.DetZ.moving:
            self.domain.DetZ.moving = False
        else:
            if value:
                self.domain.DetZ.command_value = self.det_inserted_pos

    det_inserted = property(get_det_inserted, set_det_inserted)

    def get_det_retracted(self):
        from numpy import isnan, nan
        value = abs(self.domain.DetZ.value - self.det_retracted_pos) < 0.001 \
            if not isnan(self.domain.DetZ.value) else nan
        return value

    def set_det_retracted(self, value):
        if self.domain.DetZ.moving:
            self.domain.DetZ.moving = False
        else:
            if value:
                self.domain.DetZ.command_value = self.det_retracted_pos

    det_retracted = property(get_det_retracted, set_det_retracted)

    def get_det_moving(self):
        return self.domain.DetZ.moving

    def set_det_moving(self, value):
        self.domain.DetZ.moving = value

    det_moving = property(get_det_moving, set_det_moving)

    def get_ensemble_homed(self):
        from numpy import product
        homed = product(self.domain.ensemble.homed[[0, 1, 2, 4, 5]])
        return homed

    def set_ensemble_homed(self, value):
        if value:
            self.ensemble_homing = True

    ensemble_homed = property(get_ensemble_homed, set_ensemble_homed)

    home_program_filename = "Home (safe).ab"

    ensemble_homing = action_property("self.home_ensemble()",
                                      stop="self.stop_ensemble_homing()")

    def home_ensemble(self):
        from time import sleep
        self.action = "homing"
        # The entrance window of the helium code need to be at least
        # 10 mm away from the stages position at Z=0.
        det_z_return = self.det_z.value
        det_z_retracted = det_z_return + 10
        debug(f"Retracting detector to {det_z_retracted} mm...")
        self.det_z.value = det_z_retracted

        laser_y_return = self.laser_y_value
        laser_y_retracted = self.laser_y_retracted
        debug(f"Retracting Laser Y to {laser_y_retracted} mm...")
        self.laser_y_value = laser_y_retracted

        while not all([
            abs(self.det_z.value - det_z_retracted) < 0.001,
            abs(self.laser_y_value - laser_y_retracted) < 0.001,
        ]):
            if self.action != "homing":
                break
            sleep(0.10)

        debug(f"Detector at {self.det_z.value} mm")
        debug(f"Laser Y at {self.laser_y_value} mm")

        if all([
            self.action == "homing",
            abs(self.det_z.value - det_z_retracted) < 0.001,
            abs(self.laser_y_value - laser_y_retracted) < 0.001,
        ]):
            debug(f"Starting {self.home_program_filename!r}...")
            self.domain.ensemble.program_filename = self.home_program_filename
            while self.domain.ensemble.program_filename != self.home_program_filename:
                if self.action != "homing":
                    break
                sleep(0.01)
            while self.domain.ensemble.program_filename == self.home_program_filename:
                if self.action != "homing":
                    break
                sleep(0.01)
            debug(f"Finished {self.home_program_filename!r}")

        debug(f"Returning detector to {det_z_return} mm...")
        self.det_z.value = det_z_return

        debug(f"Returning laser Y to {laser_y_return} mm...")
        self.laser_y_value = laser_y_return

        while not all([
            abs(self.det_z.value - det_z_return) < 0.001,
            abs(self.laser_y_value - laser_y_return) < 0.001,
        ]):
            sleep(0.10)

        debug(f"Detector at {self.det_z.value} mm")
        debug(f"Laser Y at {self.laser_y_value} mm")

        self.action = ""

    def stop_ensemble_homing(self):
        if self.action == "homing":
            self.action = ""
        if self.domain.ensemble.program_filename == self.home_program_filename:
            self.domain.ensemble.program_running = False

    @property
    def laser_y_retracted(self):
        from numpy import clip
        return clip(self.laser_y_value + 5, self.laser_y.low_limit, self.laser_y.high_limit)

    det_z_value = alias_property("det_z.value")
    det_z = alias_property("domain.DetZ")

    @property
    def laser_y_value(self):
        return value(self.laser_y)

    @laser_y_value.setter
    def laser_y_value(self, value):
        self.laser_y.value = value

    laser_y = alias_property("domain..LaserY")

    @property
    def ensemble_homing_prohibited(self):
        if self.ensemble_program_running:
            reason = "Program running"
        elif not self.ensemble_online:
            reason = "Offline"
        else:
            reason = ""
        return reason

    program_filename = "NIH-diffractometer_PP.ab"

    def get_ensemble_program_running(self):
        return self.domain.ensemble.program_filename == self.program_filename

    def set_ensemble_program_running(self, value):
        if value:
            self.domain.ensemble.program_filename = self.program_filename
        else:
            self.ensemble.integer_registers[0] = 0

    ensemble_program_running = property(get_ensemble_program_running, set_ensemble_program_running)

    def get_timing_system_running(self):
        return self.timing_system.sequencer.running

    def set_timing_system_running(self, value):
        self.timing_system.sequencer.running = value

    timing_system_running = property(get_timing_system_running,
                                     set_timing_system_running)

    @property
    def timing_system_online(self):
        return self.timing_system.online

    x = persistent_property("x", 0.0)  # sample saved inserted position
    y = persistent_property("y", 0.0)  # sample saved inserted position

    @property
    def yr(self):
        return self.y + 11.0  # retract position

    @property
    def xr(self):
        return self.x + 3.0  # retract position

    def get_at_inserted_position(self):
        return self.inserted

    def set_at_inserted_position(self, value):
        """Define current position as 'inserted'"""
        if value:
            self.x, self.y = self.domain.SampleX.command_value, self.domain.SampleY.command_value
            debug(f'x, y = {self.x}, {self.y}')

    at_inserted_position = property(get_at_inserted_position,
                                    set_at_inserted_position)

    def get_inserted(self):
        from numpy import isnan, nan, allclose
        x, y = self.domain.SampleX.value, self.domain.SampleY.value
        value = allclose((x, y), (self.x, self.y), atol=0.05)
        if any(isnan([x, y])):
            value = nan
        return value

    def set_inserted(self, value):
        if value:
            self.inserting_sample = True
        else:
            self.retracting_sample = True

    inserted = property(get_inserted, set_inserted)

    def get_retracted(self):
        from numpy import isnan, nan, allclose
        x, y = self.domain.SampleX.value, self.domain.SampleY.value
        value = allclose((x, y), (self.xr, self.yr), atol=0.005)
        if any(isnan([x, y])):
            value = nan
        return value

    def set_retracted(self, value):
        if value:
            self.retracting_sample = True
        else:
            self.inserting_sample = True

    retracted = property(get_retracted, set_retracted)

    inserting_sample = action_property("self.insert_sample()",
                                       stop="self.stop_sample()")

    retracting_sample = action_property("self.retract_sample()",
                                        stop="self.stop_sample()")

    def insert_sample(self):
        x, y = self.x, self.y  # destination
        self.cancelled = False
        self.timeout = 10
        debug("insert sample: x -> %r" % x)
        self.domain.SampleX.command_value = x
        debug("insert sample: x=%r" % self.domain.SampleX.value)
        while not abs(self.domain.SampleX.value - x) < 0.005:
            from time import sleep
            sleep(0.1)
            if self.cancelled:
                warning("insert sample: x cancelled")
                return
            if self.timed_out:
                warning("insert sample: x timed out")
                return
            debug("insert sample: x=%r" % self.domain.SampleX.value)
        debug("insert sample: x=%r" % self.domain.SampleX.value)

        debug("insert sample: y -> %r" % y)
        self.domain.SampleY.command_value = y
        debug("insert sample: y=%r" % self.domain.SampleY.value)

    def retract_sample(self):
        x, y = self.xr, self.yr  # destination
        self.cancelled = False
        self.timeout = 10
        debug("retract sample: y -> %r" % y)
        self.domain.SampleY.command_value = y
        debug("retract sample: y=%r" % self.domain.SampleY.value)
        while not abs(self.domain.SampleY.value - y) < 0.005:
            from time import sleep
            sleep(0.1)
            if self.cancelled:
                warning("retract sample: y cancelled")
                return
            if self.timed_out:
                warning("retract sample: y timed out")
                return
            debug("retract sample: y=%r" % self.domain.SampleY.value)

        debug("retract sample: y=%r" % self.domain.SampleY.value)

        debug("retract sample: x -> %r" % x)
        self.domain.SampleX.command_value = x
        debug("retract sample: x=%r" % self.domain.SampleX.value)

    timeout_start = persistent_property("timeout_start", 0.0)
    timeout_period = persistent_property("timeout_period", 0.0)

    def get_timeout(self):
        return self.timeout_period

    def set_timeout(self, value):
        self.timeout_period = value
        from time import time
        self.timeout_start = time()

    timeout = property(get_timeout, set_timeout)

    @property
    def timed_out(self):
        from time import time
        return time() - self.timeout_start > self.timeout

    def stop_sample(self):
        self.domain.SampleX.moving, self.domain.SampleY.moving = False, False

    def get_moving_sample(self):
        return self.inserting_sample or self.retracting_sample

    def set_moving_sample(self, value):
        if not value:
            self.inserting_sample = False
            self.retracting_sample = False

    moving_sample = property(get_moving_sample, set_moving_sample)

    def get_fault(self):
        return self.domain.ensemble.fault

    def set_fault(self, value):
        self.domain.ensemble.fault = value

    fault = property(get_fault, set_fault)

    @property
    def ensemble_online(self):
        from numpy import isnan
        return not isnan(self.domain.SampleX.command_value)

    def get_XY_enabled(self):
        return self.domain.SampleX.enabled * self.domain.SampleY.enabled

    def set_XY_enabled(self, value):
        self.domain.SampleX.enabled, self.domain.SampleY.enabled = value, value

    XY_enabled = property(get_XY_enabled, set_XY_enabled)

    @property
    def jog_table_possible(self):
        from numpy import isnan
        return not isnan(self.jog_table_motor.value)

    jogging_table = action_property("self.jog_table()",
                                    stop="self.stop_jogging_table()")

    @property
    def jog_table_end(self):
        return self.jog_table_start - 0.050

    def jog_table(self):
        # Move Downstream Table X back and forth
        from time import sleep
        self.action = "jogging table"
        self.jog_table_start = self.jog_table_motor.command_value

        debug(f"{self.jog_table_motor}.command_value -> {self.jog_table_end}")
        self.jog_table_motor.command_value = self.jog_table_end
        while abs(self.jog_table_motor.value - self.jog_table_end) > self.jog_table_motor.readback_slop:
            if self.action != "jogging table":
                debug("Cancelled by user")
                break
            sleep(0.10)
        debug(f"{self.jog_table_motor}.value = {self.jog_table_motor.value}")

        debug(f"{self.jog_table_motor}.command_value -> {self.jog_table_start}")
        self.jog_table_motor.command_value = self.jog_table_start
        while abs(self.jog_table_motor.value - self.jog_table_start) > self.jog_table_motor.readback_slop:
            if self.action != "jogging table":
                debug("Cancelled by user")
                break
            sleep(0.10)
        debug(f"{self.jog_table_motor}.value = {self.jog_table_motor.value}")

        self.action = ""

    def stop_jogging_table(self):
        if self.action == "jogging table":
            self.action = ""

    jog_table_start = persistent_property("job_table_start", nan)

    @property
    def jog_table_motor(self):
        return self.domain.Table2X

    def get_xray_safety_shutters_open(self):
        return self.domain.xray_safety_shutters_open.value

    def set_xray_safety_shutters_open(self, value):
        self.domain.xray_safety_shutters_open.value = value

    xray_safety_shutters_open = property(get_xray_safety_shutters_open,
                                         set_xray_safety_shutters_open)

    def get_xray_safety_shutters_enabled(self):
        return self.domain.xray_safety_shutters_enabled.value

    def set_xray_safety_shutters_enabled(self, value):
        self.domain.xray_safety_shutters_enabled.value = value

    xray_safety_shutters_enabled = property(get_xray_safety_shutters_enabled,
                                            set_xray_safety_shutters_enabled)

    def get_xray_safety_shutters_auto_open(self):
        return self.domain.xray_safety_shutters_auto_open.value

    def set_xray_safety_shutters_auto_open(self, value):
        self.domain.xray_safety_shutters_auto_open.value = value

    xray_safety_shutters_auto_open = property(get_xray_safety_shutters_auto_open,
                                              set_xray_safety_shutters_auto_open)

    def get_laser_safety_shutter_open(self):
        return self.domain.laser_safety_shutter_open.value

    def set_laser_safety_shutter_open(self, value):
        self.domain.laser_safety_shutter_open.value = value

    laser_safety_shutter_open = property(get_laser_safety_shutter_open,
                                         set_laser_safety_shutter_open)

    def get_laser_safety_shutter_auto_open(self):
        return self.domain.laser_safety_shutter_open.value

    def set_laser_safety_shutter_auto_open(self, value):
        self.domain.laser_safety_shutter_open.value = value

    laser_safety_shutter_auto_open = property(get_laser_safety_shutter_auto_open,
                                              set_laser_safety_shutter_auto_open)

    def get_mode(self):
        return self.timing_system.composer.mode

    def set_mode(self, value):
        self.timing_system.composer.mode = value

    mode = property(get_mode, set_mode)

    @property
    def modes(self):
        return self.timing_system.composer.modes

    def get_ms_on(self):
        return self.timing_system.composer.ms_on

    def set_ms_on(self, value):
        self.timing_system.composer.ms_on = value

    ms_on = property(get_ms_on, set_ms_on)

    def get_pump_on(self):
        return self.timing_system.composer.pump_on

    def set_pump_on(self, value):
        self.timing_system.composer.pump_on = value

    pump_on = property(get_pump_on, set_pump_on)

    def get_pump_on_command(self):
        # return self.timing_system.composer.get_default("pump_on")
        return self.timing_system.composer.pump_on

    def set_pump_on_command(self, value):
        self.timing_system.composer.pump_on = value

    pump_on_command = property(get_pump_on_command, set_pump_on_command)

    pump_step_choices = ["1(linear)", "0.1", "0.2", "0.5", "1", "2.5", "5", "10", "25", "50"]

    def get_pump_step(self):
        """'1(linear)','0.1','0.2','0.5','1','2.5','5','10','25','50'"""
        from numpy import isnan
        step = ""
        i = self.pump_step_index
        if not isnan(i):
            if 0 <= i < len(self.pump_step_choices):
                step = self.pump_step_choices[i]
            else:
                step = "[%r]" % i
        return step

    def set_pump_step(self, value):
        if value in self.pump_step_choices:
            i = self.pump_step_choices.index(value)
        else:
            i = 0
        self.pump_step_index = i

    pump_step = property(get_pump_step, set_pump_step)

    def get_pump_step_index(self):
        """0-9 = 1(linear),0.1,0.2,0.5,1,2.5,5,10,25,50"""
        from numpy import nan
        try:
            i = int(self.domain.ensemble.integer_registers[2])
        except (IndexError, ValueError):
            i = nan
        return i

    def set_pump_step_index(self, value):
        self.ensemble.integer_registers[2] = value

    pump_step_index = property(get_pump_step_index, set_pump_step_index)

    def get_pump_position(self):
        return self.domain.PumpA.value

    def set_pump_position(self, value):
        self.action = "move pump"
        self.domain.PumpA.command_value = value

    pump_position = property(get_pump_position, set_pump_position)

    def get_pump_speed(self):
        return self.domain.PumpA.speed

    def set_pump_speed(self, value):
        self.domain.PumpA.speed = value

    pump_speed = property(get_pump_speed, set_pump_speed)

    def get_pump_homed(self):
        return self.domain.PumpA.homed

    def set_pump_homed(self, value):
        self.action = "home pump"
        self.domain.PumpA.homing = value

    pump_homed = property(get_pump_homed, set_pump_homed)

    @property
    def pump_movable(self):
        pump_movable = True
        if self.pump_on and self.ensemble_program_running:
            pump_movable = False
        if self.domain.PumpA.moving:
            pump_movable = False
        return pump_movable

    def get_pump_enabled(self):
        return self.domain.PumpA.enabled

    def set_pump_enabled(self, value):
        self.domain.PumpA.enabled = value

    pump_enabled = property(get_pump_enabled, set_pump_enabled)

    @property
    def pump_operating_manually(self):
        return any([
            self.sample_loading,
            self.sample_circulating,
            self.sample_extracting,
        ])

    load_step = persistent_property("load_step", 700)
    extract_step = persistent_property("extract_step", -700)
    circulate_step = persistent_property("circulate_step", 700)
    action = persistent_property("action", "")

    def get_sample_loading(self):
        return self.domain.PumpA.moving and self.action == "load sample"

    def set_sample_loading(self, value):
        if value:
            self.action = "load sample"
            self.domain.PumpA.command_value += self.load_step
        else:
            self.action = ""
            self.domain.PumpA.moving = False

    sample_loading = property(get_sample_loading, set_sample_loading)

    def get_sample_extracting(self):
        return self.domain.PumpA.moving and self.action == "extract sample"

    def set_sample_extracting(self, value):
        if value:
            self.action = "extract sample"
            self.domain.PumpA.command_value += self.extract_step
        else:
            self.action = ""
            self.domain.PumpA.moving = False

    sample_extracting = property(get_sample_extracting, set_sample_extracting)

    def get_sample_circulating(self):
        return self.domain.PumpA.moving and self.action == "circulate sample"

    def set_sample_circulating(self, value):
        if value:
            self.action = "circulate sample"
            self.domain.PumpA.command_value += self.circulate_step
        else:
            self.action = ""
            self.domain.PumpA.moving = False

    sample_circulating = property(get_sample_circulating, set_sample_circulating)

    @property
    def temperature_online(self):
        """"""
        from numpy import isnan
        return not isnan(self.domain.temperature.value)

    def get_temperature_setpoint(self):
        """sample temperature"""
        return self.domain.temperature.command_value

    def set_temperature_setpoint(self, value):
        self.domain.temperature.command_value = value

    temperature_setpoint = property(get_temperature_setpoint, set_temperature_setpoint)

    def get_temperature(self):
        """sample temperature"""
        return self.domain.temperature.value

    def set_temperature(self, value):
        self.domain.temperature.value = value

    temperature = property(get_temperature, set_temperature)

    @property
    def timing_system(self):
        return self.domain.timing_system_client

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    domain_name = "BioCARS"

    @property
    def ensemble(self):
        from Ensemble_client import ensemble
        return ensemble


SAXS_WAXS_control = control = SAXS_WAXS_Control()


def value(motor):
    from numpy import nan, isnan
    from time import sleep
    value = nan
    retries = 3
    for _ in range(0, retries):
        value = motor.value
        logging.debug(f"{motor}.value = {value}")
        if not isnan(value):
            break
        sleep(1)
    return value


if __name__ == "__main__":  # for debugging
    logging.basicConfig(level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")
    self = SAXS_WAXS_control
    print("self.pump_operating_manually")
