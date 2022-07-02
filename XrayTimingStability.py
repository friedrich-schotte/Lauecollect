"""
Monitors the timing stability the X-ray pulse, with respect to the
storage ring bunch clock.

Setup:
MCP-PMT -> Agilent oscilloscope, channel 3.
FPGA Timing system, output "X scope trig" -> Agilent oscilloscope, channel 4.
Define Measurement 2 as "Delta-Time(4-3)".
From Edge # 1, Rising - To Edge # 2, Falling.
(Measurement 1 should be "Delta-Time(2-3)", which is needed by Lauecollect.)

Author: Friedrich Schotte, NIH, 9 Aug 2010 - 10 Oct 2010
"""
from numpy import *
from thread import start_new_thread
from id14 import id14b_scope

__version__ = "2.1"

# Default settings
title = "X-ray Timing"
nom_delay = 0.0 # calibration constant (not used)
naverage = 10
default_logfile = "//id14bxf/data/X-ray Timing.txt"

# Initialization
active = False # collecting data?
cancelled = False

def delay():
    delay_measurement = id14b_scope.measurement(2)
    # Ignore measurment made when there is not X-ray beam.
    if remote_shutter_state() == "closed":
        status ("Waiting for X-ray shutter to open...")
        return nan
    # Count only measurements made at the maximum sampling rate, 20 GS/s
    if id14b_scope.sampling_rate >= 2e10:
        dt = delay_measurement.value
        return dt
    else:
        status ("Waiting for sampling rate to increase to 20 GS/s...")
        return nan

def measure():
    from numpy import nan,isnan
    from time import sleep
    while not cancelled:
        while active:
            last_measurement = log.dt[-1] if len(log.dt) > 0 else nan
            measurement = delay()
            while measurement == last_measurement or isnan(measurement):
                if not active: break
                if measurement == last_measurement and not isnan(measurement):
                    status("Waiting for oscilloscope to trigger...")
                sleep(0.3)
                measurement = delay()
            if not active: break
            status ("Measuring %s" % time_string(measurement))
            log.append(measurement)
            sleep(0.3)
        status("not active")
        sleep(0.3)


class Log(object):
    """Stores time-stamped data"""
    def __init__(self):
        self.filename = default_logfile
        self.timestamp = 0
        self.T = zeros(0)
        self.DT = zeros(0)

    def append(self,dt):
        from time import time
        from os import makedirs
        from os.path import exists,dirname,getmtime

        # A measurement that is a duplicate of the last is probably old.
        self.read_file()
        if len(self.DT) > 0 and dt == self.DT[-1]: return

        t = time()
        self.T = concatenate((self.T,[t]))
        self.DT = concatenate((self.DT,[dt]))
        
        if not exists(self.filename):
            if not exists(dirname(self.filename)): makedirs(dirname(self.filename))
            logfile = file(self.filename,"ab")
            logfile.write("#date time\tdelay[s]\n")
        logfile = file(self.filename,"ab")
        logfile.write("%s\t%s\n" % (date_string(t),repr(dt)))
        logfile.close()
        self.timestamp = getmtime(self.filename)
        ##print "updated log file: %.0f" % self.timestamp

    def read_file(self):
        "Check log file for changes and reread it"
        from os.path import exists,getmtime
        from table import table
        
        if not exists(self.filename):
            self.T,self.DT = zeros(0),zeros(0)
            self.timestamp = 0
            self.loaded_filename = ""
        else: 
            current_timestamp = getmtime(self.filename)
            if abs(current_timestamp - self.timestamp) > 2 or \
                self.filename != self.loaded_filename:
                if self.timestamp != 0:
                    print "log file changed by %g s" % \
                        (current_timestamp - self.timestamp)
                status("Reading %s..." % self.filename)
                try:
                    logfile = table(self.filename,separator="\t")
                    self.T = array(map(timestamp,logfile.date_time))
                    self.DT = logfile.delay
                    self.timestamp = current_timestamp
                    self.loaded_filename = self.filename
                except Exception,details:
                    print "%s unreadable: %s" % (self.filename,details)
                    if self.loaded_filename != self.filename:
                        self.T,self.DT = zeros(0),zeros(0)
                        self.timestamp = current_timestamp
                        self.loaded_filename = self.filename
                status("Reading %s... done" % self.filename)

    def get_t(self):
        "Timestamps"
        self.read_file()
        return self.T
    t = property(get_t)
    
    def get_dt(self):
        "Recorded time delays"
        self.read_file()
        return self.DT
    dt = property(get_dt)
        
