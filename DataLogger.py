#!/usr/bin/env python
"""
Monitors a counter and displays a time chart.
Author: Friedrich Schotte, Jun 26, 2011 - Oct 4, 2017
"""
from __future__ import with_statement,division
from numpy import *
from thread import start_new_thread
from instrumentation import *
from logging import debug,warn
from normpath import normpath
from time_string import date_time,timestamp,time_string,seconds

__version__ = "1.4.4" # main: name argument

# Default settings
naverage = 1
default_logfile = "Test-1.log"
#default_logfile = "//mx340hs/data/anfinrud_1510/Logfiles/Temperature-1.log"
counter_name = "temperature_controller.readT"
waiting_time = 0.3 # delay between measurements

# Initialization
active = False # collecting data?
cancelled = False


def counter_value():
    """Current value of a counter, motor or EPICS record"""
    return value(counter_name)

def counter_unit():
    """Unit symbol of a counter, motor or EPICS record"""
    return unit(counter_name)

def counter_description():
    """Descriptive comment of a counter, motor or EPICS record"""
    return description(counter_name)

def value(name):
    """The value of a process variable, if name is a process variable.
    Otherwise, name is assumed to be the name of a Python object and
    its 'value' property is used.
    name: string, name of EPICS process variable or name of Python variable
    """
    from CA import caget
    try: x = eval(name)
    except: return tofloat(caget(name))
    return tofloat(getattr(x,"value",x))

def description(name):
    """Descriptive comment of a counter, motor or EPICS record
    name: string, name of EPICS process variable or name of Python variable
    """
    from os.path import splitext
    desc = ""
    if desc == "":
        try: desc = eval(name).name
        except: pass
    if desc == "":
        try: desc = eval(splitext(name)[0]).name
        except: pass
    if desc == "":
        try: desc = eval(splitext(name)[0]).DESC
        except: pass
    return desc

def unit(name):
    """Unit symbol of a counter, motor or EPICS record
    name: string, name of EPICS process variable or name of Python variable
    """
    from os.path import splitext
    unit = ""
    if unit == "":
        try: unit = eval(name).unit
        except: pass
    if unit == "":
        try: unit = eval(splitext(name)[0]).unit
        except: pass
    if unit == "":
        try: unit = eval(splitext(name)[0]).EGU
        except: pass
    return unit

def tofloat(x):
    """Like builtin 'float', but do not raise an exception, return 'nan'
    instead."""
    try: return float(x)
    except: return nan

def measure():
    from numpy import nan,isnan
    from time import sleep
    while not cancelled:
        while active:
            last_measurement = log.value[-1] if len(log.value) > 0 else nan
            measurement = counter_value()
            while measurement == last_measurement or isnan(measurement):
                if not active: status("not active"); break
                if measurement == last_measurement and not isnan(measurement):
                    status("Waiting for update...")
                sleep(waiting_time)
                measurement = counter_value()
            if not active: status("not active"); break
            status ("Measuring %s" % tostr(measurement))
            log.append(measurement)
            sleep(waiting_time)
        sleep(waiting_time)

def watch_logfile():
    """Check whether logfile is beeing update and reload it if needed."""
    from time import sleep
    while not cancelled:
        log.read_file()
        sleep(2.5)
    

