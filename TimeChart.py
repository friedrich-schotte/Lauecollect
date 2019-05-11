"""Time Chart window
Author: Friedrich Schotte
Date created: 2016-06-23
Date last modified: 2019-05-10
"""
import wx
from logging import debug,warn,info,error
from EditableControls import ComboBox

__version__ = "1.4" # markersize 

class TimeChart(wx.Panel):
    """Time Chart window"""
    name = "TimeChart"
    from persistent_property import persistent_property
    from time import time
    time_window = persistent_property("time_window",60.0) # seconds
    center_time = persistent_property("center_time",time()-30.0) # seconds
    show_latest = persistent_property("show_latest",True)

    def __init__(self,parent=None,title="Chart",object=None,
        t_name="date time",v_name="value",
        axis_label="",refresh_period=1.0,name=None,PV=None,size=(500,500),
        *args,**kwargs):
        """title: string
        object: has attribute given by t_name,y_name
        t_name: e.g. "t_history" or "date time"
        v_name: e.g. "x_history", "y_history" or "value"
        PV: EPICS process variable name, e.g. 'NIH:TEMP.RBV'
        """
        wx.Window.__init__(self,parent,size=size)
        self.title = title
        if object is not None: self.object = object
        self.t_name = t_name
        self.v_name = v_name
        self.axis_label = axis_label
        self.refresh_period = refresh_period
        if name is not None: self.name = name
        self.PV = PV

        # Controls
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
        self.figure = Figure(figsize=(4,3))
        self.canvas = FigureCanvasWxAgg(self,-1,self.figure)

        style = wx.TE_PROCESS_ENTER
        self.PVChoice = ComboBox(self,style=style,size=(120,-1))

        self.TimeFraction = wx.ScrollBar(self)
        self.TimeFraction.SetScrollbar(800,200,100000,100,True)
        # SetScrollbar(position,thumbSize,range,pageSize,refresh)
        # [Arguments misnamed "orientation,position,thumbSize,range,refresh"
        # in WxPython 2.9.1.1]

        choices = ["10s","30s","1min","2min","5min","10min","30min",
                   "1h","2h","6h","12h","1d","2d","5d"]
        self.TimeWindow = ComboBox(self,style=style,choices=choices)

        # Callbacks
        self.Bind(wx.EVT_COMBOBOX,self.OnPVChoice,self.PVChoice)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnPVChoice,self.PVChoice)

        events = [
            wx.EVT_SCROLL_TOP,wx.EVT_SCROLL_BOTTOM,
            wx.EVT_SCROLL_LINEUP,wx.EVT_SCROLL_LINEDOWN,
            wx.EVT_SCROLL_PAGEUP,wx.EVT_SCROLL_PAGEDOWN,
            wx.EVT_SCROLL_THUMBRELEASE,
            wx.EVT_SCROLL_THUMBTRACK,
        ]
        for e in events: self.Bind(e,self.OnTimeFractionChanged,self.TimeFraction)
        self.Bind(wx.EVT_COMBOBOX,self.OnTimeWindowChanged,self.TimeWindow)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnTimeWindowChanged,self.TimeWindow)
        self.Bind(wx.EVT_WINDOW_DESTROY,self.OnDestroy,self)

        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.canvas,proportion=1,flag=wx.EXPAND)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALIGN_CENTER_VERTICAL
        hbox.Add(self.PVChoice,proportion=1,flag=flag)
        hbox.Add(self.TimeFraction,proportion=2,flag=wx.EXPAND|flag)
        hbox.Add(self.TimeWindow,flag=flag)
        
        vbox.Add(hbox,flag=wx.EXPAND)
        self.SetSizer(vbox)
        self.SetSizeHints(minW=-1,minH=200,maxW=-1,maxH=-1)
        self.Fit()
        
        # Refresh
        self.attributes = [self.t_name,self.v_name,"start_time"]
        from time import time
        self.values = {self.t_name:[],self.v_name:[],"start_time":time()-60}
        ##self.values = dict([(n,[]) for n in self.attributes])
        self.old_values = self.values

        from threading import Thread
        self.refresh_thread = Thread(target=self.refresh_background,
            name=self.name+".refresh")
        self.refreshing = False

        from wx.lib.newevent import NewEvent
        self.EVT_THREAD = NewEvent()[1]
        self.Bind(self.EVT_THREAD,self.OnUpdate)
        self.thread = Thread(target=self.keep_updated,
            name=self.name+".keep_updated")
        self.thread.start()

        self.UpdateControls()

        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer,self.timer)
        self.timer.Start(1000,oneShot=True)

    def get_object(self):
        """logfile object"""
        if self.PV is not None:
            from channel_archiver import channel_archiver
            object = channel_archiver.logfile(self.PV)
        else: object = self.__object__
        return object
    def set_object(self,object):
        self.__object__ = object
    object = property(get_object,set_object)

    __object__ = None

    def OnDestroy(self,event):
        """"""
        info("TimeChart: %s destroyed" % self.name)

    def OnTimer(self,event):
        """Perform periodic updates"""
        try: self.UpdateControls()
        except Exception,msg:
            import traceback
            error("TimeChart: %s\n%s" % (msg,traceback.format_exc()))
        self.timer.Start(1000,oneShot=True)        

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        ##debug("TimeChart: keep_updated: refresh_period %r" % self.refresh_period)
        from time import time
        from sleep import sleep # interruptible sleep
        import traceback
        while True:
            try:
                sleep(self.refresh_period)
                self.update()
            except wx.PyDeadObjectError: break
            except Exception,msg:
                error("TimeChart: %s\n%s" % (msg,traceback.format_exc()))

    def update(self):
        """Retrigger fresh of chart if data changed."""
        # Needs to be called from background thread.
        if self.Shown:
            self.update_data()
            if self.data_changed: 
                event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
                # call OnUpdate in GUI thread
                wx.PostEvent(self.EventHandler,event)

    def refresh(self):
        """Force update"""
        from threading import Thread
        if not self.refreshing and self.Shown:
            self.refresh_thread = Thread(target=self.refresh_background,
                name=self.name+".refresh")
            self.refreshing = True
            self.refresh_thread.start()

    def refresh_background(self):
        """Force update"""
        self.update_data()
        if self.data_changed: 
            event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
            wx.PostEvent(self.EventHandler,event) # call OnUpdate in GUI thread
        self.refreshing = False

    def update_data(self):
        """Retreive status information"""
        from numpy import copy
        self.old_values = dict((n,copy(self.values[n])) for n in self.values) 
        ##for n in self.attributes: self.values[n] = copy(getattr(self.object,n))
        self.values[self.t_name],self.values[self.v_name] = \
            self.object.history(self.t_name,self.v_name,
            time_range=self.tmin_tmax)
        self.values["start_time"] = self.object.start_time

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        from numpy import array_equal
        if sorted(self.values.keys()) != sorted(self.old_values.keys()):
            debug("data changed? keys changed")
            changed = True
        else:
            changed = not all([array_equal(self.values[a],self.old_values[a]) \
                for a in self.values])
        ##debug("data changed: %r" % changed)
        return changed

    def OnUpdate(self,event=None):
        """Handle data changed"""
        self.RefreshChart()

    def RefreshChart(self):
        """Update the chart"""
        ##debug("TimeChart: RefreshChart")
        from pylab import setp,DateFormatter
        from numpy import isnan,nanmax,nanmin,ptp,ceil,floor,array,arange
        t_data,v_data = self.values[self.t_name],self.values[self.v_name]
        n = min(len(t_data),len(v_data))
        t_data,v_data = t_data[0:n],v_data[0:n]
        date = days(t_data)
        ##self.figure.subplots_adjust(bottom=0.4) ##,left=0.2,right=0.97,top=0.92)
        self.plot = self.figure.add_subplot(1,1,1)
        self.plot.clear()
        self.plot.plot(date,v_data,'.',color=[0,0,1],markersize=1)
        self.plot.set_xlim(days(self.tmin_tmax))
        trange = ptp(self.tmin_tmax)
        s,m,h,d = 1,60,3600,86400
        steps = array([
            0.1*s,0.2*s,0.5*s,
            1*s,2*s,5*s,10*s,15*s,30*s,
            1*m,2*m,5*m,10*m,15*m,30*m,
            1*h,2*h,3*h,6*h,12*h,
            1*d,7*d,28*d,
        ])
        dt = trange/10
        dt = max(steps[steps <= dt])
        if dt < 1*m: date_format = "%H:%M:%S"
        elif dt < 1*h: date_format = "%H:%M"
        elif dt < 1*d: date_format = "%H"
        else: date_format = "%d %H"
        self.plot.xaxis.set_major_formatter(DateFormatter(date_format))
        self.plot.xaxis_date()
        tmin,tmax = ceil(self.tmin/dt)*dt,floor(self.tmax/dt)*dt
        self.plot.xaxis.set_ticks(days(arange(tmin,tmax+1e-6,dt)))
        setp(self.plot.get_xticklabels(),rotation=90,fontsize=10)
        setp(self.plot.get_yticklabels(),fontsize=10)
        label = self.axis_label
        self.plot.set_ylabel(label)
        self.plot.grid()
        self.figure.tight_layout() ##rect=[0,0.12,1,1]
        self.canvas.draw()

    @property
    def tmin_tmax(self):
        """Minimum and maximum value of time axis"""
        return [self.tmin,self.tmax]

    @property
    def tmin(self):
        """Minimum value of time axis"""
        from time import time
        tmin = self.tmax-self.time_window
        return tmin

    @property
    def tmax(self):
        """Maximum value of time axis"""
        from time import time
        if self.show_latest: tmax = time()
        else: tmax = self.center_time + self.time_window/2
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
        if not dt > 1.0: dt = 1.0
        return dt

    def UpdateControls(self):
        """Make sure control are up to date"""
        from time_string import time_string
        text = time_string(self.time_window)
        if self.TimeWindow.Value != text: self.TimeWindow.Value = text
        self.UpdatePVChoice()
        self.UpdateScrollbar()

    def UpdatePVChoice(self):
        """"""
        from channel_archiver import channel_archiver
        if self.PV: self.PVChoice.Value = self.PV
        else: self.PVChoice.Value = self.object.name
        self.PVChoice.Items = channel_archiver.PVs

    def OnPVChoice(self,event):
        """Change the process variable to be plotted"""
        self.PV = str(self.PVChoice.Value)
        self.refresh()

    def OnTimeWindowChanged(self,event):
        """Adjust chart x-axis to reflesh the new time range"""
        from time_string import seconds
        self.time_window = seconds(self.TimeWindow.Value)
        ## debug("TimeChart: time window changed: %r" % self.time_window)
        self.UpdateScrollbar()
        self.refresh()

    def OnTimeFractionChanged(self,event):
        """Called when time window position is changed"""
        debug("start %r, end %r" % (self.start_fraction,self.end_fraction))
        self.show_latest = True if self.end_fraction >= 1 else False
        debug("show latest %r" % self.show_latest)
        center_fraction = (self.start_fraction+self.end_fraction)/2
        self.center_time = self.start_time + self.full_time_range * center_fraction
        from time_string import date_time
        debug("center time %r" % date_time(self.center_time))
        self.refresh()

    def OnResize(self,event):
        self.RefreshChart()
        event.Skip() # call default handler

    def UpdateScrollbar(self):
        from numpy import rint,clip
        range = self.TimeFraction.Range
        thumbsize_fraction = clip(self.time_window/self.full_time_range,0,1)
        thumb_position_fraction = clip((self.tmin - self.start_time)/self.full_time_range,0,1)
        pagesize_fraction = 0.5*thumbsize_fraction
        thumbsize = int(rint(thumbsize_fraction*range))
        thumb_position = int(rint(thumb_position_fraction*range))
        pagesize = int(rint(pagesize_fraction*range))
        ##debug("SetScrollbar(%r,%r,%r,%r)" % (thumb_position,thumbsize,range,pagesize))
        self.TimeFraction.SetScrollbar(thumb_position,thumbsize,range,pagesize,
            True)

    def get_start_fraction(self):
        position = self.TimeFraction.ThumbPosition
        range = max(self.TimeFraction.Range,1)
        return float(position)/range
    def set_start_fraction(self,fraction):
        fraction = max(0,min(fraction,1))
        range = max(self.TimeFraction.Range,1)
        self.TimeFraction.ThumbPosition = rint(fraction*range) 
    start_fraction = property(get_start_fraction,set_start_fraction)

    def get_end_fraction(self):
        from numpy import rint
        position = self.TimeFraction.ThumbPosition
        size = self.TimeFraction.ThumbSize
        end = position+size
        range = max(self.TimeFraction.Range,1.0)
        return float(end)/range
    def set_end_fraction(self,fraction):
        from numpy import rint
        fraction = max(0,min(fraction,1))
        range = max(self.TimeFraction.Range,1)
        size = self.TimeFraction.ThumbSize
        self.TimeFraction.ThumbPosition = rint(fraction*range) - size 
    end_fraction = property(get_end_fraction,set_end_fraction)

