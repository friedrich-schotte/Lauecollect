"""Friedrich Schotte, 27 Jun 2012 - 9 Nov 2012"""
from pdb import pm
from numpy import *
import lauecollect_new as lauecollect
##from interpolate_2D import interpolate_2D
from lauecollect_new import interpolate_2D
from matplotlib.mlab import griddata
from pylab import *

lauecollect.param.path = "//id14bxf/data/anfinrud_1211/Data/Laue/PYP-E46Q-H/PYP-E46Q-H46.1-288K"
phi = 0

PHI,Z,X,Y,OFFSET = array(lauecollect.align_table())[0:5]

phi1,phi2 = unique(PHI)[0:2]
nsteps_phi = 5
phis = arange(phi1,phi2+1e-6,(phi2-phi1)/(nsteps_phi-1))
nsteps_z = 22
z1,z2 = min(Z),max(Z)
zs = arange(z1,z2+1e-6,(z2-z1)/(nsteps_z-1))
phis2d,zs2d = meshgrid(phis,zs)

##offsets2d = griddata(PHI,Z,OFFSET,phis2d,zs2d)
offsets2d = array([[interpolate_2D(PHI,Z,OFFSET,phi,z) for phi in phis]
                   for z in zs])

figure(figsize=(8.5,11))
subplot(211)
plot(zs2d,offsets2d)
xlabel("GonZ[mm]"); ylabel("offset[mm]")
legend(["%.3f deg" % x for x in phis])
grid()

subplot(212)
imshow(offsets2d,cmap=cm.jet,interpolation="nearest")
colorbar()
xticks(xticks()[0],["%.3f" % x for x in phis],rotation=90)
yticks(yticks()[0],["%.3f" % y for y in zs])
xlabel("Phi[deg]"); ylabel("GonZ[mm]")

show()
