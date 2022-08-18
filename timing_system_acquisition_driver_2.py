"""
Author: Friedrich Schotte
Date created: 2022-04-25
Date last modified: 2022-08-17
Revision comment: Debugging
"""
__version__ = "2.1.2"

import logging

from monitored_property import monitored_property
from thread_property_2 import thread_property, cancelled

from alias_property import alias_property
from cached_function import cached_function


@cached_function()
def timing_system_acquisition_driver(timing_system):
    return Timing_System_Acquisition_Driver(timing_system)


class Timing_System_Acquisition_Driver(object):
    def __init__(self, timing_system):
        self.timing_system = timing_system

    def __repr__(self):
        return f"{self.timing_system}.acquisition"

    @thread_property
    def sequences_loading(self):
        from time import sleep
        logging.info("Timing system sequences loading...")
        self.sequencer.set_queue_sequences(self.sequences)
        while not cancelled():
            sleep(0.25)
            if not self.sequencer.update_queues:
                break
        logging.info("Timing system sequences loaded")

    @monitored_property
    def first_scan_point(
            self,
            sequencer_queue_repeat_count,
            sequencer_queue_length,
            sequencer_queue_sequence_count,
            sequences_per_scan_point,
    ):
        first = (sequencer_queue_repeat_count * sequencer_queue_length +
                 sequencer_queue_sequence_count) // sequences_per_scan_point
        # assert(first == self.registers.image_number.count)
        return first

    @first_scan_point.setter
    def first_scan_point(self, first):
        from numpy import isnan

        first = float(first)
        if not isnan(first):
            first = int(first)
            repeat_count = (first * self.sequences_per_scan_point) // self.sequencer_queue_length
            sequence_count = (first * self.sequences_per_scan_point) % self.sequencer_queue_length

            # self.sequencer_queue_repeat_count = repeat_count
            setattr(self, "sequencer_queue_repeat_count", repeat_count)
            # self.sequencer_queue_sequence_count = sequence_count
            setattr(self, "sequencer_queue_sequence_count", sequence_count)

            self.registers.image_number.count = first
            self.registers.pass_number.count = 0
            self.registers.pulses.count = 0

    @monitored_property
    def last_scan_point(
            self,
            sequencer_queue_max_repeat_count,
            sequencer_queue_length,
            sequences_per_scan_point,
    ):
        last = (sequencer_queue_max_repeat_count * sequencer_queue_length
                // sequences_per_scan_point - 1)
        return last

    @last_scan_point.setter
    def last_scan_point(self, last):
        from numpy import isnan, ceil

        last = float(last)
        if not isnan(last):
            last = int(last)
            max_repeat_count = int(ceil((last + 1) * self.sequences_per_scan_point / self.sequencer_queue_length))

            # self.sequencer_queue_max_repeat_count = max_repeat_count
            setattr(self, "sequencer_queue_max_repeat_count", max_repeat_count)

    @thread_property
    def generating_packets(self):
        from time import sleep
        logging.info("Generating packets: started")
        sequences = self.sequences
        sequences = self.sequencer.unique_sequences(sequences)
        sequences = [s for s in sequences if not s.is_cached]

        for i, sequence in enumerate(sequences):
            if cancelled():
                break
            if not sequence.is_cached:
                logging.info("Generating packets: %.0f/%.0f" % (i + 1, len(sequences)))
                _ = sequence.data

        if not cancelled():
            logging.info("Uploading packets...")
            self.sequencer.set_queue_sequences(self.sequences)
            while not cancelled():
                sleep(0.25)
                if not self.sequencer.update_queues:
                    break

        logging.info("Generating packets: done")

    @property
    def sequences(self):
        # Update "following_delay" properties
        sequences = self.Sequences(sequences=self.sequences_simple)[:]

        sequences_basic = self.sequences_basic
        n = len(sequences_basic)
        for i, sequence in enumerate(sequences):
            sequence_basic = sequences_basic[i % n]
            for attribute in "xdet_on", "pump_on", "acquiring", "image_number_inc":
                value = getattr(sequence_basic, attribute)
                setattr(sequence, attribute, value)
        return sequences

    delay_scan_values = alias_property("delay_scan.values")
    laser_on_scan_values = alias_property("laser_on_scan.values")
    delay_scan_scan_point_divider = alias_property("delay_scan.scan_point_divider")
    laser_on_scan_scan_point_divider = alias_property("laser_on_scan.scan_point_divider")

    @property
    def sequences_simple(self):
        delay_values = repeat(self.delay_scan.sequences, self.delay_scan.scan_point_divider)
        laser_on_values = repeat(self.laser_on_scan.values, self.laser_on_scan.scan_point_divider)
        N = max(len(delay_values), len(laser_on_values))
        delay_values = tile(delay_values, N // len(delay_values))
        laser_on_values = tile(laser_on_values, N // len(laser_on_values))

        sequences = tile(self.sequences_basic, N)

        for i in range(0, N):
            sequences[i].update(delay_values[i])
            sequences[i].laser_on &= laser_on_values[i]

        return sequences

    @property
    def sequences_basic(self):
        sequences = self.Sequences(acquiring=True, image_number_inc=0)[:]
        sequences[-1].image_number_inc = 1
        return sequences

    def Sequences(self, sequences=None, acquiring=True, **kwargs):
        return self.sequencer.Sequences(sequences=sequences, acquiring=acquiring, **kwargs)

    sequencer_queue_length = alias_property("sequencer.queue_length")
    sequencer_queue_repeat_count = alias_property("sequencer.queue_repeat_count")
    sequencer_queue_sequence_count = alias_property("sequencer.queue_sequence_count")
    sequencer_queue_max_repeat_count = alias_property("sequencer.queue_max_repeat_count")

    sequences_per_scan_point = alias_property("composer.sequences_per_scan_point")

    registers = alias_property("timing_system.registers")
    sequencer = alias_property("timing_system.sequencer")
    composer = alias_property("timing_system.composer")
    delay_scan = alias_property("timing_system.delay_scan")
    laser_on_scan = alias_property("timing_system.laser_on_scan")

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    domain_name = alias_property("timing_system.domain_name")


def repeat(a_list, n):
    """tile([1,2,3],2) -> [1,1,2,2,3,3]"""
    from copy import deepcopy
    new_list = []
    for elem in a_list:
        for i in range(0, n):
            new_list.append(deepcopy(elem))
    return new_list


def tile(a_list, n):
    """tile([1,2,3],2) -> [1,2,3,1,2,3]"""
    from copy import deepcopy
    new_list = []
    for i in range(0, n):
        for elem in a_list:
            new_list.append(deepcopy(elem))
    return new_list


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from timing_system_driver_9 import timing_system_driver

    timing_system = timing_system_driver(domain_name)
    self = timing_system_acquisition_driver(timing_system)

    from handler import handler as _handler
    from reference import reference as _reference


    @_handler
    def report(event=None):
        logging.info(f'event = {event}')


    property_names = [
        # "first_scan_point",
        # "last_scan_point",
        "sequencer_queue_repeat_count",
    ]

    for property_name in property_names:
        _reference(self, property_name).monitors.add(report)
