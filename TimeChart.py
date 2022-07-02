"""Time Chart window
Author: Friedrich Schotte
Date created: 2016-06-23
Date last modified: 2021-07-01
Revision comment: Cleanup
"""
from logging import debug, info, error

import wx

from EditableControls import ComboBox

__version__ = "1.6.3"


class TimeChart(wx.Panel):
    """Time Chart window"""
    name = "TimeChart"
    from persistent_property import persistent_property
    from time import time
    time_window = persistent_property("time_window", 60.0)  # seconds
    center_time = persistent_property("center_time", time() - 30.0)  # seconds
    show_latest = persistent_property("show_latest", True)

    def __init__(self, parent=None, title="Chart", object=None,
                 t_name="date time", v_name="value",
                 axis_label="", refresh_period=1.0, name=None, size=(500, 500),
                 *_args, **_kwargs):
        """title: string
        object: has attribute given by t_name,y_name
        t_name: e.g. "t_history" or "date time"
        v_name: e.g. "x_history", "y_history" or "value"
        """
        wx.Window.__init__(self, parent, size=size)
        self.title = title
        if object is not None:
            self.object = object
        self.t_name = t_name
        self.v_name = v_name
        self.axis_label = axis_label
        self.refresh_period = refresh_period
        if name is not None:
            self.name = name

        # Controls
        import logging
        # Suppress "CACHEDIR="
        # Suppress "Using fontManager instance from ..."
        # Suppress "FigureCanvasWxAgg - __init__() - bitmap w:400 h:300"
        logging.getLogger("matplotlib").level = logging.INFO
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
        self.figure = Figure(figsize=(4, 3))
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)

        style = wx.TE_PROCESS_ENTER

        self.TimeFraction = wx.ScrollBar(self)
        self.TimeFraction.SetScrollbar(800, 200, 100000, 100, True)
        # SetScrollbar(position,thumbSize,range,pageSize,refresh)
        # [Arguments misnamed "orientation,position,thumbSize,range,refresh"
        # in WxPython 2.9.1.1]

        choices = ["10s", "30s", "1min", "2min", "5min", "10min", "30min",
                   "1h", "2h", "6h", "12h", "1d", "2d", "5d"]
        self.TimeWindow = ComboBox(self, style=style, choices=choices)

        # Callbacks

        events = [
            wx.EVT_SCROLL_TOP, wx.EVT_SCROLL_BOTTOM,
            wx.EVT_SCROLL_LINEUP, wx.EVT_SCROLL_LINEDOWN,
            wx.EVT_SCROLL_PAGEUP, wx.EVT_SCROLL_PAGEDOWN,
            wx.EVT_SCROLL_THUMBRELEASE,
            wx.EVT_SCROLL_THUMBTRACK,
        ]
        for e in events:
            self.Bind(e, self.OnTimeFractionChanged, self.TimeFraction)
        self.Bind(wx.EVT_COMBOBOX, self.OnTimeWindowChanged, self.TimeWindow)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTimeWindowChanged, self.TimeWindow)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy, self)

        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.canvas, proportion=1, flag=wx.EXPAND)

        h_box = wx.BoxSizer(wx.HORIZONTAL)
        h_box.Add(self.TimeFraction, proportion=2, flag=wx.EXPAND)
        h_box.Add(self.TimeWindow, flag=wx.EXPAND)

        vbox.Add(h_box, flag=wx.EXPAND)
        self.SetSizer(vbox)
        self.SetSizeHints(minW=-1, minH=200, maxW=-1, maxH=-1)
        self.Fit()

        # Refresh
        self.attributes = [self.t_name, self.v_name, "start_time", "tmin", "tmax"]
        self.values = dict([(a, self.default_value(a)) for a in self.attributes])
        from numpy import copy
        self.old_values = dict((n, copy(self.values[n])) for n in self.values)

        from threading import Thread
        self.refresh_thread = Thread(target=self.refresh_background,
                                     name=self.name + ".refresh")
        self.refreshing = False

        from wx.lib.newevent import NewEvent
        self.EVT_THREAD = NewEvent()[1]
        self.Bind(self.EVT_THREAD, self.OnUpdate)
        self.thread = Thread(target=self.keep_updated,
                             name=self.name + ".keep_updated")
        self.thread.start()

        self.UpdateControls()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(1000, oneShot=True)

    def OnDestroy(self, _event):
        """"""
        info("%s destroyed" % self.name)

    def OnTimer(self, _event):
        """Perform periodic updates"""
        try:
            self.UpdateControls()
        except Exception as msg:
            import traceback
            error("%s\n%s" % (msg, traceback.format_exc()))
        self.timer.Start(1000, oneShot=True)

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        # debug("keep_updated: refresh_period %r" % self.refresh_period)
        from sleep import sleep  # interruptable sleep
        import traceback
        while True:
            try:
                sleep(self.refresh_period)
                self.update()
            except RuntimeError:
                break
            except Exception as msg:
                error("%s\n%s" % (msg, traceback.format_exc()))

    def update(self):
        """Re-trigger fresh of chart if data changed."""
        # Needs to be called from background thread.
        if self.Shown:
            self.update_data()
            if self.data_changed:
                event = wx.PyCommandEvent(self.EVT_THREAD.typeId, self.Id)
                # call OnUpdate in GUI thread
                wx.PostEvent(self.EventHandler, event)

    def refresh(self):
        """Force update"""
        from threading import Thread
        if not self.refreshing and self.Shown:
            self.refresh_thread = Thread(target=self.refresh_background,
                                         name=self.name + ".refresh")
            self.refreshing = True
            self.refresh_thread.start()

    def refresh_background(self):
        """Force update"""
        self.update_data()
        if self.data_changed:
            event = wx.PyCommandEvent(self.EVT_THREAD.typeId, self.Id)
            wx.PostEvent(self.EventHandler, event)  # call OnUpdate in GUI thread
        self.refreshing = False

    def update_data(self):
        """Retrieve status information"""
        from numpy import copy
        self.old_values = dict((n, copy(self.values[n])) for n in self.values)
        self.values = dict([(a, self.value(a)) for a in self.attributes])

    def value(self, attribute_name):
        if attribute_name == self.t_name:
            t, v = self.object.history(self.t_name, self.v_name,
                                       time_range=self.tmin_tmax)
            value = t
        elif attribute_name == self.v_name:
            t, v = self.object.history(self.t_name, self.v_name,
                                       time_range=self.tmin_tmax)
            value = v
        elif attribute_name == "start_time":
            value = self.object.start_time
        elif attribute_name == "tmin":
            value = self.tmin
        elif attribute_name == "tmax":
            value = self.tmax
        else:
            value = getattr(self, attribute_name)
        return value

    def default_value(self, attribute_name):
        from numpy import nan
        from time import time
        value = nan
        if attribute_name in (self.t_name, self.v_name):
            value = []
        elif attribute_name == "start_time":
            value = time() - 60
        elif attribute_name == "tmin":
            value = time() - 60
        elif attribute_name == "tmax":
            value = time()
        return value

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        from numpy import array_equal
        if sorted(self.values.keys()) != sorted(self.old_values.keys()):
            debug("data changed? keys changed")
            changed = True
        else:
            changed = not all([array_equal(self.values[a], self.old_values[a])
                               for a in self.values])
        # debug("data changed: %r" % changed)
        return changed

    def OnUpdate(self, _event=None):
        """Handle data changed"""
        self.RefreshChart()

    plot = None

    def RefreshChart(self):
        """Update the chart"""
        from pylab import setp, DateFormatter
        from numpy import isnan, ptp, ceil, floor, array, arange
        t_data, v_data = self.values[self.t_name], self.values[self.v_name]
        n = min(len(t_data), len(v_data))
        t_data, v_data = t_data[0:n], v_data[0:n]
        date = days(t_data)
        # self.figure.subplots_adjust(bottom=0.4) # ,left=0.2,right=0.97,top=0.92)
        self.plot = self.figure.add_subplot(1, 1, 1)
        self.plot.clear()
        self.plot.plot(date, v_data, '.', color=[0, 0, 1], markersize=2)
        tmin, tmax = self.tmin, self.tmax
        if not isnan(tmin) and not isnan(tmax):
            self.plot.set_xlim(days(tmin), days(tmax))
        time_range = ptp(self.tmin_tmax)
        s, m, h, d = 1, 60, 3600, 86400
        steps = array([
            0.1 * s, 0.2 * s, 0.5 * s,
            1 * s, 2 * s, 5 * s, 10 * s, 15 * s, 30 * s,
            1 * m, 2 * m, 5 * m, 10 * m, 15 * m, 30 * m,
            1 * h, 2 * h, 3 * h, 6 * h, 12 * h,
            1 * d, 7 * d, 28 * d,
        ])
        dt = time_range / 10
        step_choices = steps[steps <= dt]
        if len(step_choices) > 0:
            dt = max(step_choices)
        if dt < 1 * m:
            date_format = "%H:%M:%S"
        elif dt < 1 * h:
            date_format = "%H:%M"
        elif dt < 1 * d:
            date_format = "%H"
        else:
            date_format = "%d %H"
        self.plot.xaxis.set_major_formatter(DateFormatter(date_format))
        self.plot.xaxis_date()
        tmin, tmax = ceil(self.tmin / dt) * dt, floor(self.tmax / dt) * dt
        self.plot.xaxis.set_ticks(days(arange(tmin, tmax + 1e-6, dt)))
        setp(self.plot.get_xticklabels(), rotation=90, fontsize=10)
        setp(self.plot.get_yticklabels(), fontsize=10)
        label = self.axis_label
        self.plot.set_ylabel(label)
        self.plot.grid()
        self.figure.tight_layout()  # rect=[0,0.12,1,1]
        self.canvas.draw()

    @property
    def tmin_tmax(self):
        """Minimum and maximum value of time axis"""
        return [self.tmin, self.tmax]

    @property
    def tmin(self):
        """Minimum value of time axis"""
        tmin = self.tmax - self.time_window
        return tmin

    @property
    def tmax(self):
        """Maximum value of time axis"""
        from time import time
        if self.show_latest:
            tmax = time()
        else:
            tmax = self.center_time + self.time_window / 2
        return tmax

    @property
    def start_time(self):
        """Time of earliest data point in seconds since 1970-01-01 00:00:00 UTC"""
        return self.values["start_time"]

    @property
    def full_time_range(self):
        """Full time range from start of logfile to now"""
        from time import time
        dt = time() - self.start_time
        if not dt > 1.0:
            dt = 1.0
        return dt

    def UpdateControls(self):
        """Make sure control are up to date"""
        from time_string import time_string
        text = time_string(self.time_window)
        if self.TimeWindow.Value != text:
            self.TimeWindow.Value = text
        self.UpdateScrollbar()

    def OnTimeWindowChanged(self, _event):
        """Adjust chart x-axis to refresh the new time range"""
        from time_string import seconds
        from numpy import isnan
        time_window = seconds(self.TimeWindow.Value)
        if not isnan(time_window):
            self.time_window = time_window
        #  debug("time window changed: %r" % self.time_window)
        self.UpdateScrollbar()
        self.refresh()

    def OnTimeFractionChanged(self, _event):
        """Called when time window position is changed"""
        debug("start %r, end %r" % (self.start_fraction, self.end_fraction))
        self.show_latest = True if self.end_fraction >= 1 else False
        debug("show latest %r" % self.show_latest)
        center_fraction = (self.start_fraction + self.end_fraction) / 2
        self.center_time = self.start_time + self.full_time_range * center_fraction
        from time_string import date_time
        debug("center time %r" % date_time(self.center_time))
        self.refresh()

    def OnResize(self, event):
        self.RefreshChart()
        event.Skip()  # call default handler

    def UpdateScrollbar(self):
        from numpy import clip
        time_range = self.TimeFraction.Range
        thumb_size_fraction = clip(self.time_window / self.full_time_range, 0, 1)
        thumb_position_fraction = clip((self.tmin - self.start_time) / self.full_time_range, 0, 1)
        pagesize_fraction = 0.5 * thumb_size_fraction
        thumb_size = to_int(thumb_size_fraction * time_range)
        thumb_position = to_int(thumb_position_fraction * time_range)
        pagesize = to_int(pagesize_fraction * time_range)
        # debug("SetScrollbar(%r,%r,%r,%r)" % (thumb_position,thumb_size,range,pagesize))
        self.TimeFraction.SetScrollbar(thumb_position, thumb_size, time_range, pagesize,
                                       True)

    def get_start_fraction(self):
        position = self.TimeFraction.ThumbPosition
        time_range = max(self.TimeFraction.Range, 1)
        return float(position) / time_range

    def set_start_fraction(self, fraction):
        fraction = max(0, min(fraction, 1))
        time_range = max(self.TimeFraction.Range, 1)
        self.TimeFraction.ThumbPosition = to_int(fraction * time_range)

    start_fraction = property(get_start_fraction, set_start_fraction)

    def get_end_fraction(self):
        position = self.TimeFraction.ThumbPosition
        size = self.TimeFraction.ThumbSize
        end = position + size
        time_range = max(self.TimeFraction.Range, 1.0)
        return float(end) / time_range

    def set_end_fraction(self, fraction):
        fraction = max(0, min(fraction, 1))
        time_range = max(self.TimeFraction.Range, 1)
        size = self.TimeFraction.ThumbSize
        self.TimeFraction.ThumbPosition = to_int(fraction * time_range - size)

    end_fraction = property(get_end_fraction, set_end_fraction)


