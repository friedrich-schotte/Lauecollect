#!/usr/bin/env python
"""
FPGA Timing System Simulator

Author: Friedrich Schotte
Date created: 2021-08-30
Date last modified: 2021-09-16
Revision comment: Multiplied software register addresses by 4
"""
__version__ = "1.1.2"

import traceback
from logging import info, warning

from cached_function import cached_function


@cached_function()
def timing_system_simulator_registers(name):
    return Timing_System_Simulator_Registers(name)


class Timing_System_Simulator_Registers:
    def __init__(self, name):
        self.name = name
        self.read_configuration()

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__.lower(), self.name)

    def __len__(self):
        return len(self.names)

    def __iter__(self):
        for name in self.names:
            yield self.register(name)

    @property
    def timing_system(self):
        from timing_system_simulator import timing_system_simulator
        return timing_system_simulator(self.name)

    def load_values(self, filename):
        self.values = open(filename).read()

    def save_values(self, filename):
        open(filename, "w").write(self.values)

    names = []

    def read_configuration(self):
        self.names = []
        # debug("Reading %r" % self.configuration_filename)
        text = open(self.configuration_filename).read()
        for line in text.splitlines():
            fields = line.split("\t")
            try:
                description = fields[0]
            except IndexError:
                description = ""
            try:
                name = fields[1]
            except IndexError:
                name = ""
            try:
                address = int(fields[2], base=16)
            except (IndexError, ValueError):
                address = 0
            try:
                bit_offset = int(fields[3])
            except (IndexError, ValueError):
                bit_offset = 0
            try:
                bits = int(fields[4])
            except (IndexError, ValueError):
                bits = 32
            register = self.Register(self, description, name, address, bit_offset, bits)
            setattr(self, name, register)
            self.names.append(name)

    @property
    def values(self):
        lines = ["#mnemonic\tcount\n"]
        for register in self:
            lines.append("%s\t%r" % (register.name, register.count))
        text = "\n".join(lines)
        return text

    @values.setter
    def values(self, text):
        for line in text.splitlines():
            if not line.startswith("#"):
                fields = line.split()
                try:
                    name = fields[0]
                except IndexError:
                    warning("ignoring line %r" % line)
                    continue
                try:
                    count = int(fields[1])
                except (IndexError, ValueError):
                    warning("ignoring line %r" % line)
                    continue
                self.register(name).count = count

    def register(self, name):
        if name not in self.names:
            register = self.Register(self, name=name)
            setattr(self, name, register)
            self.names.append(name)
        register = getattr(self, name)
        return register

    class Register(object):
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

        def __repr__(self):
            return "%s(%r,%r,0x%08X,%r,%r)" % (
                type(self).__name__,
                self.description,
                self.name,
                self.address,
                self.bit_offset,
                self.bits
            )

        @property
        def bitmask(self):
            return self.registers.bitmask(self.bit_offset, self.bits)

        def get_count(self):
            return self.registers.read(self.address, self.bitmask)

        def set_count(self, value):
            self.registers.write(self.address, self.bitmask, value << self.bit_offset)

        count = property(get_count, set_count)

    @property
    def configuration_filename(self):
        return self.timing_system.directory + "/registers.txt"

    def read(self, address, bitmask):
        value = self.read_address(address)
        bit_offset = self.bit_offset(bitmask)
        value = (value & bitmask) >> bit_offset
        # debug("read(0x%08X,0x%08X): %d" % (address,bitmask,value));
        return value

    def write(self, address, bitmask, value):
        # debug("write 0x%08X,0x%08X,%d" % (address,bitmask,value));
        old_value = self.read_address(address)
        bit_offset = self.bit_offset(bitmask)
        new_value = (old_value & ~bitmask) | (value & bitmask)
        self.write_address(address, new_value)

    @staticmethod
    def bit_offset(bitmask):
        for bit_offset in range(0, 32):
            if (bitmask >> bit_offset) & 1 != 0:
                break
        else:
            bit_offset = 0
        return bit_offset

    @staticmethod
    def bitmask(bit_offset, bits):
        bitmask = ((1 << bits) - 1) << bit_offset
        return bitmask

    def read_address(self, address):
        """"Get value of 32-bit register aligned on 4-byte boundary
        return value: 32-bit unsigned integer"""
        if self.is_software_register_address(address):
            address *= 4
        data = self.register_page_data(self.base_address(address))
        value = data[self.register_index(address)]
        return value

    def write_address(self, address, value):
        """"Change 32-bit register aligned on 4-byte boundary
        value: 32-bit unsigned integer"""
        if self.is_software_register_address(address):
            address *= 4
        data = self.register_page_data(self.base_address(address))
        # debug("".join(traceback.format_stack()))
        # debug(f"{data.filename}[{self.register_index(address)}] = {value}")
        data[self.register_index(address)] = value

    @staticmethod
    def is_software_register_address(address):
        return address < 1024

    def base_address(self, address):
        base_address = address // self.pagesize * self.pagesize
        return base_address

    def register_index(self, address):
        base_address = self.base_address(address)
        register_index = (address - base_address) // 4
        return register_index

    from cached_function import cached_function

    @cached_function()
    def register_page_data(self, base_address):
        filename = self.register_page_filename(base_address)
        self.initialize_register_page_file(filename)
        from numpy import memmap, uint32
        data = memmap(filename, uint32)
        return data

    def initialize_register_page_file(self, filename):
        from os.path import exists, getsize
        if not exists(filename) or getsize(filename) != self.pagesize:
            if exists(filename):
                data = open(filename, "rb").read()
            else:
                data = b""
            data = data.ljust(self.pagesize, b"\0")[0:self.pagesize]
            open(filename, "rb").write(data)

    def register_page_filename(self, base_address):
        base_address = base_address // self.pagesize * self.pagesize
        return self.timing_system.directory + "/registers/0x%08X.dat" % base_address

    pagesize = 256


if __name__ == "__main__":  # for testing
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS"
    # name = "LaserLab"

    self = timing_system_simulator_registers(name)
    print(f"self = {self}")

    filename = self.timing_system.directory + "/register-values.txt"
    print("print(self.values)")
    print(f"self.load_values({filename!r})")
    print(f"self.save_values({filename!r})")
