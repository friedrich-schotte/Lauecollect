#!/bin/env python
"""Setup: 
source ~schotte/Software/Test/setup_env.sh
"""
from xppdaq import xppdaq
##from beamline import xppdaq

run_template = "exp=xppj1216:run=%d:smd:dir=/reg/d/ffb/xpp/xppj1216/xtc:live"
Nevents = 20

xppdaq.configure(Nevents)
xppdaq.begin(Nevents)
run_number = xppdaq.runnumber()
xppdaq.wait()
xppdaq.disconnect()

run = run_template % run_number
print("run: %s" % run)


