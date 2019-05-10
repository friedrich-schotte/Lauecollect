#!/usr/bin/env python
# Friedrich Schotte, Mar 2, 2016-Mar 2, 2016
from inspect import getfile
from os.path import dirname
dir=dirname(getfile(lambda x:None))
if dir == "": dir = "."
execfile(dir+"/EnsembleSAXS_PP_Panel.py")
