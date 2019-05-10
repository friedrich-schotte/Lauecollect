"""
Instrumentation for LCLS XPP Hutch
Friedrich Schotte, 19 Oct 2010 - 27 Jan 2016
"""
from pdb import pm
from logging import debug,info,warn,error
try: import xppbeamline
except: warn("xppbeamline not available")
from refill import time_to_next_refill
from undulator import undulator
from EPICS_motor import motor # EPICS-controlled motors
from xray_attenuator import xray_attenuator
from timing_system import *
import timing_system as timing
from marccd import marccd
from agilent_scope import agilent_scope
from lecroy_scope import lecroy_scope
from variable_attenuator import variable_attenuator
from ms_shutter import ms_shutter
from temperature_controller import temperature_controller
from sample_illumination import illuminator_on
from xray_safety_shutters import xray_safety_shutters_open,\
     xray_safety_shutters_enabled
from laser_safety_shutter import laser_safety_shutter_open
from CA import PV
from dummy_motor import DummyMotor
from dummy_counter import DummyCounter
from timing_XPP import lxd
from sample_translation import sample_stage # no longer used, but needed by Lauecollect

__version__ = "2.7.2"

# Undulators
U23 = DummyMotor("ID14ds")
U27 = DummyMotor("ID14us")

# Motors in ID14-C optics hutch

# white beam slits (at 28 m) 
Slit1H = DummyMotor("14IDA:Slit1Hsize",readback="14IDA:Slit1Ht2.C")
Slit1V = DummyMotor("14IDA:Slit1Vsize",readback="14IDA:Slit1Vt2.C")

# Vertical deflecting mirror incidence angle in units of mrad
# resolution 0.4 urad (Resolution of indidivual motors 0.2 um, distance 1 m)
mir1Th = DummyMotor("14IDC:mir1Th")
# Horizontal deflecting mirror incidence angle in units of mrad
mir2Th = DummyMotor("14IDC:mir2Th")

# Vertical beamstearing control, piezo DAC voltage (0-10 V)
MirrorV = DummyMotor("14IDA:DAC1_4")
# Horizonal beamstearing angle in units of mrad
MirrorH = DummyMotor("14IDC:mir2Th")

# Motors in ID14-B end station

# Table horizontal pseudo motor.
TableX = motor("14IDB:table1",command="X",readback="EX")
# Table vertical pseudo motor.
TableY = motor("14IDB:table1",command="Y",readback="EY")
# Chopper
ChopX = DummyMotor("14IDB:m1")
ChopY = DummyMotor("14IDB:m2")

# Sample slits (reading only)
sl,sr = motor("XPP:SB2:MMS:06"),motor("XPP:SB2:MMS:05")
su,sd = motor("XPP:SB2:MMS:07"),motor("XPP:SB2:MMS:08")
from slit import gap,center
shg,sho = gap(sl,sr),center(sl,sr)
svg,svo = gap(su,sd),center(su,sd)

# Collimator
CollX = motor("14IDB:m35")
CollY = motor("14IDB:m36")
# Goniometer 
from diffractometer import diffractometer # configurable by DiffractometerPanel.py
# Sample-to-detector distance
DetZ = DummyMotor("14IDB:m3")
# PIN diode in front of CCD detector
DetX = motor("14IDB:m33")
DetY = motor("14IDB:m34",readback_slop=0.030,min_step=0.030)
# readback_slop: otherwise Thorlabs motor gets hung in "Moving" state
# min_step: otherwise Thorlabs motor gets hung in "Moving" state"

# Laser beam attenuator wheel in 14ID-B X-ray hutch
VNFilter = motor("14IDB:m32",readback_slop=0.1,min_step=0.050)
# readback_slop [deg]" otherwise Thorlabs motor gets hung in "Moving" state
# min_step [deg]" otherwise Thorlabs motor gets hung in "Moving" state"
# This filter is mounted such that when the motor is homed (at 0) the
# attuation is minimal (OD 0.04) and increasing to 2.7 when the motor
# moves in positive direction.
# Based on measurements by Hyun Sun Cho and Friedrich Schotte, made 11 Nov 2014
trans = variable_attenuator(VNFilter,motor_range=[10,290],OD_range=[0,2.66])
trans.motor_min=0
trans.OD_min=0
trans.motor_max=300
trans.OD_max=2.66