class Log(object):
    """Stores time-stamped data"""
    def __init__(self):
        self.filename = normpath(default_logfile)
        self.loaded_filename = ""
        self.timestamp = 0
        self.T = zeros(0)
        self.VALUE = zeros(0)
        from thread import allocate_lock
        self.lock = allocate_lock()

    def append(self,value):
        from time import time
        from os import makedirs
        from os.path import exists,dirname,getmtime

        # A measurement that is a duplicate of the last is probably old.
        self.read_file()
        if len(self.VALUE) > 0 and value == self.VALUE[-1]: return

        t = time()
        self.T = concatenate((self.T,[t]))
        self.VALUE = concatenate((self.VALUE,[value]))
        
        if not exists(self.filename):
            if not exists(dirname(self.filename)): makedirs(dirname(self.filename))
            logfile = file(self.filename,"ab")
            logfile.write("#date time\tvalue[%s]\n" % counter_unit())
        logfile = file(self.filename,"ab")
        logfile.write("%s\t%s\n" % (date_time(t),tostr(value)))
        logfile.close()
        self.timestamp = getmtime(self.filename)
        ##debug("updated log file: %.0f" % self.timestamp)

    def read_file(self):
        "Check log file for changes and reread it"
        with self.lock: # Allow only one thread at a time inside this function.
            from os.path import exists,getmtime
            from table import table
            
            if not exists(self.filename):
                ##debug("file %r not found" % self.filename)
                self.T,self.VALUE = zeros(0),zeros(0)
                self.timestamp = 0
                self.loaded_filename = ""
            else: 
                current_timestamp = getmtime(self.filename)
                if abs(current_timestamp - self.timestamp) > 2 or \
                    self.filename != self.loaded_filename:
                    if self.timestamp != 0:
                        dt = (current_timestamp - self.timestamp)
                        ##debug ("log file changed by %g s" % dt)
                    ##debug("Reading %s" % self.filename)
                    status("Reading %s..." % self.filename)
                    try:
                        logfile = table(self.filename,separator="\t")
                        self.T = array(map(timestamp,logfile.date_time))
                        self.VALUE = logfile.value
                        self.timestamp = current_timestamp
                        self.loaded_filename = self.filename
                    except Exception,details:
                        ##debug("%s unreadable: %s" % (self.filename,details))
                        if self.loaded_filename != self.filename:
                            self.T,self.VALUE = zeros(0),zeros(0)
                            self.timestamp = current_timestamp
                            self.loaded_filename = self.filename
                    status("Reading %s... done" % self.filename)

    def get_t(self):
        """Timestamps"""
        return self.T
    t = property(get_t)
    
    def get_value(self):
        """Recorded values"""
        return self.VALUE
    value = property(get_value)
        
import wx