log = Log()    

import wx

class TimingChart (wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,parent=None)
        # Menus
        self.title = title
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
        self.slider = wx.Slider(self)
        self.slider.Max = 1000
        self.Bind(wx.EVT_SLIDER,self.OnSlider)
        self.CreateStatusBar()
        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.canvas,proportion=1,flag=wx.EXPAND)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(self.active,proportion=0)
        hbox.Add(self.slider,proportion=1,flag=wx.EXPAND)
        vbox.Add(hbox,proportion=0,flag=wx.EXPAND)
        self.SetSizer(vbox)
        self.Fit()
        
        # Default settings.
        self.max_dt = +400e-12
        self.min_dt = -400e-12
        self.reject_outliers = False
        self.outlier_cutoff = 2.5
        self.Size = 640,480

        # Restore last saved settings.
        self.settings = ["Size","logfile","nom_delay","average_count",
            "max_dt","min_dt","fraction","reject_outliers","outlier_cutoff"]
        self.update_settings()

        # Initialization
        self.npoints = 0

        self.Show()
        self.update()

    def get_logfile(self): return log.filename
    def set_logfile(self,new_logfile):
        log.filename = str(new_logfile)
    logfile = property(get_logfile,set_logfile)

    def get_nom_delay(self): return nom_delay
    def set_nom_delay(self,value): global nom_delay; nom_delay = value
    nom_delay = property(get_nom_delay,set_nom_delay)

    def get_average_count(self): return naverage
    def set_average_count(self,value):
        global naverage; naverage = max(1,int(value))
    average_count = property(get_average_count,set_average_count)

    def get_fraction(self): return 1 - float(self.slider.Value)/self.slider.Max
    def set_fraction(self,value):
        self.slider.Value  = rint(max(0,min(1-value,1))*self.slider.Max)
    fraction = property(get_fraction,set_fraction)

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

    def refresh_chart(self):
        # Generate a chart.
        from pylab import setp,date2num,DateFormatter
        from datetime import datetime
        ps = 1e-12
        t,dt = self.data
        date = array([date2num(datetime.fromtimestamp(x)) for x in t])
        self.figure.subplots_adjust(bottom=0.2)
        self.plot = self.figure.add_subplot(1,1,1)
        self.plot.clear()
        self.plot.set_xlabel("time")
        self.plot.xaxis_date()
        setp(self.plot.get_xticklabels(),rotation=90,fontsize=10)
        self.plot.set_ylabel("timing error [ps]")
        self.plot.grid()
        if not all(isnan(dt)):
            self.plot.plot(date,(dt-self.nom_delay)/ps,'.')
            # Restrict the time range plotted according to the slider.
            tmin,tmax = amin(date[~isnan(dt)]),amax(date[~isnan(dt)])
            ##tmin = tmax - self.fraction*(tmax-tmin)
            self.plot.set_xlim(tmin,tmax)
        tmin,tmax = self.plot.get_xlim()
        if tmax-tmin < 5./24/60: date_format = "%H:%M:%S"
        elif tmax-tmin < 1: date_format = "%H:%M"
        else: date_format = "%b %d %H:%M"
        self.plot.xaxis.set_major_formatter(DateFormatter(date_format))
        if not isnan(self.min_dt): self.plot.set_ylim(ymin=self.min_dt/ps)
        if not isnan(self.max_dt): self.plot.set_ylim(ymax=self.max_dt/ps)
        self.canvas.draw()

    def get_data(self):
        """Data points to be plotted
        returns (t,dt)
        t: time stamp in seconds since 1 Jan 1970 00:00 UST
        dt: delay in seconds"""
        t,dt = self.raw_data
        valid = ~isnan(dt)
        t,dt = t[valid],dt[valid]
        # Average data.
        n = self.average_count
        N = int(ceil(float(len(dt))/n))
        T,DT = zeros(N),zeros(N)
        for i in range(0,N):
            T[i] = average(t[i*n:(i+1)*n])
            DT[i] = self.average(dt[i*n:(i+1)*n])
        t,dt = T,DT
        # Restrict the time range plotted according to the slider.
        tmin,tmax = nanmin(t),nanmax(t)
        tmin = tmax - self.fraction*(tmax-tmin)
        selected = (tmin<=t) & (t<=tmax)
        t,dt = t[selected],dt[selected]
        return t,dt
    data = property(get_data)

    def average(self,data):
        if not self.reject_outliers: return average(data)
        while True:
            i = abs(data-average(data)) < self.outlier_cutoff*std(data)
            if sum(i) == len(data): break
            data = data[i]
        return average(data)
        
    def get_raw_data(self):
        """Data points to be plotted
        returns (t,dt)
        t: time stamp in seconds since 1 Jan 1970 00:00 UST
        dt: delay in seconds"""
        t,dt = log.t,log.dt
        n = min(len(t),len(dt))
        return t[:n],dt[:n]
    raw_data = property(get_raw_data)
        
    def OnSelectLogfile(self,event):
        """Called from menu File/Watch Directory...
        Let the user pick the directory which contains all the log files to watch.
        """
        from os.path import basename,dirname
        dlg = wx.FileDialog(self,"Select Logfile",
            style=wx.FD_SAVE,
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

    def OnSlider(self,event):
        "called when slider is moved"
        self.refresh_chart()

    def OnActive(self,event):
        "called when 'Active' buttoin is toggled"
        global active
        active = self.active.Value

    def update_settings(self,event=None):
        "Monitors the settings file and reloads it if it is updated."
        from os.path import exists
        from os import makedirs
        if not hasattr(self,"settings_timestamp"): self.settings_timestamp = 0
        if not hasattr(self,"saved_state"): self.saved_state = self.State
        
        if mtime(self.settings_file()) != self.settings_timestamp:
            if exists(self.settings_file()):
                ##print "reading %r" % self.settings_file()
                self.State = file(self.settings_file()).read()
            self.settings_timestamp = mtime(self.settings_file())
            self.saved_state = self.State
        elif self.saved_state != self.State or not exists(self.settings_file()):
            if not exists(self.settings_dir()): makedirs(self.settings_dir())
            ##print "writing %r" % self.settings_file()
            file(self.settings_file(),"wb").write(self.State)
            self.settings_timestamp = mtime(self.settings_file())
            self.saved_state = self.State

        # Relaunch this procedure after 2 s
        self.settings_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update_settings,self.settings_timer)
        self.settings_timer.Start(2000,oneShot=True)

    def GetState(self):
        state = ""
        for attr in self.settings:
            line = attr+" = "+repr(eval("self."+attr))
            state += line+"\n"
        return state
    def SetState(self,state):
        for line in state.split("\n"):
            line = line.strip(" \n\r")
            if line != "":
                try: exec("self."+line)
                except: print "ignoring "+line; pass
    State = property(GetState,SetState)

    def settings_file(self):
        "pathname of the file used to store persistent parameters"
        return self.settings_dir()+"/"+module_name()+"_settings.py"

    def settings_dir(self):
        "pathname of the file used to store persistent parameters"
        from os.path import dirname
        path = module_dir()+"/settings"
        return path


