"""
Instrumentation of the 14-ID beamline
Author: Friedrich Schotte
Date created: 2007-12-08
Data last modified: 2019-05-22
"""
__version__ = "3.6" # temperature

from pdb import pm
from refill import time_to_next_refill
from undulator import undulator
from EPICS_motor import motor # EPICS-controlled motors
from xray_attenuator import xray_attenuator
from timing_system import timing_system
from timing_sequencer import timing_sequencer
from Ensemble_SAXS import Ensemble_SAXS,Sequence,Sequences
from agilent_scope import agilent_scope
from lecroy_scope import lecroy_scope
from variable_attenuator import variable_attenuator
from ms_shutter import ms_shutter
# Had to comment this out because the id14b20 computer could not load it???? RH
from oasis_chiller import chiller
from temperature import temperature
from omega_thermocouple import thermocouple
from sample_translation import sample_stage
from syringe_pump import syringe_pump
from sample_illumination import illuminator_on
from xray_safety_shutters import xray_safety_shutters_open,\
     xray_safety_shutters_enabled, xray_safety_shutters_auto_open
from laser_safety_shutter import laser_safety_shutter_open,\
     laser_safety_shutter_auto_open
from LokToClock import LokToClock
from CA import PV,caget
from combination_motor import tilt
from GigE_camera_client import Camera
from cavro_centris_syringe_pump_IOC import volume,port
from sample_frozen import sample_frozen
from freeze_intervention import freeze_intervention
from configuration import configuration,configurations,config,configs
from collect import collect
from diagnostics import diagnostics

# Machine
ring_current = PV("S:SRcurrentAI.VAL")
bunch_current = PV("BNCHI:BunchCurrentAI.VAL")

# Undulators
U23 = undulator("ID14ds")
U27 = undulator("ID14us")

# Motors in ID14-C optics hutch

# white beam slits (at 28 m) 
Slit1H = motor("14IDA:Slit1Hsize",name="Slit1H",readback="14IDA:Slit1Ht2.C",readback_slop=0.002)
Slit1V = motor("14IDA:Slit1Vsize",name="Slit1V",readback="14IDA:Slit1Vt2.C",readback_slop=0.002)

# Heat-load chopper
HLC = motor("14IDA:m5",name="HLC")

# Vertical deflecting mirror incidence angle in units of mrad
# resolution 0.4 urad (Resolution of indidivual motors 0.2 um, distance 1 m)
mir1Th = motor("14IDC:mir1Th",name="mir1Th")
# Vertical beamstearing control, piezo DAC voltage (0-10 V)
MirrorV = motor("14IDA:DAC1_4",name="MirrorV",readback="VAL")
mir1bender = motor("14IDC:m6",name="mir1bender") 

# Horizontal deflecting mirror incidence angle in units of mrad
##mir2Th = motor("14IDC:mir2Th") # unreliable, tends to hang
# Mirror individual jacks (distance 1.045 m)
mir2X1 = motor("14IDC:m12",name="mir2X1") # H mirror X1-upstream
mir2X2 = motor("14IDC:m13",name="mir2X2") # H mirror X1-downstream 
mir2Th = tilt(mir2X1,mir2X2,distance=1.045,name="mir2Th",unit="mrad")
MirrorH = mir2Th
mir2bender = motor("14IDC:m14",name="mir2bender") 

# Motors in ID14-B end station

# Table horizontal pseudo motor.
TableX = motor("14IDB:table1",name="TableX",command="X",readback="EX")
# Table vertical pseudo motor.
TableY = motor("14IDB:table1",name="TableY",command="Y",readback="EY")

# JJ1 slits (upstream)
s1vg = motor("14IDC:m37",name="s1vg") # JJ1 y aperture (vertical gap)
s1vo = motor("14IDC:m38",name="s1vo") # JJ1 y translation
s1hg = motor("14IDC:m39",name="s1hg") # JJ1 x aperture (horizontal gap)
s1ho = motor("14IDC:m40",name="s1ho") # JJ1 x translation

# High-speed X-ray Chopper
ChopX = motor("14IDB:m1",name="ChopX")
ChopY = motor("14IDB:m2",name="ChopY")

# JJ2 slits (downstream)
shg = motor("14IDB:m25",name="shg") # JJ2 x aperture (horizontal gap)
sho = motor("14IDB:m26",name="sho") # JJ2 x offset
svg = motor("14IDB:m27",name="svg") # JJ2 y aperture (vertical gap)
svo = motor("14IDB:m28",name="svo") # JJ2 y offset

# KB mirror
KB_Vpitch     = motor("14IDC:pm4",name="KB_Vpitch") 
KB_Vheight    = motor("14IDC:pm3",name="KB_Vheight") 
KB_Vcurvature = motor("14IDC:pm1",name="KB_Vcurvature")
KB_Vstripe    = motor("14IDC:m15",name="KB_Vstripe") # Rob Henning 2018-10-04
KB_Hpitch     = motor("14IDC:pm8",name="KB_Hpitch") 
KB_Hheight    = motor("14IDC:pm7",name="KB_Hheight") 
KB_Hcurvature = motor("14IDC:pm5",name="KB_Hcurvature")
KB_Hstripe    = motor("14IDC:m44",name="KB_Hstripe") # Rob Henning 2018-10-04

