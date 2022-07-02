#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-05-31
Date last modified: 2021-05-31
Revision comment:
"""
__version__ = "1.0"

import wx

from Event_Controls import CheckBox_Control, ToggleButton_Control


class Sample_Illumination_Panel(wx.Panel):
    """Light switch for LED illuminator controlled by timing system"""

    def __init__(self, parent, domain_name):
        self.domain_name = domain_name
        wx.Panel.__init__(self, parent)
        self.Sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.State = State(self, self.domain_name)
        self.PP_Control = PP_Control(self, self.domain_name)

        label = wx.StaticText(self, label="Illumination:")
        self.Sizer.Add(label, flag=wx.ALIGN_CENTER)
        self.Sizer.Add(self.State, flag=wx.ALIGN_CENTER)
        self.Sizer.Add(self.PP_Control, flag=wx.ALIGN_CENTER)


class PP_Control(CheckBox_Control):
    def __init__(self, parent, domain_name):
        self.domain_name = domain_name
        super().__init__(parent=parent)

    label = "PP Controlled"

    @property
    def value_reference(self):
        from reference import reference
        return reference(self.control, "PP_controlled")

    @property
    def enabled_reference(self):
        from reference import reference
        return reference(self.control, "online")

    @property
    def control(self): return control(self.domain_name)


class State(ToggleButton_Control):
    def __init__(self, parent, domain_name):
        self.domain_name = domain_name
        super().__init__(parent=parent)

    @property
    def value_reference(self):
        from reference import reference
        return reference(self.control, "state")

    @property
    def enabled_reference(self):
        from reference import reference
        return reference(self.control, "enabled")

    @property
    def label_reference(self):
        from reference import reference
        return reference(self.control, "label")

    size = (45, -1)

    @property
    def control(self): return control(self.domain_name)


def control(domain_name):
    from sample_illumination_control import sample_illumination_control
    return sample_illumination_control(domain_name)


if __name__ == '__main__':
    # from pdb import pm

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from redirect import redirect

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect(f"{domain_name}.Sample_Illumination_Panel", format=msg_format)

    from Control_Panel import Control_Panel


    class Test_Panel(Control_Panel):
        @property
        def ControlPanel(self):
            return Sample_Illumination_Panel(self, self.name)


    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = Test_Panel(name=domain_name)
    app.MainLoop()
