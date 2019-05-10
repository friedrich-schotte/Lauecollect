"""
Friedrich Schotte, NIH, 3 Feb 2012 - 6 Feb 2012
"""
from lecroy_scope import lecroy_scope
from lecroy_scope_waveform import read_waveform
from time import sleep
from pylab import *

scope = lecroy_scope("pico9.niddk.nih.gov")
dir = "//Femto/C/All Projects/APS/Instrumentation/Software/Software/test"
filename = dir+"/test1.trc"

print 'scope.sampling_mode = "Sequence"'
print 'scope.nsegments = 1100'
print 'scope.trigger_mode = "Stop"'
print 'scope.clear_sweeps()'
print 'scope.trigger_mode = "Single"'
print 'while scope.trigger_mode == "Single": sleep(0.1)'
print 'scope.save_waveform(1,filename)'
print 't,U = read_waveform(filename)'
print 'plot(t[0:5].T,U[0:5].T,".",ms=5,mew=0); grid(); show()'
