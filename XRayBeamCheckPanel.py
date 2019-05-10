#!/usr/bin/env python
"""Grapical User Interface for X-ray beam stabilization
Friedrich Schotte, Nov 23, 2015 - Oct 25, 2017
"""
from pdb import pm # for debugging
import logging
from tempfile import gettempdir
logfile = gettempdir()+"/XRayBeamCheckPanel.log"
logging.basicConfig(level=logging.DEBUG,
    format="%(asctime)s %(levelname)s: %(message)s",
    logfile=logfile,
)
from logging import debug,warn,info,error
from xray_beam_check import Xray_Beam_Check
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
from BeamProfile_window import BeamProfile
from TimeChart import TimeChart
from persistent_property import persistent_property
import wx
__version__ = "1.1.2" # logging

class XrayBeamCheckPanel(BasePanel,Xray_Beam_Check):
    title = "X-Ray Beam Check"
    standard_view = [
        "X [mrad]",
        "Y [V]",
        "X Corr. [mrad]",
        "Y Corr. [V]",
        "X Scan",
        "Y Scan",
        "X Correction",
        "Y Correction",
    ]

    def __init__(self,parent=None):
        Xray_Beam_Check.__init__(self)
        
        parameters = [
            [[PropertyPanel,"Timing Mode",      self.settings,"timing_mode"  ],{"choices":self.settings.timing_modes}],
            [[PropertyPanel,"Beamline Mode",    self.settings,"beamline_mode"],{"choices":self.settings.beamline_modes}],
            [[TimeChart,    "X Control History",self.log,"date time","x_control"],{"axis_label":"Control X [mrad]","name":self.name+".TimeChart"}],
            [[TimeChart,    "Y Control History",self.log,"date time","y_control"],{"axis_label":"Control Y [V]"   ,"name":self.name+".TimeChart"}],
            [[PropertyPanel,"Logfile",          self.log,"filename"       ],{}],
            [[TweakPanel,   "X [mrad]",         self,"x_control"          ],{"digits":4}],
            [[TweakPanel,   "Y [V]",            self,"y_control"          ],{"digits":4}],
            [[PropertyPanel,"X Corr. [mrad]",   self,"x_control_corrected"],{"digits":4,"read_only":True}],
            [[PropertyPanel,"Y Corr. [V]",      self,"y_control_corrected"],{"digits":4,"read_only":True}],
            [[TogglePanel,  "X Scan",           self,"x_scan_running"     ],{"type":"Start/Cancel"}],
            [[TogglePanel,  "Y Scan",           self,"y_scan_running"     ],{"type":"Start/Cancel"}],
            [[ButtonPanel,  "X Correction",     self,"apply_x_correction" ],{"label":"Apply"}],
            [[ButtonPanel,  "Y Correction",     self,"apply_y_correction" ],{"label":"Apply"}],
        ]
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subpanels=[Settings],
        )
        
class Settings(BasePanel,Xray_Beam_Check.Settings):
    title = "Settings"
    standard_view = [
        "X1 Motor",
        "X2 Motor",
        "Y Motor",
        "X Resolution [mrad]",
        "Y Resolution [V]",
        "X Scan Step [mrad]",
        "Y Scan Step [V]",
        "X Aperture Motor",
        "Y Aperture Motor",
        "X Aperture (scan) [mm]",
        "Y Aperture (scan) [mm]",
        "X Aperture (norm) [mm]",
        "Y Aperture (norm) [mm]",
    ]

    def __init__(self,parent=None):
        Xray_Beam_Check.__init__(self)
        
        parameters = [
            [[PropertyPanel,"Timing System",      self,"timing_system_ip_address"],{}],
            [[PropertyPanel,"Oscilloscope",       self,"scope_ip_address"  ],{}],
            [[PropertyPanel,"X1 Motor",           self,"x1_motor"          ],{}],
            [[PropertyPanel,"X2 Motor",           self,"x2_motor"          ],{}],
            [[PropertyPanel,"Y Motor",            self,"y_motor"           ],{}],
            [[TweakPanel,   "X Resolution [mrad]",self,"x_resolution"      ],{"digits":4}],
            [[TweakPanel,   "Y Resolution [V]",   self,"y_resolution"      ],{"digits":4}],
            [[TweakPanel,   "X Scan Step [mrad]", self,"dx_scan"           ],{"digits":4}],
            [[TweakPanel,   "Y Scan Step [V]",    self,"dy_scan"           ],{"digits":4}],
            [[PropertyPanel,"X Aperture Motor",   self,"x_aperture_motor"  ],{}],
            [[PropertyPanel,"Y Aperture Motor",   self,"y_aperture_motor"  ],{}],
            [[TweakPanel,   "X Aperture [mm]",    self,"x_aperture"        ],{"digits":4}],
            [[TweakPanel,   "Y Aperture [mm]",    self,"y_aperture"        ],{"digits":4}],
            [[TweakPanel,   "X Aperture (scan) [mm]",self,"x_aperture_scan"],{"digits":4}],
            [[TweakPanel,   "Y Aperture (scan) [mm]",self,"y_aperture_scan"],{"digits":4}],
            [[TweakPanel,   "X Aperture (norm) [mm]",self,"x_aperture_norm"],{"digits":4}],
            [[TweakPanel,   "Y Aperture (norm) [mm]",self,"y_aperture_norm"],{"digits":4}],
        ]
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            parameters=parameters,
            standard_view=self.standard_view,
            subname=False,
        )

if __name__ == '__main__':
    from pdb import pm
    import logging
    from tempfile import gettempdir
    logfile = gettempdir()+"/XRayBeamCheckPanel.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        logfile=logfile,
    )
    from logging_filename import log_to_file
    log_to_file(logfile+"2","DEBUG")
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    panel = XrayBeamCheckPanel()
    app.MainLoop()
    ##import threading; info("%r" % threading.enumerate())
