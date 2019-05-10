"""
Run on "mond" node "daq-xpp-mon05.pcdsn" or "daq-xpp-mon06.pcdsn".
Only one instance can run per node.

Setup:
ssh daq-xpp-mon06.pcdsn
source /reg/g/psdm/etc/ana_env.sh
mpirun -n 4 python daq_image_mpi_test.py 

DAQ Control - (uncheck) Record Run - Begin Running

Chris O'Grady, Jan 22, 2016
"""
from psana import *
from numpy import *
from logging import info,warn,debug

ds = DataSource('shmem=XPP.0:stop=no')
src = Source('rayonix')

from mpi4py import MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

fiducials = []
for nevent,evt in enumerate(ds.events()):
    if nevent%size==rank:  # different ranks look at different events
        raw = evt.get(Camera.FrameV1,src)
        if raw is None: continue
        fiducials.append(evt.get(EventId).fiducials())
        if nevent == 100: break

all_fiducials = comm.gather(fiducials) # from all ranks
if rank==0:
    all_fiducials = sort(concatenate((all_fiducials[:]))) # put in one long list
    print all_fiducials

MPI.Finalize()
