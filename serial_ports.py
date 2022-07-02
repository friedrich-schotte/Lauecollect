"""
Author: Friedrich Schotte
Date created: 2021-04-07
Date last modified: 2021-10-03
Revision comment: Make sure emulated ports come first
"""
__version__ = "1.0.2"


def serial_ports():
    """list of serial device names"""
    from platform import system
    from serial.tools.list_ports import comports
    if system() == 'Darwin':
        prefix = 'cu.usbserial'
    elif system() == 'Windows':
        prefix = 'COM'
    elif system() == 'Linux':
        prefix = '/dev/ttyUSB'
    else:
        prefix = ''
    ports = [port.device for port in comports() if prefix in port.device]

    from serial_port_emulator import emulated_port_names
    emulated_ports = emulated_port_names()
    for emulated_port in emulated_ports:
        if emulated_port in ports:
            ports.remove(emulated_port)
    ports = emulated_ports + ports

    return ports


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=msg_format)

    print('serial_ports()')