#!/usr/bin/env python
"""
View archived EPICS process variable history
Author: Friedrich Schotte
Date created: 2017-10-04
Date last modified: 2021-12-10
Revision comment: Cleanup: channel_archiver
"""
__version__ = "1.6.1"

from logging import debug, info, error

import wx

from Control_Panel import Control_Panel


class Channel_Archiver_Viewer(Control_Panel):
    icon = "Archiver"

    @property
    def title(self): return "Channel Archiver Viewer [%s]" % self.name

    @property
    def ControlPanel(self):
        return Channel_Archiver_Chart(self, domain_name=self.name)

    @property
    def menuBar(self):
        menuBar = super().menuBar

        # More
        menu = wx.Menu()
        menuBar.Insert(0, menu, "&File")
        ID = 201
        menu.Append(ID, "New Window")
        self.Bind(wx.EVT_MENU, self.OnNewWindow, id=ID)

        return menuBar

    def OnNewWindow(self, _event):
        Channel_Archiver_Viewer(self.name)


class Channel_Archiver_Chart(wx.Panel):
    domain_name = "BioCARS"

    @property
    def db_name(self):
        return "Channel_Archiver_Chart/%s" % self.domain_name

    from db_property import db_property

    @property
    def default_center_time(self):
        from time import time
        return time() - self.time_window / 2

    time_window = db_property("time_window", 60.0, local=True)  # seconds
    center_time = db_property("center_time", default_center_time, local=True)
    show_latest = db_property("show_latest", True, local=True)

    @property
    def default_PV_name(self):
        PV_name = self.PV_names[0] if len(self.PV_names) > 0 else ""
        return PV_name

    PV_name = db_property("PV_name", default_PV_name, local=True, private=True)

    def __init__(self,
                 parent=None,
                 domain_name=None,
                 PV_name=None,
                 ):
        """
        domain_name: e.g. "BioCARS", "LaserLab"
        PV_name: EPICS process variable name, e.g. 'NIH:TEMP.RBV'
        """
        wx.Window.__init__(self, parent=parent, size=(500, 500))

        if domain_name is not None:
            self.domain_name = domain_name
        if PV_name is not None:
            self.PV_name = PV_name

        self.t_name = "date time"
        self.v_name = "value"
        self.axis_label = ""
        self.refresh_period = 2

        suppress_matplotlib_debug_messages()

        # Controls
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
        self.figure = Figure()
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
        debug("self.canvas.MinSize: %r" % self.canvas.MinSize)
        self.canvas.MinSize = 1, 1
        self.plot = self.figure.add_subplot(1, 1, 1)

        from EditableControls import ComboBox
        style = wx.TE_PROCESS_ENTER
        self.PVChoice = ComboBox(self, style=style, size=(120, -1))

        self.TimeFraction = wx.ScrollBar(self)
        self.TimeFraction.SetScrollbar(800, 200, 100000, 100, True)
        # SetScrollbar(position,thumbSize,range,pageSize,refresh)
        # [Arguments misnamed "orientation,position,thumbSize,range,refresh"
        # in WxPython 2.9.1.1]

        choices = ["10s", "30s", "1min", "2min", "5min", "10min", "30min",
                   "1h", "2h", "6h", "12h", "1d", "2d", "5d"]
        self.TimeWindow = ComboBox(self, style=style, choices=choices)

        # Callbacks
        self.Bind(wx.EVT_COMBOBOX, self.OnPVChoice, self.PVChoice)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnPVChoice, self.PVChoice)

        events = [
            wx.EVT_SCROLL_TOP,
            wx.EVT_SCROLL_BOTTOM,
            wx.EVT_SCROLL_LINEUP,
            wx.EVT_SCROLL_LINEDOWN,
            wx.EVT_SCROLL_PAGEUP,
            wx.EVT_SCROLL_PAGEDOWN,
            wx.EVT_SCROLL_THUMBRELEASE,
            wx.EVT_SCROLL_THUMBTRACK,
        ]
        for e in events:
            self.Bind(e, self.OnTimeFractionChanged, self.TimeFraction)
        self.Bind(wx.EVT_COMBOBOX, self.OnTimeWindowChanged, self.TimeWindow)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTimeWindowChanged, self.TimeWindow)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroy, self)

        # Layout
        v_box = wx.BoxSizer(wx.VERTICAL)
        v_box.Add(self.canvas, proportion=1, flag=wx.EXPAND)

        h_box = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALIGN_CENTER_VERTICAL
        h_box.Add(self.PVChoice, proportion=1, flag=flag)
        h_box.Add(self.TimeFraction, proportion=2, flag=flag)  # was: wx.EXPAND|flag
        h_box.Add(self.TimeWindow, flag=flag)

        v_box.Add(h_box, flag=wx.EXPAND)
        self.SetSizer(v_box)
        self.SetSizeHints(minW=-1, minH=200, maxW=-1, maxH=-1)
        self.Fit()

        # Refresh
        self.attributes = [self.t_name, self.v_name, "start_time", "t_min", "t_max"]
        self.values = dict([(a, self.default_value(a)) for a in self.attributes])
        from numpy import copy
        self.old_values = dict((n, copy(self.values[n])) for n in self.values)

        from threading import Thread
        self.refresh_thread = Thread(target=self.refresh_background)
        self.refreshing = False

        from wx.lib.newevent import NewEvent
        self.EVT_THREAD = NewEvent()[1]
        self.Bind(self.EVT_THREAD, self.OnUpdate)
        self.thread = Thread(target=self.keep_updated)
        self.thread.start()

        self.UpdateControls()

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(1000, oneShot=True)

    def __repr__(self):
        return f"{self.class_name}({self.domain_name!r}, {self.PV_name!r})"

    @property
    def class_name(self):
        return type(self).__name__

    @property
    def log(self):
        return self.channel_archiver.logfile(self.PV_name)

    @property
    def PV_names(self):
        return self.channel_archiver.PVs

    @property
    def channel_archiver(self):
        from channel_archiver import channel_archiver
        return channel_archiver(self.domain_name)

    def OnDestroy(self, _event):
        info(f"{self} destroyed")

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
        from time import sleep
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
        """Re-trigger refresh of chart if data changed."""
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
            self.refresh_thread = Thread(target=self.refresh_background)
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
        if attribute_name in (self.t_name, self.v_name):
            t, v = self.log.history(self.t_name, self.v_name,
                                    time_range=self.t_min_t_max)
            if attribute_name == self.t_name:
                value = t
            else:
                value = v
        elif attribute_name == "start_time":
            value = self.log.start_time
        elif attribute_name == "t_min":
            value = self.t_min
        elif attribute_name == "t_max":
            value = self.t_max
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
        elif attribute_name == "t_min":
            value = time() - 60
        elif attribute_name == "t_max":
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

    def RefreshChart(self):
        """Update the chart"""
        from pylab import setp, DateFormatter
        from numpy import isnan, ptp, ceil, floor, array, arange
        t_data, v_data = self.values[self.t_name], self.values[self.v_name]
        n = min(len(t_data), len(v_data))
        t_data, v_data = t_data[0:n], v_data[0:n]
        date = days(t_data)
        # self.figure.subplots_adjust(bottom=0.4) # ,left=0.2,right=0.97,top=0.92)
        self.plot.clear()
        self.plot.plot(date, v_data, '.', color=[0, 0, 1], markersize=2)
        t_min, t_max = self.t_min, self.t_max
        if not isnan(t_min) and not isnan(t_max):
            self.plot.set_xlim(days(t_min), days(t_max))
        t_range = ptp(self.t_min_t_max)
        s, m, h, d = 1, 60, 3600, 86400
        steps = array([
            0.1 * s, 0.2 * s, 0.5 * s,
            1 * s, 2 * s, 5 * s, 10 * s, 15 * s, 30 * s,
            1 * m, 2 * m, 5 * m, 10 * m, 15 * m, 30 * m,
            1 * h, 2 * h, 3 * h, 6 * h, 12 * h,
            1 * d, 7 * d, 28 * d,
        ])
        dt = t_range / 10
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
        t_min, t_max = ceil(self.t_min / dt) * dt, floor(self.t_max / dt) * dt
        self.plot.xaxis.set_ticks(days(arange(t_min, t_max + 1e-6, dt)))
        setp(self.plot.get_xticklabels(), rotation=90, fontsize=10)
        setp(self.plot.get_yticklabels(), fontsize=10)
        label = self.axis_label
        self.plot.set_ylabel(label)
        self.plot.grid()
        self.figure.tight_layout()  # rect=[0,0.12,1,1]
        self.canvas.draw()

    @property
    def t_min_t_max(self):
        """Minimum and maximum value of time axis"""
        return [self.t_min, self.t_max]

    @property
    def t_min(self):
        """Minimum value of time axis"""
        t_min = self.t_max - self.time_window
        return t_min

    @property
    def t_max(self):
        """Maximum value of time axis"""
        from time import time
        if self.show_latest:
            t_max = time()
        else:
            t_max = self.center_time + self.time_window / 2
        return t_max

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
        self.UpdatePVChoice()
        self.UpdateScrollbar()

    def UpdatePVChoice(self):
        """"""
        self.PVChoice.Items = self.PV_names
        self.PVChoice.Value = self.PV_name

    def OnPVChoice(self, _event):
        """Change the process variable to be plotted"""
        self.PV_name = str(self.PVChoice.Value)
        self.refresh()

    def OnTimeWindowChanged(self, _event):
        """Adjust chart x-axis to refresh the new time range"""
        from time_string import seconds
        from numpy import isnan
        time_window = seconds(self.TimeWindow.Value)
        if not isnan(time_window):
            self.time_window = time_window
        # debug("time window changed: %r" % self.time_window)
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
        thumb_position_fraction = clip((self.t_min - self.start_time) / self.full_time_range, 0, 1)
        page_size_fraction = 0.5 * thumb_size_fraction
        thumb_size = to_int(thumb_size_fraction * time_range)
        thumb_position = to_int(thumb_position_fraction * time_range)
        page_size = to_int(page_size_fraction * time_range)
        # debug("SetScrollbar(%r,%r,%r,%r)" % (thumb_position,thumb_size,time_range,page_size))
        self.TimeFraction.SetScrollbar(thumb_position, thumb_size, time_range, 
                                       page_size, True)

    def get_start_fraction(self):
        position = self.TimeFraction.ThumbPosition
        t_range = max(self.TimeFraction.Range, 1)
        return float(position) / t_range

    def set_start_fraction(self, fraction):
        fraction = max(0, min(fraction, 1))
        t_range = max(self.TimeFraction.Range, 1)
        self.TimeFraction.ThumbPosition = to_int(fraction * t_range)

    start_fraction = property(get_start_fraction, set_start_fraction)

    def get_end_fraction(self):
        position = self.TimeFraction.ThumbPosition
        size = self.TimeFraction.ThumbSize
        end = position + size
        t_range = max(self.TimeFraction.Range, 1.0)
        return float(end) / t_range

    def set_end_fraction(self, fraction):
        fraction = max(0, min(fraction, 1))
        t_range = max(self.TimeFraction.Range, 1)
        size = self.TimeFraction.ThumbSize
        self.TimeFraction.ThumbPosition = to_int(fraction * t_range - size)

    end_fraction = property(get_end_fraction, set_end_fraction)


