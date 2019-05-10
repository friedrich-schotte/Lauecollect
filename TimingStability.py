"""
Analyzes Lauecollect logfiles and generates a chart of the
history of the timing error.
Author: Friedrich Schotte, NIH, 7 Jun 2010 - 4 Feb 2017
"""
from numpy import *
import wx
from logging import debug,info,warn,error

__version__ = "2.5" # separate timing logfile

class TimingStabilityChart (wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self,parent=None)
        self.title = "Laser to X-ray Timing"
        # Menus
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append (101,"Watch directory...\tCtrl+O",
            "Select top level folder containig all log files to watch.")
        self.Bind (wx.EVT_MENU,self.SelectToplevelDir,id=101)
        menu.Append (112,"&Save As...","Creates text file with numerical data.")
        self.Bind (wx.EVT_MENU,self.OnSave,id=112)
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
        self.liveControl = wx.CheckBox(self,label="Live")
        self.Bind(wx.EVT_CHECKBOX,self.OnLive,self.liveControl)
        self.slider = wx.Slider(self)
        self.Bind(wx.EVT_SLIDER,self.OnSlider)
        self.CreateStatusBar()
        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.canvas,proportion=1,flag=wx.EXPAND)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALIGN_CENTRE_VERTICAL|wx.ALL
        hbox.Add(self.liveControl,proportion=0,flag=flag,border=5)
        hbox.Add(self.slider,proportion=1,flag=wx.EXPAND)
        vbox.Add(hbox,proportion=0,flag=wx.EXPAND)
        self.SetSizer(vbox)
        self.Fit()
        
        # Default settings.
        global toplevel_dir
        toplevel_dir = "//mx340hs/data/anfinrud_1702/Data/WAXS"
        self.export_filename = "//mx340hs/data/anfinrud_1702/Logfiles/Timing Stability.txt"
        self.timepoints = []
        self.max_dt = +400e-12
        self.min_dt = -400e-12
        self.Size = 640,480
        self.update_interval = 10 # seconds

        # Initialization

        # Restore last saved settings.
        self.config_dir = wx.StandardPaths.Get().GetUserDataDir()+\
            "/TimingStability"
        self.config = wx.FileConfig(localFilename=self.config_dir+"/settings.py")
        self.settings = "timepoints","max_dt","min_dt","Size","export_filename",\
            "live","update_interval"
        for name in self.settings:
            try: setattr(self,name,eval(self.config.Read(name)))
            except: pass
        try: toplevel_dir = eval(self.config.Read('toplevel_dir'))
        except: pass
        try: self.slider.Value = eval(self.config.Read('fraction'))
        except: pass
        # Restore window position.
        try:
            x,y = eval(self.config.Read('Position'))
            if x >= 0 and y >= 0: self.Position = x,y
        except: pass

        self.Show()

        # Initialization
        self.npoints = 0
        from threading import Thread
        self.update_task = Thread(target=read_logfiles,name="read_logfiles")
        self.update()

    def update(self,event=None):
        # Do some work.
        from time import time
        # Relaunch background update task after it is done, afte rwating a specified
        # time, given by 'update_interval'.
        if self.live and not self.update_task.isAlive() and \
            time()-update_completed > self.update_interval:
            from threading import Thread
            global cancelled; cancelled = False
            self.update_task = Thread(target=read_logfiles,name="read_logfiles")
            self.update_task.start()
        self.refresh()
        # Relaunch yourself.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update)
        self.timer.Start(1000,oneShot=True)

    def refresh(self,event=None):
        "Generate the plot"
        # Update window title.
        self.SetTitle(self.title+" - "+toplevel_dir)
        # Update the chart.
        if len(data.t) != self.npoints: self.refresh_chart()
        self.npoints = len(data.t)
        # Update status bar.
        text = str(self.GetStatusBar().GetStatusText()).replace('\x00','')
        if text == "" or "..." in text: self.SetStatusText(status)

    def refresh_chart(self):
        # Generate a chart.
        from pylab import setp,date2num,DateFormatter
        from datetime import datetime
        t,act_delay,nom_delay = data.t,data.act_delay,data.nom_delay
        global date,dt # for debugging
        date = array([date2num(datetime.fromtimestamp(x)) for x in t])
        dt = act_delay - nom_delay
        # Filter the data to be plotted.
        # Timepoints > 1us cannot be measured reliably.
        ##dt[abs(nom_delay) > 1e-6] = nan
        # If specified, show only the timing error for selected time points.
        if len(self.timepoints) > 0:
            for timepoint in self.timepoints:
                dt[abs(nom_delay-timepoint) > 10e-12] = nan
        self.figure.subplots_adjust(bottom=0.2)
        self.plot = self.figure.add_subplot(1,1,1)
        self.plot.clear()
        self.plot.set_xlabel("time")
        self.plot.xaxis_date()
        formatter = DateFormatter('%b %d %H:%M')
        self.plot.xaxis.set_major_formatter(formatter)
        setp(self.plot.get_xticklabels(),rotation=90,fontsize=10)
        self.plot.set_ylabel("timing error [ps]")
        self.plot.grid()
        if not all(isnan(dt)):
            order = argsort(date)
            self.plot.plot(date[order],dt[order]/1e-12,'.')
            # Restrict the time range plotted according to the slider.
            tmin,tmax = amin(date[~isnan(dt)]),amax(date[~isnan(dt)])
            fraction = 1-self.slider.GetValue()/100.
            tmin = tmax - fraction*(tmax-tmin)
            self.plot.set_xlim(tmin,tmax)
        if not isnan(self.min_dt): self.plot.set_ylim(ymin=self.min_dt/1e-12)
        if not isnan(self.max_dt): self.plot.set_ylim(ymax=self.max_dt/1e-12)
        self.canvas.draw()
        
    def get_data(self):
        """Date and time error as tuple of two numpy arrays.
        Returns (t,dt)
        t: number of seconds since 1 Jan 1970 00:00:00 UTC as floating point
        value.
        dt: Laser to X-ray timing error in seconds
        """
        from pylab import date2num
        from datetime import datetime
        t,act_delay,nom_delay = data.t,data.act_delay,data.nom_delay
        dt = act_delay - nom_delay
        # Filter the data to be plotted.
        selected = ~isnan(dt)
        # Timepoints > 1us cannot be measured reliably.
        selected &= (abs(nom_delay) <= 1e-6)
        # If specified, show only the timing error for selected time points.
        if len(self.timepoints) > 0:
            for timepoint in self.timepoints:
                selected &= (abs(nom_delay-timepoint) <= 10e-12)
        t = t[selected]; dt = dt[selected]
        if not all(isnan(dt)):
            order = argsort(t)
            t = t[order]
            dt = dt[order]
            # Restrict the time range plotted according to the slider.
            tmin,tmax = amin(t[~isnan(dt)]),amax(t[~isnan(dt)])
            fraction = 1-self.slider.GetValue()/100.
            tmin = tmax - fraction*(tmax-tmin)
            selected = [(tmin <= t) & (t <= tmax)]
            t = t[selected]
            dt = dt[selected]
        return t,dt
    data = property(get_data)

    def SelectToplevelDir(self,event):
        """Called from menu File/Watch Directory...
        Let the user pick the directory which contains all the log files to watch.
        """
        global toplevel_dir
        dlg = wx.DirDialog(self, "Where to look for Lauecollect log files:",
            style=wx.DD_DEFAULT_STYLE)
        dlg.SetPath(toplevel_dir)
        # ShowModal pops up a dialog box and returns control only after the user
        # has selects OK or Cancel.
        OK = (dlg.ShowModal() == wx.ID_OK) 
        dlg.Destroy()
        if not OK: return
        toplevel_dir = str(dlg.GetPath())
        self.SaveSettings()
        reset()
        global update_completed; update_completed = 0

    def OnSave(self,event):
        "Called from menu File/Save As..."
        from os.path import dirname,basename
        from inspect import getfile
        filename = self.export_filename
        dlg = wx.FileDialog(self,"Save Displayed Data Points As",
            style=wx.SAVE|wx.OVERWRITE_PROMPT,
            defaultFile=basename(filename),defaultDir=dirname(filename),
            wildcard="Text Files (*.txt)|*.txt|All Files (*.*)|*.*")
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            header = "X-ray to laser timing error recorded by Lauecollect\n"
            modulename = getfile(lambda x: None)
            header += "Generated by "+basename(modulename)+" "+__version__+"\n"
            header += "Filtered, including only these timepoints: "
            for t in self.timepoints: header += time_string(t)+", "
            header = header.rstrip(", ")
            if len(self.timepoints) == 0: header += "all <= 1 us"
            labels="date time,dt[s]"
            t,dt = self.data
            date_time = map(datestring,t)
            from textfile import save
            save ([date_time,dt],filename,header,labels)
            self.export_filename = filename
        dlg.Destroy()

    def OnExit(self,event):
        "Called on File/Exit or when the windows's close button is clicked"
        self.SaveSettings()
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
        self.refresh_chart()

    def OnLive(self,event):
        "called when 'Active' buttoin is toggled"
        global cancelled,update_completed
        cancelled = not self.liveControl.Value
        if self.liveControl.Value == True: update_completed = 0

    def get_live(self):
        "Is 'Live' checkbox checked?"
        return self.liveControl.Value
    def set_live(self,value): self.liveControl.Value = value
    live = property(get_live,set_live)

    def SaveSettings(self):
        # Save settings for next time.
        from os.path import exists
        from os import makedirs
        if not exists(self.config_dir): makedirs(self.config_dir)
        for name in self.settings:
            self.config.Write (name,repr(getattr(self,name)))
        self.config.Write ("toplevel_dir",repr(toplevel_dir))
        self.config.Write ("fraction",repr(self.slider.Value))
        self.config.Write ("Position",repr(self.Position))
        self.config.Flush()


