"""
Author: Friedrich Schotte
Date created: 2022-04-25
Date last modified: 2022-08-03
Revision comment:
"""
__version__ = "2.0"

import logging

from scan_driver import Scan_Driver
from cached_function import cached_function
from monitored_value_property import monitored_value_property
from alias_property import alias_property
from monitored_property import monitored_property
from db_property import db_property


@cached_function()
def timing_system_delay_scan_driver(timing_system):
    return Timing_System_Delay_Scan_Driver(timing_system)


class Timing_System_Delay_Scan_Driver(Scan_Driver):
    def __init__(self, timing_system):
        super().__init__(domain_name=timing_system.domain_name)
        self.timing_system = timing_system

    def __repr__(self):
        return f"{self.timing_system}.delay_scan"

    @property
    def db_name(self):
        return f"{self.timing_system.db_name}/delay_scan"

    motor_name = db_property("motor_name", "timing_system.composer.delay")

    @monitored_property
    def motor(self, motor_name):
        full_motor_name = f"self.{motor_name}"
        object_name = ".".join(full_motor_name.split(".")[0:-1])
        property_name = full_motor_name.split(".")[-1]
        # noinspection PyBroadException
        try:
            motor_object = eval(object_name)
        except Exception as x:
            logging.error(f"{object_name!r}: {x}")
            if motor_name:
                dummy_motor_name = f"{self.domain_name}.{motor_name}"
            else:
                dummy_motor_name = ""
            from dummy_motor import Dummy_Motor
            motor = Dummy_Motor(dummy_motor_name)
        else:
            from reference import reference
            motor = reference(motor_object, property_name)
        return motor

    # PVs to be hosted
    values_string = db_property("values_string", "", local=True)
    wait = monitored_value_property(False)
    return_value = alias_property("timing_system.delay.value")
    ready = monitored_value_property(True)

    @monitored_property
    def values(self, sequences_cached):
        return [delay(sequence) for sequence in sequences_cached]

    # Imported PVs
    enabled = alias_property("acquisition.scanning.delay")
    scan_point_divider = alias_property("acquisition.scan_point_dividers.delay")

    # Diagnostics PVs to be hosted
    motor_value = alias_property("timing_system.composer.delay")
    motor_command_value = alias_property("motor_value")
    motor_moving = monitored_value_property(False)

    def format(self, value):
        from time_string import time_string
        return time_string(value)

    def value_of_formatted_value(self, formatted_value):
        from time_string import seconds
        return seconds(formatted_value)

    def handle_values_index_change(self, values_index, time):
        logging.debug(f"[Ignoring values_index={values_index}]")

    def handle_collecting_dataset_change(self, collecting_dataset):
        logging.debug(f"[Ignoring collecting_dataset={collecting_dataset}]")

    @monitored_property
    def sequences_cached(self, values_string):
        return self.sequences_of_values_string(values_string)

    @property
    def sequences(self):
        return self.sequences_of_values_string(self.values_string)

    def sequences_of_values_string(self, values_string):
        import traceback
        sequences = self.sequence
        expr = values_string
        if expr:
            # noinspection PyBroadException
            try:
                expr = self.sequence_expander.delay_sequences(expr)
            except Exception:
                logging.error("delay_sequences(%r): %s" % (expr, traceback.format_exc()))
                expr = ""
        if expr:
            from timing_system_sequence_driver_2 import Timing_System_Sequence_Driver  # noqa - for eval
            from timing_system_driver_9 import timing_system_driver  # noqa - for eval
            from numpy import nan  # noqa - for eval
            # noinspection PyBroadException
            try:
                sequences = eval(expr)
            except Exception:
                logging.error("eval(%r): %s" % (expr, traceback.format_exc()))
        from as_list import as_list
        sequences = as_list(sequences)
        return sequences

    @property
    def sequence_expander(self):
        from timing_system_sequence_expander_driver_3 import timing_system_sequence_expander_driver
        return timing_system_sequence_expander_driver(self.timing_system)

    @property
    def sequence(self):
        return self.timing_system_sequencer.Sequence(acquiring=True)

    timing_system_sequencer = alias_property("timing_system.sequencer")


def delay(sequence):
    from numpy import nan
    if hasattr(sequence, "laser_on") and not sequence.laser_on:
        delay = nan
    elif hasattr(sequence, "nom_delay"):
        delay = sequence.nom_delay
    else:
        delay = nan
    return delay


if __name__ == '__main__':
    from handler import handler
    from reference import reference

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from timing_system_driver_9 import timing_system_driver

    timing_system = timing_system_driver(domain_name)
    self = timing_system_delay_scan_driver(timing_system)

    @handler
    def report(event):
        logging.info(f"{event}")

    # print(f"self.values_string = {self.values_string!r}")

    attributes = [
        # "values_string",
        # "sequences",
        # "values",
        # "value_count",
    ]
    for attribute in attributes:
        reference(self, attribute).monitors.add(report)
