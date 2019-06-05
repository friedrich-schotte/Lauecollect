#!/usr/bin/env python
"""Ice diffraction detection
Authors: Hyun Sun Cho, Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2017-10-31
Date last modified: 2018-10-31
"""
from logging import debug,warn,info,error
from sample_frozen import sample_frozen
from sample_frozen_optical import sample_frozen_optical
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
import wx

__version__ = "1.4" # ROI

class SampleFrozenPanel(BasePanel):

    name = "SampleFrozenPanel"
    title = "Sample Frozen"
    standard_view = [
        "Diffraction Spots",
        "Threshold [spots]",
        "Deice enabled",
        "Deicing",
        "Optical Server enabled",
        "Optical Intervention enabled",
        "Scattering Power",
    ]
    parameters = [
        [[TogglePanel,  "Aux. Deicing",          sample_frozen,"aux_deicing"],{"type":"Not active/Active"}],
        [[TogglePanel,  "Retracted",          sample_frozen,"retract"],{"type":"Inserted/Retracted"}],
        [[PropertyPanel,"Diffraction Spots",sample_frozen,"diffraction_spots"],{"read_only":True}],
        [[PropertyPanel,  "Optical Scattering",          sample_frozen_optical,"scattering"],{"read_only":True}],
        [[PropertyPanel,"Optical box dim (mm)",             sample_frozen_optical,"box_dimensions"],{"choices":[100,50,25,10]}],
        [[TogglePanel,  "XRay detection",    sample_frozen,"running"],{"type":"Off/On"}],
        [[TogglePanel,  "XRay aux intervention",    sample_frozen,"is_intervention_enabled"],{"type":"Off/On"}],
        [[TogglePanel,  "XRay retract inter.",    sample_frozen,"retract_deicing"],{"type":"Off/On"}],
        [[TogglePanel,  "Optical detection",    sample_frozen_optical,"is_running"],{"type":"Off/On"}],
        [[TogglePanel,  "Optical intervention",    sample_frozen_optical,"is_intervention_enabled"],{"type":"Off/Monitoring"}],
        [[PropertyPanel,"XRay image ROIX",             sample_frozen,"ROIX"],{"choices":[1000,900]}],
        [[PropertyPanel,"XRay image ROIY",             sample_frozen,"ROIY"],{"choices":[1000,900]}],
        [[PropertyPanel,"XRay image WIDTH",            sample_frozen,"WIDTH"],{"choices":[150,300,400]}],
        [[PropertyPanel,"Retracted time [sec]",sample_frozen,"retracted_time"],{"choices":[1,5,10,20]}],
        [[PropertyPanel,"Retracted time opt. [sec]",sample_frozen_optical,"retracted_time"],{"choices":[1,5,10,20]}],
        [[PropertyPanel,"Threshold [spots]",sample_frozen,"threshold_N_spts"],{"choices":[1,10,20,50]}],
        [[PropertyPanel,"Threshold [counts]",sample_frozen_optical,"scattering_threshold"],{"choices":[5,10,20,50]}],
        [[PropertyPanel,"Threshold [Temp. in C]",sample_frozen_optical,"frozen_threshold_temperature"],{"choices":[-20,-18,-15,-10]}],

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
    from redirect import redirect
    import autoreload
    #redirect('SampleFrozenPanelOpt',level="INFO")
    #logfile = gettempdir()+"/SampleFrozenPanelOpt.log"
##    logging.basicConfig(
##        level=logging.INFO,
##        format="%(asctime)s %(levelname)s: %(message)s",
##        logfile=logfile,
##    )


    # Needed to initialize WX library
    app = wx.App(redirect=False)
    panel = SampleFrozenPanel()
    #sample_frozen_optical.is_running = True
    #sample_frozen.running = True
    app.MainLoop()
