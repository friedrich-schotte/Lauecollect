"""
Author: Friedrich Schotte
Date created: 2022-03-30
Date last modified: 2022-05-08
Revision comment:
"""
__version__ = "1.0"

from PV_record import PV_record
from cached_function import cached_function
from PV_property import PV_property
from PV_record_property import PV_record_property


@cached_function()
def timing_system_channel_client(channels, base_name):
    return Timing_System_Channel_Client(channels, base_name)


class Timing_System_Channel_Client(PV_record):
    base_name = "channel"

    def __init__(self, channels, base_name):
        super().__init__(domain_name=channels.name)
        self.channels = channels
        self.base_name = base_name

    def __repr__(self):
        return f"{self.channels}.{self.base_name}"

    @property
    def prefix(self):
        return f'{self.channels.prefix}.{self.base_name}'.upper()

    trig_count = PV_record_property(type_name="timing_system_register_client")
    acq_count = PV_record_property(type_name="timing_system_register_client")
    acq = PV_record_property(type_name="timing_system_register_client")
    delay = PV_record_property(type_name="timing_system_register_client")

    PP_enabled = PV_property(dtype=bool)
    input = PV_record_property(type_name="timing_system_register_client")
    description = PV_property(dtype=str)
    mnemonic = PV_property(dtype=str)
    special = PV_property(dtype=str)
    special_choices = PV_property(dtype=list)
    specout = PV_record_property(type_name="timing_system_register_client")
    offset_HW = PV_property(dtype=float)
    offset_sign = PV_property(dtype=float)
    offset_sign_choices = PV_property(dtype=list)
    pulse_length_HW = PV_property(dtype=float)
    pulse = PV_record_property(type_name="timing_system_register_client")
    pulse_choices = PV_property(dtype=list)
    offset_PP = PV_property(dtype=float)
    pulse_length_PP = PV_property(dtype=float)
    enable = PV_record_property(type_name="timing_system_register_client")
    timed = PV_property(dtype=str)
    timed_choices = PV_property(dtype=list)
    gated = PV_property(dtype=str)
    gated_choices = PV_property(dtype=list)
    counter_enabled = PV_property(dtype=bool)
    output_status = PV_property(dtype=str)
    output_status_choices = PV_property(dtype=list)
    override = PV_record_property(type_name="timing_system_register_client")
    override_state = PV_record_property(type_name="timing_system_register_client")

    stepsize = PV_property(dtype=float)
    offset = PV_property(dtype=float)
    pulse_length = PV_property(dtype=float)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system_client import timing_system_client

    timing_system = timing_system_client(domain_name)
    self = timing_system_channel_client(timing_system.channels, "scl")

    print("self.override.count")
    print("self.override_state.count")
