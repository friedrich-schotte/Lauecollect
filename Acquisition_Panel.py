#!/usr/bin/env python
"""
Control Panel for Data Collection

Author: Friedrich Schotte
Date created: 2018-10-17
Date last modified: 2022-07-16
Revision comment: Using collection_variables_with_count
"""
__version__ = "3.7.3"

from logging import debug
import wx

from Control_Panel import Control_Panel


class Acquisition_Panel(Control_Panel):
    """Control self for data collection"""
    icon = "Tool"

    @property
    def title(self): return "PP Acquire [%s]" % self.name

    @property
    def ControlPanel(self):
        return PP_Acquire_Control_Panel(self, self.name)


class PP_Acquire_Control_Panel(wx.Panel):

    @property
    def acquisition(self):
        from acquisition_control import acquisition_control
        return acquisition_control(self.domain_name)

    def __init__(self, parent, domain_name):
        wx.Panel.__init__(self, parent=parent)

        self.domain_name = domain_name

        from EditableControls import ComboBox, TextCtrl, Choice
        from Directory_Browse_Control import Directory_Browse_Control
        from Event_Control import Event_Control
        from reference import reference

        border = 2
        left = wx.ALIGN_LEFT
        cv = wx.ALIGN_CENTER_VERTICAL
        a = wx.ALL
        e = wx.EXPAND

        frame = wx.BoxSizer()
        self.Sizer = frame

        layout = wx.BoxSizer(wx.VERTICAL)
        frame.Add(layout, flag=wx.EXPAND | wx.ALL, border=10, proportion=1)
        layout_flag = wx.EXPAND

        group = wx.FlexGridSizer(cols=2)
        layout.Add(group, flag=layout_flag, border=border, proportion=1)
        group.AddGrowableCol(1, proportion=1)

        label = wx.StaticText(self, label="Method:")
        group.Add(label, flag=cv, border=0)

        subgroup = wx.BoxSizer(wx.HORIZONTAL)

        control = Event_Control(
            self,
            control_type=ComboBox,
            references={
                'Value': reference(self.acquisition, "method_name"),
                'Items': reference(self.acquisition, "method_names"),
                'Enabled': reference(self.acquisition, "method_online"),
            }
        )
        subgroup.Add(control, flag=left | a | e, border=0, proportion=1)

        from wx.lib.buttons import GenButton
        control = Event_Control(
            self,
            control_type=GenButton,
            references={
                'BackgroundColour': reference(self.acquisition, "method_color"),
                'ForegroundColour': reference(self.acquisition, "method_color"),
                'Enabled': reference(self.acquisition, "method_online"),
            },
            size=(25, 23),
        )
        subgroup.Add(control, flag=left | a | cv, border=0)

        control = Event_Control(
            self,
            control_type=wx.ToggleButton,
            references={
                'Value': reference(self.acquisition, "configuring"),
                'Enabled': reference(self.acquisition, "method_online"),
            },
            label="Configure",
        )
        subgroup.Add(control, flag=left | a | e, border=0)

        control = wx.Button(self, label="Methods...")
        self.Bind(wx.EVT_BUTTON, self.show_methods, control)
        subgroup.Add(control, flag=left | cv | a, border=0)

        group.Add(subgroup, flag=left | a | e, border=border)

        label = wx.StaticText(self, label="Time to Finish:")
        group.Add(label, flag=cv, border=0)
        control = Event_Control(
            self,
            control_type=wx.StaticText,
            references={
                'Label': reference(self.acquisition, "time_to_finish_message"),
                'Enabled': reference(self.acquisition, "online"),
            }
        )
        group.Add(control, flag=left | a | e, border=border)

        group.AddSpacer(20)
        group.AddSpacer(20)

        label = wx.StaticText(self, label="Path:")
        group.Add(label, flag=cv, border=0)
        control = Event_Control(
            self,
            control_type=Directory_Browse_Control,
            references={
                'Value': reference(self.acquisition, "directory"),
                'Enabled': reference(self.acquisition, "online"),
            }
        )
        group.Add(control, flag=left | a | e, border=border)

        label = wx.StaticText(self, label="Description:")
        group.Add(label, flag=cv, border=0)
        control = Event_Control(
            self,
            control_type=TextCtrl,
            references={
                'Value': reference(self.acquisition, "description"),
                'Enabled': reference(self.acquisition, "online"),
            }
        )
        group.Add(control, flag=left | a | e, border=border)

        group = wx.BoxSizer(wx.HORIZONTAL)
        layout.Add(group, flag=layout_flag, border=border)
        flag = wx.ALIGN_CENTER_VERTICAL

        control = Event_Control(
            self,
            control_type=wx.ToggleButton,
            references={
                'Value': reference(self.acquisition, "collecting_dataset"),
                'Label': reference(self.acquisition, "collecting_dataset_label"),
                'Enabled': reference(self.acquisition, "collecting_dataset_enabled"),
            }
        )
        group.Add(control, flag=flag, border=border, proportion=1)

        control = Event_Control(
            self,
            control_type=wx.ToggleButton,
            references={
                'Value': reference(self.acquisition, "erasing_dataset"),
                'Label': reference(self.acquisition, "erasing_dataset_label"),
                'Enabled': reference(self.acquisition, "erasing_dataset_enabled"),
            }
        )
        group.Add(control, flag=flag, border=border, proportion=1)

        label = wx.StaticText(self, label="Repeat:")
        group.Add(label, flag=flag, border=border)

        control = Event_Control(
            self,
            control_type=TextCtrl,
            references={
                'Value': reference(self.acquisition, "repeat_count_text"),
                'Enabled': reference(self.acquisition, "online"),
            },
            size=(45, -1),
        )
        group.Add(control, flag=flag, border=border)

        control = Event_Control(
            self,
            control_type=wx.ToggleButton,
            references={
                'Value': reference(self.acquisition, "finish_series"),
                'Label': reference(self.acquisition, "finish_series_label"),
                'Enabled': reference(self.acquisition, "online"),
            }
        )
        group.Add(control, flag=flag, border=border, proportion=1)

        control = Event_Control(
            self,
            control_type=Choice,
            references={
                'Value': reference(self.acquisition, "finish_series_variable"),
                'Items': reference(self.acquisition, "collection_variables_with_count"),
                'Enabled': reference(self.acquisition, "online"),
            }
        )
        group.Add(control, flag=flag, border=border, proportion=1)

        from Sound_Control import Sound_Control
        control = Event_Control(
            self,
            control_type=Sound_Control,
            references={
                'Value': reference(self.acquisition, "play_sound_value"),
                'Enabled': reference(self.acquisition, "online"),
            },
        )
        group.Add(control, flag=flag, border=border)

        indicator = Event_Control(
            self,
            control_type=wx.StaticText,
            references={
                'Label': reference(self.acquisition, "info_message"),
                'Enabled': reference(self.acquisition, "online"),
            }
        )
        layout.Add(indicator, flag=layout_flag, border=border, proportion=0)

        indicator = Event_Control(
            self,
            control_type=wx.StaticText,
            references={
                'Label': reference(self.acquisition, "status_message"),
                'Enabled': reference(self.acquisition, "online"),
            }
        )
        layout.Add(indicator, flag=layout_flag, border=border, proportion=0)

        indicator = Event_Control(
            self,
            control_type=wx.StaticText,
            references={
                'Label': reference(self.acquisition, "actual_message"),
                'Enabled': reference(self.acquisition, "online"),
            }
        )
        layout.Add(indicator, flag=layout_flag, border=border, proportion=0)

        self.Fit()  # needed?

    def show_methods(self, _event=None):
        debug("Showing methods...")
        self.configuration_panel.start()

    @property
    def configuration_panel(self):
        from application import application
        return application(
            domain_name=self.domain_name,
            module_name="Configuration_Table_Panel",
            command=f"Configuration_Table_Panel('{self.domain_name}.method')",
        )

    @staticmethod
    def play_sound():
        from sound import play_sound
        play_sound("ding")


if __name__ == '__main__':
    # from pdb import pm

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from redirect import redirect

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    redirect(f"{domain_name}.Acquisition_Panel", format=msg_format)
    # import autoreload

    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = Acquisition_Panel(name=domain_name)
    app.MainLoop()
