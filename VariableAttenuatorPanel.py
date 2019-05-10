#!/usr/bin/env python
# Friedrich Schotte, 16 Nov 2014
from inspect import getfile
from os.path import dirname
def f(): pass
dir=dirname(getfile(f))
execfile(dir+"/LaserAttenuatorLaserXrayHutch.py")