# Collimator
CollX = motor("14IDB:m35",name="CollX")
CollY = motor("14IDB:m36",name="CollY")
# Goniometer 
from diffractometer import diffractometer # configurable by DiffractometerPanel.py
# Goniometer rotation
Phi = motor("14IDB:m151",name="Phi")
# Goniometer translations
GonX = motor("14IDB:m152",name="GonX")
GonY = motor("14IDB:m153",name="GonY")
GonZ = motor("14IDB:m150",name="GonZ")
# Sample-to-detector distance
DetZ = motor("14IDB:m3",name="DetZ")
# PIN diode in front of CCD detector
DetX = motor("14IDB:m33",name="DetX")
DetY = motor("14IDB:m34",name="DetY",readback_slop=0.030,min_step=0.030)
# readback_slop: otherwise Thorlabs motor gets hung in "Moving" state
# min_step: otherwise Thorlabs motor gets hung in "Moving" state"

# Channel cut scan photon "Energy" pseudo-motor (moves Phi aind DetY)
E = motor('14IDB:Energy_CC',name="E")
Energy = E

# Laser transfer line periscope mirrors in laser lab
PeriscopeH = motor("14IDLL:m6",name="PeriscopeH")
PeriscopeV = motor("14IDLL:m7",name="PeriscopeV")

# Laser focus translation
LaserX = motor("14IDB:m30",name="LaserX")
LaserY = motor("14IDB:m42",name="LaserY")
LaserZ = motor("14IDB:m31",name="LaserZ")

# 6-GHz oscilloscope in ID14-B experiments hutch
id14b_scope = agilent_scope("id14b-scope.cars.aps.anl.gov")

# X-ray diagnostics oscilloscope in ID14-B experiments hutch
xray_scope = lecroy_scope(name='xray_scope',
    default_ip_address_and_port='id14b-xscope.cars.aps.anl.gov:2000')
id14b_xscope = xray_scope # for backward compatibility
xscope = xray_scope # shortcut

# ps laser diagnostics oscilloscope in laser hutch
laser_scope = lecroy_scope(name='laser_scope',
    default_ip_address_and_port='id14l-scope.cars.aps.anl.gov:2000')
id14l_scope = laser_scope # for backward compatibility
lscope = laser_scope # shortcut

# Diagnostics oscilloscope in ID14-B control hutch
diagnostics_scope = lecroy_scope(name='diagnostics_scope',
    default_ip_address_and_port='id14b-wavesurfer.cars.aps.anl.gov:2000')
id14b_wavesurfer = diagnostics_scope # for backward compatibility

# Online diagnostics:
#
# Setup required:
# Agilent 6-GHz oscilloscope in X-ray hutch:
# C1 = MSM detector, C2 = photodiode, C3 damaged, C4 = MCP-PMT,
# AUX(back) = trigger
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
from rayonix_detector_continuous import rayonix_detector
##from rayonix_detector import rayonix_detector
ccd = xray_detector = rayonix_detector

# Sample temperature
Temperature = temperature = PV("NIH:TEMP.RBV")

# Laser beam attenuator wheel in 14-ID Laser Lab
VNFilter1 = motor("14IDLL:m8",name="VNFilter1",readback_slop=0.030,min_step=0.030)
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

# Laser beam attenuator wheel in 14ID-B X-ray hutch
VNFilter2 = motor("14IDB:m32",name="VNFilter2",readback_slop=0.1,min_step=0.050)
# readback_slop [deg]" otherwise Thorlabs motor gets hung in "Moving" state
# min_step [deg]" otherwise Thorlabs motor gets hung in "Moving" state"
# This filter is mounted such that when the motor is homed (at 0) the
# attuation is minimal (OD 0.04) and increasing to 2.7 when the motor
# moves in positive direction.
# Based on measurements by Hyun Sun Cho and Friedrich Schotte, made 11 Nov 2014
# Recalibrated by Philip Anfinrud and Hyun Sun Cho 2018-10-28
trans2 = variable_attenuator(VNFilter2,motor_range=[5,285],OD_range=[0,2.66])
trans2.motor_min=0
trans2.OD_min=0
trans2.motor_max=300
trans2.OD_max=2.66

trans = trans1 # alias for "lauecollect"
VNFilter = VNFilter1 # alias for "lauecollect"

# Fast NIH Diffractometer, Aerotech "Ensemble" controller, F. Schotte, 30 Jan 2013 
from Ensemble import SampleX,SampleY,SampleZ,SamplePhi,PumpA,PumpB,msShut
from Ensemble_triggered_motion import triggered_motion
from Ensemble import ensemble_motors,ensemble
from Ensemble_SAXS_pp import Ensemble_SAXS
##from Alio_pp import Ensemble_SAXS # Added by RH 2018-10-04
# NIH Peristalitc pump, F. Schotte Nov 12, 2014
from peristaltic_pump import PumpA,PumpB,peristaltic_pump

# Cameras
microscope_camera = Camera("MicroscopeCamera")
widefield_camera = Camera("WideFieldCamera")

# Dummy for compatibility of XPP
class xray_detector_trigger(object):
    class count(object): value = 0

# Configurations
for n in configuration.configuration_names:
    try: exec("%s = configuration(%r,globals=globals())" % (n,n))
    except: pass
    
##BioCARS_methods_testing = configuration("BioCARS_methods_testing",globals=globals()) # Rob Henning 2018-10-04
