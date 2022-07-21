#!/usr/bin/env python
"""
Top-level Panel for BioCARS

Author: Friedrich Schotte
Date created: 2020-02-04
Date last modified: 2021-07-14
Revision comment: Added: Power Scan
"""
__version__ = "1.12"

import wx
import wx.lib.scrolledpanel


from Control_Panel import Control_Panel


class BioCARS_Panel(Control_Panel):
    name = "BioCARS_Panel"
    title = "BioCARS Instrumentation"
    icon = "NIH"
    domain_name = "BioCARS"

    @property
    def ControlPanel(self):
        panel = wx.lib.scrolledpanel.ScrolledPanel(self, style=wx.RAISED_BORDER)
        panel.SetupScrolling(scroll_x=False, scroll_y=True)

        frame = wx.BoxSizer()
        panel.Sizer = frame
        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)

        from Launch_Button import Launch_Button
        size = (170, -1)  # determines minimum width of buttons
        icon_size = 24
        style = wx.BU_LEFT
        proportion = 1
        flag = wx.EXPAND | wx.ALL
        border = 0
        space = 10

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="IOCs && Servers...",
            domain_name=self.domain_name,
            module_name="Servers_Panel",
            command=f"Servers_Panel('{self.domain_name}')",
            icon="Server",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Timing System...",
            domain_name=self.domain_name,
            module_name="Timing_Panel",
            command=f"Timing_Panel('{self.domain_name}')",
            icon="Timing System",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="PP Acquire...",
            domain_name=self.domain_name,
            module_name="Acquisition_Panel",
            command=f"Acquisition_Panel('{self.domain_name}')",
            icon="Tool",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Microscope Camera...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.MicroscopeCamera')",
            icon="camera",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Wide-Field Camera...",
            domain_name=self.domain_name,
            module_name="Camera_Viewer",
            command=f"Camera_Viewer('{self.domain_name}.WideFieldCamera')",
            icon="camera",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="SAXS-WAXS Control...",
            domain_name=self.domain_name,
            module_name="SAXS_WAXS_Control_Panel",
            command=f"SAXS_WAXS_Control_Panel('{self.domain_name}')",
            icon="SAXS-WAXS Control",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Environment Configurations...",
            domain_name=self.domain_name,
            module_name="Environment_Configurations_Panel",
            command=f"Environment_Configurations_Panel('{self.domain_name}')",
            icon="Utility",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Modes / Configurations...",
            domain_name=self.domain_name,
            module_name="Configuration_Tables_Panel",
            command=f"Configuration_Tables_Panel('{self.domain_name}')",
            icon="Tool",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Method Configuration...",
            domain_name=self.domain_name,
            module_name="Configuration_Table_Panel",
            command=f"Configuration_Table_Panel('{self.domain_name}.method')",
            icon="Tool",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="X-Ray Oscilloscope...",
            domain_name=self.domain_name,
            module_name="Scope_Panel",
            command=f"Scope_Panel('{self.domain_name}.xray_scope')",
            icon="oscilloscope",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Laser Oscilloscope...",
            domain_name=self.domain_name,
            module_name="Scope_Panel",
            command=f"Scope_Panel('{self.domain_name}.laser_scope')",
            icon="oscilloscope",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Rayonix Detector...",
            domain_name=self.domain_name,
            module_name="Rayonix_Detector_Panel",
            command=f"Rayonix_Detector_Panel('{self.domain_name}')",
            icon="Rayonix Detector",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="ADXV Live Image...",
            domain_name=self.domain_name,
            module_name="ADXV_Live_Image_Panel",
            command=f"ADXV_Live_Image_Panel('{self.domain_name}')",
            icon="ADXV",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Heat-Load Chopper Modes...",
            domain_name=self.domain_name,
            module_name="Configuration_Table_Panel",
            command=f"Configuration_Table_Panel('{self.domain_name}.heat_load_chopper_modes')",
            icon="Utility",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="High-Speed Chopper Modes...",
            domain_name=self.domain_name,
            module_name="Configuration_Table_Panel",
            command=f"Configuration_Table_Panel('{self.domain_name}.Julich_chopper_modes')",
            icon="Utility",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Motor Scan...",
            domain_name=self.domain_name,
            module_name="Motor_Scan_Panel",
            command=f"Motor_Scan_Panel('{self.domain_name}')",
            icon="Tool",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Temperature...",
            domain_name=self.domain_name,
            module_name="Temperature_System_Panel",
            command="Temperature_System_Panel()",
            icon="temperature",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Lightwave TEC...",
            domain_name=self.domain_name,
            module_name="Lightwave_Temperature_Controller_Panel",
            command="Lightwave_Temperature_Controller_Panel()",
            icon="Lightwave Temperature Controller",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Oasis Chiller...",
            domain_name=self.domain_name,
            module_name="Oasis_Chiller_Panel",
            command=f"Oasis_Chiller_Panel('{self.domain_name}')",
            icon="Oasis Chiller",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Channel Archiver...",
            domain_name=self.domain_name,
            module_name="Channel_Archiver_Panel",
            command=f"Channel_Archiver_Panel('{self.domain_name}')",
            icon="Archiver",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Channel Archiver Viewer...",
            domain_name=self.domain_name,
            module_name="Channel_Archiver_Viewer",
            command=f"Channel_Archiver_Viewer('{self.domain_name}')",
            icon="Archiver",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="X-Ray Beam Check...",
            domain_name=self.domain_name,
            module_name="XRay_Beam_Check_Panel",
            command="XRay_Beam_Check_Panel()",
            icon="Tool",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Ensemble Motors...",
            domain_name=self.domain_name,
            module_name="Ensemble_Motors_Panel",
            command="Ensemble_Motors_Panel()",
            icon="Tool",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        layout.AddSpacer(space)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Power Scan...",
            domain_name=self.domain_name,
            module_name="Power_Scan_Panel",
            command=f"Power_Scan_Panel('{self.domain_name}')",
            icon="Tool",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Laser Attenuator [in X-Ray Hutch]...",
            domain_name=self.domain_name,
            module_name="LaserAttenuatorXrayHutchPanel",
            command="LaserAttenuatorXrayHutchPanel()",
            icon="Tool",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        control = Launch_Button(
            parent=panel,
            size=size,
            style=style,
            icon_size=icon_size,
            label="Laser Attenuator [in Laser Lab]...",
            domain_name=self.domain_name,
            module_name="LaserAttenuatorLaserLabPanel",
            command="LaserAttenuatorLaserLabPanel()",
            icon="Tool",
        )
        layout.Add(control, proportion=proportion, flag=flag, border=border)

        return panel


if __name__ == '__main__':
    from redirect import redirect

    redirect("BioCARS.BioCARS_Panel")
    app = wx.GetApp() if wx.GetApp() else wx.App()
    self = BioCARS_Panel()
    app.MainLoop()
