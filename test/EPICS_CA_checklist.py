"""This script is to test various implementations of the Python to EPICS
interface.
EpicsCA: Matt Newille, U Chicago
epics: Matt Newille, U Chicago
CA: Friedrich Schotte, NIH

Friedrich Schotte, APS, 17 Apr 2010
"""

from CA import caput,caget,cainfo,PV # choices: EpicsCA, epics, CA

# PVs used by lauecollect
PVs = [
    "Mt:TopUpTime2Inject",
    "14IDA:Slit1Hsize.VAL",
    "14IDA:Slit1Vsize.VAL",
    "14IDC:mir1Th.RBV",
    "14IDC:mir2Th.RBV",
    "ACIS:ShutterPermit",
    "PA:14ID:A_SHTRS_CLOSED.VAL",
    "14IDA:shutter_auto_enable1",
    "14IDB:B1Bi0.VAL",
    "14IDB:Dliepcr1:Out1Mbbi",
    "14IDA:DAC1_4.VAL",
    "14IDC:mir2Th.VAL",
    "14IDB:beamCheckV",
    "14IDB:beamCheckH",
    "14IDA:DAC1_4.VAL",
    "14IDC:mir2Th.VAL",
    "PA:14ID:A_SHTRS_CLOSED.VAL",
    "ACIS:ShutterPermit",
    "PA:14ID:A_SHTRS_CLOSED.VAL",
    "14IDA:m5.VAL",
    "14IDA:LA2000_SPEED",
    "14IDB:DAC1_2.VAL",
    "14IDB:DAC1_3.VAL",
    "14IDB:xiaStatus.VAL",
    "14IDB:DAC1_1.VAL",
    "14IDB:B1Bi0.VAL",
]
for pv in PVs: print "%s: %r" % (pv,caget(pv))