class DataLogger (wx.Frame):
    show_end = True
    def __init__(self,name=""):
        """name: defines settings filename."""
        if name == "": name = type(self).__name__
        self.name = name
        ##debug("DataLogger: name: %r" % self.name)
        wx.Frame.__init__(self,parent=None)
        
        # Icon
        from Icon import SetIcon
        SetIcon(self,"Data Logger")
        
        # Menus
        self.title = self.name
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append (101,"Logfile...\tCtrl+O",
            "Where to store the timing history files to watch.")
        self.Bind (wx.EVT_MENU,self.OnSelectLogfile,id=101)
        menu.Append (121,"E&xit","Closes this window.")
        self.Bind (wx.EVT_MENU,self.OnExit,id=121)
        menuBar.Append (menu,"&File")
        self.Bind(wx.EVT_CLOSE,self.OnExit)
        menu = wx.Menu()
        menu.Append (402,"&Options...","Parameters")
        self.Bind (wx.EVT_MENU,self.OnOptions,id=402)
        menuBar.Append (menu,"&Options")
        menu = wx.Menu()
        menu.Append (501,"&About...","Version information")
        self.Bind (wx.EVT_MENU,self.OnAbout,id=501)
        menuBar.Append (menu,"&Help")
        self.SetMenuBar (menuBar)
        # Controls
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
        self.figure = Figure(figsize=(4,3))
        self.canvas = FigureCanvasWxAgg(self,-1,self.figure)
        self.figure.subplots_adjust(bottom=0.2)
        self.plot = self.figure.add_subplot(1,1,1)
        self.active = wx.ToggleButton(self,label="Active")
        self.Bind(wx.EVT_TOGGLEBUTTON,self.OnActive,self.active)
        self.TimeFraction = wx.ScrollBar(self)
        self.TimeFraction.SetScrollbar(0,200,1000,100,True)
        # SetScrollbar(position,thumbSize,range,pageSize,refresh)
        # [Arguments misnamed "orientation,position,thumbSize,range,refresh"
        # in WxPython 2.9.1.1]
        self.TimeFraction.DefaultColour = self.TimeFraction.BackgroundColour 
        events = [wx.EVT_SCROLL_TOP,wx.EVT_SCROLL_BOTTOM,
                  wx.EVT_SCROLL_LINEUP,wx.EVT_SCROLL_LINEDOWN,
                  wx.EVT_SCROLL_PAGEUP,wx.EVT_SCROLL_PAGEDOWN,
                  wx.EVT_SCROLL_THUMBRELEASE]
        for e in events: self.Bind(e,self.OnTimeFractionChanged,self.TimeFraction)
        choices = ["10s","30s","1min","2min","5min","10min","30min",
                   "1h","2h","6h","12h","1d","2d","5d"]
        style = wx.TE_PROCESS_ENTER
        self.TimeWindow = wx.ComboBox(self,style=style,choices=choices)
        self.Bind(wx.EVT_COMBOBOX,self.OnTimeWindowChanged,self.TimeWindow)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnTimeWindowChanged,self.TimeWindow)
        self.CreateStatusBar()
        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.canvas,proportion=1,flag=wx.EXPAND)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.active,proportion=0)
        hbox.Add(self.TimeFraction,proportion=1,flag=wx.EXPAND)
        vbox.Add(hbox,proportion=0,flag=wx.EXPAND)
        hbox.Add(self.TimeWindow,proportion=0)
        self.SetSizer(vbox)
        self.Fit()
        
        # Default settings.
        self.time_window = 60 # seconds
        self.max_value = nan
        self.min_value = nan
        self.waiting_time = 0.3
        self.reject_outliers = False
        self.outlier_cutoff = 2.5
        self.show_statistics = True
        self.average_count = 1
        self.Size = 640,480

        # Restore last saved settings.
        self.settings = ["counter_name","Size","logfile",
            "average_count","max_value","min_value","end_fraction","reject_outliers",
            "outlier_cutoff","show_statistics","time_window"]
        self.update_settings()

        # Initialization
        self.npoints = 0

        self.Show()
        self.update()

        start_new_thread (measure,())
        start_new_thread (watch_logfile,())

    def get_counter_name(self): return counter_name
    def set_counter_name(self,new_counter_name):
        global counter_name
        counter_name = str(new_counter_name)
    counter_name = property(get_counter_name,set_counter_name)

    def get_logfile(self): return log.filename
    def set_logfile(self,new_logfile):
        log.filename = normpath(str(new_logfile))
    logfile = property(get_logfile,set_logfile)

    def get_average_count(self): return naverage
    def set_average_count(self,value):
        global naverage; naverage = max(1,toint(value))
    average_count = property(get_average_count,set_average_count)

    def get_waiting_time(self): return waiting_time
    def set_waiting_time(self,value):
        global waiting_time; waiting_time = value
    waiting_time = property(get_waiting_time,set_waiting_time)

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
        position = self.TimeFraction.ThumbPosition
        size = self.TimeFraction.ThumbSize
        end = position+size
        range = max(self.TimeFraction.Range,1.0)
        return float(end)/range
    def set_end_fraction(self,fraction):
        fraction = max(0,min(fraction,1))
        range = max(self.TimeFraction.Range,1)
        size = self.TimeFraction.ThumbSize
        self.TimeFraction.ThumbPosition = rint(fraction*range) - size 
    end_fraction = property(get_end_fraction,set_end_fraction)

    def get_time_window(self):
        value = seconds(self.TimeWindow.Value)
        debug("Read TimeWindow %r: %g s" % (self.TimeWindow.Value,value))
        return value
    def set_time_window(self,value):
        text = time_string(value)
        if text == "": text = "1min"
        self.TimeWindow.Value = text
        debug("Set TimeWindow %g s: %r" % (value,self.TimeWindow.Value))
    time_window = property(get_time_window,set_time_window)

    def update(self,event=None):
        # Do some work.
        self.refresh()
        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(1000,oneShot=True)

    def refresh(self,event=None):
        "Generate the plot"
        # Update window title.
        title = self.title+" - "+self.logfile
        if self.Title != title: self.Title = title
        # Update the chart.
        if len(log.t) != self.npoints: self.refresh_chart()
        self.npoints = len(log.t)
        # Update status bar.
        self.SetStatusText(status_text)

    def UpdateTimeFraction(self):
        """Adjust the thumb size of the scroll bar"""
        t,value = self.raw_data
        if len(t) > 0: tmin,tmax = nanmin(t),nanmax(t)
        else: tmin,tmax = nan,nan
        position = self.TimeFraction.ThumbPosition
        thumb_size = self.TimeFraction.ThumbSize
        page_size = self.TimeFraction.PageSize
        range = max(self.TimeFraction.Range,1)
        dt = tmax-tmin if tmax != tmin else 1
        ##debug("full time range dt=%r s" % dt)
        # Set the step size such that the scroll bar move by half the time
        # window when using the cursor keys.
        new_range = dt/(self.time_window/10.)
        # The thumb size represents the time window as fraction of the full
        # range.
        new_thumb_size = clip(self.time_window/dt*new_range,1,new_range)
        center_fraction = (position+0.5*thumb_size)/range
        new_position = center_fraction*new_range - 0.5*new_thumb_size
        new_position = toint(rint(new_position))
        new_thumb_size = max(toint(rint(new_thumb_size)),1)
        new_page_size = new_thumb_size
        page_size = max(toint(rint(page_size)),1)
        new_range = max(toint(rint(new_range)),1)
        if self.show_end: new_position = new_range-new_thumb_size
        if new_position == position and new_thumb_size == thumb_size and \
            new_page_size == page_size and new_range == range: return
        ##debug("UpdateTimeFraction: new position %r, thumb_size %r, page size %r, range %r" %
        ##    (new_position,new_thumb_size,new_page_size,new_range))
        if not (isnan(new_position) or isnan(new_thumb_size)
            or isnan(new_page_size)):
            self.TimeFraction.SetScrollbar(new_position,new_thumb_size,
                new_range,new_page_size,True)
        position = self.TimeFraction.ThumbPosition
        thumb_size = self.TimeFraction.ThumbSize
        page_size = self.TimeFraction.PageSize
        range = self.TimeFraction.Range
        ##debug("UpdateTimeFraction: position %r, thumb_size: %r, page size %r, range %r" %
        ##    (position,thumb_size,page_size,range))

    def refresh_chart(self):
        # Generate a chart.
        from pylab import setp,DateFormatter
        t,value = self.data
        date = days(t)
        self.figure.subplots_adjust(bottom=0.2)
        self.plot = self.figure.add_subplot(1,1,1)
        self.plot.clear()
        if self.show_statistics and len(value) > 0:
            unit = counter_unit()
            def nanmean(x): return nansum(x)/sum(~isnan(x))
            def nanstd(x): return std(x[~isnan(x)])
            mean = nanmean(value)
            sdev = nanstd(value)
            min = nanmin(value)
            max = nanmax(value)
            text  = "mean %.3f %s\n" % (mean,unit)
            text += "sdev %.3f %s\n" % (sdev,unit)
            text += "min  %.3f %s\n" % (min,unit)
            text += "max  %.3f %s\n" % (max,unit)
            text += "pkpk %.3f %s\n" % (max-min,unit)
            self.plot.text(0.02,0.97,text,verticalalignment="top",fontsize="small",
                transform=self.plot.transAxes)
            # Annotate chart
            t1,t2 = days(self.trange)
            self.plot.plot((t1,t2),(mean,mean),"-",color=[1,0.2,0.2])
            self.plot.plot((t1,t2),(mean+sdev,mean+sdev),"-",color=[1,0.6,0.6])
            self.plot.plot((t1,t2),(mean-sdev,mean-sdev),"-",color=[1,0.6,0.6])
        if not all(isnan(value)):
            ##debug("plotting %r,%r" % (date[0:5],value[0:5]))
            self.plot.plot(date,value,'.',color=[0,0,1])
        ##else: debug("nothing plotted")
        trange = self.tmax-self.tmin
        if trange <= 5*60: date_format = "%H:%M:%S"
        elif trange < 24*60*60: date_format = "%H:%M"
        else: date_format = "%b %d %H:%M"
        ##debug("date_format=%r" % date_format)
        self.plot.xaxis.set_major_formatter(DateFormatter(date_format))
        self.plot.set_xlabel("time")
        self.plot.xaxis_date()
        setp(self.plot.get_xticklabels(),rotation=90,fontsize=10)
        label = counter_description()
        if counter_unit(): label += "["+counter_unit()+"]"
        self.plot.set_ylabel(label)
        self.plot.grid()
        if not isnan(self.min_value): self.plot.set_ylim(ymin=self.min_value)
        if not isnan(self.max_value): self.plot.set_ylim(ymax=self.max_value)
        if not isnan(self.tmin): self.plot.set_xlim(xmin=days(self.tmin))
        if not isnan(self.tmax): self.plot.set_xlim(xmax=days(self.tmax))
        self.canvas.draw()
        self.UpdateTimeFraction()
        R,G,B = self.TimeFraction.DefaultColour
        if self.show_end: R,G,B = rint(R*0.9),rint(G*0.9),rint(B*0.9)
        if self.TimeFraction.BackgroundColour != (R,G,B): 
            self.TimeFraction.BackgroundColour = R,G,B
            self.TimeFraction.Refresh()

    def get_data(self):
        """Data points to be plotted
        returns (t,value)
        t: time stamp in seconds since 1 Jan 1970 00:00 UST
        value: values"""
        t,value = self.raw_data
        valid = ~isnan(t) & ~isnan(value)
        t,value = t[valid],value[valid]
        # Average data.
        if self.average_count > 1:
            n = self.average_count
            N = toint(ceil(float(len(value))/n))
            T,VALUE = zeros(N),zeros(N)
            for i in range(0,N):
                T[i] = average(t[i*n:(i+1)*n])
                VALUE[i] = self.average(value[i*n:(i+1)*n])
            t,value = T,VALUE
        # Restrict the time range plotted according to the time window position
        # control.
        if len(t) > 0:
            selected = (self.tmin <= t) & (t <= self.tmax)
            t,value = t[selected],value[selected]
        return t,value
    data = property(get_data)

    def get_trange(self):
        """Minimum and maximum of x axis, as pair of values"""
        t,value = self.raw_data
        f1,f2 = self.start_fraction,self.end_fraction
        if self.show_end:
            df = f2-f1
            f2 = 1
            f1 = f2-df
        ##debug("range %r to %r" % (f1,f2))
        fc = (f1+f2)/2
        if len(t) > 0:
            tmin,tmax = nanmin(t),nanmax(t)
            if fc < 0.5:
                t1 = tmin + f1*(tmax-tmin)
                t2 = t1 + self.time_window
                if t2 > tmax: t2 = tmax
            else:
                t2 = tmin + f2*(tmax-tmin)
                t1 = t2 - self.time_window
                if t1 < tmin: t1 = tmin
        else: t1,t2 = 0,600
        return array([t1,t2])
    trange = property(get_trange)

    def get_tmin(self): return self.trange[0]
    tmin = property(get_tmin)

    def get_tmax(self): return self.trange[1]
    tmax = property(get_tmax)

    def average(self,data):
        if not self.reject_outliers: return average(data)
        while True:
            i = abs(data-average(data)) < self.outlier_cutoff*std(data)
            if sum(i) == len(data): break
            data = data[i]
        return average(data)
        
    def get_raw_data(self):
        """Data points to be plotted
        returns (t,value)
        t: time stamp in seconds since 1 Jan 1970 00:00 UST
        value: values"""
        t,value = log.t,log.value
        n = min(len(t),len(value))
        return t[:n],value[:n]
    raw_data = property(get_raw_data)
        
    def OnSelectLogfile(self,event):
        """Called from menu File/Watch Directory...
        Let the user pick the directory which contains all the log files to watch.
        """
        from os.path import basename,dirname
        dlg = wx.FileDialog(self,"Select Logfile",
            style=wx.SAVE,
            defaultFile=basename(self.logfile),defaultDir=dirname(self.logfile),
            wildcard="Text files (*.txt;*.log)|*.txt;*.log|"
            "All Files (*.*)|*.*")
        # ShowModal pops up a dialog box and returns control only after the user
        # has selects OK or Cancel.
        OK = (dlg.ShowModal() == wx.ID_OK) 
        dlg.Destroy()
        if not OK: return
        self.logfile = str(dlg.GetPath())

    def OnExit(self,event):
        "Called on File/Exit or when the windows's close button is clicked"
        global active,cancelled
        active = False
        cancelled = True
        self.Destroy()

    def OnOptions(self,event):
        "Change parameters controlling the centering procedure."
        dlg = Options(self)
        dlg.CenterOnParent()
        dlg.Show()

    def OnAbout(self,event):
        "Called from the Help/About"
        from os.path import basename
        from inspect import getfile
        filename = getfile(lambda x: None)
        info = basename(filename)+" "+__version__+"\n"+__doc__
        dlg = wx.MessageDialog(self,info,"About",wx.OK|wx.ICON_INFORMATION)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()

    def OnTimeFractionChanged(self,event):
        """Called when time window position is changed"""
        ##debug("Time fraction changed: end %g" % self.end_fraction)
        self.show_end = self.end_fraction >= 1
        self.refresh_chart()

    def OnTimeWindowChanged(self,event):
        """Called when time window width is changed"""
        debug("Time window changed: %r" % self.time_window)
        self.time_window = self.time_window # normalizes displayed value
        self.refresh_chart()

    def OnActive(self,event):
        """called when 'Active' buttoin is toggled"""
        global active
        active = self.active.Value

    def update_settings(self,event=None):
        """Monitors the settings file and reloads it if it is updated."""
        from os.path import exists
        from os import makedirs
        if not hasattr(self,"settings_timestamp"): self.settings_timestamp = 0
        if not hasattr(self,"saved_state"): self.saved_state = self.State
        
        if self.saved_state != self.State or not exists(self.settings_file()):
            if not exists(self.settings_dir()): makedirs(self.settings_dir())
            ##debug("writing %r" % self.settings_file())
            file(self.settings_file(),"wb").write(self.State)
            self.settings_timestamp = mtime(self.settings_file())
            self.saved_state = self.State
        elif mtime(self.settings_file()) != self.settings_timestamp:
            if exists(self.settings_file()):
                ##debug("reading %r" % self.settings_file())
                self.State = file(self.settings_file()).read()
            self.settings_timestamp = mtime(self.settings_file())
            self.saved_state = self.State

        # Relaunch this procedure after 2 s
        self.settings_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update_settings,self.settings_timer)
        self.settings_timer.Start(2000,oneShot=True)

    def GetState(self):
        state = ""
        for attr in self.settings:
            line = attr+" = "+tostr(eval("self."+attr))
            state += line+"\n"
        return state
    def SetState(self,state):
        ##debug("SetState %r" % state)
        for line in state.split("\n"):
            line = line.strip(" \n\r")
            if line != "":
                try: exec("self."+line)
                except: warn("ignoring "+line); pass
        if hasattr(self,"logfile"):
            ##debug("logfile %r" % self.logfile)
            self.logfile = normpath(self.logfile)
            ##debug("logfile %r" % self.logfile)
    State = property(GetState,SetState)

    def settings_file(self):
        """pathname of the file used to store persistent parameters"""
        return self.settings_dir()+"/"+self.name+"_settings.py"

    def settings_dir(self):
        """pathname of the file used to store persistent parameters"""
        from os.path import dirname
        path = module_dir()+"/settings"
        return path


