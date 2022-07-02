#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-10-03
Date last modified: 2021-10-03
Revision comment:
"""
__version__ = "1.0.0"

import os

if os.name == 'nt':
    from serial_port_emulator_windows import serial_port_emulator, emulated_port_names
else:
    from serial_port_emulator_posix import serial_port_emulator, emulated_port_names

if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    print("port = serial_port_emulator()")
    print("emulated_port_names()")