class Options (wx.Dialog):
    "Allows the use to configure camera properties"
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Options")
        # Controls
        style = wx.TE_PROCESS_ENTER
        self.NomDelay = wx.TextCtrl (self,size=(80,-1),style=style)
        self.Max = wx.TextCtrl (self,size=(80,-1),style=style)
        self.Min = wx.TextCtrl (self,size=(80,-1),style=style)
        self.AverageCount = wx.TextCtrl (self,size=(80,-1),style=style)
        self.RejectOutliers = wx.Choice (self,size=(80,-1),choices=["Yes","No"])
        self.OutlierCutoff = wx.TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_CHOICE,self.OnEnter)

        # Layout
        layout = wx.BoxSizer()
        grid = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        
        label = "Nominal value (calibration):"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.NomDelay,flag=flag)

        label = "Vertical scale upper limit:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Max,flag=flag)

        label = "Vertical scale lower limit:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Min,flag=flag)

        label = "Average count:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.AverageCount,flag=flag)

        label = "Reject Outliers:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.RejectOutliers,flag=flag)

        label = "Outlier Cutoff:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.OutlierCutoff,flag=flag)

        # Leave a 10-pixel wide space around the panel.
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self):
        self.NomDelay.Value = time_string(self.Parent.nom_delay).replace("off","auto")
        self.Min.Value = time_string(self.Parent.min_dt).replace("off","auto")
        self.Max.Value = time_string(self.Parent.max_dt).replace("off","auto")
        self.AverageCount.Value = str(self.Parent.average_count)
        self.RejectOutliers.StringSelection = "Yes" if self.Parent.reject_outliers else "No"
        self.OutlierCutoff.Value = str(self.Parent.outlier_cutoff)

    def OnEnter(self,event):
        self.Parent.nom_delay = seconds(self.NomDelay.Value)
        self.Parent.min_dt = seconds(self.Min.Value)
        self.Parent.max_dt = seconds(self.Max.Value)
        try: self.Parent.average_count = int(eval(self.AverageCount.Value))
        except: pass
        self.Parent.reject_outliers = (self.RejectOutliers.StringSelection == "Yes")
        try: self.Parent.outlier_cutoff = float(eval(self.OutlierCutoff.Value))
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

