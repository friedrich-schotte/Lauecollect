"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-07-29
Revision comment:
"""
__version__ = "2.0"

import logging
from traceback import format_exc

from PV_property import PV_property
from alias_property import alias_property
from db_property import db_property
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property


class Timing_System_Register_Driver(object):
    def __init__(self,
                 registers,
                 description="",
                 name="",
                 address=0,
                 bit_offset=0,
                 bits=32
                 ):
        self.registers = registers
        self.description = description
        self.name = name
        self.address = address
        self.bit_offset = bit_offset
        self.bits = bits

    description = monitored_value_property("")
    address = monitored_value_property(0)
    bit_offset = monitored_value_property(0)
    bits = monitored_value_property(0)

    def __repr__(self):
        return f"{self.class_name}({self.description!r}, {self.name!r}, 0x{self.address:08X}, {self.bit_offset}, {self.bits})"

    @property
    def class_name(self):
        return type(self).__name__

    @property
    def prefix(self):
        return f"{self.registers.prefix}.{self.name}"

    @property
    def db_name(self):
        return f"{self.registers.db_name}.{self.name}"

    @property
    def timing_system(self):
        return self.registers.timing_system

    count = PV_property(dtype=int, upper_case=False)

    offset = db_property("offset", 0.0)
    sign = 1

    @monitored_property
    def value(self, dial, offset):
        return dial * self.sign + offset

    @value.setter
    def value(self, value):
        from numpy import isnan
        value = float(value)
        if not isnan(value):
            self.dial = self.dial_from_user(value)

    command_value = alias_property("value")

    @monitored_property
    def dial(self, count, stepsize):
        return count * stepsize

    @dial.setter
    def dial(self, value):
        self.count = self.count_from_dial(value)

    @property
    def min_count(self):
        """Lowest allowed count"""
        if self.custom_min_count is not None:
            return self.custom_min_count
        return 0

    @min_count.setter
    def min_count(self, value):
        if value < 0:
            value = 0
        self.custom_min_count = value

    custom_min_count = None

    @staticmethod
    def calculate_max_count(max_count):
        return max_count

    def input_references_max_count(self):
        from reference import reference
        if hasattr(self.registers, f"{self.name}_max_count"):
            references = [reference(self.registers, f"{self.name}_max_count")]
        else:
            references = [reference(self, "default_max_count")]
        return references

    max_count = monitored_property(
        calculate=calculate_max_count,
        input_references=input_references_max_count,
    )

    @monitored_property
    def default_max_count(self, bits):
        return 2 ** bits - 1

    @property
    def min_dial(self):
        dial_value = self.min_count * self.stepsize
        return dial_value

    @min_dial.setter
    def min_dial(self, min_dial):
        # noinspection PyBroadException
        try:
            self.min_count = self.count_from_dial(min_dial)
        except Exception:
            logging.warning(f"{self}.min_dial = {min_dial!r}: {format_exc()}")

    @property
    def max_dial(self):
        dial_value = self.max_count * self.stepsize
        return dial_value

    @max_dial.setter
    def max_dial(self, max_dial):
        # noinspection PyBroadException
        try:
            self.max_count = self.count_from_dial(max_dial)
        except Exception:
            logging.warning(f"{self!r}.max_dial = {max_dial!r}: {format_exc()}")

    @property
    def min_value(self):
        return self.min_dial * self.sign + self.offset

    @min_value.setter
    def min_value(self, value):
        self.min_dial = self.dial_from_user(value)

    @property
    def max_value(self):
        return self.max_dial * self.sign + self.offset

    @max_value.setter
    def max_value(self, value):
        self.max_dial = self.dial_from_user(value)

    def count_from_value(self, value):
        """Convert user value to integer register count"""
        return self.count_from_dial(self.dial_from_user(value))

    def value_from_count(self, count):
        """Convert integer register count to user value"""
        dial_value = count * self.stepsize
        return dial_value * self.sign + self.offset

    def count_from_dial(self, dial_value):
        """Convert delay in seconds to integer register count"""
        count = self.next_count(dial_value / self.stepsize)
        return count

    def dial_from_user(self, value):
        return (value - self.offset) / self.sign

    @staticmethod
    def calculate_stepsize(stepsize):
        return stepsize

    def input_references_stepsize(self):
        from reference import reference
        if hasattr(self.registers, f"{self.name}_stepsize"):
            references = [reference(self.registers, f"{self.name}_stepsize")]
        else:
            references = [reference(self, "default_stepsize")]
        return references

    stepsize = monitored_property(
        calculate=calculate_stepsize,
        input_references=input_references_stepsize,
    )

    default_stepsize = db_property("stepsize", 1.0)

    def next_count(self, count):
        """Round value to the next allowed integer count"""
        from numpy import rint, isnan, nan
        from to_int import to_int

        if isnan(count):
            return nan
        if count < self.min_count:
            count = self.min_count
        if count > self.max_count:
            count = self.max_count
        count = to_int(rint(count))
        return count


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS"
    # name = "LaserLab"

    from timing_system_driver_9 import timing_system_driver
    from timing_system_registers_driver_2 import timing_system_registers_driver

    timing_system = timing_system_driver(name)
    registers = timing_system_registers_driver(timing_system)
    # self = registers.ch4_delay
    self = registers.hlcnd

    from handler import handler as _handler
    from reference import reference as _reference

    @_handler
    def report(event=None):
        logging.info(f'event = {event}')

    property_names = [
        "value",
        "stepsize",
        "offset",
    ]
    for property_name in property_names:
        print(f"self.{property_name} = {getattr(self, property_name)}")
    for property_name in property_names:
        _reference(self, property_name).monitors.add(report)