def days(seconds):
    """Convert a time stamp from seconds since 1 Jan 1970 0:00 UTC to days
    since 1 Jan 1 AD 0:00 localtime
    seconds: scalar or array"""
    # Determine the offset, which his time zone and daylight saving time
    # dependent.
    from numpy import mean,isnan,asarray,nan
    seconds = asarray(seconds)
    try: t = mean(seconds[~isnan(seconds)])
    except: t = nan
    if not isnan(t):
        from datetime import datetime; from pylab import date2num
        offset = date2num(datetime.fromtimestamp(t)) - t/86400
    else: offset = nan
    return seconds/86400 + offset

from Panel import BasePanel
class ArchiveViewer(BasePanel):
    name = "ArchiveViewer"
    title = "Archive Viewer"
    standard_view = ["Data"]
    def __init__(self,PV,parent=None):        
        from channel_archiver import channel_archiver
        log = channel_archiver.logfile(PV)
        parameters = [
            [[TimeChart,"Data"],{"PV":PV,"refresh_period":2}],
        ]
        BasePanel.__init__(self,
            name=self.name,
            title=self.title,
            icon="Archiver",
            parent=parent,
            parameters=parameters,
            standard_view=self.standard_view,
            refresh=False,
            live=False,
        )

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/TimeChart.log"
    logging.basicConfig(level=logging.DEBUG,
        ##filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s")
    app = wx.App(redirect=False)
    panel = ArchiveViewer('NIH:TEMP.RBV')
    self = panel.controls[0]
    app.MainLoop()
