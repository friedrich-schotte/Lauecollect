#!/bin/env python
from psana import *
from time import time

##run = "exp=xpptut15:run=240:smd"
run = "exp=xppj1216:run=9:smd:dir=/reg/d/ffb/xpp/xppj1216/xtc:live"

start = time()
ds = DataSource(run)
det = Detector('rayonix',ds.env())
src = Source('rayonix')
for nevent,evt in enumerate(ds.events()):
    print nevent
    ##img = det.raw(evt)
    raw = evt.get(Camera.FrameV1,src)
    if raw is  None: continue
    img = raw.data16()
print img.shape
print nevent/(time()-start),"Hz"

import matplotlib.pyplot as plt
##plt.imshow(img,vmin=-2,vmax=2)
##plt.show()
