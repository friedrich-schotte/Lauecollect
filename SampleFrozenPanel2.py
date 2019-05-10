#!/usr/bin/env python
"""Ice diffraction detection
Authors: Hyun Sun Cho, Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2017-10-31
Date last modified: 2018-10-31
"""
from logging import debug,warn,info,error
from sample_frozen import sample_frozen
#from sample_frozen_optical2 import sample_frozen_optical
print('1')
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
print('2')
import wx
print('3')
__version__ = "1.4" # ROI 

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
        [[PropertyPanel,"ROIY",             sample_frozen,"ROIX"],{"choices":[1000,900]}],
        [[PropertyPanel,"WIDTH",            sample_frozen,"WIDTH"],{"choices":[150,300,400]}],
        #[[TogglePanel,  "Optical Server enabled",    sample_frozen_optical,"is_running"],{"type":"Off/On"}],
        #[[TogglePanel,  "Optical Intervention enabled",    sample_frozen_optical,"is_intervention_enabled"],{"type":"Off/Monitoring"}],
        #[[PropertyPanel,  "Scattering",          sample_frozen_optical,"scattering"],{"read_only":True}],
        
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
    print('4')
    logfile = gettempdir()+"/SampleFrozenPanel.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        #logfile=logfile,
    )
    print('5')
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    print('6')
    panel = SampleFrozenPanel()
    print('7')
    app.MainLoop()