def days(seconds):
    """Convert a time stamp from seconds since 1 Jan 1970 0:00 UTC to days
    since 1 Jan 1 AD 0:00 localtime
    seconds: scalar or array"""
    # Determine the offset, which his time zone and daylight saving time
    # dependent.
    from numpy import isnan, asarray, nan
    seconds = asarray(seconds)
    t = nanmean(seconds)
    if not isnan(t):
        from datetime import datetime
        from pylab import date2num
        offset = date2num(datetime.fromtimestamp(t)) - t / 86400
    else:
        offset = nan
    return seconds / 86400 + offset


def nanmean(a):
    # Avoid nanmean([]), nanmean([nan]): "RuntimeWarning: Mean of empty slice"
    from numpy import all, isnan, nan, nanmean
    if all(isnan(a)):
        value = nan
    else:
        value = nanmean(a)
    return value


def to_int(x):
    """Try to convert x to an integer number without raising an exception."""
    from numpy import rint
    x = rint(x)
    try:
        x = int(x)
    except (ValueError, TypeError):
        x = 0
    return x


def suppress_matplotlib_debug_messages():
    import logging
    # Loaded backend macosx version unknown.
    # Loaded backend qt5agg version unknown.
    # Loaded backend wxagg version unknown
    # (repeating 13 times)
    logging.getLogger("matplotlib.pyplot").setLevel(logging.WARNING)
    # Matching :family=sans-serif:style=normal:variant=normal:weight=normal:stretch=normal:size=10.0.
    # score(<Font 'cmmi10' (cmmi10.ttf) normal normal 400 normal>) = 10.05
    # (repeating 465 times)
    logging.getLogger("matplotlib.font_manager").setLevel(logging.WARNING)
    logging.getLogger("matplotlib.backends.backend_wx").setLevel(logging.WARNING)


if __name__ == "__main__":
    # import autoreload

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    from redirect import redirect
    redirect(f"{domain_name}.Channel_Archiver_Viewer", level="DEBUG", format=msg_format)

    import wx
    app = wx.GetApp() if wx.GetApp() else wx.App()

    import locale
    locale.setlocale(locale.LC_ALL, "")  # wxPython 4.1.0 sets it to "en-US"

    self = Channel_Archiver_Viewer(domain_name)
    app.MainLoop()
