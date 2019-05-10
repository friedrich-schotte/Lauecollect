#!/usr/bin/env python
"""Ice diffraction detection
Authors: Hyun Sun Cho, Friedrich Schotte
Date created: 2017-10-31
Date last modified: 2017-11-01
"""
from logging import debug,warn,info,error
from sample_frozen import sample_frozen
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
import wx
__version__ = "1.3" # ROI 

class SampleFrozenPanel(BasePanel):
    name = "SampleFrozenPanel"
    title = "Sample Frozen"
    standard_view = [
        "Diffraction Spots",
        "Threshold [spots]",
        "Deice enabled",
        "Deicing",
    ]
    parameters = [
        [[PropertyPanel,"Diffraction Spots",sample_frozen,"diffraction_spots"],{"read_only":True}],
        [[PropertyPanel,"Threshold [spots]",sample_frozen,"threshold_N_spts"],{"choices":[1,10,20,50]}],
        [[TogglePanel,  "Deice enabled",    sample_frozen,"running"],{"type":"Off/Monitoring"}],
        [[TogglePanel,  "Deicing",          sample_frozen,"deicing"],{"type":"Not active/Active"}],
        [[PropertyPanel,"ROIX",             sample_frozen,"ROIX"],{"choices":[1000,900]}],
        [[PropertyPanel,"ROIY",             sample_frozen,"ROIY"],{"choices":[1000,900]}],
        [[PropertyPanel,"WIDTH",            sample_frozen,"WIDTH"],{"choices":[150,300,400]}],
    ]
    def __init__(self,parent=None):
        BasePanel.__init__(self,
            parent=parent,
            name=self.name,
            title=self.title,
            icon="Tool",
            parameters=self.parameters,
            standard_view=self.standard_view,
        )

if __name__ == '__main__':
    from pdb import pm
    import logging
    from tempfile import gettempdir
    logfile = gettempdir()+"/SampleFrozenPanel.log"
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        logfile=logfile,
    )
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    panel = SampleFrozenPanel()
    app.MainLoop()
