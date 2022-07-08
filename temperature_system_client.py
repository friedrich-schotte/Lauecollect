"""
Authors: Friedrich Schotte
Date created: 2021-11-26
Date last modified: 2022-07-02
Revision comment: Added: domain_name
"""
__version__ = "1.6"

import logging

from cached_function import cached_function
from EPICS_motor import EPICS_motor


@cached_function()
def temperature_system_client(domain_name):
    return Temperature_System_Client(domain_name)


class Temperature_System_Client(EPICS_motor):
    from PV_property import PV_property
    from numpy import nan

    def __init__(self, domain_name):
        self.__domain_name__ = domain_name
        name = "temperature_system"
        prefix = f"{self.__domain_name__}:temperature_system".upper()
        super().__init__(prefix=prefix, name=name, timeout=1e6, readback_slop=0.050)

    def __repr__(self):
        return f"{self.__class_name__}({self.__domain_name__!r})"

    @property
    def __class_name__(self):
        return type(self).__name__.lower()

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


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s, line %(lineno)d: %(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = temperature_system_client("BioCARS")

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

    from reference import reference as _reference
    from handler import handler as _handler


    @_handler
    def report(event): logging.info(f"event={event}")

    _reference(self, "chiller_set_T_OK").monitors.add(report)
    _reference(self, "chiller_nominal_set_T").monitors.add(report)
    _reference(self, "chiller_set_T").monitors.add(report)
