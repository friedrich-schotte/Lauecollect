"""
Authors: Friedrich Schotte
Date created: 2021-11-26
Date last modified: 2021-12-02
Revision comment: Added parameter TEC_slew_dT
"""
__version__ = "1.5"

import logging
from reference import reference
from handler import handler
from EPICS_motor import EPICS_motor


class Temperature_System(EPICS_motor):
    from PV_property import PV_property
    from numpy import nan

    def __init__(self, prefix, name):
        super().__init__(prefix=prefix, name=name, timeout=1e6, readback_slop=0.050)

    # Parameters
    chiller_T_min = PV_property("chiller_T_min", nan)
    chiller_T_max = PV_property("chiller_T_max", nan)
    chiller_headstart_time = PV_property("chiller_headstart_time", nan)
    TEC_default_P = PV_property("TEC_default_P", nan)
    TEC_default_I = PV_property("TEC_default_I", nan)
    TEC_default_D = PV_property("TEC_default_D", nan)
    TEC_slew_P = PV_property("TEC_slew_P", nan)
    TEC_slew_I = PV_property("TEC_slew_I", nan)
    TEC_slew_D = PV_property("TEC_slew_D", nan)
    TEC_slew_dT = PV_property("TEC_slew_dT", nan)

    # Diagnostics
    slew = PV_property("slew", nan)
    hold = PV_property("hold", nan)
    slewing = PV_property("slewing", nan)
    TEC_PID_OK = PV_property("TEC_PID_OK", nan)
    TEC_P = PV_property("TEC_P", nan)
    TEC_I = PV_property("TEC_I", nan)
    TEC_D = PV_property("TEC_D", nan)
    TEC_set_T = PV_property("TEC_set_T", nan)
    chiller_set_T_OK = PV_property("chiller_set_T_OK", nan)
    chiller_nominal_set_T = PV_property("chiller_nominal_set_T", nan)
    chiller_set_T = PV_property("chiller_set_T", nan)
    chiller_T = PV_property("chiller_T", nan)


temperature_system = Temperature_System(prefix="BIOCARS:TEMPERATURE_SYSTEM", name="temperature_system")

if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = temperature_system  # for debugging

    print(f'self = {self}')
    print('')
    print(f'self.VAL = {self.VAL}')
    print(f'self.RBV = {self.RBV}')
    print(f'self.DMOV = {self.DMOV}')
    print('')
    print(f'self.slew = {self.slew}')
    print('')
    print(f'self.TEC_default_P = {self.TEC_default_P}')
    print(f'self.TEC_default_I = {self.TEC_default_I}')
    print(f'self.TEC_default_D = {self.TEC_default_D}')
    print('')
    print(f'self.chiller_T_min = {self.chiller_T_min}')
    print(f'self.chiller_T_max = {self.chiller_T_max}')
    print('')

    @handler
    def report(event): logging.info(f"event={event}")

    reference(self, "chiller_set_T_OK").monitors.add(report)
    reference(self, "chiller_nominal_set_T").monitors.add(report)
    reference(self, "chiller_set_T").monitors.add(report)
