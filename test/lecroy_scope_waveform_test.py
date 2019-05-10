import sys; sys.path = ["//Femto/C/All Projects/Software/TWAX/Hyun Sun"] + sys.path
from pdb import pm
from lecroy_scope_waveform import read_waveform
import inspect; print inspect.getfile(read_waveform)

filename = "/Data/2014.11/WAXS/HbCN/HbCN1/HbCN1_27_10ms_on_xray.trc"
t,U = read_waveform(filename)
from pylab import *
i = 0
Nplot = 2
plot(t[i:i+Nplot].T,U[i:i+Nplot].T,".",ms=5,mew=0)
grid()
xlabel("t [s]")
ylabel("U [V]")
ylim(-4,4)
show()

