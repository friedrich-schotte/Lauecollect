from psana import *
ds = DataSource('exp=xpptut15:run=240')
det = Detector('rayonix',ds.env())
for nevent,evt in enumerate(ds.events()):
    img = det.raw_data(evt)
    break

import matplotlib.pyplot as plt
plt.imshow(img,vmin=-2,vmax=2)
plt.show()
