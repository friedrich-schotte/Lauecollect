"""
Coordinate the operation of the Lightwave TEC and  the Oasis
chiller

Authors: Friedrich Schotte, Philip Anfinrud
Date created: 2021-11-26
Date last modified: 2022-07-02
Revision comment: Renamed temperature_system_driver
"""
__version__ = "1.7"

import logging

from cached_function import cached_function
from handler import handler
from reference import reference


@cached_function()
def temperature_system_driver(name): return Temperature_System_Driver(name)


class Temperature_System_Driver:
    from alias_property import alias_property
    from monitored_property import monitored_property
    from db_property import db_property
    from timer_property import timer_property

    def __init__(self, domain_name):
        self.domain_name = domain_name
        reference(self, "TEC_nominal_set_T").monitors.add(handler(self.handle_TEC_nominal_set_T_change))
        reference(self, "TEC_PID_OK").monitors.add(handler(self.handle_TEC_PID_OK_change))
        reference(self, "time").monitors.add(handler(self.on_timer))

    def __repr__(self):
        return f"{self.class_name}({self.domain_name})"

    VAL = alias_property("nominal_set_T")
    RBV = alias_property("TEC_T")
    DMOV = alias_property("TEC.DMOV")

    nominal_set_T = db_property("nominal_set_T", 22.0, local=True)

    @monitored_property
    def TEC_nominal_set_T(self, nominal_set_T, chiller_T):
        from numpy import isnan, clip
        if isnan(chiller_T):
            chiller_T = 8.0
        return clip(chiller_T - 75, nominal_set_T, chiller_T + 75)

    def handle_TEC_nominal_set_T_change(self, event):
        self.TEC_set_T = event.value

    @monitored_property
    def chiller_nominal_set_T(
            self,
            scanning,
            nominal_set_T,
            chiller_T_min,
            chiller_T_max,
            time,
            chiller_set_point_times_and_values,
    ):
        if scanning:
            T = lookup(chiller_set_point_times_and_values, time)
            # logging.debug(f"scanning = {scanning}, T = {T}")
        else:
            if nominal_set_T >= chiller_T_min + 75:
                T = chiller_T_max
            else:
                T = chiller_T_min
        return T

    time = timer_property(period=2)

    @monitored_property
    def chiller_set_T_OK(self, chiller_set_T, chiller_nominal_set_T, time):
        from numpy import isnan
        if isnan(chiller_set_T):
            OK = True
        elif isnan(chiller_nominal_set_T):
            OK = True
        else:
            OK = chiller_set_T == chiller_nominal_set_T
        return OK

    @chiller_set_T_OK.setter
    def chiller_set_T_OK(self, OK):
        from numpy import isnan
        if OK:
            T = self.chiller_nominal_set_T
            if not isnan(T):
                logging.debug(f"chiller_set_T = {T}")
                self.chiller_set_T = T

    def on_timer(self):
        if not self.chiller_set_T_OK:
            logging.debug(f"chiller_set_T_OK: {self.chiller_set_T_OK}")
            self.chiller_set_T_OK = True

    @monitored_property
    def slewing(self, TEC_T, TEC_set_T, TEC_slew_dT, scanning, scan_slewing):
        if not scanning:
            slewing = abs(TEC_T - TEC_set_T) > TEC_slew_dT
        else:
            slewing = scan_slewing
        return slewing

    TEC_slew_dT = db_property("TEC_slew_dT", 1.0)

    @monitored_property
    def TEC_PID_OK(self, slewing, slew, hold):
        if slewing:
            OK = slew
        else:
            OK = hold
        return OK

    @TEC_PID_OK.setter
    def TEC_PID_OK(self, OK):
        if OK:
            if self.slewing:
                self.slew = True
            else:
                self.hold = True

    def handle_TEC_PID_OK_change(self, event):
        TEC_PID_OK = event.value
        logging.debug(f"TEC_PID_OK: {TEC_PID_OK}")
        if not TEC_PID_OK:
            self.TEC_PID_OK = True

    @monitored_property
    def slew(self, TEC_PID, TEC_slew_PID):
        slew = allclose(TEC_PID, TEC_slew_PID)
        return slew

    @slew.setter
    def slew(self, slew):
        if slew:
            self.TEC_PID = self.TEC_slew_PID
        else:
            self.TEC_PID = self.TEC_default_PID

    @monitored_property
    def hold(self, TEC_PID, TEC_default_PID):
        return allclose(TEC_PID, TEC_default_PID)

    @hold.setter
    def hold(self, hold):
        if hold:
            self.TEC_PID = self.TEC_default_PID
        else:
            self.TEC_PID = self.TEC_slew_PID

    TEC_set_T = alias_property("TEC.command_value")
    TEC_T = alias_property("TEC.value")
    TEC_PID = alias_property("TEC.PIDCOF")

    TEC_P = alias_property("TEC.PCOF")
    TEC_I = alias_property("TEC.ICOF")
    TEC_D = alias_property("TEC.DCOF")

    @monitored_property
    def TEC_slew_PID(self, TEC_slew_P, TEC_slew_I, TEC_slew_D):
        from numpy import array
        return array([TEC_slew_P, TEC_slew_I, TEC_slew_D])

    TEC_slew_P = db_property("TEC_slew_P", 0.75)
    TEC_slew_I = db_property("TEC_slew_I", 0.0)
    TEC_slew_D = db_property("TEC_slew_D", 0.0)

    @monitored_property
    def TEC_default_PID(self, TEC_default_P, TEC_default_I, TEC_default_D):
        from numpy import array
        return array([TEC_default_P, TEC_default_I, TEC_default_D])

    TEC_default_P = db_property("TEC_default_P", 0.75)
    TEC_default_I = db_property("TEC_default_I", 0.178)
    TEC_default_D = db_property("TEC_default_D", 0.422)

    @property
    def TEC(self):
        from lightwave_temperature_controller import lightwave_temperature_controller
        return lightwave_temperature_controller

    chiller_T_min = db_property("chiller_T_min", 8.0)
    chiller_T_max = db_property("chiller_T_max", 54.0)

    chiller_T = alias_property("chiller.value")
    chiller_set_T = alias_property("chiller.command_value")

    @property
    def chiller(self):
        from oasis_chiller import oasis_chiller
        return oasis_chiller

    scanning = alias_property("scan.scanning")
    scan_slewing = alias_property("scan.slewing")

    @monitored_property
    def chiller_set_point_times_and_values(
            self,
            rising_ramp_start_times,
            falling_ramp_start_times,
            chiller_headstart_time,
            chiller_T_min,
            chiller_T_max,
            scan_times_and_temperatures,
    ):
        # If the maximum TEC temperature exceeds the chiller switch temperature (e.g. 79 C),
        #    15 s in advance of the start of a rising ramp, switch the set point to high limit (e.g. 45 C)
        #    15 s in advance of the start of a falling ramp, switch the set point to idle temperature (e.g. 8 C)
        from numpy import clip, inf
        temperatures = scan_times_and_temperatures[1]
        T = {}
        if len(temperatures) > 0:
            max_temp = max(temperatures)
            if max_temp < chiller_T_min + 75:
                T[0] = chiller_T_min
            else:
                if temperatures[0] >= chiller_T_min + 75:
                    T[0] = chiller_T_max
                else:
                    T[0] = chiller_T_min
                times = clip(rising_ramp_start_times - chiller_headstart_time, 0, inf)
                for t in times:
                    T[t] = chiller_T_max
                times = clip(falling_ramp_start_times - chiller_headstart_time, 0, inf)
                for t in times:
                    T[t] = chiller_T_min
        times = sorted(T.keys())
        values = [T[t] for t in times]
        return times, values

    chiller_headstart_time = db_property("chiller_headstart_time", 15)

    @monitored_property
    def rising_ramp_start_times(self, scan_times_and_temperatures):
        from numpy import diff
        t, T = scan_times_and_temperatures
        times = t[0:-1][diff(T) > 0]
        return times

    @monitored_property
    def falling_ramp_start_times(self, scan_times_and_temperatures):
        from numpy import diff
        t, T = scan_times_and_temperatures
        times = t[0:-1][diff(T) < 0]
        return times

    scan_times_and_temperatures = alias_property("scan.trajectory_times_values")

    @property
    def scan(self):
        from temperature_scan_client import temperature_scan_client
        return temperature_scan_client(self.domain_name)

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def db_name(self):
        return f"{self.class_name}/{self.domain_name}"


def allclose(x, y):
    from numpy import allclose
    try:
        slew = allclose(x, y)
    except Exception as x:
        logging.warning(f"allclose({x},{y}): {x}")
        slew = False
    return slew


def lookup(x_y, x0):
    from numpy import nan
    x, y = x_y
    y0 = nan
    for i in range(len(x) - 1, -1, -1):
        if x0 >= x[i]:
            y0 = y[i]
            break
    return y0


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = temperature_system_driver("BioCARS")


    @handler
    def report(event): logging.info(f"event={event}")

    reference(self, "chiller_set_T_OK").monitors.add(report)
    reference(self, "chiller_set_T").monitors.add(report)
    reference(self, "chiller_nominal_set_T").monitors.add(report)
