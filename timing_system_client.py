"""
Author: Friedrich Schotte
Date created: 2022-03-28
Date last modified: 2022-08-03
Revision comment: Removed property no longer needed
"""
__version__ = "1.2.5"

import logging

from PV_connected_property import PV_connected_property
from PV_record import PV_record
from cached_function import cached_function
from PV_record_property import PV_record_property
from PV_property import PV_property
from timing_system_channel_client import timing_system_channel_client as channel


@cached_function()
def timing_system_client(domain_name): return Timing_System_Client(domain_name)


class Timing_System_Client(PV_record):
    online = PV_connected_property("online")

    timing_system_online = PV_property(name="online", dtype=bool)
    all_register_names = PV_property(dtype=list)

    registers = PV_record_property(type_name="timing_system_registers_client")
    channels = PV_record_property(type_name="timing_system_channels_client")
    sequencer = PV_record_property(type_name="timing_system_sequencer_client")
    composer = PV_record_property(type_name="timing_system_composer_client")
    acquisition = PV_record_property(type_name="timing_system_acquisition_client")
    delay_scan = PV_record_property(type_name="scan_client")
    laser_on_scan = PV_record_property(type_name="scan_client")

    p0_shift = PV_record_property(type_name="timing_system_register_client")

    delay = PV_record_property(type_name="timing_system_variable_client")

    clock_period = PV_property(dtype=float)
    clock_multiplier = PV_property(dtype=int)
    clock_divider = PV_property(dtype=int)
    bct = PV_property(dtype=float)
    P0t = PV_property(dtype=float)
    clk_shift_stepsize = PV_property(dtype=float)
    hsct = PV_property(dtype=float)
    hlc_nslots = PV_property(dtype=int)
    phase_matching_period = PV_property(dtype=float)
    hlc_div = PV_property(dtype=int)
    nsl_div = PV_property(dtype=int)
    hlct = PV_property(dtype=float)
    nslt = PV_property(dtype=float)

    sequence = PV_property(dtype=str)
    acquisition_sequence = PV_property(dtype=str)

    timing_system_prefix = PV_property(name="prefix", dtype=str)
    prefixes = PV_property(dtype=list)
    ip_address = PV_property(dtype=str)
    configuration_name = PV_property(dtype=str)
    configuration_names = PV_property(dtype=list)
    loading_configuration = PV_property(dtype=bool)
    saving_configuration = PV_property(dtype=bool)


for i in range(0, 24):
    setattr(Timing_System_Client, f"ch{i + 1}", PV_record_property(channel))

if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = timing_system_client(domain_name)

    from handler import handler as _handler
    from reference import reference as _reference

    @_handler
    def report(event=None):
        logging.info(f'event = {event}')

    references = [
        _reference(self.registers.image_number, "count"),
        _reference(self.registers.hlcnd, "value"),
    ]
    for ref in references:
        ref.monitors.add(report)
