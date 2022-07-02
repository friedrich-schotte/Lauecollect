#!/usr/bin/env python
"""ILX Lightwave LDT-5948 Precision Temperature Controller

Communication Parameters: 115200 baud, 8 data bits, 1 stop bit, parity: none
flow control: none
2 = TxD, 3 = RxD, 5 = Gnd (DCE = Data Circuit-terminating Equipment)
9600 baud is the factory setting, but can be changed from the front panel:
MAIN/LOCAL - COMMUNICATION 1/7 - down - RS323 Baud
Possible baud rates are: 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200,
and 230400.

The controller accepts ASCII text commands. Each command needs to by terminated
with a newline or carriage return character.
Replies are terminated with carriage return and newline.
Command that are not queries generate the reply "Ready".
If a query is not understood, the controller replies with "Ready" as well.

Commands:
*IDN? identification, expecting: "ILX Lightwave,LDT-5948,59481287,01.02.06"
MEASure:Temp? - Report the actual temperature.
SET:Temp?     - Report the temperature set point.
SET:Temp 37.0 - Change temperature set point to 37 degrees C.
MEASure:PTE?  - Read heater power in W
OUTPUT?       - Serve loop enabled? 0 or 1
OUTPUT 1      - Enable servo loop
OUTPUT 0      - Disable servo loop

Author: Friedrich Schotte
Date created: 2021-03-24
Date last modified: 2021-10-05
Revision comment: Simulating temperature dynamics
"""
__version__ = "1.1"

from logging import debug, warning, exception


def run():
    lightwave_temperature_controller_simulator.run()


class Lightwave_Temperature_Controller_Simulator:
    from persistent_property import persistent_property
    from thread_property_2 import thread_property

    def __init__(self):
        self.processing_commands = False
        self.updating_temperature = False
        self.IOC_online = False

    def run(self):
        self.running = True
        wait()
        self.running = False

    @property
    def running(self):
        return all([
            self.processing_commands,
            self.updating_temperature,
            self.IOC_online,
        ])

    @running.setter
    def running(self, running):
        self.processing_commands = running
        self.updating_temperature = running
        self.IOC_online = running

    @thread_property
    def processing_commands(self):
        from thread_property_2 import cancelled
        from serial_port_emulator import serial_port_emulator

        self.port = serial_port_emulator()

        while not cancelled():
            command = self.port.read()
            debug(f"Received {command}")
            replies = self.replies(command)
            debug(f"Replying {replies}")
            self.port.write(replies)

    @property
    def IOC_online(self):
        from CAServer import casget
        return casget(self.PV_name) is not None

    @IOC_online.setter
    def IOC_online(self, IOC_online):
        from CAServer import casput, casdel
        if IOC_online:
            casput(self.PV_name, 1)
        else:
            casdel(self.PV_name)

    PV_name = "NIH:LIGHTWAVE_SIM.ONLINE"

    port = None

    partial_command = b""

    def replies(self, commands):
        replies = b""

        try:
            commands = commands.replace(b"\r\n", b"\n")
            commands = commands.replace(b"\n\r", b"\n")
            commands = commands.replace(b"\r", b"\n")

            commands = commands.split(b"\n")
            if commands:
                commands[0] = self.partial_command + commands[0]
                commands, self.partial_command = commands[0:-1], commands[-1]

            for command in commands:
                command = command.strip()
                if command:
                    replies += self.replies2(command) + b"\r\n"
        except Exception:
            exception(f"Parsing {commands!r}")
            self.partial_command = b""
        return replies

    def replies2(self, commands):
        """Process multiple commands, separated by semicolon (;)"""
        replies = []
        for command in commands.split(b";"):
            command = command.strip()
            if command:
                replies.append(self.reply(command))
        reply = b"; ".join(replies)
        return reply

    ID_string = b"ILX Lightwave,LDT-5948,59481287,01.02.06"

    def reply(self, command):
        command = command.strip(b"\r\n ")
        command = command.upper()

        if command.endswith(b"?"):
            query = command.strip(b"?")
            if matches(query, b"*IDN"):
                reply = self.ID_string
            elif matches(query, b"MEASURE:TEMP"):
                reply = b"%r" % (self.read_temperature,)
            elif matches(query, b"SET:TEMP"):
                reply = b"%r" % (self.set_temperature,)
            elif matches(query, b"OUTPUT"):
                reply = b"%r" % (int(self.enabled),)
            elif matches(query, b"MEASURE:PTE"):
                reply = b"%r" % (self.power,)
            elif matches(query, b"MEASURE:VTE"):
                reply = b"%r" % (self.voltage,)
            elif matches(query, b"MEASURE:ITE"):
                reply = b"%r" % (self.current,)
            elif matches(query, b"PID"):
                reply = b"%r, %r, %r" % (self.feedback_P, self.feedback_I, self.feedback_D)
            elif matches(query, b"LIMIT:ITE:HIGH"):
                reply = b"%r" % (self.current_high_limit,)
            elif matches(query, b"LIMIT:ITE:LOW"):
                reply = b"%r" % (self.current_low_limit,)
            elif matches(query, b"TRIGGER:IN:ENABlE"):
                reply = b"%r" % (int(self.trigger_enabled),)
            elif matches(query, b"TRIGGER:IN:START"):
                reply = b"%r" % (self.trigger_start,)
            elif matches(query, b"TRIGGER:IN:STOP"):
                reply = b"%r" % (self.trigger_stop,)
            elif matches(query, b"TRIGGER:IN:STEPSIZE"):
                reply = b"%r" % (self.trigger_stepsize,)
            else:
                warning(f"{command}: Not understood")
                reply = b"Ready"
        else:
            if b" " in command:
                command, parameter = command.split(b" ", 1)
                try:
                    value = eval(parameter)
                except Exception as x:
                    warning(f"{command}: {parameter}: {x}")
                    value = None
            else:
                value = None
            if matches(command, b"SET:TEMP"):
                self.set_temperature = value
            elif matches(command, b"OUTPUT"):
                self.enabled = value
            elif matches(command, b"PID"):
                self.feedback_P, self.feedback_I, self.feedback_D = value
            else:
                warning(f"{command}: Not understood")
            reply = b"Ready"

        return reply

    set_temperature = persistent_property("set_temperature", 20.0)
    enabled = persistent_property("enabled", False)

    @property
    def read_temperature(self):
        return self.temperature + random_noise(0.001)

    @thread_property
    def updating_temperature(self):
        from thread_property_2 import cancelled
        from time import time, sleep

        self.time = time()
        while not cancelled():
            self.update_temperature()
            sleep(0.25)

    def update_temperature(self):
        from time import time
        from numpy import exp

        t = time()
        t0 = self.time
        T0 = self.temperature
        T_target = self.set_temperature if self.enabled else self.heat_sink_temperature
        dt = t - t0
        dT0 = T0 - T_target
        dT = dT0 * exp(-dt / self.tau)
        T = T_target + dT
        self.time = t
        self.temperature = T

    time = 0
    temperature = 20.0
    heat_sink_temperature = 20.0
    tau = 4.0  # heat dissipation time constant [in seconds]

    @property
    def power(self):
        power = abs(self.voltage * self.current)
        return power

    @property
    def voltage(self):
        if self.enabled:
            V = 0.5 + random_noise(0.01)
        else:
            V = 0.0
        return V

    @property
    def current(self):
        if self.enabled:
            current = 0.25 + random_noise(0.01)
        else:
            current = 0.0
        return current

    feedback_P = persistent_property("feedback_P", 0.75)
    feedback_I = persistent_property("feedback_I", 0.3)
    feedback_D = persistent_property("feedback_D", 0.3)

    current_low_limit = persistent_property("current_low_limit", -4.0)
    current_high_limit = persistent_property("current_high_limit", 4.0)

    trigger_enabled = persistent_property("trigger_enabled", False)
    trigger_start = persistent_property("trigger_start", 20.0)
    trigger_stop = persistent_property("trigger_stop", 30.0)
    trigger_stepsize = persistent_property("trigger_stepsize", 0.01)


