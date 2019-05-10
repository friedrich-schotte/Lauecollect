#!/usr/bin/env python
"""Grapical User Interface for X-ray beam stabilization
Friedrich Schotte, Nov 23, 2015 - Mar 6, 2017
"""
from pdb import pm # for debugging
from logging import debug,warn,info,error
##import logging; logging.basicConfig(level=logging.DEBUG)
from xray_beam_stabilization import Xray_Beam_Stabilization
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
from BeamProfile_window import BeamProfile
from TimeChart import TimeChart
from persistent_property import persistent_property
import wx
__version__ = "1.2" # TimeChart new API

class Panel(BasePanel,Xray_Beam_Stabilization):
    standard_view = [
        "Image",
        "Image filename",
        "Nominal X [mm]",
        "Nominal Y [mm]",
        "Beam X [mm]",
        "Beam Y [mm]",
        "Calibration X [mrad/mm]",
        "Calibration Y [V/mm]",
        "Control X [mrad]",
        "Control Y [V]",
        "Control X corr. [mrad]",
        "Control Y corr. [V]",
        "Correct X",
        "Correct Y",
    ]
    saturation_level = persistent_property("saturation_level",10000.0) # counts

    def __init__(self,parent=None):
        Xray_Beam_Stabilization.__init__(self)
        
        parameters = [
            [[BeamProfile,  "Image",                  self                      ],{}],
            [[TimeChart,    "History X",              self.log,"date time","x"],{"axis_label":"X [mm]","name":self.name+".TimeChart"}],
            [[TimeChart,    "History Y",              self.log,"date time","y"],{"axis_label":"Y [mm]","name":self.name+".TimeChart"}],
            [[TimeChart,    "History Control X",      self.log,"date time","x_control"],{"axis_label":"Control X [mrad]","name":self.name+".TimeChart"}],
            [[TimeChart,    "History Control Y",      self.log,"date time","y_control"],{"axis_label":"Control Y [V]"   ,"name":self.name+".TimeChart"}],
            [[PropertyPanel,"History Length",         self,"history_length"     ],{}],
            [[PropertyPanel,"History filter",         self,"history_filter"     ],{"choices":["","1pulses","5pulses"]}],
            [[PropertyPanel,"Logfile",                self.log,"filename"       ],{}],
            [[PropertyPanel,"Image filename",         self,"image_basename"     ],{"read_only":True}],
            [[PropertyPanel,"Image timestamp",        self,"image_timestamp"    ],{"type":"date","read_only":True}],
            [[PropertyPanel,"Analysis filter",        self,"analysis_filter"    ],{"choices":["","1pulses","5pulses"]}],
            [[PropertyPanel,"Image usable",           self,"image_OK"           ],{"type":"Unusable/OK","read_only":True}],
            [[PropertyPanel,"Overloaded pixels",      self,"image_overloaded"   ],{"read_only":True}],
            [[PropertyPanel,"Signal-to-noise ratio",  self,"SNR"                ],{"digits":1,"read_only":True}],
            [[TogglePanel,  "Auto update",            self,"auto_update"        ],{"type":"Off/On"}],
            [[TweakPanel,   "Average count",          self,"average_samples"    ],{"digits":0}],
            [[TweakPanel,   "ROI center X [mm]",      self,"x_ROI_center"       ],{"digits":3}],
            [[TweakPanel,   "ROI center Y [mm]",      self,"y_ROI_center"       ],{"digits":3}],
            [[TweakPanel,   "ROI width [mm]",         self,"ROI_width"          ],{"digits":3}],
            [[TweakPanel,   "Saturation level",       self,"saturation_level"   ],{"digits":0}],
            [[TweakPanel,   "Nominal X [mm]",         self,"x_nominal"          ],{"digits":3}],
            [[TweakPanel,   "Nominal Y [mm]",         self,"y_nominal"          ],{"digits":3}],
            [[PropertyPanel,"Beam X [mm]",            self,"x_beam"             ],{"digits":3,"read_only":True}],
            [[PropertyPanel,"Beam Y [mm]",            self,"y_beam"             ],{"digits":3,"read_only":True}],
            [[PropertyPanel,"Beam X avg. [mm]",       self,"x_average"          ],{"digits":3,"read_only":True}],
            [[PropertyPanel,"Beam Y avg. [mm]",       self,"y_average"          ],{"digits":3,"read_only":True}],
            [[TweakPanel,   "Calibration X [mrad/mm]",self,"x_gain"             ],{"digits":4}],
            [[TweakPanel,   "Calibration Y [V/mm]",   self,"y_gain"             ],{"digits":4}],
            [[PropertyPanel,"Control X PV",           self,"x_PV"               ],{}],
            [[PropertyPanel,"Control Y PV",           self,"y_PV"               ],{}],
            [[PropertyPanel,"Control X read PV",      self,"x_read_PV"          ],{}],
            [[PropertyPanel,"Control Y read PV",      self,"y_read_PV"          ],{}],
            [[TweakPanel,   "Control X [mrad]",       self,"x_control"          ],{"digits":4}],
            [[TweakPanel,   "Control Y [V]",          self,"y_control"          ],{"digits":4}],
            [[TweakPanel,   "Control X avg. [mrad]",  self,"x_control_average"  ],{"digits":4}],
            [[TweakPanel,   "Control Y avg. [V]",     self,"y_control_average"  ],{"digits":4}],
            [[PropertyPanel,"Control X corr. [mrad]", self,"x_control_corrected"],{"digits":4,"read_only":True}],
            [[PropertyPanel,"Control Y corr. [V]",    self,"y_control_corrected"],{"digits":4,"read_only":True}],
            [[TogglePanel,  "Stabilization X",        self,"x_enabled"          ],{"type":"Off/On"}],
            [[TogglePanel,  "Stabilization Y",        self,"y_enabled"          ],{"type":"Off/On"}],
            [[ButtonPanel,  "Correct X",              self,"apply_x_correction" ],{"label":"Correct X"}],
            [[ButtonPanel,  "Correct Y",              self,"apply_y_correction" ],{"label":"Correct Y"}],
            [[ButtonPanel,  "Correct Position",       self,"apply_correction"   ],{"label":"Correct"}],
        ]
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title="X-Ray Beam Stabilization",
            parameters=parameters,
            standard_view=self.standard_view,
            refresh=True,
            live=True,
        )
        

if __name__ == '__main__':
    import logging; logging.basicConfig(level=logging.DEBUG)
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    panel = Panel()
    app.MainLoop()
