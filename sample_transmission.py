"""
Measure the transmission of te WAXS/SAXS sample cell over the translation range
used for scattering data collection.
Setup: DS PIN diode, mounted on detector support, 2 mm Al attenuator taped in front
(to avoid saturating the response). DS PIN diode -> Mini-Circuits bias Tee, 9 V bias ->
WaveSurfer oscilloscope in control Hutch CH2.

Friedrich Schotte, 10 Oct 2010
"""
from id14 import id14b_wavesurfer,GonY,mson
import lauecollect_advanced as lauecollect
from numpy import *

I0 = id14b_wavesurfer.measurement(1)
DS_PIN = id14b_wavesurfer.measurement(2)

def measure_T():
    print "offset..."
    mson.value = 0 # disable X-ray beam
    lauecollect.single_image()
    I0_offset,DS_PIN_offset = I0.average,DS_PIN.average
    mson.value = 1 # reenable X-ray beam
    print "reference..."
    GonY.value = 4.096-1; GonY.wait() # bypassing sample cell
    lauecollect.single_image()
    I00,DS_PIN0 = I0.average,DS_PIN.average
    print "sample..."
    GonY.value = 4.096; GonY.wait() # X-ray beam through sample cell
    lauecollect.single_image()
    I01,DS_PIN1 = I0.average,DS_PIN.average

    T = ((DS_PIN1-DS_PIN_offset)/(I01-I0_offset)) / ((DS_PIN0-DS_PIN_offset)/(I01-I0_offset))
    print "transmission %.4f" % T
    return T

def average_T():
    global N,T
    N = 5
    T = zeros(N)
    for i in range(0,N): T[i] = measure_T()

    print "T = %.4f+/-%.4f" % (average(T),std(T)/sqrt(N-1))

# helium purged capillary: T = 0.9076+/-0.0023
# water filled capillary: T = 0.7841+/-0.0012
