"""Simulate motors of 14-IDB beamline
Author: Friedrich Schotte,
Date created: 2016-06-25
Date last modified: 2019-05-26
"""
__version__ = "1.8" # Slit1H,Slit1V: readback

class sim_id14:
    name = "sim_id14"
    from sim_motor import sim_EPICS_motor as motor
    from sim_safety_shutter import sim_EPICS_safety_shutter

    current = motor("S:SRcurrentAI",name="current",description="Ring current")
    sbcurrent = motor("BNCHI:BunchCurrentAI",name="sbcurrent",description="Bunch current")

    # Undulators
    U23 = motor("ID14ds:Gap",name="U23",description="U23 gap")
    U27 = motor("ID14us:Gap",name="U27",description="U23 gap")

    # Safety shutter
    FE_shutter_enabled = motor("ACIS:ShutterPermit",
        name="FE_shutter_enabled",description="Shutter 14IDA enabled")
    ID14A_shutter = sim_EPICS_safety_shutter(
        name="ID14A_shutter",
        description="Shutter 14IDA",
        command_value="14IDA:shutter_in1.VAL",
        value="PA:14ID:STA_A_FES_OPEN_PL.VAL",
        auto_open="14IDA:shutter_auto_enable1.VAL",
    )
    ID14A_shutter.IOC.transform_functions["command_value"] = lambda x:1-x,lambda x:1-x
    # (old version)
    ID14A_shutter_open = motor("PA:14ID:STA_A_FES_OPEN_PL",
        name="ID14A_shutter_open",description="Shutter 14IDA open")
    ID14A_shutter_auto = motor("14IDA:shutter_auto_enable1",
        name="ID14A_shutter_auto",description="Shutter 14IDA auto")

    # white beam slits (at 28 m) 
    Slit1H = motor("14IDA:Slit1Hsize",name="Slit1H",description="White beam slits H gap",
      readback="14IDA:Slit1Ht2.C")
    Slit1V = motor("14IDA:Slit1Vsize",name="Slit1V",description="White beam slits V gap",
      readback="14IDA:Slit1Vt2.C")

    # Heatload chopper
    HLC = motor("14IDA:m5",name="HLC",description="Heatload chopper")

    # Vertical deflecting mirror
    # Incidence angle
    mir1Th = motor("14IDC:mir1Th",name="mir1Th",description="Vert. mirror angle",unit="mrad")
    # Piezo DAC voltage (0-10 V)
    MirrorV = motor("14IDA:DAC1_4",name="MirrorV",description="Vert. beam stearing",unit="V")
    mir1bender = motor("14IDC:m6",name="mir1bender",description="Vert. mirror bender") 

    # Horizontal deflecting mirror
    # Upstream
    mir2X1 = motor("14IDC:m12",name="mir2X1",description="Horiz. mirror jack 1")
    # Downstream (distance 1.045 m)
    mir2X2 = motor("14IDC:m13",name="mir2X2",description="Horiz. mirror jack 2")
    mir2bender = motor("14IDC:m14",name="mir2bender",description="Horiz. mirror bender") 

    # Safety shutter
    ID14C_shutter = sim_EPICS_safety_shutter(
        name="ID14C_shutter",
        description="Shutter 14IDC",
        command_value="14IDA:shutter_in2.VAL",
        value="PA:14ID:STA_B_SCS_OPEN_PL.VAL",
        auto_open="14IDA:shutter_auto_enable2.VAL",
    )
    ID14C_shutter.IOC.transform_functions["command_value"] = lambda x:1-x,lambda x:1-x
    # (old version)
    ID14C_shutter_open = motor("PA:14ID:STA_B_SCS_OPEN_PL",
        name="ID14C_shutter_open",description="Shutter 14IDC open")
    ID14C_shutter_auto = motor("14IDA:shutter_auto_enable2",
        name="ID14C_shutter_auto",description="Shutter 14IDC auto")

    # JJ1 slits (upstream)
    s1hg = motor("14IDC:m39",name="s1hg",description="JJ1 slits horiz. gap)")
    s1ho = motor("14IDC:m40",name="s1ho",description="JJ1 slits horiz. offset")
    s1vg = motor("14IDC:m37",name="s1vg",description="JJ1 slits vert. gap)")
    s1vo = motor("14IDC:m38",name="s1vo",description="JJ1 slits vert. offset")

    # High-speed X-ray Chopper
    ChopX = motor("14IDB:m1",name="ChopX",description="High-speed chopper X")
    ChopY = motor("14IDB:m2",name="ChopY",description="High-speed chopper Y")

    # JJ2 Sample slits
    shg = motor("14IDB:m25",name="shg",description="Sample slits horiz. gap")
    sho = motor("14IDB:m26",name="sho",description="Sample slits horiz. offset")
    svg = motor("14IDB:m27",name="svg",description="Sample slits vert. gap")
    svo = motor("14IDB:m28",name="svo",description="Sample slits vert. offset")

    # KB mirror
    KB_Vpitch     = motor("14IDC:pm4",name="KB_Vpitch",    description="KB vert. pitch") 
    KB_Vheight    = motor("14IDC:pm3",name="KB_Vheight",   description="KB vert. height") 
    KB_Vcurvature = motor("14IDC:pm1",name="KB_Vcurvature",description="KB vert. curv.")
    KB_Vstripe    = motor("14IDC:m15",name="KB_Vstripe",   description="KB vert. stripe")
    KB_Hpitch     = motor("14IDC:pm8",name="KB_Hpitch",    description="KB horiz. pitch") 
    KB_Hheight    = motor("14IDC:pm7",name="KB_Hheight",   description="KB horiz. height") 
    KB_Hcurvature = motor("14IDC:pm5",name="KB_Hcurvature",description="KB horiz. curv.")
    KB_Hstripe    = motor("14IDC:m44",name="KB_Hstripe",   description="KB horiz. stripe")

    # Collimator
    CollX = motor("14IDB:m35",name="CollX",description="Collimator X")
    CollY = motor("14IDB:m36",name="CollY",description="Collimator Y")

    # Alio diffractometer
    GonX = motor("14IDB:m152",name="GonX",description="Alio X")
    GonY = motor("14IDB:m153",name="GonY",description="Alio Y")
    GonZ = motor("14IDB:m150",name="GonZ",description="Alio Z")
    Phi  = motor("14IDB:m151",name="Phi",description="Alio Phi")

    # Sample-to-detector distance
    DetZ = motor("14IDB:m3",name="DetZ",description="Detector distance")

    # Laser safety shutter
    laser_safety_shutter = sim_EPICS_safety_shutter(
        name="laser_safety_shutter",
        description="Laser Safety Shutter",
        command_value="14IDB:lshutter.VAL",
        value="14IDB:B1Bi0.VAL",
        auto_open="14IDB:lshutter_auto.VAL",
    )
    laser_safety_shutter.IOC.transform_functions["value"] = lambda x:1-x,lambda x:1-x
    # (old version)
    laser_safety_shutter_open = motor("14IDB:B1Bi0",
        name="laser_safety_shutter",description="Laser Safety Shutter")
    laser_safety_shutter_auto = motor("14IDB:lshutter_auto",
        name="laser_safety_shutter_auto",description="Laser Safety Shutter auto")

    # Laser beam attenuator wheel in 14ID-B X-ray hutch
    VNFilter = motor("14IDB:m32",name="VNFilter",description="Laser att. X-Ray hutch")


