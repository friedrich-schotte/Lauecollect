#!/usr/bin/env python
"""
Report the values of a EPICS Process Variables

Author: Friedrich Schotte
Date created: 2020-05-06
Date last modified: 2020-05-06
Revision comment: 
"""
__version__ = "1.0"

from CA import caget
from sys import argv, stderr
if not len(argv) > 1: 
    stderr.write("usage %s PV [PV ...]\n" % argv[0])
    exit(1)
for PV in argv[1:]:
    print("%s: %r" % (PV,caget(PV)))
