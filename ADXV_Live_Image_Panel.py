#!/usr/bin/env python
"""Instruct the ADXV image display application to display a live image during
data collection

Author: Friedrich Schotte
Date created: 2019-06-02
Date last modified: 2022-06-22
Revision comment: Added: show_data_collection_image
"""
from logging import info
from Panel_3 import BasePanel
import wx

__version__ = "1.2"


class ADXV_Live_Image_Panel(BasePanel):
    def __init__(self, domain_name="BioCARS"):
        self.domain_name = domain_name
        super().__init__()
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy)

    @property
    def name(self): return f"{self.domain_name}/ADXV_Live_Image_Panel"

    @property
    def ADXV_live_image(self):
        from ADXV_live_image import ADXV_live_image
        return ADXV_live_image(self.domain_name)

    @property
    def title(self): return f"ADXV Live Image [{self.domain_name}]"

    standard_view = [
        "Live image",
        "ADXV status",
        "Mode",
        "Continuous Filename",
        "Collection Filename",
        "Live filename",
        "IP Address",
        "Refresh interval",
    ]

    @property
    def parameters(self):
        return [
            [["Live image", self.ADXV_live_image, "live_image"], {"type": "Off/On"}],
            [["ADXV status", self.ADXV_live_image, "online"], {"type": "Offline/Online", "read_only": True}],
            [["Mode", self.ADXV_live_image, "show_data_collection_image"], {"type": "Continuous/Collection"}],
            [["Continuous Filename", self.ADXV_live_image, "image_filename"], {"read_only": True}],
            [["Collection Filename", self.ADXV_live_image, "data_collection_image_filename"], {"read_only": True}],
            [["Live filename", self.ADXV_live_image, "live_image_filename"], {"read_only": True}],
            [["IP Address", self.ADXV_live_image, "ip_address"], {}],
            [["Refresh interval", self.ADXV_live_image, "refresh_interval"], {"format": "%g", "unit": "s"}],
        ]

    icon = "ADXV"
    label_width = 140
    width = 320

    def OnDestroy(self, event):
        info("Shutting down")
        self.ADXV_live_image.live_image = False
        event.Skip()


if __name__ == '__main__':
    from redirect import redirect
    from wx_init import wx_init

    redirect("ADXV_Live_Image_Panel")

    domain_name = "BioCARS"

    wx_init()
    app = wx.App()
    self = ADXV_Live_Image_Panel(domain_name)
    app.MainLoop()
