"""
This is to play sound in a GUI application

Author: Friedrich Schotte
Date created: 2020-09-23
Date last modified: 2021-04-25
Revision comment: Issue: On Windows, size growing out of control
"""
__version__ = "1.0.4"

from logging import debug, warning

import wx


class Sound_Control(wx.Button):
    from persistent_property import persistent_property
    value = persistent_property("value", "int(time()/5) % 2")
    event = persistent_property("event", [1, 0])  # [1,0] - transition from 1 to 0
    sound = persistent_property("sound", "ding")

    icon_name = "Sound"
    icon_margin = 4

    def __init__(self, parent, *args, **kwargs):
        wx.Button.__init__(self, parent, *args, **kwargs)
        self.set_icon()

        self.Bind(wx.EVT_BUTTON, self.handle_button, self)
        self.Bind(wx.EVT_SIZE, self.handle_resize, self)

        # Initialization
        self.previous_value = None
        self.current_value = None

    def GetValue(self):
        return self.current_value

    def SetValue(self, value):
        debug(f"Got value = {value!r}")
        self.previous_value = self.current_value
        self.current_value = value
        event = [self.previous_value, self.current_value]
        trigger = (event == self.event)
        debug(f"{event} == {self.event}? {trigger}")
        if trigger:
            self.play_sound()

    Value = property(GetValue, SetValue)

    def handle_button(self, _event):
        self.play_sound()

    from run_async import run_async

    @run_async
    def play_sound(self):
        debug("Playing sound.")
        from sound import play_sound
        play_sound(self.sound)

    def handle_resize(self, event):
        debug(f"event.Size {event.Size}")
        self.set_icon()
        event.Skip()

    def set_icon(self):
        bitmap = self.scaled_bitmap
        if bitmap:
            self.Bitmap = bitmap
            self.BitmapMargins = (self.icon_margin, self.icon_margin)

    def DoGetBestSize(self):
        default_size = wx.Button.DoGetBestSize(self)
        # w, h = default_size
        # size = h, h
        size = 27, 27
        debug(f"Adjusted size from {default_size} to {size}")
        return size

    @property
    def scaled_bitmap(self):
        bitmap = self.bitmap
        if bitmap:
            bitmap = rescale(bitmap, self.bitmap_size)
        return bitmap

    @property
    def bitmap_size(self):
        w, h = self.Size
        mw, mh = (self.icon_margin, self.icon_margin)
        d = 4  # internal space
        bitmap_size = max(w - 2 * mw - d, 1), max(h - 2 * mh - d, 1)
        debug(f"Size: {self.Size}: bitmap_size: {bitmap_size}")
        return bitmap_size

    @property
    def bitmap(self):
        from Icon import icon_filename
        filename = icon_filename(self.icon_name)
        if filename:
            try:
                icon = wx.Image(filename)
            except Exception as x:
                warning("%s: %s" % (filename, x))
                icon = None
        else:
            icon = None
        if icon:
            bitmap = wx.Bitmap(icon)
        else:
            bitmap = None
        return bitmap


def rescale(bitmap, bitmap_size):
    w, h = bitmap_size
    return bitmap.ConvertToImage().Rescale(w, h, wx.IMAGE_QUALITY_HIGH).ConvertToBitmap()


if __name__ == '__main__':
    import logging

    fmt = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=fmt)

    app = wx.GetApp() if wx.GetApp() else wx.App()
    frame = wx.Frame(None)
    self = Sound_Control(frame)
    self.Enabled = True
    frame.Fit()
    frame.Show()
    app.MainLoop()
