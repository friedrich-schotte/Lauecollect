#!/usr/bin/env python
"""
Oasis thermoelectric chiller by Solid State Cooling Systems,
www.sscooling.com, via RS-323 interface
Model: Oasis 160
See: Oasis Thermoelectric Chiller Manual, Section 7 "Oasis RS-232
communication", p. 15-16
https://www.2spi.com/catalog/documents/uc160-190_manual-rev-m12%20.pdf

Settings: 9600 baud, 8 bits, parity none, stop bits 1, flow control none
DB09 connector pin 2 = TxD, 3 = RxD, 5 = Ground

The controller accepts binary commands and generates binary replies.
It can accept a maximum of two commands per second.
Commands are have the length of one to three bytes.
Replies have a length of either one or two bytes, depending on the command.

Command byte: bit 7: remote control active (1 = remote control,0 = local control)
              bit 6  remote on/off (1 = Oasis running, 0 = Oasis in standby mode)
              bit 5: communication direction (1 = write,0 = read)
              bits 4-0: 00001 [1]: Set-point temperature (followed by 2 bytes: temperature in C * 10)
                        00110 [6]: Temperature low limit (followed by 2 bytes: temperature in C * 10)
                        00111 [7]: Temperature high limit(followed by 2 bytes: temperature in C * 10)
                        01000 [8]: Faults (followed by 1 byte)
                        01001 [9]: Actual temperature (followed by 2 bytes: temperature in C * 10)
                        11110 [30]: % of Maximum thermoelectric power (followed by 3 bytes)
                                    Byte 1 = Mode, Cooling or Heating. If bit 7(MSB) = 0,
                                    then the system is cooling, if bit 7 = 1, then the system is heating.
                                    Ignore the remaining bits, they are arbitrary.
                                    (HEX<80 = cooling, HEX>80 = heating)
                                    Bytes 2 & 3 = %TE Power = (61787-(Byte2+256*Byte3))*100/1235
                        11111 [31]: Reset alarms and restart chiller

The 2-byte value is a 16-bit binary number encoding the temperature in units
of 0.1 degrees Celsius (range 0-400 for 0-40.0 C)

The fault byte is a bit map (0 = OK, 1 = Fault):
bit 0: Tank Level Low
bit 2: Temperature above alarm range
bit 4: RTD Fault
bit 5: Pump Fault
bit 7: Temperature below alarm range

Undocumented commands:
C6:       Receive the lower limit. (should receive back C6 14 00)
E6 14 00: Set set point low limit to 2C
C7:       Receive the upper limit. (should receive back C7 C2 01)
E7 C2 01: Set set point high limit to 45C
E-mail by John Kissam <jkissam@sscooling.com>, May 31, 2016,
"RE: Issue with Oasis 160 (S/N 8005853)"

Author: Friedrich Schotte
Date created: 2021-04-07
Date last modified: 2021-12-04
Revision comment: Added physical model for temperature
"""
__version__ = "1.1"

from logging import debug, info, warning, exception


def run():
    oasis_chiller_simulator.run()


