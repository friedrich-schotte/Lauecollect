"""Simulate motors of 14-IDB beamline
Author: Friedrich Schotte,
Date created: 2016-06-25
Date last modified: 2022-07-06
Revision comment: Changed speed of HLC, ChopX, ChopY
"""
__version__ = "1.11.2"


class Sim_ID14(object):
    name = "sim_id14"

    motor_names = [
        "current", "sbcurrent", "U23", "U27",
        "FE_shutter_enabled",
        "ID14A_shutter",
        # "FE_shutter","FE_shutter_auto",
        "Slit1H", "Slit1V",
        "HLC",
        "mir1Th", "MirrorV", "mir1bender",
        "mir2X1", "mir2X2", "mir2bender",
        "ID14C_shutter",
        # "safety_shutter","safety_shutter_auto",
        "s1hg", "s1ho", "s1vg", "s1vo",
        "ChopX", "ChopY",
        "shg", "sho", "svg", "svo",
        "KB_Vpitch", "KB_Vheight", "KB_Vcurvature", "KB_Vstripe",
        "KB_Hpitch", "KB_Hheight", "KB_Hcurvature", "KB_Hstripe",
        "Table2X",
        # "Table2Y",
        "CollX", "CollY",
        "GonX", "GonY", "GonZ", "Phi",
        "HuberPhi",
        "DetZ",
        "laser_safety_shutter",
        # "laser_safety_shutter_open","laser_safety_shutter_auto",
        "VNFilter",
        "LaserX", "LaserY", "LaserZ",
    ]

    from sim_motor import sim_EPICS_motor as motor
    from sim_safety_shutter import sim_EPICS_safety_shutter

    current = motor("S:SRcurrentAI", name="current", description="Ring current")
    sbcurrent = motor("BNCHI:BunchCurrentAI", name="sbcurrent", description="Bunch current")

    # Undulators
    U23 = motor("ID14ds:Gap", name="U23", description="U23 gap")
    U27 = motor("ID14us:Gap", name="U27", description="U23 gap")

    # Safety shutter
    FE_shutter_enabled = motor("ACIS:ShutterPermit",
                               name="FE_shutter_enabled", description="Shutter 14IDA enabled")
    ID14A_shutter = sim_EPICS_safety_shutter(
        name="ID14A_shutter",
        description="Shutter 14IDA",
        command_value="14IDA:shutter_in1.VAL",
        value="PA:14ID:STA_A_FES_OPEN_PL.VAL",
        auto_open="14IDA:shutter_auto_enable1.VAL",
    )
    ID14A_shutter.IOC.transform_functions["command_value"] = lambda x: 1 - x, lambda x: 1 - x
    # (old version)
    ID14A_shutter_open = motor("PA:14ID:STA_A_FES_OPEN_PL",
                               name="ID14A_shutter_open", description="Shutter 14IDA open")
    ID14A_shutter_auto = motor("14IDA:shutter_auto_enable1",
                               name="ID14A_shutter_auto", description="Shutter 14IDA auto")

    # white beam slits (at 28 m) 
    Slit1H = motor("14IDA:Slit1Hsize", name="Slit1H", description="White beam slits H gap",
                   readback="14IDA:Slit1Ht2.C")
    Slit1V = motor("14IDA:Slit1Vsize", name="Slit1V", description="White beam slits V gap",
                   readback="14IDA:Slit1Vt2.C")

    # Heatload chopper
    HLC = motor("14IDA:m5", name="HLC", description="Heatload chopper", speed=1.0)

    # Vertical deflecting mirror
    # Incidence angle
    mir1Th = motor("14IDC:mir1Th", name="mir1Th", description="Vert. mirror angle", unit="mrad")
    # Piezo DAC voltage (0-10 V)
    MirrorV = motor("14IDA:DAC1_4", name="MirrorV", description="Vert. beam steering", unit="V")
    mir1bender = motor("14IDC:m6", name="mir1bender", description="Vert. mirror bender")

    # Horizontal deflecting mirror
    # Upstream
    mir2X1 = motor("14IDC:m12", name="mir2X1", description="Horiz. mirror jack 1")
    # Downstream (distance 1.045 m)
    mir2X2 = motor("14IDC:m13", name="mir2X2", description="Horiz. mirror jack 2")
    mir2bender = motor("14IDC:m14", name="mir2bender", description="Horiz. mirror bender")

    # Safety shutter
    ID14C_shutter = sim_EPICS_safety_shutter(
        name="ID14C_shutter",
        description="Shutter 14IDC",
        command_value="14IDA:shutter_in2.VAL",
        value="PA:14ID:STA_B_SCS_OPEN_PL.VAL",
        auto_open="14IDA:shutter_auto_enable2.VAL",
    )
    ID14C_shutter.IOC.transform_functions["command_value"] = lambda x: 1 - x, lambda x: 1 - x
    # (old version)
    ID14C_shutter_open = motor("PA:14ID:STA_B_SCS_OPEN_PL",
                               name="ID14C_shutter_open", description="Shutter 14IDC open")
    ID14C_shutter_auto = motor("14IDA:shutter_auto_enable2",
                               name="ID14C_shutter_auto", description="Shutter 14IDC auto")

    # JJ1 slits (upstream)
    s1hg = motor("14IDC:m39", name="s1hg", description="JJ1 slits horiz. gap)")
    s1ho = motor("14IDC:m40", name="s1ho", description="JJ1 slits horiz. offset")
    s1vg = motor("14IDC:m37", name="s1vg", description="JJ1 slits vert. gap)")
    s1vo = motor("14IDC:m38", name="s1vo", description="JJ1 slits vert. offset")

    # High-speed X-ray Chopper
    ChopX = motor("14IDB:m1", name="ChopX", description="High-speed chopper X", speed=1.0)
    ChopY = motor("14IDB:m2", name="ChopY", description="High-speed chopper Y", speed=1.0)

    # JJ2 Sample slits
    shg = motor("14IDB:m25", name="shg", description="Sample slits horiz. gap")
    sho = motor("14IDB:m26", name="sho", description="Sample slits horiz. offset")
    svg = motor("14IDB:m27", name="svg", description="Sample slits vert. gap")
    svo = motor("14IDB:m28", name="svo", description="Sample slits vert. offset")

    # KB mirror
    KB_Vpitch = motor("14IDC:pm4", name="KB_Vpitch", description="KB vert. pitch")
    KB_Vheight = motor("14IDC:pm3", name="KB_Vheight", description="KB vert. height")
    KB_Vcurvature = motor("14IDC:pm1", name="KB_Vcurvature", description="KB vert. curv.")
    KB_Vstripe = motor("14IDC:m15", name="KB_Vstripe", description="KB vert. stripe")
    KB_Hpitch = motor("14IDC:pm8", name="KB_Hpitch", description="KB horiz. pitch")
    KB_Hheight = motor("14IDC:pm7", name="KB_Hheight", description="KB horiz. height")
    KB_Hcurvature = motor("14IDC:pm5", name="KB_Hcurvature", description="KB horiz. curv.")
    KB_Hstripe = motor("14IDC:m44", name="KB_Hstripe", description="KB horiz. stripe")

    # IDB Downstream table horizontal pseudo motor.
    Table2X = motor("14IDC:table2", name="Table2X", command="X", readback="EX", description="DS Table X")
    # IDB Downstream table vertical pseudo motor.
    Table2Y = motor("14IDC:table2", name="Table2Y", command="Y", readback="EY", description="DS Table Y")

    # Collimator
    CollX = motor("14IDB:m35", name="CollX", description="Collimator X")
    CollY = motor("14IDB:m36", name="CollY", description="Collimator Y")

    # Alio diffractometer
    GonX = motor("14IDB:m152", name="GonX", description="Alio X")
    GonY = motor("14IDB:m153", name="GonY", description="Alio Y")
    GonZ = motor("14IDB:m150", name="GonZ", description="Alio Z")
    Phi = motor("14IDB:m151", name="Phi", description="Alio Phi")

    # Huber diffractometer (for E-field experiments)
    HuberPhi = motor("14IDB:m16", name="HuberPhi", description="Huber Phi")

    # Sample-to-detector distance
    DetZ = motor("14IDB:m3", name="DetZ", description="Detector distance")

    # Laser safety shutter
    laser_safety_shutter = sim_EPICS_safety_shutter(
        name="laser_safety_shutter",
        description="Laser Safety Shutter",
        command_value="14IDB:lshutter.VAL",
        value="14IDB:B1Bi0.VAL",
        auto_open="14IDB:lshutter_auto.VAL",
    )
    laser_safety_shutter.IOC.transform_functions["value"] = lambda x: 1 - x, lambda x: 1 - x
    # (old version)
    laser_safety_shutter_open = motor("14IDB:B1Bi0",
                                      name="laser_safety_shutter", description="Laser Safety Shutter")
    laser_safety_shutter_auto = motor("14IDB:lshutter_auto",
                                      name="laser_safety_shutter_auto", description="Laser Safety Shutter auto")

    # Laser beam attenuator wheel in 14ID-B X-ray hutch
    VNFilter = motor("14IDB:m32", name="VNFilter", description="Laser att. X-Ray hutch")

    # Laser focus translation
    LaserX = motor("14IDB:m30", name="LaserX", description="Laser X")
    LaserY = motor("14IDB:m42", name="LaserY", description="Laser Y")
    LaserZ = motor("14IDB:m31", name="LaserZ", description="Laser Z")

    def get_motors(self):
        return [getattr(self, n) for n in self.motor_names]

    motors = property(get_motors)

    def get_running(self):
        return any([motor.EPICS_enabled for motor in self.motors])

    def set_running(self, value):
        if value:
            for motor in self.motors:
                motor.EPICS_enabled = True
        else:
            for motor in self.motors:
                motor.EPICS_enabled = False

    running = property(get_running, set_running)

    def run(self):
        self.running = True
        from time import sleep
        try:
            while True:
                sleep(0.25)
        except KeyboardInterrupt:
            pass
        self.running = False


sim_id14 = Sim_ID14()

if __name__ == "__main__":
    self = sim_id14  # for debugging
    # print("sim_id14.running = True")
    # print("sim_id14.running = False")
    # print("sim_id14.running")
    # print("sim_id14.run()")
    print("self.Table2X.EPICS_enabled = True")
    print("self.Table2X.command_PV_name")
    print("self.Table2X.readback_PV_name")
