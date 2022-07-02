#!/usr/bin/env python
"""
Setup:
- Install the software package 'com0com' from https://sourceforge.net/projects/com0com
- Run: Start > Programs > com0com > Setup
- Create pairs of emulated com ports: COM3 & COM4, COM5 & COM6, ....

Author: Friedrich Schotte
Date created: 2021-10-03
Date last modified: 2021-10-03
Revision comment: First port of pair my be even or odd numbered
"""
__version__ = "1.0.1"

import logging


class serial_port_emulator:
    _port = None
    messages = []

    @property
    def port(self):
        self.connect()
        return self._port

    def connect(self):
        from serial import Serial
        if self._port is None:
            port_names = emulator_port_names()
            if not port_names:
                self.error("Please install 'com0com' from https://sourceforge.net/projects/com0com.")
            else:
                for port_name in port_names:
                    try:
                        self._port = Serial(port_name)
                        break
                    except OSError:
                        pass
                if self._port:
                    logging.info(f"Using port pair {self.name} <-> {self.paired_name}")
                else:
                    self.error(f"All available emulated serial port in use {port_names}.")
                    self.error(f"Use Programs > com0com > Setup to add more.")

    def error(self, message):
        if message not in self.messages:
            logging.error(message)
            self.messages.append(message)

    def read(self):
        if self.port:
            data = self.port.read(1)
            n_bytes = self.port.in_waiting
            if n_bytes:
                data += self.port.read(n_bytes)
        else:
            data = b''
        return data

    def write(self, data):
        if self.port:
            self.port.write(data)

    @property
    def name(self):
        if self._port:
            name = self._port.name
        else:
            name = ""
        return name

    @property
    def paired_name(self):
        if self._port:
            name = emulated_port_name(self._port.name)
        else:
            name = ""
        return name


def check_available_ports():
    import serial.tools.list_ports
    lst = serial.tools.list_ports.comports()
    for element in lst:
        print(element.device,element.description)


def emulated_port_name_pairs():
    port_names = all_emulated_port_names()
    n_pairs = len(port_names) // 2
    port_names = port_names[0:n_pairs*2]
    pairs = list(zip(port_names[0::2], port_names[1::2]))
    return pairs


def emulator_port_names():
    """Ports available for the instrument simulator: COM3, COM5, ..."""
    names = [pair[0] for pair in emulated_port_name_pairs()]
    return names


def emulated_port_names():
    """Ports available for the user of an simulated instrument: COM4, COM6, ..."""
    names = [pair[1] for pair in emulated_port_name_pairs()]
    return names


def emulated_port_name(emulator_port_name):
    """COM3 -> COM4, COM5 -> COM6"""
    name = ""
    for pair in emulated_port_name_pairs():
        if emulator_port_name == pair[0]:
            name = pair[1]
    return name


def all_emulated_port_names():
    from serial.tools.list_ports import comports
    keyword = "serial port emulator"
    names = sorted([port.device for port in comports() if keyword in port.description])
    return names


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    self = serial_port_emulator()
    print("emulated_port_names()")
    print("self.read()")