lightwave_temperature_controller_simulator = Lightwave_Temperature_Controller_Simulator()


def matches(short_name, full_name):
    """e.g. short name 'LIM:T:HI' matches full name 'LIMIT:TEMP:HIGH'"""
    short_words = short_name.split(b":")
    full_words = full_name.split(b":")
    if len(short_words) != len(full_words):
        matches = False
    else:
        matches = all([
            word_matches(short_word, full_word)
            for short_word, full_word in zip(short_words, full_words)
        ])
    return matches


def word_matches(short_name, full_name):
    """e.g. short name 'MEAS' matches full name 'MEASURE'"""
    return full_name.upper().find(short_name.upper()) == 0


def random_noise(standard_deviation):
    from numpy.random import normal
    noise = normal(scale=standard_deviation)
    return noise


def wait():
    from time import sleep
    try:
        while True:
            sleep(0.25)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = lightwave_temperature_controller_simulator
    print(f"self.set_temperature = {self.set_temperature}")
    print(f"self.read_temperature = {self.read_temperature}")
    print(f"self.enabled = {self.enabled}")
    print(r'self.replies(b"*IDN?\n\r")')
    print(r'self.replies(b"MEASure:Temp?\n\r")')
    print(r'self.replies(b"SET:Temp?\n\r")')
    print(r'self.replies(b"SET:Temp 22.0\n\r")')
    print(r'self.replies(b"MEASure:PTE?\n\r")')
    print(r'self.replies(b"OUTPUT?\n\r")')
    print(r'self.replies(b"OUTPUT 1\n\r")')
    print(r'self.replies(b"OUTPUT 0\n\r")')
    print("self.running = True")
    print(r'dev = open("/dev/ttys005","br+")')
    print(r"dev.write(b'*IDN?\n\r'); dev.flush()")
