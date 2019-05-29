 #!/usr/bin/env python
"""Support module for SAXS/WAXS control panel.
Author: Friedrich Schotte, Valentyn Stadnydskyi
Date created: 2017-06-12
Date last modified: 2019-05-29
"""
__version__ = "1.8.2" # added temperature control

from logging import debug,info,warn,error
from instrumentation import *
from Ensemble_client import ensemble as ensemble_tcp
from temperature import temperature

class SAXS_WAXS_Control(object):
    name = "SAXS_WAXS_control"
    from persistent_property import persistent_property
    from action_property import action_property
    from instrumentation import DetZ

    cancelled = persistent_property("cancelled",False)

    environment_choices = ['0 (NIH)','1 (APS)','2 (LCLS)']

    def get_environment(self):
        """'0 (NIH)','1 (APS)','2 (LCLS)'"""
        from numpy import isnan
        i = self.environment_index
        if 0 <= i < len(self.environment_choices):
            value = self.environment_choices[i]
        elif isnan(i): value = 'offline'
        else: value = str(i)
        return value
    def set_environment(self,value):
        if value in self.environment_choices:
            i = self.environment_choices.index(value)
        else: i = 0
        self.environment_index = i
    environment = property(get_environment,set_environment)

    def get_environment_index(self):
        """0=NIH, 1=APS, 2=LCLS"""
        return ensemble.UserInteger0
    def set_environment_index(self,value):
        ensemble.UserInteger0 = value
    environment_index = property(get_environment_index,set_environment_index)

    det_inserted_pos = 185.8
    det_retracted_pos = 485.8

    def get_det_inserted(self):
        from numpy import isnan,nan
        value = abs(DetZ.value-self.det_inserted_pos) < 0.001\
            if not isnan(DetZ.value) else nan
        return value
    def set_det_inserted(self,value):
        if DetZ.moving: DetZ.moving = False
        else:
            if value: DetZ.command_value = self.det_inserted_pos
    det_inserted = property(get_det_inserted,set_det_inserted)

    def get_det_retracted(self):
        from numpy import isnan,nan
        value = abs(DetZ.value-self.det_retracted_pos) < 0.001\
            if not isnan(DetZ.value) else nan
        return value
    def set_det_retracted(self,value):
        if DetZ.moving: DetZ.moving = False
        else:
            if value: DetZ.command_value = self.det_retracted_pos
    det_retracted = property(get_det_retracted,set_det_retracted)

    def get_det_moving(self): return DetZ.moving
    def set_det_moving(self,value): DetZ.moving = value
    det_moving = property(get_det_moving,set_det_moving)

    def get_ensemble_homed(self):
        from numpy import product
        homed = product(ensemble.homed[[0,1,2,4,5]])
        return homed
    def set_ensemble_homed(self,value):
        if value: self.ensemble_homing = True
    ensemble_homed = property(get_ensemble_homed,set_ensemble_homed)

    home_program_filename = "Home (safe).ab"

    def get_ensemble_homing(self):
        return ensemble.program_filename == self.home_program_filename
    def set_ensemble_homing(self,value):
        if value:
            self.action = "homing"
            # The entrace window of the helium code need to be at least
            # 10 mm away from the stages position at Z=0.
            detz = DetZ.command_value
            DetZ.command_value = detz + 10
            from time import sleep
            while DetZ.moving: sleep(0.10)
            ensemble.program_filename = self.home_program_filename
            while ensemble.program_filename == "": sleep(0.01)
            while ensemble.program_filename == self.home_program_filename:
                sleep(0.01)
            DetZ.command_value = detz
            while DetZ.moving: sleep(0.10)
            self.action = ""
        if not value:
            if ensemble.program_filename == self.home_program_filename:
                ensemble.program_running = False
    ensemble_homing = property(get_ensemble_homing,set_ensemble_homing)

    @property
    def ensemble_homing_prohibited(self):
        if self.ensemble_program_running: reason = "Program running"
        elif not self.ensemble_online: reason = "Offline"
        else: reason = ""
        return reason

    program_filename = "NIH-diffractometer_PP.ab"

    def get_ensemble_program_running(self):
        return ensemble.program_filename == self.program_filename
    def set_ensemble_program_running(self,value):
        if value: ensemble.program_filename = self.program_filename
        else: ensemble_tcp.integer_registers[0] = 0
    ensemble_program_running = property(get_ensemble_program_running,set_ensemble_program_running)

    def get_timing_system_running(self):
        return Ensemble_SAXS.running
    def set_timing_system_running(self,value):
        Ensemble_SAXS.running = value
    timing_system_running = property(get_timing_system_running,
        set_timing_system_running)

    @property
    def timing_system_online(self):
        return timing_system.online

    x = persistent_property("x",0.0) #sample saved inserted position
    y = persistent_property("y",0.0) #sample saved inserted position

    @property
    def yr(self): return self.y + 11.0 # retract position
    @property
    def xr(self): return self.x + 3.0 # retract position

    def get_at_inserted_position(self):
        return self.inserted
    def set_at_inserted_position(self,value):
        """Define current position as 'inserted'"""
        if value: self.x,self.y = SampleX.command_value,SampleY.command_value
    at_inserted_position = property(get_at_inserted_position,
        set_at_inserted_position)

    def get_inserted(self):
        from numpy import isnan,nan,allclose
        x,y = SampleX.value,SampleY.value
        value = allclose((x,y),(self.x,self.y),atol=0.005)
        if any(isnan([x,y])): value = nan
        return value
    def set_inserted(self,value):
        if value: self.inserting_sample = True
        else: self.retracting_sample = True
    inserted = property(get_inserted,set_inserted)

    def get_retracted(self):
        from numpy import isnan,nan,allclose
        x,y = SampleX.value,SampleY.value
        value = allclose((x,y),(self.xr,self.yr),atol=0.005)
        if any(isnan([x,y])): value = nan
        return value
    def set_retracted(self,value):
        if value: self.retracting_sample = True
        else: self.inserting_sample = True
    retracted = property(get_retracted,set_retracted)

    inserting_sample = action_property("self.insert_sample()",
        stop="self.stop_sample()")

    retracting_sample = action_property("self.retract_sample()",
        stop="self.stop_sample()")

    def insert_sample(self):
        x,y = self.x,self.y # destination
        self.cancelled = False
        self.timeout = 10
        debug("retract sample: x -> %r" % x);
        SampleX.command_value = x
        debug("insert sample: x=%r" % SampleX.value);
        while not abs(SampleX.value - x) < 0.005:
            from time import sleep
            sleep(0.1)
            if self.cancelled: warn("insert sample: x cancelled"); return
            if self.timed_out: warn("insert sample: x timed out"); return
            debug("insert sample: x=%r" % SampleX.value);
        debug("insert sample: x=%r" % SampleX.value);

        debug("insert sample: y -> %r" % y);
        SampleY.command_value = y
        debug("insert sample: y=%r" % SampleY.value);

    def retract_sample(self):
        x,y = self.xr,self.yr # destination
        self.cancelled = False
        self.timeout = 10
        debug("retract sample: y -> %r" % y);
        SampleY.command_value = y
        debug("retract sample: y=%r" % SampleY.value);
        while not abs(SampleY.value - y) < 0.005:
            from time import sleep
            sleep(0.1)
            if self.cancelled: warn("retract sample: y cancelled"); return
            if self.timed_out: warn("retract sample: y timed out"); return
            debug("retract sample: y=%r" % SampleY.value);
        debug("retract sample: y=%r" % SampleY.value);

        debug("retract sample: x -> %r" % x);
        SampleX.command_value = x
        debug("retract sample: x=%r" % SampleX.value);

    timeout_start = persistent_property("timeout_start",0.0)
    timeout_period = persistent_property("timeout_period",0.0)

    def get_timeout(self):
        return self.timeout_period
    def set_timeout(self,value):
        self.timeout_period = value
        from time import time
        self.timeout_start = time()
    timeout = property(get_timeout,set_timeout)

    @property
    def timed_out(self):
        from time import time
        return time()-self.timeout_start > self.timeout

    def stop_sample(self):
        SampleX.moving,SampleY.moving = False,False

    def get_moving_sample(self):
        return self.inserting_sample or self.retracting_sample
    def set_moving_sample(self,value):
        if not value:
            self.inserting_sample = False
            self.retracting_sample = False
    moving_sample = property(get_moving_sample,set_moving_sample)

    def get_fault(self): return ensemble.fault
    def set_fault(self,value): ensemble.fault = value
    fault = property(get_fault,set_fault)

    @property
    def ensemble_online(self):
        from numpy import isnan
        return not isnan(SampleX.command_value)

    def get_XY_enabled(self): return SampleX.enabled * SampleY.enabled
    def set_XY_enabled(self,value): SampleX.enabled,SampleY.enabled = True,True
    XY_enabled = property(get_XY_enabled,set_XY_enabled)

    def get_xray_safety_shutters_open(self):
        return xray_safety_shutters_open.value
    def set_xray_safety_shutters_open(self,value):
        xray_safety_shutters_open.value = value
    xray_safety_shutters_open = property(get_xray_safety_shutters_open,
        set_xray_safety_shutters_open)

    def get_xray_safety_shutters_enabled(self):
        return xray_safety_shutters_enabled.value
    def set_xray_safety_shutters_enabled(self,value):
        xray_safety_shutters_enabled.value = value
    xray_safety_shutters_enabled = property(get_xray_safety_shutters_enabled,
        set_xray_safety_shutters_enabled)

    def get_xray_safety_shutters_auto_open(self):
        return xray_safety_shutters_auto_open.value
    def set_xray_safety_shutters_auto_open(self,value):
        xray_safety_shutters_auto_open.value = value
    xray_safety_shutters_auto_open = property(get_xray_safety_shutters_auto_open,
        set_xray_safety_shutters_auto_open)

    def get_laser_safety_shutter_open(self):
        return laser_safety_shutter_open.value
    def set_laser_safety_shutter_open(self,value):
        laser_safety_shutter_open.value = value
    laser_safety_shutter_open = property(get_laser_safety_shutter_open,
        set_laser_safety_shutter_open)

    def get_laser_safety_shutter_auto_open(self):
        return laser_safety_shutter_auto_open.value
    def set_laser_safety_shutter_auto_open(self,value):
        laser_safety_shutter_auto_open.value = value
    laser_safety_shutter_auto_open = property(get_laser_safety_shutter_auto_open,
        set_laser_safety_shutter_auto_open)

    def get_mode(self): return Ensemble_SAXS.mode
    def set_mode(self,value): Ensemble_SAXS.mode = value
    mode = property(get_mode,set_mode)

    @property
    def modes(self): return Ensemble_SAXS.modes

    def get_ms_on(self): return Ensemble_SAXS.ms_on
    def set_ms_on(self,value): Ensemble_SAXS.ms_on = value
    ms_on = property(get_ms_on,set_ms_on)

    def get_pump_on(self): return Ensemble_SAXS.pump_on
    def set_pump_on(self,value): Ensemble_SAXS.pump_on = value
    pump_on = property(get_pump_on,set_pump_on)

    def get_pump_on_command(self): return Ensemble_SAXS.get_default("pump_on")
    def set_pump_on_command(self,value): Ensemble_SAXS.pump_on = value
    pump_on_command = property(get_pump_on_command,set_pump_on_command)

    pump_step_choices = ["1(linear)","0.1","0.2","0.5","1","2.5","5","10","25","50"]

    def get_pump_step(self):
        """'1(linear)','0.1','0.2','0.5','1','2.5','5','10','25','50'"""
        i = self.pump_step_index
        if 0 <= i < len(self.pump_step_choices): step = self.pump_step_choices[int(i)]
        else: step = ''
        return step
    def set_pump_step(self,value):
        if value in self.pump_step_choices:
            i = self.pump_step_choices.index(value)
        else: i = 0
        self.pump_step_index = i
    pump_step = property(get_pump_step,set_pump_step)

    def get_pump_step_index(self):
        """0-9 = 1(linear),0.1,0.2,0.5,1,2.5,5,10,25,50"""
        from numpy import nan
        try: i = ensemble.integer_registers[2]
        except: i = nan
        return i
    def set_pump_step_index(self,value):
        ensemble_tcp.integer_registers[2] = value
    pump_step_index = property(get_pump_step_index,set_pump_step_index)

    def get_pump_position(self): return PumpA.value
    def set_pump_position(self,value):
        self.action = "move pump"
        PumpA.command_value = value
    pump_position = property(get_pump_position,set_pump_position)

    def get_pump_speed(self): return PumpA.speed
    def set_pump_speed(self,value): PumpA.speed = value
    pump_speed = property(get_pump_speed,set_pump_speed)

    def get_pump_homed(self): return PumpA.homed
    def set_pump_homed(self,value):
        self.action = "home pump"
        PumpA.homing = value
    pump_homed = property(get_pump_homed,set_pump_homed)

    @property
    def pump_movable(self):
        pump_movable = True
        if SAXS_WAXS_control.pump_on and self.ensemble_program_running:
            pump_movable = False
        if PumpA.moving: pump_movable = False
        return pump_movable

    def get_pump_enabled(self): return PumpA.enabled
    def set_pump_enabled(self,value): PumpA.enabled = value
    pump_enabled = property(get_pump_enabled,set_pump_enabled)

    load_step      = persistent_property("load_step",700)
    extract_step   = persistent_property("extract_step",-700)
    circulate_step = persistent_property("circulate_step",700)
    action         = persistent_property("action","")

    def get_sample_loading(self):
        return PumpA.moving and self.action == "load sample"
    def set_sample_loading(self,value):
        if value:
            self.action = "load sample"
            PumpA.command_value += self.load_step
        else:
            self.action = ""
            PumpA.moving = False
    sample_loading = property(get_sample_loading,set_sample_loading)

    def get_sample_extracting(self):
        return PumpA.moving and self.action == "extract sample"
    def set_sample_extracting(self,value):
        if value:
            self.action = "extract sample"
            PumpA.command_value += self.extract_step
        else:
            self.action = ""
            PumpA.moving = False
    sample_extracting = property(get_sample_extracting,set_sample_extracting)

    def get_sample_circulating(self):
        return PumpA.moving and self.action == "circulate sample"
    def set_sample_circulating(self,value):
        if value:
            self.action = "circulate sample"
            PumpA.command_value += self.circulate_step
        else:
            self.action = ""
            PumpA.moving = False
    sample_circulating = property(get_sample_circulating,set_sample_circulating)

    @property
    def temperature_online(self):
        """"""
        from instrumentation import temperature
        from numpy import isnan
        return not isnan(temperature.value)

    def get_temperature_setpoint(self):
        """sample temperature"""
        from instrumentation import temperature
        return temperature.command_value
    def set_temperature_setpoint(self,value):
        from instrumentation import temperature
        temperature.command_value = value
    temperature_setpoint = property(get_temperature_setpoint,set_temperature_setpoint)

    def get_temperature(self):
        """sample temperature"""
        from instrumentation import temperature
        return temperature.value
    def set_temperature(self,value):
        from instrumentation import temperature
        temperature.value = value
    temperature = property(get_temperature,set_temperature)

SAXS_WAXS_control = control = SAXS_WAXS_Control()


if __name__ == "__main__": # for debugging
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s")
    self = SAXS_WAXS_control
    print("control.det_inserted = True")
    print("control.det_retracted = True")
    print("control.det_moving = False")
    print("control.det_moving")
