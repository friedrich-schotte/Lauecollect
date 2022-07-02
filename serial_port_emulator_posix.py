#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-03-29
Date last modified: 2021-05-17
Revision comment: Fixed: Issue: "*IDN?" in MacOS Terminal window
    Added: More stringent criteria for "is_emulated"
"""
__version__ = "1.0.1"

from logging import info


class term:
    """Indices of tty attributes return by termios.tcgetattr"""
    iflag = 0
    oflag = 1
    cflag = 2
    lflag = 3
    ispeed = 4
    ospeed = 5
    cc = 6


class serial_port_emulator:
    def __init__(self):
        import pty
        import termios

        self.master_fd, self.slave_fd = pty.openpty()
        info(f"Listening on {self.name}...")

        # Get current pty attributes.
        termAttr = termios.tcgetattr(self.master_fd)
        # Disable canonical and echo modes.
        termAttr[term.lflag] &= ~termios.ICANON
        termAttr[term.lflag] &= ~termios.ISIG
        termAttr[term.lflag] &= ~termios.ECHO
        termAttr[term.lflag] &= ~termios.ECHOE
        termAttr[term.lflag] &= ~termios.ECHOKE
        termAttr[term.lflag] &= ~termios.ECHOCTL
        # Disable newline / carriage return conversion.
        termAttr[term.iflag] &= ~termios.INLCR
        termAttr[term.oflag] &= ~termios.OPOST
        termAttr[term.oflag] &= ~termios.ONLCR
        # Disable interrupt, quit, and suspend character processing.
        termAttr[term.cc][termios.VINTR] = b'\0'
        termAttr[term.cc][termios.VQUIT] = b'\0'
        termAttr[term.cc][termios.VSUSP] = b'\0'
        # Set revised pty attributes immediately.
        termios.tcsetattr(self.master_fd, termios.TCSANOW, termAttr)

    def read(self):
        from os import read
        return read(self.master_fd, 1024)

    def write(self, reply):
        from os import write
        write(self.master_fd, reply)

    @property
    def name(self):
        import os
        return os.ttyname(self.slave_fd)


def emulated_port_names():
    from platform import system
    from glob import glob

    if system() == 'Darwin':
        tty_names = glob("/dev/ttys???")
    elif system() == 'Linux':
        tty_names = glob("/dev/pts/*")
    else:
        tty_names = []
    names = [tty_name for tty_name in tty_names if is_emulated(tty_name)]
    return names


def is_emulated(tty_name):
    import os
    import termios
    try:
        fd = os.open(tty_name, os.O_RDONLY | os.O_NONBLOCK)
    except OSError:
        is_emulated = False
    else:
        termAttr = termios.tcgetattr(fd)
        os.close(fd)
        # Check if postprocessing is disabled
        criteria = [
            termAttr[term.lflag] & termios.ICANON == 0,
            termAttr[term.lflag] & termios.ISIG == 0,
            termAttr[term.lflag] & termios.ECHO == 0,
            termAttr[term.lflag] & termios.ECHOE == 0,
            termAttr[term.lflag] & termios.ECHOKE == 0,
            termAttr[term.lflag] & termios.ECHOCTL == 0,
            termAttr[term.iflag] & termios.INLCR == 0,
            termAttr[term.oflag] & termios.OPOST == 0,
            termAttr[term.oflag] & termios.ONLCR == 0,
            termAttr[term.cc][termios.VINTR] == b'\0',
            termAttr[term.cc][termios.VQUIT] == b'\0',
            termAttr[term.cc][termios.VSUSP] == b'\0',
        ]
        is_emulated = all(criteria)
    return is_emulated


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    print("port = serial_port_emulator()")
    print("emulated_port_names()")
