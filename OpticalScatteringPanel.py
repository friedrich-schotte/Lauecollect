#!/usr/bin/env python
"""Optical Scattering Server Panel
Authors: Valentyn Stadnytskyi
Date created: 2019-05-30
Date last modified: 2019-05-30
"""
from logging import debug,warn,info,error
from optical_scattering import optical_scattering
from Panel import BasePanel,PropertyPanel,ButtonPanel,TogglePanel,TweakPanel
import wx

__version__ = "0.0.0" #initial

class OpticalScatteringPanel(BasePanel):

    name = "OpticalScatteringPanel"
    title = "Optical Scattering Panel"
    standard_view = [
        "Scattering",
        "box dim (mm)",
    ]
    parameters = [
        [[PropertyPanel,"Scattering",optical_scattering,"mean"],{"read_only":True}],
        [[PropertyPanel,"box dim (mm)",optical_scattering,"region_size_xy"],{"choices":[[100,100],[50,50],[20,20],[10,10]]}],
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
debug('Show debug')
if __name__ == '__main__':
    from pdb import pm
    #import logging
    from tempfile import gettempdir
    #from redirect import redirect
    #import autoreload
    #redirect('SampleFrozenPanelOpt',level="INFO")
    #logfile = gettempdir()+"/SampleFrozenPanelOpt.log"
##    logging.basicConfig(
##        level=logging.INFO,
##        format="%(asctime)s %(levelname)s: %(message)s",
##        logfile=logfile,
##    )


    # Needed to initialize WX library

    app = wx.App(redirect=False)
    panel = OpticalScatteringPanel()
    #sample_frozen_optical.is_running = True
    #sample_frozen.running = True
    app.MainLoop()
