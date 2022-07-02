#!/usr/bin/env python
"""
Change the value of an EPICS Process Variable via Channel Access protocol
Author: Friedrich Schotte
Date created: 2020-05-06
Date last modified: 2020-05-06
"""
__version__ = "1.0"

from CA import caput
from sys import argv, stderr
if not len(argv) == 3: 
    stderr.write("usage %s PV value\n" % argv[0])
    exit(1)
PV = argv[1]
value = argv[2]
try: value = eval(value)
except: pass
caput(PV,value)