class Options (wx.Dialog):
    "Allows the use to configure camera properties"
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Options")
        # Controls
        style = wx.TE_PROCESS_ENTER
        self.Counter = wx.TextCtrl (self,size=(80,-1),style=style)
        self.Max = wx.TextCtrl (self,size=(80,-1),style=style)
        self.Min = wx.TextCtrl (self,size=(80,-1),style=style)
        self.ShowStatistics = wx.Choice (self,size=(80,-1),choices=["Yes","No"])
        self.AverageCount = wx.TextCtrl (self,size=(80,-1),style=style)
        self.RejectOutliers = wx.Choice (self,size=(80,-1),choices=["Yes","No"])
        self.OutlierCutoff = wx.TextCtrl (self,size=(80,-1),style=style)
        self.WaitingTime = wx.TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_CHOICE,self.OnEnter)

        # Layout
        layout = wx.BoxSizer()
        grid = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        
        label = "Counter:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Counter,flag=flag)

        label = "Vertical scale upper limit:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Max,flag=flag)

        label = "Vertical scale lower limit:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Min,flag=flag)

        label = "Show Statistics:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.ShowStatistics,flag=flag)

        label = "Average count:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.AverageCount,flag=flag)

        label = "Reject Outliers:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.RejectOutliers,flag=flag)

        label = "Outlier Cutoff:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.OutlierCutoff,flag=flag)

        label = "Waiting Time:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.WaitingTime,flag=flag)

        # Leave a 10-pixel wide space around the panel.
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self):
        self.Counter.Value = self.Parent.counter_name
        self.Min.Value = tostr(self.Parent.min_value).replace("nan","auto")
        self.Max.Value = tostr(self.Parent.max_value).replace("nan","auto")
        self.ShowStatistics.StringSelection = "Yes" if self.Parent.show_statistics else "No"
        self.AverageCount.Value = str(self.Parent.average_count)
        self.RejectOutliers.StringSelection = "Yes" if self.Parent.reject_outliers else "No"
        self.OutlierCutoff.Value = str(self.Parent.outlier_cutoff)
        self.WaitingTime.Value = "%s s" % tostr(self.Parent.waiting_time)

    def OnEnter(self,event):
        self.Parent.counter_name = self.Counter.Value
        try: self.Parent.min_value = eval(self.Min.Value)
        except: self.Parent.min_value = nan
        try: self.Parent.max_value = eval(self.Max.Value)
        except: self.Parent.max_value = nan
        self.Parent.show_statistics = (self.ShowStatistics.StringSelection == "Yes")
        try: self.Parent.average_count = int(eval(self.AverageCount.Value))
        except: pass
        self.Parent.reject_outliers = (self.RejectOutliers.StringSelection == "Yes")
        try: self.Parent.outlier_cutoff = float(eval(self.OutlierCutoff.Value))
        except: pass
        try: self.Parent.waiting_time = eval(self.WaitingTime.Value.rstrip("s"))
        except: pass

        self.update()
        self.Parent.refresh_chart()

