"""
Monitor and control the X-ray safety shutters of the 14ID beamline.
There two X-ray safety shutters in the 14IDB beamline:
Front end shutter, upstream the first optics hutch: 14IDA
And the exit of the second optics hutch: 14IDC
Author: Friedrich Schotte
Date created: 2013-11-03
Date last modified: 2021-12-05
Revision comment: Keep auto-open of the front-end (ID14A) shutter enabled
"""
__version__ = "1.4"

from numpy import nan

from CA import PV


class XraySafetyShutterOpen(object):
    disable_auto_mode = False  # Disable "Auto Open" after shutter opened?
    monitoring = False
    auto_motor_enabled_time = 0

    def __init__(self, state_PV, change_PV):
        self.state_PV = state_PV
        self.change_PV = change_PV

    def get_value(self):
        from CA import caget
        PV_state = caget(self.state_PV)
        if PV_state == 1:
            state = True
        elif PV_state == 0:
            state = False
        elif PV_state is None:
            state = nan
        else:
            state = False
        return state

    def set_value(self, value):
        """value = True: open the shutter, value = False, close the shutter"""
        from CA import caput
        if value:
            caput(self.change_PV, 0)
        else:
            caput(self.change_PV, 1)

    value = property(get_value, set_value)


ID14A_shutter_open = XraySafetyShutterOpen(
    "PA:14ID:STA_A_FES_OPEN_PL.VAL",
    "14IDA:shutter_in1.VAL",
)
# Open: 14IDA:shutter_in1.VAL = 0
# Close: 14IDA:shutter_in1.VAL = 1
# Auto open: 14IDA:shutter_auto_enable1.VAL

ID14C_shutter_open = XraySafetyShutterOpen(
    "PA:14ID:STA_B_SCS_OPEN_PL.VAL",
    "14IDA:shutter_in2.VAL",
)


# Open: 14IDA:shutter_in2.VAL = 0
# Close: 14IDA:shutter_in2.VAL = 1
# Auto open: 14IDA:shutter_auto_enable2.VAL

class XraySafetyShuttersOpen(object):
    @property
    def value(self):
        return ID14A_shutter_open.value and ID14C_shutter_open.value

    @value.setter
    def value(self, opened):
        if opened:
            ID14A_shutter_open.value = True
            ID14C_shutter_open.value = True
        else:
            # Keep the front-end shutter open.
            # Close only the safety shutter and te exit of the optics hutch.
            ID14C_shutter_open.value = False


xray_safety_shutters_open = XraySafetyShuttersOpen()


class XraySafetyShuttersEnabled(object):
    def __init__(self, PV_name):
        self.PV_name = PV_name

    @property
    def value(self):
        from CA import caget
        value = caget(self.PV_name)
        from numpy import nan
        if value is None:
            value = nan
        return value


xray_safety_shutters_enabled = XraySafetyShuttersEnabled("ACIS:ShutterPermit.VAL")

ID14A_shutter_auto_open = PV("14IDA:shutter_auto_enable1.VAL")
ID14C_shutter_auto_open = PV("14IDA:shutter_auto_enable2.VAL")


class XraySafetyShuttersAutoOpen(object):
    @property
    def value(self):
        return ID14A_shutter_auto_open.value and ID14C_shutter_auto_open.value

    @value.setter
    def value(self, auto_open):
        if auto_open:
            ID14A_shutter_auto_open.value = True
            ID14C_shutter_auto_open.value = True
        else:
            # ID14A_shutter_auto_open.value = False
            ID14C_shutter_auto_open.value = False


xray_safety_shutters_auto_open = XraySafetyShuttersAutoOpen()

if __name__ == "__main__":  # for testing
    # from CA import caget  # for testing

    print('ID14A_shutter_open.value')
    print('ID14A_shutter_open.value = True')
    print('ID14A_shutter_open.value = False')
    print('ID14A_shutter_auto_open.value')
    print('ID14C_shutter_open.value')
    print('ID14C_shutter_open.value = True')
    print('ID14C_shutter_open.value = False')
    print('ID14C_shutter_auto_open.value')
    print('xray_safety_shutters_enabled.value')
    print('xray_safety_shutters_auto_open.value')
    print('xray_safety_shutters_open.value')
    print('xray_safety_shutters_open.value = False')
    print('xray_safety_shutters_open.value = True')
