#!/usr/bin/env python
"""
Generate a log of an EPICS Process Variable, printing its value every time it
changes, including a time stamp.

Author: Friedrich Schotte
Date created: 2020-04-19
Date last modified: 2020-05-06
Revision comment:  Added documentation
"""
__version__ = "1.0.1"

from CA import camonitor
from sys import argv, stderr
if not len(argv) > 1: 
    stderr.write("usage %s PV [PV ...]\n" % argv[0])
    exit(1)
for PV in argv[1:]:
    camonitor(PV)

from time import sleep
while True:
    try: sleep(1)
    except KeyboardInterrupt: break