def status(text):
    "Display an informational message in the status bar"
    global status_text
    status_text = text

status_text = ""

def remote_shutter_state():
    """Tell the status of 'Remote Shutter' (in beamline frontend).
    Return 'open' or 'closed'"""
    from CA import caget
    state = caget("PA:14ID:A_SHTRS_CLOSED.VAL")
    if state == 1: return "closed"
    if state == 0: return "open"

def days(seconds):
    """Convert a time stamp from seconds since 1 Jan 1970 0:00 UTC to days
    since 1 Jan 1 AD 0:00 localtime
    seconds: scalar or array"""
    # Determine the offset, which his time zone and daylight saving time
    # dependent.
    t = nanmean(seconds)
    if not isnan(t):
        from datetime import datetime; from pylab import date2num
        offset = date2num(datetime.fromtimestamp(t)) - t/86400
    else: offset = nan
    return seconds/86400 + offset

def nanmean(x):
    """Average value of the array a, ignoring 'Not a Number' elements"""
    if not hasattr(x,"__len__"): return x
    x = asanyarray(x)
    valid = ~isnan(x)
    return sum(x[valid])/sum(valid)

def tostr(x):
    """Replacement for built-in function 'tostr'.
    Fixes Microsoft quirk nan -> '1.#QNAN' or '1.#IND'. inf -> '1.#INF'"""
    if issubclass(type(x),float):
        if isnan(x): return "nan"
        if isinf(x) and x>0: return "inf"
        if isinf(x) and x<0: return "-inf"
        return "%g" % x
    return repr(x)

