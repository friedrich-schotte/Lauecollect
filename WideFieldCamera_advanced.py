#!/usr/bin/env python
# Friedrich Schotte, 1 Oct 2014 - 2 Jul 2017
from inspect import getfile
from os.path import dirname
def f(): pass
dir=dirname(getfile(f))
if dir == "": dir = "."
execfile(dir+"/WideFieldCamera.py")
