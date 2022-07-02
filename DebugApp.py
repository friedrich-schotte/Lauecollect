"""
Author: Friedrich Schotte
Date created: 2022-04-30
Date last modified: 2022-04-30
Revision comment:
"""
__version__ = "1.0"

import logging
import wx


class DebugApp(wx.App):
    # https://github.com/wxWidgets/wxPython-Classic/blob/master/samples/mainloop/mainloop.py
    def __init__(self):
        super().__init__(clearSigInt=False)

    def MainLoop(self):

        # Create an event loop and make it active.  If you are
        # only going to temporarily have a nested event loop then
        # you should get a reference to the old one and set it as
        # the active event loop when you are done with this one...
        event_loop = wx.GUIEventLoop()
        old = wx.EventLoop.GetActive()
        wx.EventLoop.SetActive(event_loop)

        # This outer loop determines when to exit the application,
        # for this example we let the main frame reset this flag
        # when it closes.
        try:
            while self.TopWindow:
                # At this point in the outer loop you could do
                # whatever you implemented your own MainLoop for.  It
                # should be quick and non-blocking, otherwise your GUI
                # will freeze.

                # call_your_code_here()

                # This inner loop will process any GUI events
                # until there are no more waiting.
                while event_loop.Pending():
                    event_loop.Dispatch()

                # Send idle events to idle handlers.  You may want to
                # throttle this back a bit somehow so there is not too
                # much CPU time spent in the idle handlers.  For this
                # example, I'll just snooze a little...
                from time import sleep
                sleep(0.10)
                event_loop.ProcessIdle()
        except KeyboardInterrupt:
            pass

        wx.EventLoop.SetActive(old)


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    app = DebugApp()

    frame = wx.Frame(None)
    text = wx.StaticText(frame, label="This is a test.")
    frame.Fit()
    frame.Show()

    app.MainLoop()