def toint(x):
    """Convert x to integer without throwing an exception"""
    try: return int(x)
    except: return 0

def module_dir():
    "directory of the current module"
    from os.path import dirname
    module_dir = dirname(module_path())
    if module_dir == "": module_dir = "."
    return module_dir

def module_path():
    "full pathname of the current module"
    from sys import path
    from os import getcwd
    from os.path import basename,exists
    from inspect import getmodulename,getfile
    # 'getfile' retreives the source file name name compiled into the .pyc file.
    pathname = getfile(lambda x: None)
    if exists(pathname): return pathname
    # The module might have been compiled on a different machine or in a
    # different directory.
    pathname = pathname.replace("\\","/")
    filename = basename(pathname)
    dirs = [dir for dir in [getcwd()]+path if exists(dir+"/"+filename)]
    if len(dirs) == 0: warn("pathname of file %r not found" % filename)
    dir = dirs[0] if len(dirs) > 0 else "."
    pathname = dir+"/"+filename
    return pathname

def module_name():
    from inspect import getmodulename,getfile
    return getmodulename(getfile(lambda x: None))

def mtime(filename):
    """Modication timestamp of a file, in seconds since 1 Jan 1970 12:00 AM GMT"""
    from os.path import getmtime
    try: return getmtime(filename)
    except: return 0 # file does not exist

def main():
    from sys import argv
    global app,win
    app = wx.App(redirect=False)
    if len(argv) > 1: name = argv[1]
    else: name = module_name()
    win = DataLogger(name=name)
    app.MainLoop()
    
log = Log()    

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging # for debugging
    from tempfile import gettempdir
    logfile = gettempdir()+"/DataLogger.log"
    logging.basicConfig(level=logging.DEBUG,
        filename=logfile,
        format="%(asctime)s %(levelname)s: %(message)s")
    main()
    ##start_new_thread (main,()) # use for debugging
