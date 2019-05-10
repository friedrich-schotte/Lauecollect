#!/usr/bin/env python
"""Control panel for simulated beamline environment of APS 14-IDB 
Author: Friedrich Schotte,
Date created: 2016-06-13
Date last modified: 2019-04-26
"""
from sim_id14 import sim_id14
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
import wx
__version__ = "1.7" # Mirror benders, JJ1 slits, KB mirror, collimator

class SimID14Panel(BasePanel,sim_id14):
    name = "sim_id14"
    title = "14ID-B Simulator"
    motors = [
        "current","sbcurrent","U23","U27",
        "FE_shutter_enabled",
        "ID14A_shutter",
        ##"FE_shutter","FE_shutter_auto",
        "Slit1H","Slit1V",
        "HLC",
        "mir1Th","MirrorV","mir1bender",
        "mir2X1","mir2X2","mir2bender",
        "ID14C_shutter",
        ##"safety_shutter","safety_shutter_auto",
        "s1hg","s1ho","s1vg","s1vo",
        "ChopX","ChopY",
        "shg","sho","svg","svo",
        "KB_Vpitch","KB_Vheight","KB_Vcurvature","KB_Vstripe",
        "KB_Hpitch","KB_Hheight","KB_Hcurvature","KB_Hstripe",
        "CollX","CollY",
        "GonX","GonY","GonZ","Phi",
        "DetZ",
        "laser_safety_shutter",
        ##"laser_safety_shutter_open","laser_safety_shutter_auto",
        "VNFilter",
    ]
    standard_view = [eval("sim_id14."+motor+".description") for motor in motors]

    layout = [[
        eval("sim_id14."+motor+".description"),
        [TweakPanel,   [],{"name":motor+".value","digits":4,"width":60}],
        [TogglePanel,  [],{"name":motor+".EPICS_enabled","type":"Off/On","width":40}],
        [PropertyPanel,[],{"name":motor+".prefix","width":120}]
    ] for motor in motors]
    
    def __init__(self,parent=None):
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            layout=self.layout,
            standard_view=self.standard_view,
            label_width=170,
            icon="BioCARS",
        )
        
if __name__ == '__main__':
    from pdb import pm # for debugging
    ##import logging; logging.basicConfig(level=logging.DEBUG)
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False) # to initialize WX...
    panel = SimID14Panel()
    wx.app.MainLoop()
    wx.App.Exit(wx.app)