def days(seconds):
    """Convert a time stamp from seconds since 1 Jan 1970 0:00 UTC to days
    since 1 Jan 1 AD 0:00 localtime
    seconds: scalar or array"""
    # Determine the offset, which his time zone and daylight saving time
    # dependent.
    from numpy import mean, isnan, asarray, nan
    seconds = asarray(seconds)
    try:
        t = mean(seconds[~isnan(seconds)])
    except (TypeError, ValueError):
        t = nan
    if not isnan(t):
        from datetime import datetime
        from pylab import date2num
        offset = date2num(datetime.fromtimestamp(t)) - t / 86400
    else:
        offset = nan
    return seconds / 86400 + offset


def to_int(x):
    """Try to convert x to an integer number without raising an exception."""
    from numpy import rint
    x = rint(x)
    try:
        x = int(x)
    except (ValueError, TypeError):
        x = 0
    return x


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(funcName)s: %(message)s"
    from redirect import redirect

    redirect("TimeChart", level="DEBUG", format=msg_format)

    from Panel import BasePanel
    from xray_beam_check import Xray_Beam_Check


    class XRay_Beam_Check_Panel(BasePanel, Xray_Beam_Check):
        title = "X-Ray Beam Check"
        standard_view = ["X Control History"]

        def __init__(self):
            self.parameters = [
                [[TimeChart, "X Control History", self.log, "date time", "x_control"], {"axis_label": "Control X [mrad]", "name": self.name + ".TimeChart"}],
            ]
            BasePanel.__init__(self)


    app = wx.GetApp() if wx.GetApp() else wx.App()
    panel = XRay_Beam_Check_Panel()
    self = panel.controls[0]
    app.MainLoop()