class Options (wx.Dialog):
    "Allows the use to configure camera properties"
    def __init__ (self,parent):
        wx.Dialog.__init__(self,parent,-1,"Beam Centering Options")
        # Controls
        style = wx.TE_PROCESS_ENTER
        self.Timepoints = wx.TextCtrl (self,size=(80,-1),style=style)
        self.Max = wx.TextCtrl (self,size=(80,-1),style=style)
        self.Min = wx.TextCtrl (self,size=(80,-1),style=style)
        self.UpdateInterval = wx.TextCtrl (self,size=(80,-1),style=style)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)

        # Layout
        layout = wx.BoxSizer()
        grid = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        
        label = "Filter chart, including only these timepoints:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Timepoints,flag=flag)

        label = "Vertical scale upper limit:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Max,flag=flag)

        label = "Vertical scale lower limit:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Min,flag=flag)

        label = "Update Interval:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.UpdateInterval,flag=flag)

        # Leave a 10-pixel wide space around the panel.
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self):
        parent = self.Parent
        timepoints = ""
        for t in parent.timepoints: timepoints += time_string(t)+","
        timepoints = timepoints.strip(",")
        self.Timepoints.Value = timepoints
        self.Min.Value = time_string(self.Parent.min_dt).replace("off","auto")
        self.Max.Value = time_string(self.Parent.max_dt).replace("off","auto")
        self.UpdateInterval.Value = time_string(self.Parent.update_interval)

    def OnEnter(self,event):
        text = self.Timepoints.Value
        self.Parent.timepoints = \
            [seconds(t) for t in text.split(",") if not isnan(seconds(t))]
        self.Parent.min_dt = seconds(self.Min.Value)
        self.Parent.max_dt = seconds(self.Max.Value)
        self.Parent.update_interval = seconds(self.UpdateInterval.Value)
        self.update()
        self.Parent.refresh_chart()


