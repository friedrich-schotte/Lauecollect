#!/bin/env python
"""Setup: 
source ~schotte/Software/Test/setup_env.sh
"""
from xppdaq import xppdaq
from time import time
from logging import info,warn,debug

run_template = "exp=xppj1216:run=%d:smd:dir=/reg/d/ffb/xpp/xppj1216/xtc:live"
Nimages = 20
Nevents = Nimages*12

xppdaq.configure(Nevents)
xppdaq.begin(Nevents)
run_number = xppdaq.runnumber()
xppdaq.wait()
xppdaq.disconnect()
run = run_template % run_number
print("acqired run: %s" % run)

from datastream import datastream
start = time()
image_id = "%s:%d" % (run,0)
print("getting image %r" % image_id)
img = datastream.image(image_id)
while img is None: datastream.image(image_id)
print("%s\n%s"%(img.shape,img[0:2,0:2]))
print("waited for %.1f s to get first image." % ((time()-start)))