def timestamp(date_time):
    "Convert a date string to number of seconds til 1 Jan 1970."
    from time import strptime,mktime
    return mktime(strptime(date_time,"%d-%b-%y %H:%M:%S"))

def date_string(time):
    "Convert a time stamp in number of seconds til 1 Jan 1970 to a string"
    from time import strftime,localtime
    return strftime("%d-%b-%y %H:%M:%S",localtime(time))

def time_string(t):
    """Convert time given in seconds in more readable format
    such as ps, ns, ms, s, min, hours and days."""
    if t == "off": return "off"
    try: t = float(t)
    except: return "off"
    if t != t: return "off" # not a number
    if t == 0: return "0"
    if abs(t) < 0.5e-12: return "0"
    if abs(t) < 999e-12: return "%.3gps" % (t*1e12)
    if abs(t) < 999e-9: return "%.3gns" % (t*1e9)
    if abs(t) < 999e-6: return "%.3gus" % (t*1e6)
    if abs(t) < 999e-3: return "%.3gms" % (t*1e3)
    if abs(t) <= 59: return "%.3gs" % t
    if abs(t) <= 3600-1: return "%02d:%02dmin" % (t/60,round(t%60))
    if abs(t) <= 24*3600-1: return "%d:%02dh" % (round(t/3600),round(t%3600/60))
    return str(int(t/(24*3600)))+"d "+str(int(round(t%(24*3600)/3600)))+"h"

def seconds (text):
    """ convert a text string like "10ns" into a floating point value in seconds.
    Units accepted are "s","ms", "us", "ns", "ps" "min", "hour" ("h") """
    from numpy import nan
    text = text.replace("hours","*3600")
    text = text.replace("hour","*3600")
    text = text.replace("h","*3600")
    text = text.replace("min","*60")
    text = text.replace("s","")
    text = text.replace("m","*1e-3")
    text = text.replace("u","*1e-6")
    text = text.replace("n","*1e-9")
    text = text.replace("p","*1e-12")
    try: return float(eval(text))
    except: return nan

def repr(x):
    """Replacement for built-in function 'repr'.
    Fixes Microsoft quirk nan -> '1.#QNAN' or '1.#IND'. inf -> '1.#INF'"""
    if issubclass(type(x),float):
        if isnan(x): return "nan"
        if isinf(x) and x>0: return "inf"
        if isinf(x) and x<0: return "-inf"
    return __builtins__.repr(x)

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
    if len(dirs) == 0: print "pathname of file %r not found" % filename
    dir = dirs[0] if len(dirs) > 0 else "."
    pathname = dir+"/"+filename
    return pathname

def module_name():
    from inspect import getmodulename,getfile
    return getmodulename(getfile(lambda x: None))

def mtime(filename):
    "Modication timestamp of a file, in seconds since 1 Jan 1970 12:00 AM GMT"
    from os.path import getmtime
    try: return getmtime(filename)
    except: return 0 # file does not exist

def main():
    global app,win
    start_new_thread (measure,())
    app = wx.App(0)
    win = TimingChart()
    app.MainLoop()
    

if __name__ == "__main__":
    main()
    ##start_new_thread (main,()) # use for debugging


