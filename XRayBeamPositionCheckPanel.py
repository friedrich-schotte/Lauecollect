#!/usr/bin/env python
"""Grapical User Interface for X-ray beam stabilization
Friedrich Schotte, Nov 1, 2016 - Nov 1, 2016
"""
from pdb import pm # for debugging
from logging import debug,warn,info,error
##import logging; logging.basicConfig(level=logging.DEBUG)
from xray_beam_position_check import xray_beam_position_check,Xray_Beam_Position_Check
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
from BeamProfile_window import BeamProfile
from TimeChart import TimeChart
from persistent_property import persistent_property
import wx
__version__ = "1.0"

class XrayBeamCheckPanel(BasePanel,Xray_Beam_Position_Check):
    title = "X-Ray Beam Position Check"
    standard_view = [
        "Image",
        "X [mrad]",
        "Y [V]",
        "X Corr. [mrad]",
        "Y Corr. [V]",
        "Acquire Image",
        "X Correction",
        "Y Correction",
    ]
    saturation_level = persistent_property("saturation_level",10000.0) # counts

    def __init__(self,parent=None):
        Xray_Beam_Position_Check.__init__(self)
        
        parameters = [
            [[BeamProfile,  "Image",                  self                      ],{}],
            [[TweakPanel,   "Saturation level",       self,"saturation_level"   ],{"digits":0}],
            [[PropertyPanel,"Image timestamp",        self,"image_timestamp"    ],{"type":"date","read_only":True}],
            [[PropertyPanel,"Image usable",           self,"image_OK"           ],{"type":"Unusable/OK","read_only":True}],
            [[PropertyPanel,"Overloaded pixels",      self,"image_overloaded"   ],{"read_only":True}],
            [[PropertyPanel,"Signal-to-noise ratio",  self,"SNR"                ],{"digits":1,"read_only":True}],
            [[PropertyPanel,"X Beam [mm]",            self,"x_beam"             ],{"digits":3,"read_only":True}],
            [[PropertyPanel,"Y Beam [mm]",            self,"y_beam"             ],{"digits":3,"read_only":True}],
            [[PropertyPanel,"X Error [mm]",           self,"x_error"            ],{"digits":3,"read_only":True}],
            [[PropertyPanel,"Y Error [mm]",           self,"y_error"            ],{"digits":3,"read_only":True}],
            [[PropertyPanel,"X Beam avg. [mm]",       self,"x_average"          ],{"digits":3,"read_only":True}],
            [[PropertyPanel,"Y Beam avg. [mm]",       self,"y_average"          ],{"digits":3,"read_only":True}],
            [[TweakPanel,   "X [mrad]",               self,"x_control"          ],{"digits":4}],
            [[TweakPanel,   "Y [V]",                  self,"y_control"          ],{"digits":4}],
            [[PropertyPanel,"X Corr. [mrad]",         self,"x_control_corrected"],{"digits":4,"read_only":True}],
            [[PropertyPanel,"Y Corr. [V]",            self,"y_control_corrected"],{"digits":4,"read_only":True}],
            [[TogglePanel,  "Acquire Image",          self,"acquire_image_running"],{"type":"Start/Cancel"}],
            [[ButtonPanel,  "Correction",             self,"apply_correction"   ],{"label":"Apply"}],
            [[ButtonPanel,  "X Correction",           self,"apply_x_correction" ],{"label":"Apply"}],
            [[ButtonPanel,  "Y Correction",           self,"apply_y_correction" ],{"label":"Apply"}],
        ]
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subpanels=[Settings],
        )
        
class Settings(BasePanel,Xray_Beam_Position_Check.Settings):
    title = "Settings"
    standard_view = [
        "X1 Motor",
        "X2 Motor",
        "Y Motor",
        "X Aperture Motor",
        "Y Aperture Motor",
        "X Aperture (scan) [mm]",
        "Y Aperture (scan) [mm]",
        "X Aperture (norm) [mm]",
        "Y Aperture (norm) [mm]",
        "History Length",
        "Average count",
        "ROI center X [mm]",
        "ROI center Y [mm]",
        "ROI width [mm]",
        "Nominal X [mm]",
        "Nominal Y [mm]",
    ]

    def __init__(self,parent=None):
        Xray_Beam_Position_Check.__init__(self)
        
        parameters = [
            [[PropertyPanel,"Timing System",      self,"timing_system_ip_address"],{}],
            [[PropertyPanel,"X1 Motor",           self,"x1_motor"             ],{}],
            [[PropertyPanel,"X2 Motor",           self,"x2_motor"             ],{}],
            [[PropertyPanel,"Y Motor",            self,"y_motor"              ],{}],
            ##[[TweakPanel,   "X Resolution [mrad]",self,"x_resolution"      ],{"digits":4}],
            ##[[TweakPanel,   "Y Resolution [V]",   self,"y_resolution"      ],{"digits":4}],
            [[PropertyPanel,"X Aperture Motor",   self,"x_aperture_motor"     ],{}],
            [[PropertyPanel,"Y Aperture Motor",   self,"y_aperture_motor"     ],{}],
            [[TweakPanel,   "X Aperture [mm]",    self,"x_aperture"        ],{"digits":4}],
            [[TweakPanel,   "Y Aperture [mm]",    self,"y_aperture"        ],{"digits":4}],
            [[TweakPanel,   "X Aperture (scan) [mm]",self,"x_aperture_scan"],{"digits":4}],
            [[TweakPanel,   "Y Aperture (scan) [mm]",self,"y_aperture_scan"],{"digits":4}],
            [[TweakPanel,   "X Aperture (norm) [mm]",self,"x_aperture_norm"],{"digits":4}],
            [[TweakPanel,   "Y Aperture (norm) [mm]",self,"y_aperture_norm"],{"digits":4}],
            [[TweakPanel,   "Calibration X [mrad/mm]",self,"x_gain"             ],{"digits":4}],
            [[TweakPanel,   "Calibration Y [V/mm]",   self,"y_gain"             ],{"digits":4}],
            [[PropertyPanel,"History Length",         self,"history_length"     ],{}],
            [[TweakPanel,   "Average count",          self,"average_samples"    ],{"digits":0}],
            [[TweakPanel,   "ROI center X [mm]",      self,"x_ROI_center"       ],{"digits":3}],
            [[TweakPanel,   "ROI center Y [mm]",      self,"y_ROI_center"       ],{"digits":3}],
            [[TweakPanel,   "ROI width [mm]",         self,"ROI_width"          ],{"digits":3}],
            [[TweakPanel,   "Nominal X [mm]",         self,"x_nominal"          ],{"digits":3}],
            [[TweakPanel,   "Nominal Y [mm]",         self,"y_nominal"          ],{"digits":3}],
            [[PropertyPanel,"Image filename",         self,"image_filename"     ],{"read_only":True}],
        ]
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subname=True,
        )

if __name__ == '__main__':
    import logging; logging.basicConfig(level=logging.DEBUG)
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    panel = XrayBeamCheckPanel()
    app.MainLoop()
