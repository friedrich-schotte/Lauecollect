"""
Friedrich Schotte, NIH, 3 Feb 2012 - 9 Mar 2012
"""
from lecroy_scope import lecroy_scope
from lecroy_scope_waveform import read_waveform
from time import sleep
from pylab import *
__version__ = "1.1"

id14b_xscope = lecroy_scope("164.54.161.27") # id14b-xscope
xray_trace = id14b_xscope.channel(1)
dir = "/net/id14bxf/data/anfinrud_1203/Test/I0"
filename = dir+"/test1.trc"

print 'xray_trace.acquire_sequence(100)'
print 'xray_trace.is_acquiring'
print 'xray_trace.save_waveform(filename)'
print 't,U = read_waveform(filename)'
print 'plot(t[0:5].T,U[0:5].T,".",ms=5,mew=0); grid(); show()'
