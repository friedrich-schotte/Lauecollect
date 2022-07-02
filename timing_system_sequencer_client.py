"""
Author: Friedrich Schotte
Date created: 2022-03-28
Date last modified: 2022-04-11
Revision comment:
"""
__version__ = "1.0"

from PV_record import PV_record
from cached_function import cached_function


@cached_function()
def timing_system_sequencer_client(timing_system, base_name="sequencer"):
    return Timing_System_Sequencer_Client(timing_system, base_name)


class Timing_System_Sequencer_Client(PV_record):
    from PV_property import PV_property

    base_name = "sequencer"

    def __init__(self, timing_system, base_name):
        super().__init__(domain_name=timing_system.name)
        self.timing_system = timing_system
        self.base_name = base_name

    def __repr__(self):
        return f"{self.timing_system}.{self.base_name}"

    @property
    def prefix(self):
        return f'{self.timing_system.prefix}.{self.base_name}'.upper()

    queue_active = PV_property(dtype=bool)
    acquiring = PV_property(dtype=bool)
    current_queue_length = PV_property(dtype=int)
    current_queue_sequence_count = PV_property(dtype=int)
    current_queue_repeat_count = PV_property(dtype=int)
    current_queue_max_repeat_count = PV_property(dtype=int)
    queue_length = PV_property(dtype=int)
    queue_sequence_count = PV_property(dtype=int)
    queue_repeat_count = PV_property(dtype=int)
    queue_max_repeat_count = PV_property(dtype=int)
    next_queue_sequence_count = PV_property(dtype=int)
    cache_enabled = PV_property(dtype=bool)
    cache_size = PV_property(dtype=int)
    remote_cache_size = PV_property(dtype=int)
    configured = PV_property(dtype=bool)
    running = PV_property(dtype=bool)
    phase_matching_period = PV_property(dtype=float)

    @property
    def composer(self):
        from timing_system_composer_client import timing_system_composer_client
        return timing_system_composer_client(self.timing_system)


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    from timing_system_client import timing_system_client

    timing_system = timing_system_client(domain_name)
    self = timing_system_sequencer_client(timing_system, "sequencer")

    print("self.delay")