toplevel_dir = "//mx340hs/data/anfinrud_1702/Data/WAXS"

class data:
    t = zeros(0)
    nom_delay = zeros(0)
    act_delay = zeros(0)

status = ""
cancelled = False
update_completed = 0
logfiles = {}
timestamps = {}

def read_logfiles():
    from table import table
    from os.path import basename,getmtime
    from time import time
    global status,update_completed
    status = "Searching for logfiles..."
    filenames = logfilenames(toplevel_dir)
    for filename in filenames:
        if cancelled: break
        # Read a file only if it has not been read before or if it was
        # modified after it was read.
        if filename in timestamps and timestamps[filename] == getmtime(filename):
            continue
        timestamps[filename] = getmtime(filename)
        status = "Reading %s..." % basename(filename)
        try:
            logfiles[filename] = table(filename,separator="\t")
            update_data()
        except Exception,msg: warn("Skipping %s: %s" % (filename,msg)); continue
    status = ""
    update_completed = time()

def reset():
    global logfiles,timestamps
    logfiles = {}
    timestamps = {}
    data.t = data.act_delay = data.nom_delay = zeros(0)

def update_data():
    from time_string import timestamp
    status = "Merging..."
    t = nom_delay = act_delay = zeros(0)
    for logfile in logfiles.values():
        t = concatenate((t,[timestamp(d,"") for d in logfile.date_time]))
        nom_delay = concatenate((nom_delay,map(filename_delay,logfile["filename"])))
        act_delay = concatenate((act_delay,logfile.act_delay))
    data.t,data.act_delay,data.nom_delay = t,act_delay,nom_delay

def filename_delay(filename):
    """Decode image filename and extract delay
    e.g. "AlCl3-2_1_90C_-10us-3.mccd" -> -10e-6"""
    from time_string import seconds
    delay = filename.replace(".mccd","")
    delay = delay.split("_")[-1]
    if delay.startswith("-"): delay = delay[1:]; sign = "-"
    else: sign = "-"
    delay = delay.split("-")[0]
    delay = sign+delay
    delay = seconds(delay)
    return delay

def logfilenames(toplevel_dir):
    """List of the pathnames of all Lauecollect logfiles in 'toplevel_dir'
    and subdirectories."""
    from os import walk
    logfiles = []
    for (dirpath,dirnames,filenames) in walk(toplevel_dir):
        if cancelled: return logfiles
        for filename in filenames:
            filename = dirpath+"/"+filename
            if not filename.endswith("_timing.txt"): continue
            logfiles += [filename]
    return logfiles

def timestamp(date_time):
    "Convert a date string to number of seconds til 1 Jan 1970."
    from time import strptime,mktime
    return mktime(strptime(date_time,"%d-%b-%y %H:%M:%S"))

def datestring(seconds):
    """Format time in seconds since 1 Jan 1970 00:00 UST as local time string
    in the format '1-Jan-70 00:00:00'"""
    from datetime import datetime
    from time import strftime,localtime
    return strftime("%d-%b-%y %H:%M:%S",localtime(seconds))

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

def main():
    global win
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
    win = TimingStabilityChart()
    wx.app.MainLoop()

if __name__ == "__main__":
    """Main program"""
    main()
    ##from thread import start_new_thread
    ##start_new_thread (main,()) # use for debugging
