#!/usr/bin/env python
"""Control panel for timing system configuration 
Author: Friedrich Schotte
Date created: 2016-07-14
Date last modified: 2019-03-15
"""
__version__ = "2.0" # Timing_Channel_Configuration_Panel

from logging import debug,info,warn,error

from Panel import BasePanel
class Timing_Channel_Configuration_Panel(BasePanel):
    name = "TimingConfiguration"
    title = "Channel Configuration"
    icon = "timing-system"
    update = None
    
    def __init__(self,parent=None,update=None):
        if update is not None: self.update = update
        if self.update is None:
            from Ensemble_SAXS_pp import Ensemble_SAXS
            self.update = [Ensemble_SAXS.update]

        from timing_system import timing_system
        self.object = timing_system

        self.standard_view = ["#"]+[str(timing_system.channels[i].channel_number+1)
                         for i in range(0,len(timing_system.channels))]

        import wx
        self.layout = [[
            "#",
            [wx.StaticText,[],{"label":"PP","size":(35,-1)}],
            [wx.StaticText,[],{"label":"I/O","size":(50,-1)}],
            [wx.StaticText,[],{"label":"Description","size":(140,-1)}],
            [wx.StaticText,[],{"label":"Mnemonic","size":(75,-1)}],
            [wx.StaticText,[],{"label":"Special\nPP","size":(75,-1)}],
            [wx.StaticText,[],{"label":"Special\nHW","size":(70,-1)}],
            [wx.StaticText,[],{"label":"Offset\nHW","size":(100,-1)}],
            [wx.StaticText,[],{"label":"Offset\nsign","size":(50,-1)}],
            [wx.StaticText,[],{"label":"Duration\nHW","size":(75,-1)}],
            [wx.StaticText,[],{"label":"Duration\nHW reg","size":(75,-1)}],
            [wx.StaticText,[],{"label":"Offset\nPP ticks","size":(70,-1)}],
            [wx.StaticText,[],{"label":"Duration\nPP ticks","size":(75,-1)}],
            [wx.StaticText,[],{"label":"Cont.","size":(45,-1)}],
            [wx.StaticText,[],{"label":"Slaved","size":(72,-1)}],
            [wx.StaticText,[],{"label":"Gated","size":(72,-1)}],
            [wx.StaticText,[],{"label":"Count\nEnabled","size":(50,-1)}],
            [wx.StaticText,[],{"label":"State","size":(60,-1)}],
        ]]
        from Panel import PropertyPanel,TogglePanel
        from numpy import inf
        self.layout += [[
            str(timing_system.channels[i].channel_number+1),
            [TogglePanel,  [],{"name":"channels[%d].PP_enabled"%i,"type":"/PP","width":35,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].input.count"%i,"type":"Out/IN","width":50,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].description"%i,"width":140,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].mnemonic"%i,"width":75,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].special"%i,"width":75,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].specout.count"%i,"type":"/70MHz/diag1/diag2","width":70,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].offset_HW"%i,"type":"time.6","width":100,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].offset_sign"%i,"type":"float","width":50,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].pulse_length_HW"%i,"type":"time","width":75,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].pulse.value"%i,"type":"time","width":75,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].offset_PP"%i,"type":"float","width":70,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].pulse_length_PP"%i,"type":"float","width":70,"refresh_period":inf}],
            [TogglePanel,  [],{"name":"channels[%d].enable.count"%i,"type":"/Cont","width":45,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].timed"%i,"width":72,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].gated"%i,"width":72,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].counter_enabled"%i,"type":"/On","width":50,"refresh_period":inf}],
            [PropertyPanel,[],{"name":"channels[%d].output_status"%i,"width":60,"refresh_period":inf}],
        ] for i in range(0,len(timing_system.channels))]

        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            icon=self.icon,
            object=self.object,
            layout=self.layout,
            standard_view=self.standard_view,
            label_width=25,
            refresh=True,
            live=True,
            update=update,
        )
        
if __name__ == '__main__':
    from pdb import pm # for debugging
    from redirect import redirect
    redirect("Timing_Channel_Configuration_Panel")
    import wx
    app = wx.App(redirect=False) # to initialize WX...
    panel = Timing_Channel_Configuration_Panel()
    app.MainLoop()