class Oasis_Chiller_Simulator:
    from persistent_property import persistent_property
    from thread_property_2 import thread_property
    from numpy import inf

    def run(self):
        from thread_property_2 import cancelled
        from CAServer import casput, casdel

        self.physics.running = True

        from serial_port_emulator import serial_port_emulator
        self.port = serial_port_emulator()

        casput("NIH:OASIS_SIM.ONLINE", 1)

        while not cancelled():
            command = self.port.read()
            debug(f"Received {command}")
            replies = self.replies(command)
            debug(f"Replying {replies}")
            self.port.write(replies)

        casdel("NIH:OASIS_SIM.ONLINE")

        self.physics.running = False

    running = thread_property(run)

    port = None

    class bits:
        remote = 0b10000000
        running = 0b01000000
        write = 0b00100000

    class codes:
        temperature_set_point = 1
        temperature_low_limit = 6
        temperature_high_limit = 7
        fault_bits = 8
        actual_temperature = 9
        feedback_P1 = 16
        feedback_I1 = 17
        feedback_D1 = 18
        feedback_P2 = 19
        feedback_I2 = 20
        feedback_D2 = 21
        power = 30
        reset = 31

    current_command = b''
    current_command_length = 0
    current_command_time = 0

    timeout = persistent_property("timeout", inf)

    def replies(self, commands):
        """Process a string of 1-byte and/or 3-byte commands"""
        from time import time

        replies = b""
        try:
            for i in range(0, len(commands)):
                byte = commands[i:i + 1]
                if time() - self.current_command_time > self.timeout:
                    self.current_command = b''
                    self.current_command_length = 0
                    self.current_command_time = 0
                if self.current_command_length == 0:
                    self.current_command_length = self.command_length(byte)
                    self.current_command = b''
                if len(self.current_command) < self.current_command_length:
                    self.current_command += byte
                    self.current_command_time = time()
                if len(self.current_command) >= self.current_command_length:
                    replies += self.reply(self.current_command)
                    self.current_command = b''
                    self.current_command_length = 0
                    self.current_command_time = 0
        except Exception:
            exception(f"Parsing {commands!r}")
            self.current_command = b''
            self.current_command_length = 0
            self.current_command_time = 0
        return replies

    def command_length(self, command_byte):
        """Decide based on the first byte whether this a 1-byte or 3-byte command."""
        return self.data_bytes(command_byte) + 1

    def data_bytes(self, command_byte):
        """The command_byte determined how many data bytes follow."""
        from struct import unpack
        command_code, = unpack("<B", command_byte)
        parameter_code = command_code & 0b00011111
        if command_code & self.bits.write:
            if parameter_code == self.codes.reset:
                data_bytes = 0
            elif parameter_code == self.codes.fault_bits:
                data_bytes = 1
            elif parameter_code == self.codes.power:
                data_bytes = 3
            else:
                data_bytes = 2
        else:
            data_bytes = 0
        return data_bytes

    def reply(self, command):
        from struct import unpack, pack
        from numpy import uint8

        if len(command) > 0:
            command_code, = unpack("<B", command[0:1])
            parameter_code = command_code & 0b00011111

            if command_code & self.bits.write:
                if parameter_code == self.codes.reset:
                    self.reset()
                else:
                    if len(command) >= 3:
                        value_16bit, = unpack("<H", command[1:3])
                        self.set_parameter_value(parameter_code, value_16bit)
                    else:
                        warning(f"{command}: Expecting 3 bytes, got {len(command)}.")
                reply = pack("<B", command_code)
            else:
                if parameter_code == self.codes.fault_bits:
                    reply = pack("<BB", command_code, uint8(self.fault_bits))
                elif parameter_code == self.codes.power:
                    reply = pack("<BBH", command_code, self.power_sign_8bit,
                                 self.power_16bit)
                else:
                    value = self.parameter_value(parameter_code)
                    reply = pack("<BH", command_code, value)
        else:
            reply = b''

        return reply

    def reset(self):
        info("Received 'reset' command")

    @property
    def power_sign_8bit(self):
        # Byte 1 = Mode, Cooling or Heating.
        # If bit 7(MSB) = 0, then the system is cooling.
        # If bit 7 = 1, then the system is heating.
        # Ignore the remaining bits, they are arbitrary.
        # (HEX<80 = cooling, HEX>80 = heating)
        power_sign_8bit = 0x80 if self.power >= 0 else 0
        return power_sign_8bit

    @property
    def power_16bit(self):
        # %TE Power = (61787-(Byte2+256*Byte3))*100/1235
        # power * 100 = (61787 - power_16bit) * 100 / 1235
        # power = (61787 - power_16bit) / 1235
        # power * 1235 = 61787 - power_16bit
        # power_16bit + power * 1235 = 61787
        # power_16bit = 61787 - power * 1235
        power_16bit = uint16(61787 - abs(self.power) * 1235)
        return power_16bit

    @property
    def power(self):
        """Range -1.0 to +1.0"""
        return 0.0

    def set_parameter_value(self, parameter_code, value_16bit):
        value = value_16bit * 0.1

        name = self.parameter_name(parameter_code)
        if name:
            setattr(self, name, value)
            debug(f"Setting parameter {parameter_code} {name!r} to {value!r}")
        else:
            warning(f"Setting parameter {parameter_code} to {value_16bit!r} not implemented")

    def parameter_value(self, parameter_code):
        name = self.parameter_name(parameter_code)
        if name:
            value = getattr(self, name)
            debug(f"Parameter {parameter_code} {name!r} is {value!r}")
        else:
            value = 0
            warning(f"Parameter {parameter_code} not implemented: Returning 0")
        value_16bit = uint16(value * 10)
        return value_16bit

    def parameter_name(self, parameter_code):
        for name in dir(self.codes):
            if getattr(self.codes, name) == parameter_code:
                break
        else:
            name = ""
        return name

    enabled = persistent_property("enabled", True)

    @property
    def actual_temperature(self):
        return self.temperature + random_noise(0.001)

    @property
    def fault_bits(self):
        bits = 0
        return bits

    feedback_P1 = persistent_property("feedback_P1", 9.0)
    feedback_I1 = persistent_property("feedback_I1", 3.2)
    feedback_D1 = persistent_property("feedback_D1", 0.2)
    feedback_P2 = persistent_property("feedback_P2", 5.0)
    feedback_I2 = persistent_property("feedback_I2", 3.5)
    feedback_D2 = persistent_property("feedback_D2", 0.3)

    temperature_low_limit = persistent_property("temperature_low_limit", -4.0)
    temperature_high_limit = persistent_property("temperature_high_limit", 4.0)

    @property
    def temperature(self):
        return self.physics.temperature

    @property
    def temperature_set_point(self):
        return self.physics.set_temperature

    @temperature_set_point.setter
    def temperature_set_point(self, T):
        self.physics.set_temperature = T

    @property
    def enabled(self):
        return self.physics.enabled

    @enabled.setter
    def enabled(self, enabled):
        self.physics.enabled = enabled

    @property
    def physics(self):
        from oasis_chiller_simulator_physics import oasis_chiller_simulator_physics
        return oasis_chiller_simulator_physics


oasis_chiller_simulator = Oasis_Chiller_Simulator()


def random_noise(standard_deviation):
    from numpy.random import normal
    noise = normal(scale=standard_deviation)
    return noise


def uint16(value):
    from numpy import uint16, clip, rint
    return uint16(clip(rint(value), 0, 65535))


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = oasis_chiller_simulator
    print(f"self.temperature_set_point = {self.temperature_set_point}")
    print(f"self.actual_temperature = {self.actual_temperature}")
    print(f"self.enabled = {self.enabled}")
    print(f"")
    print(r"self.replies(b'H') # Read actual temperature")
    print(r"self.replies(b'A') # Read set-point temperature")
    print(f"")
    print("self.running = True")
    print(f"")
    print(r'dev = open("/dev/ttys005","br+")')
    print(r"dev.write(b'H'); dev.flush()")
    print(r'self.replies(b"*IDN?\n")')
    print(r'self.replies(b"*idn?\n")')