# Laser transfer line periscope mirrors in laser lab
PeriscopeH = motor("14IDLL:m6")
PeriscopeV = motor("14IDLL:m7")

# Laser focus translation
LaserX = motor("14IDB:m30")
LaserZ = motor("14IDB:m31")

# 6-GHz oscilloscope in ID14-B experiments hutch
id14b_scope = agilent_scope("id14b-scope.cars.aps.anl.gov")

# X-ray diagnostics oscilloscope in ID14-B experiments hutch
xray_scope = lecroy_scope("id14b-xscope.cars.aps.anl.gov",name="xray_scope")
id14b_xscope = xray_scope # for backward compatibility

# ps laser diagnostics oscilloscope in laser hutch
laser_scope = lecroy_scope("id14l-scope.cars.aps.anl.gov",name="laser_scope")
id14l_scope = laser_scope # for backward compatibility

# Diagnostics oscilloscope in ID14-B control hutch
diagnostics_scope = lecroy_scope("id14b-wavesurfer.cars.aps.anl.gov",
    name="diagnostics_scope")
id14b_wavesurfer = diagnostics_scope # for backward compatibility

# Online diagnostics:
#
# Setup required:
# Agilent 6-GHz oscilloscope in X-ray hutch:
# C2 = photodiode, C3 = MCP-PMT, C4 = trigger
# The first measurement needs to be defined as Delta-Time(2,3) with
# rising edge on C2 and falling edge in C3.
# The timing skews of each channel need to be set such the measured
# time delay is 0 when the nominal  time delay is zero.
# The second measurement needs defined as Area(3).
#
# LeCroy oscilloscope in Control Hutch:
# C1 = I0 PIN diode reverse-biased, 50 Ohm, C4 = trigger
#
# LeCroy oscilloscope in Laser Lab:
# The photodiode signal from the X-ray hutch needs to be connected to
# channel 4.
# The first measurement needs to be defined as P1:area(C4) with a gate
# of about 60 ns around the pulse (360 ns delay from the trigger).

actual_delay= id14b_scope.measurement(1)
xray_pulse  = xray_scope.measurement(1)
xray_trace  = xray_scope.channel(1)
laser_pulse = laser_scope.measurement(1)
laser_trace = laser_scope.channel(4)

# X-ray area detector
try:
    from rayonix_detector_XPP import rayonix_detector
    ccd = rayonix_detector()
    ccd.auto_bkg = False # automatically acquire a background image as needed
except: warn("module 'rayonix_detector_XPP' not available")

# 14-ID Laser Lab

VNFilter1 = motor("14IDLL:m8",readback_slop=0.030,min_step=0.030)
# readback_slop: otherwise Thorlabs motor gets hung in "Moving" state
# min_step: otherwise Thorlabs motor gets hung in "Moving" state"
# This filter is mounted such that when the motor is homed (at 0) the
# attuation is minimal (OD 0.04) and increasing to 2.7 when the motor
# moves in positive direction.
trans1 = variable_attenuator(VNFilter1,motor_range=[15,295],OD_range=[0,2.66])
trans1.motor_min=0
trans1.OD_min=0
trans1.motor_max=315
trans1.OD_max=2.66

# Fast NIH Diffractometer, Aerotech "Ensemble" controller, F. Schotte, 30 Jan 2013 
from Ensemble import SampleX,SampleY,SampleZ,SamplePhi
from Ensemble_triggered_motion import triggered_motion
from Ensemble import ensemble_motors
from Ensemble_SAXS_pp import Ensemble_SAXS
# NIH Peristalitc pump, F. Schotte Nov 12, 2014
from peristaltic_pump import PumpA,PumpB,peristaltic_pump

# Dummy for compatibility of XPP
class xray_detector_trigger(object):
    class count(object):
        value = 0


