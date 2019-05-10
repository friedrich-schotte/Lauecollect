#!/usr/bin/env python
"""Laue Data Collection GUI
Friedrich Schotte, NIH, Aug 22, 2007 - May 18, 2018
"""
from pdb import pm # for debugging
# Beamline instrumentation
from lauecollect import *
import wx,wx3_compatibility
from EditableControls import TextCtrl,ComboBox # customized versions
from thread import start_new_thread
from threading import Thread
from logging import debug,info,warn,error

__version__ = "25.1" # wx 4.0

def launch():
    """Brings up the Lauecollect window."""
    # Needed to initialize WX library
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
    global win
    win = LaueCollectWindow()
    autorecovery()
    wx.app.MainLoop()

class LaueCollectWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__ (self,None)
        self.SetSize((640,400))

        self.Title = "Laue Data Collection [advanced]"

        # Menus
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        menu.Append (101,"&Load Settings...\tCtrl+O",
            "Restore settings from previously saved .par file")
        self.Bind (wx.EVT_MENU,self.OnLoadSettings,id=101)
        menu.Append (102,"&Load Sequence...",
            "Load table of values from tab separated vales .txt file")
        self.Bind (wx.EVT_MENU,self.OnLoadSequence,id=102)
        menu.AppendSeparator()
        menu.Append (103,"&Save Settings As...",
            "Save current settings as .par file")
        self.Bind (wx.EVT_MENU,self.OnSaveSettings,id=103)
        menu.Append (104,"&Save MAR CCD Image As...\tCtrl+S",
            "Writes current MAR CCD image to 16-bit TIFF file")
        self.Bind (wx.EVT_MENU,self.OnSaveImage,id=104)
        menu.AppendSeparator()
        menu.Append (110,"E&xit","Closes this window.")
        self.Bind (wx.EVT_MENU,self.Exit,id=110)
        menuBar.Append (menu,"&File")
        menu = self.OrientationMenu = wx.Menu()
        menu.Append (501,"About...","Show version number")
        self.Bind (wx.EVT_MENU,self.About,id=501)
        menuBar.Append (menu,"&Help")
        self.SetMenuBar (menuBar)

        # A "notebook" manages multiple panels with associated tabs.
        self.tabs = wx.Notebook(self, -1, style=wx.CLIP_CHILDREN)
        self.tabs.AddPage(DataCollectionPanel(self.tabs),"Collect")
        self.tabs.AddPage(OptionsPanel(self.tabs),"Options")
        self.tabs.AddPage(DetectorPanel(self.tabs),"Det.")
        self.tabs.AddPage(TemperaturePanel(self.tabs),"Temp.")
        self.tabs.AddPage(AlignPanel(self.tabs),"Align")
        self.tabs.AddPage(TranslatePanel(self.tabs),"Trans.")
        self.tabs.AddPage(PumpPanel(self.tabs),"Pump")
        self.tabs.AddPage(ChopperPanel(self.tabs),"Chop.")
        self.tabs.AddPage(DiagnosticsPanel(self.tabs),"Diag.")
        self.tabs.AddPage(XrayBeamCheckPanel(self.tabs),"X-Ray")
        self.tabs.AddPage(LaserBeamCheckPanel(self.tabs),"Laser")
        self.tabs.AddPage(TimingPanel(self.tabs),"Timing")
        self.tabs.AddPage(SamplePhotoPanel(self.tabs),"Photo")
        self.tabs.AddPage(CheckListPanel(self.tabs),"Check")

        self.Bind(wx.EVT_CLOSE, self.Exit)
        
        self.Show()

        task.run_background_threads = True
        # This thread is to run the data collection in background.
        start_new_thread (data_collection_thread,())
        # This update status info in background.
        start_new_thread (status_thread,())
        # This thread is to estimates data collection time in background.
        start_new_thread (time_remaining_thread,())
        # This thread is to periodically read the CCD in background.
        ##start_new_thread (periodically_read_ccd_thread,())

    def OnLoadSettings(self,event):
        """Called from 'Load Setting...' menu item in the File menu"""
        path = param.path
        while not exists(path) and len(path) > 2: path = dirname(path)
        filename = join(normpath(path),param.file_basename+".par")

        dlg = wx.FileDialog(self,"Load Settings",style=wx.OPEN,
            wildcard="Lauecollect Parameter Files (*.par)|*.par",
            defaultFile=basename(filename),defaultDir=dirname(filename))
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            load_settings(filename)
            global Spindle; from lauecollect import Spindle
            panels = self.tabs.GetChildren()
            for panel in panels:
                if hasattr(panel,"update_parameters"): panel.update_parameters()
            save_settings()
        dlg.Destroy()
        
    def OnLoadSequence(self,event):
        """Called from 'Load Sequence...' menu item in the File menu"""
        path = param.path
        while not exists(path) and len(path) > 2: path = dirname(path)
        filename = join(normpath(path),param.file_basename+".txt")

        dlg = wx.FileDialog(self,"Load Sequence",style=wx.OPEN,
            wildcard="Text Files (*.txt)|*.txt",
            defaultFile=basename(filename),defaultDir=dirname(filename))
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            load_variable_sequence(filename)
            panels = self.tabs.GetChildren()
            for panel in panels:
                if hasattr(panel,"update_parameters"): panel.update_parameters()
            save_settings()
        dlg.Destroy()

    def OnSaveSettings(self,event):
        "Called from the 'Save Settings As...' menu item in the File menu"
        path = param.path
        while not exists(path) and len(path) > 2: path = dirname(path)
        filename = join(normpath(path),param.file_basename+".par")

        dlg = wx.FileDialog(self,"Save Settings As",
            style=wx.SAVE|wx.OVERWRITE_PROMPT,
            wildcard="Lauecollect Parameter Files (*.par)|*.par",
            defaultFile=basename(filename),defaultDir=dirname(filename))
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
            save_settings_to_file(filename)
        dlg.Destroy()

    def OnSaveImage(self,event):
        """Called from the 'Save Image As...' menu item in the File menu.
        Saves the currect MAR CCD image as 16-bit TIFF file."""
        path = param.path
        while not exists(path) and len(path) > 2: path = dirname(path)
        filename = join(normpath(path),param.file_basename+"."+
            param.extension.strip("."))

        dlg = wx.FileDialog(self,"Save Image As",
            style=wx.SAVE|wx.OVERWRITE_PROMPT,
            wildcard="TIFF Image Files (*.mccd;*.tif)|*.mccd;*.tif",
            defaultFile=basename(filename),defaultDir=dirname(filename))
        if dlg.ShowModal() != wx.ID_OK: dlg.Destroy(); return
        filename = dlg.GetPath()
        dlg.Destroy()
        ccd.save_image(filename)
        t = time()
        while not exists2(filename) and time()-t < 2.5: sleep(0.1)
        if not exists2(filename):
            message = "Image was NOT saved as '"+basename(filename)+"'.\n"
            message += "Is the directory '"+dirname(filename)+"' \n"
            message += "writable from the MAR CCD computer?\n"
            message += "(Pathname should start with '/data' or '/net/id14bxf'.)"
            dlg = wx.MessageDialog(self,message,"Warning",wx.OK|wx.ICON_WARNING)
            dlg.CenterOnParent()
            dlg.ShowModal()
            dlg.Destroy()
            
    def Exit(self,event):
        "Called from the 'Exit' menu item in the File menu"
        task.run_background_threads = False
        self.Show(False)
        self.Destroy()
    
    def About(self,event):
        "Called from the 'About' menu item in the File menu"
        from inspect import getmodulename,getfile
        module_name = getmodulename(getfile(lambda x: None))
        import lauecollect
        info = module_name+".py version "+__version__+"\n"+\
            "lauecollect.py version "+lauecollect.__version__+"\n"+\
            "An application for time-resolved Laue data collection.\n"+\
            "Author: Friedrich Schotte, Anfinrud Lab, NIH"
        dlg = wx.MessageDialog(self,info,"About",wx.OK|wx.ICON_INFORMATION)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()


class DataCollectionPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)
        
        box = wx.BoxSizer(wx.VERTICAL)
        flag = wx.ALIGN_CENTRE_VERTICAL
        
        line = wx.BoxSizer(wx.HORIZONTAL)

        label = "Spindle"
        if Spindle.name != "": label = Spindle.name
        if Spindle.unit != "": label += " ["+Spindle.unit+"]"
        if len(label) > 13: label = ".."+label[-13:]
        self.Alabel = wx.StaticText (self,label=label+":",size=(95,-1))
        self.Alabel.Bind(wx.EVT_CONTEXT_MENU,self.spindle_motor_context_menu)
        self.Alabel.NormalForegroundColour = self.Alabel.ForegroundColour
        self.Alabel.NormalBackgroundColour = self.Alabel.BackgroundColour
        self.Alabel.NormalBackgroundStyle = self.Alabel.BackgroundStyle
        self.Alabel.Bind(wx.EVT_ENTER_WINDOW,self.highlight_spindle_motor)
        self.Alabel.Bind(wx.EVT_LEAVE_WINDOW,self.unhighlight_spindle_motor)
        line.Add(self.Alabel,flag=flag)

        self.Arange = wx.Panel(self,size=(175,25))
        subgroup = wx.BoxSizer(wx.HORIZONTAL)
        self.Amin = TextCtrl(self.Arange,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        subgroup.Add(self.Amin,flag=flag)
        label = wx.StaticText(self.Arange,label=" to ")
        subgroup.Add(label,flag=flag)
        self.Amax = TextCtrl(self.Arange,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        subgroup.Add(self.Amax,flag=flag)
        self.Arange.SetSizer(subgroup)
        self.Arange.Fit()
        line.Add(self.Arange,flag=flag)

        self.SinglePass = wx.Panel(self,size=(320,25))
        subgroup = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self.SinglePass,label=" in steps of ")
        subgroup.Add(label,flag=flag)
        self.Astep = TextCtrl (self.SinglePass,size=(50,-1),
            style=wx.TE_PROCESS_ENTER)
        subgroup.Add(self.Astep,flag=flag)
        self.SinglePassLabel = wx.StaticText(self.SinglePass,
            label=" "+Spindle.unit+" in a single pass")
        subgroup.Add(self.SinglePassLabel,flag=flag)
        self.SinglePass.SetSizer(subgroup)
        self.SinglePass.Fit()
        line.Add(self.SinglePass,proportion=1,flag=flag)

        self.TwoPasses = wx.Panel(self,size=(320,25))
        subgroup = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self.TwoPasses,label=" in two passes of steps of ")
        subgroup.Add(label,flag=flag)
        self.Astep2 = TextCtrl(self.TwoPasses,size=(35,-1),style=wx.TE_PROCESS_ENTER)
        subgroup.Add(self.Astep2,flag=flag)
        self.Ainter = wx.StaticText(self.TwoPasses,label=" interlaced by ")
        subgroup.Add(self.Ainter,flag=flag)
        self.TwoPasses.SetSizer(subgroup)
        self.TwoPasses.Fit()
        line.Add(self.TwoPasses,proportion=1,flag=flag)

        self.Afill = wx.Panel(self,size=(320,25))
        subgroup = wx.BoxSizer(wx.HORIZONTAL)
        self.AfillLabel = wx.StaticText (self.Afill,label=" "+Spindle.unit+
            " filling gaps using",pos=(0,3))
        subgroup.Add(self.AfillLabel,flag=flag)
        self.NAngles = TextCtrl (self.Afill,size=(35,-1),style=wx.TE_PROCESS_ENTER)
        subgroup.Add(self.NAngles,flag=flag)
        label = wx.StaticText (self.Afill,label="orientations")
        subgroup.Add(label,flag=flag)
        self.Afill.SetSizer(subgroup)
        self.Afill.Fit()
        line.Add(self.Afill,proportion=1,flag=flag)
  
        self.Alist = TextCtrl(self,size=(420,-1),style=wx.TE_PROCESS_ENTER)
        line.Add(self.Alist,proportion=1,flag=flag)

        button = wx.Button(self,label="Strategy...")
        self.Bind(wx.EVT_BUTTON,self.set_strategy,button)
        line.Add(button,flag=flag)

        box.Add(line,flag=wx.EXPAND)
        
        box.AddSpacer((10,10))

        line = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self,label="Laser mode:",size=(95,-1))
        line.Add(label,flag=flag)
        self.Lmode = ComboBox(self,size=(90,-1),
            choices=["on","off","off/on","off/on/off"],
            style=wx.CB_DROPDOWN|wx.PROCESS_ENTER)
        self.Bind(wx.EVT_COMBOBOX,self.on_input)
        self.Bind(wx.EVT_TEXT_ENTER,self.on_input,self.Lmode)
        line.Add(self.Lmode,flag=flag)
        box.Add(line,flag=wx.EXPAND)

        line = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self,label="Time delays:",size=(95,-1))
        line.Add(label,flag=flag)
        self.Tlist = TextCtrl(self,size=(420,-1),style=wx.TE_PROCESS_ENTER)
        line.Add(self.Tlist,proportion=1,flag=flag)
        self.TGenerate = wx.Button(self,label="Generate...",pos=(525,65-1))
        self.Bind(wx.EVT_BUTTON,self.generate_delay_list,self.TGenerate)
        line.Add(self.TGenerate,flag=flag)
        box.Add(line,flag=wx.EXPAND)

        box.AddSpacer((10,10))

        line = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self,label="File basename:",size=(95,-1))
        line.Add(label,flag=flag)
        self.Basename = TextCtrl(self,size=(250,-1),style=wx.TE_PROCESS_ENTER)
        line.Add(self.Basename,flag=flag)
        label = wx.StaticText(self,label=" Extension: ",pos=(360,100+3))
        line.Add(label,flag=flag)
        self.Extension = TextCtrl(self,size=(50,-1),style=wx.TE_PROCESS_ENTER)
        line.Add(self.Extension,flag=flag)
        box.Add(line,flag=wx.EXPAND)

        line = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self,-1,"Description:",size=(95,-1))
        line.Add(label,flag=flag)
        self.Description = TextCtrl(self,size=(500,-1),style=wx.TE_PROCESS_ENTER)
        line.Add(self.Description,proportion=1,flag=flag)
        box.Add(line,flag=wx.EXPAND)

        line = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self,-1,"Log file:",size=(95,-1))
        line.Add(label,flag=flag)
        self.Logfile = TextCtrl(self,size=(250,-1),style=wx.TE_PROCESS_ENTER)        
        line.Add(self.Logfile,flag=flag)
        box.Add(line,flag=wx.EXPAND)
        
        line = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText (self,-1,"Path:",size=(95,-1))
        line.Add(label,flag=flag)
        self.Path = TextCtrl(self,size=(420,-1),style=wx.TE_PROCESS_ENTER)
        line.Add(self.Path,proportion=1,flag=flag)
        button = wx.Button(self,label="Browse...")
        self.Bind(wx.EVT_BUTTON,self.on_browse,button)
        line.Add(button,flag=flag)
        box.Add(line,flag=wx.EXPAND)

        # Call the "on_input" routine whenever the user presses Enter.
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)


        box.AddSpacer((10,10))
        self.Summary = wx.StaticText(self,size=(500,-1))
        box.Add(self.Summary,flag=wx.EXPAND)
        box.AddSpacer((10,10))
        self.Status = wx.StaticText(self,size=(500,-1))
        box.Add(self.Status,flag=wx.EXPAND)
        box.AddSpacer((10,10))
        self.Diagnostics = wx.StaticText(self,size=(500,-1))
        box.Add(self.Diagnostics,flag=wx.EXPAND)
        
        box.AddSpacer((10,10))
        ##box.AddStretchSpacer(prop=1)
        ##spacer = wx.BoxSizer(wx.HORIZONTAL)
        ##box.Add(spacer,proportion=1,flag=wx.EXPAND|wx.ALL)

        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.single_image_button = wx.Button(self,label="Single Image",
            size=(130,-1))
        self.Bind (wx.EVT_BUTTON,self.single_image,self.single_image_button)
        self.collect_button = wx.Button(self,label="Collect Dataset",
            size=(130,-1))
        self.collect_button.SetDefault()
        self.Bind (wx.EVT_BUTTON,self.collect_dataset,self.collect_button)
        self.cancel_button = wx.Button(self,label="Cancel",size=(130,-1))
        self.Bind (wx.EVT_BUTTON,self.cancel,self.cancel_button)
        w,h = self.cancel_button.Size
        self.finish_button = wx.ToggleButton(self,label="Finish Series",
            size=(55,h))
        self.Bind (wx.EVT_TOGGLEBUTTON,self.OnToggleFinish,self.finish_button)
        self.FinishSeriesVariable = wx.Choice(self,size=(40,h))
        self.Bind (wx.EVT_CHOICE,self.on_input,self.FinishSeriesVariable)
        flag = wx.ALIGN_CENTRE_VERTICAL|wx.EXPAND
        buttons.Add(self.single_image_button,proportion=1,flag=flag)
        buttons.AddSpacer((10,10))
        buttons.Add(self.collect_button,proportion=1,flag=flag)
        buttons.AddSpacer((10,10))
        buttons.Add(self.cancel_button,proportion=1,flag=flag)
        buttons.AddSpacer((10,10))
        buttons.Add(self.finish_button,proportion=1,flag=flag)
        buttons.Add(self.FinishSeriesVariable,proportion=1,flag=flag)
        box.Add(buttons,flag=wx.EXPAND|wx.ALIGN_BOTTOM)

        # Leave a 5-pixel wide space around the panel.
        border = wx.BoxSizer(wx.VERTICAL)
        border.Add (box,0,wx.EXPAND|wx.ALL,5)
        self.SetSizer(border)
        self.Fit()

        # Periodically update the status message.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Periodically update the panel"""
        if IsShownOnScreen(self):
            self.update_parameters()
            self.update_status()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer
        check_for_autorecovery()

    def update_parameters(self):
        """Refresh the control panel"""
        reload_settings()
        if Spindle.name != "": label = Spindle.name
        else: label = "Spindle"
        if Spindle.unit != "": label += " ["+Spindle.unit+"]"
        if len(label) > 13: label = label[-13:]
        label += ":"
        if label != self.Alabel.Label: self.Alabel.Label = label
        # If rotation range os 0, use current orientation.
        if param.amin == param.amax: amin = amax = Spindle.value; astep = 0
        else: amin = param.amin; amax = param.amax; astep = param.astep
        self.Amin.Value = ("%g" % amin)
        self.Amax.Value = ("%g" % amax)
        self.Astep.Value = ("%g" % astep)
        self.Astep2.Value = ("%g" % (2*astep))
        self.Ainter.SetLabel("interlaced by %g" % astep)
        self.NAngles.Value = ("%g" % nangles())
        t = ""
        for x in param.alist: t += tostr(x)+","
        self.Alist.Value = (t.strip(","))
        self.SinglePassLabel.Label = Spindle.unit+" in a single pass"
        self.AfillLabel.Label = Spindle.unit+" filling gaps using"
        if getattr(self,"amode","") != param.amode: # avoids flickering
            if param.amode == "Single pass":
                self.Arange.Show(True); self.SinglePass.Show(True)
                self.TwoPasses.Show(False); self.Afill.Show(False)
                self.Alist.Show(False)
            elif param.amode == "Two interlaced passes": 
                self.Arange.Show(True); self.SinglePass.Show(False)
                self.TwoPasses.Show(True); self.Afill.Show(False)    
                self.Alist.Show(False)
            elif param.amode == "Filling gaps": 
                self.Arange.Show(True); self.SinglePass.Show(False)
                self.TwoPasses.Show(False); self.Afill.Show(True)
                self.Alist.Show(False)
            else:
                self.Arange.Show(False); self.SinglePass.Show(False)
                self.TwoPasses.Show(False); self.Afill.Show(False)
                self.Alist.Show(True)
            self.Layout()
        self.amode = param.amode

        separator = "/" if len(variable_choices("laser_on")) <= 2 else ","
        text = separator.join(["on" if x else "off" for x in variable_choices("laser_on")])
        self.Lmode.Value = text
        width = 90 if len(variable_choices("laser_on")) <= 2 else 500
        if self.Lmode.Size[0] != width: self.Lmode.Size = width,-1
        
        enabled = (variable_choices("laser_on") != [False])
        self.Tlist.Enabled = self.TGenerate.Enabled = enabled
        self.Tlist.Value = (self.time_string_list(timepoints()))
        self.Basename.Value = (param.file_basename)
        self.Extension.Value = (param.extension)
        self.Description.Value = (param.description)
        self.Logfile.Value = (param.logfile_filename)       
        self.Path.Value = (param.path)
        self.Summary.Label = status.image_info
        if not task.action:
            task.image_number = status.first_image_number

    def update_status(self,event=None):
        """Update the status message."""
        if not IsShownOnScreen(self): return 

        image_info = status.image_info
        if status.time_info: image_info += ", "+status.time_info
        self.Summary.SetLabel(image_info)
        self.Status.SetLabel(status.acquisition_status)
        self.Diagnostics.SetLabel(status.diagnostics_status)
        
        if not task.action:
            self.single_image_button.Enable()
            self.collect_button.Enable()
            self.cancel_button.Enable(False)
        else:
            self.single_image_button.Enable(False)
            self.collect_button.Enable(False)
            self.cancel_button.Enable()
        if not task.cancelled: self.cancel_button.Label = "Cancel"
        else: self.cancel_button.Label = "Cancelled"
        if task.image_number == 1: self.collect_button.SetLabel("Collect Dataset")
        elif task.image_number > 1: self.collect_button.SetLabel("Resume Dataset")
        if task.image_number > nimages(): self.collect_button.Enable(False)
        if self.FinishSeriesVariable.Items != collection_variables():
            self.FinishSeriesVariable.Items = collection_variables()
        if self.FinishSeriesVariable.StringSelection != options.finish_series_variable:
            self.FinishSeriesVariable.StringSelection = options.finish_series_variable

        if not task.action: self.finish_button.Value = (False)

    def single_image(self,event):
        task.action = "Single Image"

    def collect_dataset(self,event):
        task.action = "Collect Dataset"

    def cancel(self, event): 
        task.cancelled = True; task.action = ""

    def OnToggleFinish(self, event): 
        "Called when the Finish time series button is toggled"
        if self.finish_button.Value == True: task.finish_series = True
        else: task.finish_series = False

    def time_string_list(self,tlist):
        """Converts list of time delays in seconds into a comma-separated list
        of a more readble format using the units ps, ns, ms, s"""
        list=""
        for t in tlist: list = list+time_string(t)+","
        list = list.strip(",")
        return list
    
    def time_list(self,s):
        """Converts a comma-separated string with units of ps, ns, ms, s
        into list of binaryset_collection_strategy number in units of seconds"""
        wlist = s.split(",")
        tlist = []
        for w in wlist: tlist.append(seconds(w))
        return tlist

    def on_input(self,event):
        """This is called when te use switches between feilds and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        try: param.amin = float(eval(self.Amin.GetValue()))
        except ValueError: pass
        try: param.amax = float(eval(self.Amax.GetValue()))
        except ValueError: pass
        if param.amode == "Single pass":
            try: param.astep = float(eval(self.Astep.GetValue()))
            except ValueError: pass
            param.alist = self.alist()
        if param.amode == "Two interlaced passes":
            try: param.astep = float(eval(self.Astep2.GetValue()))/2
            except ValueError: pass
            param.alist = self.alist()
        if param.amode == "Filling gaps":
            try: nangles = int(eval(self.NAngles.GetValue()))
            except ValueError: return
            param.astep = abs((param.amax-param.amin)/max(nangles-1,1))
            param.alist = self.alist()
        if param.amode == "User-defined list":
            param.alist = str_to_float_list(self.Alist.GetValue())
            if param.alist == []: param.alist = [Spindle.value]
            param.amin = min(param.alist); param.amax = max(param.alist)
            if param.amax == param.amin: param.astep = 0
            elif len(param.alist) > 1:
                param.astep = (param.amax-param.amin)/(len(param.alist)-1)
            else: param.astep = 10

        text = self.Lmode.Value
        text = text.lower().strip(",").replace(" ","").replace("/",",")
        variable_set_choices("laser_on",[x == "on" for x in text.split(",")])

        t = self.time_list(self.Tlist.Value)
        variable_set_choices("delay",t)
        self.Tlist.Value = (self.time_string_list(timepoints()))
        param.file_basename = str(self.Basename.Value)
        param.extension = str(self.Extension.Value)
        param.description = self.Description.Value
        param.logfile_filename = str(self.Logfile.Value)
        param.path = str(self.Path.Value)

        options.finish_series_variable = self.FinishSeriesVariable.StringSelection
        
        save_settings()
        self.update_parameters()

    def alist(self):
        """Generates a list of angles based on the current collection
        strategy and parameters, limited to the first 50 angles"""
        alist = []
        for i in range (0,min(50,nangles())):
            alist.append(variable_choice("angle",i))
        return alist

    def highlight_spindle_motor(self,event):
        event.Skip() # The default event handler needs to receive the event,too.
        self.Alabel.SetBackgroundStyle(wx.BG_STYLE_COLOUR)
        self.Alabel.SetForegroundColour(wx.Colour(128,128,128))

    def unhighlight_spindle_motor(self,event):
        event.Skip() # The default event handler needs to receive the event,too.
        self.Alabel.SetForegroundColour(self.Alabel.NormalForegroundColour)
        self.Alabel.SetBackgroundStyle(self.Alabel.NormalBackgroundStyle)

    def spindle_motor_context_menu(self,event):
        "Show context menu for spindle motor"
        menu = wx.Menu()
        menu.Append (1,"Configure...","")
        self.Bind (wx.EVT_MENU,self.configure_spindle_motor,id=1)        
        self.PopupMenu(menu)
        menu.Destroy()
    
    def configure_spindle_motor(self,event):
        "Show confugration panel for spindle motor"
        dlg = self.SpindleMotor(self)
        dlg.CenterOnParent()
        dlg.Show()

    class SpindleMotor(wx.Dialog):
        def __init__ (self,parent):
            wx.Dialog.__init__(self,parent,-1,"Scan Motor")

            layout = wx.GridBagSizer(1,1)
            a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL

            t = "This allows you to select a different motor rather than Phi."
            comment = wx.StaticText (self,label=t)

            text = wx.StaticText (self,label="Motor:")
            layout.Add(text,(0,0),flag=a,border=5)
            choices = ["Phi","LaserX","LaserZ","SampleX","SampleY",
                "SampleZ"]
            self.Motor = ComboBox(self,choices=choices,size=(200,-1))
            layout.Add(self.Motor,(0,1),flag=a)

            buttons = wx.BoxSizer()
            button = wx.Button(self,wx.ID_OK)
            button.SetDefault()
            buttons.Add (button)
            buttons.AddSpacer((10,10))
            self.Bind(wx.EVT_BUTTON,self.OnOK,button)
            button = wx.Button(self,wx.ID_CANCEL)
            buttons.Add (button) 

            # Leave a 10-pixel wide space around the panel.
            border = wx.BoxSizer(wx.VERTICAL)
            border.Add (comment,0,wx.ALL,10) 
            border.Add (layout,0,wx.ALL,10) 
            border.Add (buttons,0,wx.ALL,10) 
            self.SetSizer(border)
            self.Fit()

            self.update_parameters()

        def update_parameters(self,event=None):
            self.Motor.Value = (param.amotor)

        def OnOK(self,event):
            amotor = self.Motor.Value
            import lauecollect
            try:
                lauecollect.Spindle = eval(amotor)
                global Spindle; from lauecollect import Spindle
            except:
                message = "Unknown motor '%s'" % amotor
                dlg = wx.MessageDialog(self,message,"Spindle motor",wx.ICON_ERROR)
                dlg.CenterOnParent()
                dlg.ShowModal()
                dlg.Destroy()
                return
            param.amotor = amotor
            save_settings()
            self.Destroy()

        
    def set_strategy(self,event):
        dlg = DataCollectionPanel.Strategy (self)
        dlg.CenterOnParent()
        dlg.Show() 

    class Strategy (wx.Dialog):
        def __init__ (self,parent):
            wx.Dialog.__init__(self,parent,-1,"Strategy",size=(270,170))
            self.items = [0,1,2,3]
            self.items[0] = wx.RadioButton(self,-1,"Single pass",pos=(10,10),
                style=wx.RB_GROUP)
            self.items[1] = wx.RadioButton(self,-1,"Two interlaced passes",pos=(10,35))
            self.items[2] = wx.RadioButton(self,-1,"Filling gaps",pos=(10,60))
            self.items[3] = wx.RadioButton(self,-1,"User-defined list",pos=(10,85))
            for item in self.items: 
                if item.GetLabel() == param.amode: item.Value = (True)
            for item in self.items: self.Bind(wx.EVT_CHECKBOX,self.on_checked,item)

            button = wx.Button(self,wx.ID_OK,pos=(50,125))
            button.SetDefault()
            self.Bind(wx.EVT_BUTTON,self.OnOK,button)
            wx.Button(self,wx.ID_CANCEL,pos=(50+85,125))

        def on_checked(self,event):
            pass

        def OnOK(self,event):
            for item in self.items:
                if item.GetValue() == True: param.amode = item.GetLabel()
            self.Destroy()

    def generate_delay_list(self,event):
        tlist = self.time_list(self.Tlist.GetValue())
        dlg = DataCollectionPanel.GenerateDelayList (self,tlist)
        dlg.CenterOnParent()
        dlg.Show()

    class GenerateDelayList (wx.Dialog):
        def __init__ (self,parent,tlist):
            wx.Dialog.__init__(self,parent,-1,"Generate Time Series",size=(310,220))
            self.tlist = list(tlist)

            a = wx.ALIGN_CENTRE_VERTICAL

            border = wx.BoxSizer(wx.VERTICAL)

            frame = wx.StaticBox(self)
            box = wx.StaticBoxSizer(frame,wx.VERTICAL)

            self.lin = wx.CheckBox(self,label="Linear time series")
            box.Add(self.lin)
            group = wx.BoxSizer(wx.HORIZONTAL)
            group.Add(wx.StaticText(self,label="from"),flag=a)
            self.linmin = TextCtrl(self,size=(60,-1))
            group.Add(self.linmin,flag=a)
            group.Add(wx.StaticText(self,label="to"),flag=a)
            self.linmax = TextCtrl(self,size=(60,-1))
            group.Add(self.linmax,flag=a)
            group.Add(wx.StaticText(self,label="in"),flag=a)
            self.linsteps = TextCtrl (self,size=(25,-1))
            group.Add(self.linsteps,flag=a)
            group.Add(wx.StaticText(self,label="steps"),flag=a)
            box.Add(group)

            self.log = wx.CheckBox(self,label="Logarithmic time series")
            box.Add(self.log)
            group = wx.BoxSizer(wx.HORIZONTAL)
            group.Add(wx.StaticText(self,label="from"),flag=a)
            self.logmin = TextCtrl(self,size=(60,-1))
            group.Add(self.logmin,flag=a)
            group.Add(wx.StaticText(self,label="to"),flag=a)
            self.logmax = TextCtrl(self,size=(60,-1))
            group.Add(self.logmax,flag=a)
            group.Add(wx.StaticText(self,label="in"),flag=a)
            self.logsteps = TextCtrl (self,size=(25,-1))
            group.Add(self.logsteps,flag=a)
            group.Add(wx.StaticText(self,label="steps per decade"),flag=a)
            box.Add(group)

            # Leave a 5-pixel wide space around the panel.
            border.Add (box,0,wx.EXPAND|wx.ALL,5)

            frame = wx.StaticBox(self)
            box = wx.StaticBoxSizer(frame,wx.VERTICAL)

            group = wx.BoxSizer(wx.HORIZONTAL)
            group.Add(wx.StaticText(self,label="Insert "),flag=a)
            self.ref_timepoint = TextCtrl(self,size=(50,-1))
            group.Add(self.ref_timepoint,flag=a)
            group.Add(wx.StaticText(self,label=" images:"),flag=a)
            box.Add(group)
            group = wx.BoxSizer(wx.HORIZONTAL)
            self.at_beginning = wx.CheckBox(self,label="at beginning,")
            group.Add(self.at_beginning,flag=a)
            group.Add(wx.StaticText(self,label="every"),flag=a)
            self.EveryImages = TextCtrl(self,size=(25,-1))
            group.Add(self.EveryImages,flag=a)
            group.Add(wx.StaticText(self,label="images,"),flag=a)
            self.at_end = wx.CheckBox(self,label="at the end")
            group.Add(self.at_end,flag=a)
            box.Add(group)
            
            # Leave a 5-pixel wide space around the panel.
            border.Add (box,0,wx.EXPAND|wx.ALL,5)

            box = wx.BoxSizer(wx.VERTICAL)
            group = wx.BoxSizer(wx.HORIZONTAL)
            button = wx.Button(self,wx.ID_OK,pos=(70,165))
            button.SetDefault()
            self.Bind(wx.EVT_BUTTON,self.OnOK,button)
            group.Add(button,flag=a)
            button = wx.Button(self,wx.ID_CANCEL,pos=(70+85,165))
            group.Add(button,flag=a)
            box.Add(group)

            # Leave a 5-pixel wide space around the panel.
            border.Add (box,0,wx.EXPAND|wx.ALL,5)
            self.SetSizer(border)
            self.Fit()

            # Analyze the previous list of time point to obtain reasonable
            # stating values for the parameters.

            # Identify reference images.
            t = timepoints()
            counts = [t.count(tp) for tp in t]
            if len(t) > 0 and max(counts) >= 2:
                ref_timepoint = t[counts.index(max(counts))]
            else: ref_timepoint = param.ref_timepoint

            self.ref_timepoint.Value = (time_string(ref_timepoint))

            t = list(self.tlist) # make a copy of 'tlist' that can be modified
            if len(t) == 0: return
            if t[0] == ref_timepoint: self.at_beginning.Value = True
            n = len(t)
            if n>1 and t[n-1] == ref_timepoint: self.at_end.Value = True
            nref = t.count(ref_timepoint)
            if n>0 and t[0]==ref_timepoint: nref -= 1
            if n>1 and t[n-1]==ref_timepoint: nref -= 1
            if nref>0: ni = int(rint(float(n)/(nref+1))-1)
            else: ni = 0
            self.EveryImages.Value = str(ni)

            # Find the longest linear series
            # Ignore reference time points and 'off' images.
            while ref_timepoint in t: t.remove(ref_timepoint)
            while nan in t: t.remove(nan)
            if len(t) == 0: return
            n = len(t)
            begin_lin=0; end_lin=0
            if n>=2:
                begin=0; end=0
                for i in range(0,n-1):
                    try:
                        if abs ((t[i+1]-t[i]) / (t[begin+1]-t[begin]+1e-25) - 1) < 0.01:
                            end = i+1;
                            if end-begin > end_lin-begin_lin: begin_lin = begin; end_lin = end;
                        else: begin = i; end = i+1
                    except: begin = i; end = i+1
 
            # Find the longest logarithmic series.
            begin_log=0; end_log=0
            if n>=2:
                begin=0; end=0
                for i in range(0,n-1):
                    try:
                        if abs (log10(t[i+1]/t[i]) / (log10(t[begin+1]/t[begin])) - 1) < 0.01:
                            end = i+1;
                            if end-begin > end_log-begin_log: begin_log = begin; end_log = end;
                        else: begin = i; end = i
                    except: begin = i; end = i
            # Make sure that it does not overlap with the previously found
            # linear series (if the latter has at least three time points).
            if end_lin-begin_lin >= 2:
                if begin_log <= end_lin: begin_log = min(end_lin+1,n-1)
            if end_log-begin_log > 1: self.log.Value = (True)
            self.logmin.Value = (time_string(t[begin_log]))
            self.logmax.Value = (time_string(t[end_log]))
            if t[begin_log] != t[end_log]:
                steps_per_decade = (end_log-begin_log)/log10(t[end_log]/t[begin_log])
                self.logsteps.Value = ("%.2g" % steps_per_decade)

            # Make sure that linear series does not overlap with the
            # logarithmic series.
            if self.log.GetValue() == True:
                if end_lin >= begin_log: end_lin = begin_log-1
                if begin_lin > end_lin: begin_lin = end_lin
            if begin_lin >= 0: self.lin.Value = (True)
            if begin_lin >= 0: self.linmin.Value = (time_string(t[begin_lin]))
            if end_lin >= 0: self.linmax.Value = (time_string(t[end_lin]))
            if begin_lin >= 0: self.linsteps.Value = (str(end_lin-begin_lin))
                
        def OnOK(self,event):
            """generate delay list"""
            t = []
            # Does series start as linear?
            if self.lin.GetValue() == True:
                t1 = seconds(self.linmin.Value)
                t2 = seconds(self.linmax.Value)
                n = int(self.linsteps.Value)
                dt = (t2-t1)/max(n,1)
                for i in range(0,n+1): t.append(t1+i*dt)
            # Does series end as logrithmic?
            if self.log.GetValue() == True:
                t1 = self.log_timepoint(seconds(self.logmin.Value))
                t2 = self.log_timepoint(seconds(self.logmax.Value))
                if log10(t2) > log10(t1): sign = 1
                else: sign = -1
                dlogt = sign * abs(1/float(self.logsteps.Value))
                n = int(floor (abs(log10(t2)-log10(t1)) / dlogt - 0.001) + 1)
                for i in range(0,n): t.append(pow(10,log10(t1)+i*dlogt))
                t.append(t2)
            # Collect 'laser off' images?
            ref_timepoint = seconds(self.ref_timepoint.Value)
            try: ni = int(eval(self.EveryImages.Value))
            except: ni = 0
            if ni > 0:
                for i in range(int(round_up(len(t),ni))-ni,0,-ni):
                    t.insert(i,ref_timepoint)
            if self.at_beginning.Value == True: t.insert(0,ref_timepoint)
            if self.at_end.Value == True: t.append(ref_timepoint)
            param.ref_timepoint = ref_timepoint

            variable_set_choices("delay",next_delays(t))
            save_settings()
            self.Parent.update_parameters()
            self.Destroy()

        def log_timepoint(t):
            """If a time point of a 'logarithmic' time series is rounded to three
            decimal digits precision, this retores the excact missing digits,
            assuming that there are an integer number of points per decade,
            to a maximum of 20 points per decade."""
            if t <= 0: return t
            logt = log10(t)
            magnitude = 10**floor(logt)
            for n in range (1,21):
                T = 10**(round(logt*n)/n)
                if abs(t-T)/magnitude < 0.005: return T
            return t
        log_timepoint = staticmethod(log_timepoint)

    def on_browse(self,event):
        """Let sthe use select a destination directory where to save the data""" 
        pathname = str(self.Path.Value)
        from os.path import exists,dirname
        while pathname and not exists(pathname): pathname = dirname(pathname)
        dlg = wx.DirDialog(self, "Choose a directory:",style=wx.DD_DEFAULT_STYLE)
        # ShowModal pops up a dialog box and returns control only after the user
        # has selects OK or Cancel.
        dlg.Path = pathname
        if dlg.ShowModal() == wx.ID_OK:
            param.path = UNIX_pathname(str(dlg.Path))
            save_settings()
        dlg.Destroy()


class OptionsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent)

        # Controls
        e = wx.TE_PROCESS_ENTER
        self.NPulses = TextCtrl (self,size=(90,-1),style=e)
        self.BunchCount = wx.StaticText (self)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.NPulses)

        self.MinWaitT = TextCtrl (self,size=(90,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input_waitt,self.MinWaitT)
        self.MaxWaitT = TextCtrl (self,size=(90,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input_waitt,self.MaxWaitT)

        self.Passes = TextCtrl(self,size=(70,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.Passes)

        self.CollectionOrder = TextCtrl(self,size=(310,-1),style=e,name="Collection order")
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterCollectionOrder,self.CollectionOrder)
        self.CollectionOrderButton = wx.Button(self,label="Edit...",size=(60,-1))
        self.Bind(wx.EVT_BUTTON,self.OnCollectionOrder,self.CollectionOrderButton)

        self.IncludeInFilename = TextCtrl (self,size=(310,-1),style=e,name="Include in filename")
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterIncludeInFilename,self.IncludeInFilename)
        self.IncludeInFilenameButton = wx.Button(self,label="Edit...",size=(60,-1))
        self.Bind(wx.EVT_BUTTON,self.OnIncludeInFilename,self.IncludeInFilenameButton)

        self.WaitFor = TextCtrl (self,size=(310,-1),style=e,name="Wait for")
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterWaitFor,self.WaitFor)
        self.WaitForButton = wx.Button(self,label="Edit...",size=(60,-1))
        self.Bind(wx.EVT_BUTTON,self.OnWaitFor,self.WaitForButton)

        choices = ["on","off","off/on","off,on,off"]
        self.XRayOn = ComboBox(self,size=(370,-1),style=e,choices=choices)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.XRayOn)
        self.Bind (wx.EVT_COMBOBOX,self.on_input,self.XRayOn)

        self.UseVariableAttenuator = wx.Choice(self,size=(70,-1),
            choices=["Yes","No"])
        self.Bind (wx.EVT_CHOICE,self.OnUseVariableAttenuator,
            self.UseVariableAttenuator)

        self.TransmissionList = TextCtrl (self,size=(240,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.TransmissionList)

        self.EstimateCollectionTime = wx.Choice(self,size=(70,-1),
            choices=["Yes","No"])
        self.Bind (wx.EVT_CHOICE,self.on_input,self.EstimateCollectionTime)

        self.Suspend = wx.Button(self,size=(70,-1),label="Setup...")
        self.Bind (wx.EVT_BUTTON,self.OnSuspendSetup,self.Suspend)

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL
        size = (-1,-1)

        i = 0
        t = wx.StaticText(self,label="Pulses per image:",size=size)
        layout.Add (t,(i,0),flag=a)
        box = wx.BoxSizer()
        box.Add (self.NPulses,flag=a)
        box.Add (wx.StaticText(self,label=" (on,off) "),flag=a)
        box.Add (self.BunchCount,flag=a)
        layout.Add (box,(i,1),flag=a)

        i += 1
        t = wx.StaticText(self,label="Min. waiting time between pulses [s]:",size=size)
        layout.Add (t,(i,0),flag=a)
        box = wx.BoxSizer()
        box.Add (self.MinWaitT,flag=a)
        box.Add (wx.StaticText(self,label=" (on,off) "),flag=a)
        box.Add (wx.StaticText(self,label=" Max. "),flag=a)
        box.Add (self.MaxWaitT,flag=a)
        box.Add (wx.StaticText(self,label=" (off)"),flag=a)
        layout.Add (box,(i,1),flag=a)

        i += 1
        t = wx.StaticText(self,label="Number of repeats:",size=size)
        layout.Add (t,(i,0),flag=a)
        layout.Add (self.Passes,(i,1),flag=a)

        i += 1
        t = wx.StaticText(self,label="Collection order:",size=size)
        layout.Add (t,(i,0),flag=a)
        box = wx.BoxSizer()
        box.Add (self.CollectionOrder,flag=a|wx.EXPAND,proportion=1)
        box.Add (self.CollectionOrderButton,flag=a)
        layout.Add (box,(i,1),flag=a)

        i += 1
        t = wx.StaticText(self,label="Include in filename:",size=size)
        layout.Add (t,(i,0),flag=a)
        box = wx.BoxSizer()
        box.Add (self.IncludeInFilename,flag=a|wx.EXPAND,proportion=1)
        box.Add (self.IncludeInFilenameButton,flag=a)
        layout.Add (box,(i,1),flag=a)

        i += 1
        t = wx.StaticText(self,label="Suspend collection waiting for:",size=size)
        layout.Add(t,(i,0),flag=a)
        box = wx.BoxSizer()
        box.Add(self.WaitFor,flag=a|wx.EXPAND,proportion=1)
        box.Add(self.WaitForButton,flag=a)
        layout.Add(box,(i,1),flag=a)

        i += 1
        t = wx.StaticText(self,label="Image with X-Ray beam:",size=size)
        layout.Add (t,(i,0),flag=a)
        layout.Add (self.XRayOn,(i,1),flag=a)

        i += 1        
        t = wx.StaticText(self,label="Use Variable Attenuator:",size=size)
        layout.Add (t,(i,0),flag=a)
        box = wx.BoxSizer()
        box.Add (self.UseVariableAttenuator,flag=a)
        box.AddSpacer ((5,5))
        box.Add (wx.StaticText(self,label="Transm."),flag=a)
        box.AddSpacer ((5,5))
        box.Add (self.TransmissionList,flag=a)
        layout.Add (box,(i,1),flag=a)

        i += 1
        t = wx.StaticText(self,label="Suspend collection during Downtime:",size=size)
        layout.Add (t,(i,0),flag=a)
        layout.Add (self.Suspend,(i,1),flag=a)
        
        i += 1
        t = wx.StaticText(self,label="Estimate collection time:",size=size)
        layout.Add (t,(i,0),flag=a)
        layout.Add (self.EstimateCollectionTime,(i,1),flag=a)
        
        # Leave a 10-pixel wide space around the panel.
        box = wx.BoxSizer()
        box.Add (layout,0,wx.ALL,10) 
        self.SetSizer(box)

        # Periodically refresh the panel
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Periodically update the panel."""
        if IsShownOnScreen(self):
            self.update_parameters()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update_parameters(self,event=None):
        reload_settings()
        if options.npulses == options.npulses_off: text = "%d" % options.npulses
        else: text = "%d,%d" % (options.npulses,options.npulses_off)
        self.NPulses.Value = text
        i = task.image_number
        s = "(%g openings x %g pulses/open = %g pulses)" % \
            (npulses(i),chopper_pulses(i),npulses(i)*chopper_pulses(i))
        self.BunchCount.SetLabel(s)
        
        s = "%.3f" % options.min_waitts[0]
        for t in options.min_waitts[1:]: s += ",%.3f" % t
        if len(options.min_waitts) > 1 or options.min_waitt_off != options.min_waitts[0]:
            s += ",%.3f" % options.min_waitt_off
        self.MinWaitT.Value = (s)
        text = ""
        if collection_variable_enabled("repeat"):
            text += "%s," % options.npasses
        if collection_variable_enabled("repeat2"):
            text += "%s," % options.npasses2
        text = text.rstrip(",")
        self.Passes.Value = text

        self.CollectionOrder.Value = \
            collection_order_to_string(collection_variable_order())
        self.IncludeInFilename.Value = \
            collection_order_to_string(options.variable_include_in_filename)
        self.WaitFor.Value = ",".join(
            [name for name in collection_variables() if variable_wait(name)])

        self.MaxWaitT.Value = "%.3f" % options.max_waitt_off

        separator = "/" if len(options.xray_on) <= 2 else ","
        s = separator.join(["on" if x else "off" for x in options.xray_on])
        self.XRayOn.Value = s
        self.XRayOn.Size = (70,-1) if len(options.xray_on) <= 2 else (370,-1)

        if collection_variable_enabled("level"): text = "Yes"
        else: text = "No"
        self.UseVariableAttenuator.StringSelection = text
        tlist = ["%.3g" % t for t in variable_choices("level")]
        text = ", ".join(tlist)
        self.TransmissionList.Value = text
        self.TransmissionList.Enable(collection_variable_enabled("level"))

        text = "Yes" if options.estimate_collection_time else "No"
        self.EstimateCollectionTime.SetStringSelection(text)

    def on_input(self, event):
        """This is called when the user switches between fields and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        values = self.NPulses.Value.split(",")
        if len(values) < 2: values *= 2
        try: options.npulses = int(eval(values[0]))
        except: pass
        try: options.npulses_off = int(eval(values[1]))
        except: pass

        text = self.Passes.Value
        if "," in text:
            try: options.npasses,options.npasses2 = eval(text)
            except: pass
        else:
            try: options.npasses,options.npasses2 = int(eval(text)),1
            except: pass
        text = self.CollectionOrder.Value
        ##try: collection_variable_set_order(collection_order_from_string(text))
        ##except Exception,msg: warn("Collection order: %r: %s" % (text,msg))
        ##try: options.variable_include_in_filename = \
        ##    flatten(collection_order_from_string(self.IncludeInFilename.Value))
        ##except: pass

        text = self.XRayOn.Value
        text = text.lower().strip(",").replace(" ","").replace("/",",")
        options.xray_on = [x == "on" for x in text.split(",")]

        text = self.TransmissionList.Value
        text = text.replace("off","nan")
        levels = str_to_float_list(text)
        for i in range(0,len(levels)):
            if isnan(levels[i]): levels[i] = None
        if len(levels) == 0: levels = [1.0]
        variable_set_choices("level",levels)

        options.estimate_collection_time = \
            (self.EstimateCollectionTime.StringSelection == "Yes")

        save_settings()
        self.update_parameters()

    def OnEnterCollectionOrder(self,event):
        text = self.CollectionOrder.Value
        try: collection_variable_set_order(collection_order_from_string(text))
        except Exception,msg: warn("Collection order: %r: %s" % (text,msg))
        save_settings()
        self.update_parameters()
        
    def OnEnterIncludeInFilename(self,event):
        try: options.variable_include_in_filename = \
            flatten(collection_order_from_string(self.IncludeInFilename.Value))
        except: pass
        save_settings()
        self.update_parameters()

    def OnEnterWaitFor(self,event):
        text = self.WaitFor.Value.replace(" ","")
        names = text.split(",")
        for name in variables(): variable_set_wait(name,name in names)
        save_settings()
        self.update_parameters()

    def on_input_waitt (self,event):
        values = self.MinWaitT.Value.split(",")
        if len(values) < 2: values *= 2
        try: options.min_waitt_off = float(eval(values[1]))
        except: pass
        values = values[0].split(",")
        try: options.min_waitts = [float(eval(value)) for value in values]
        except: pass
        value = self.MaxWaitT.GetValue()
        try: options.max_waitt_off = float(eval(value))
        except: pass
        
        # Round waiting time to closest value allowed by hardware.
        for i in range(0,len(options.min_waitts)):
            if options.min_waitts[i] <= timing_system.waitt.max:
                options.min_waitts[i] = \
                    round_next(options.min_waitts[i],timing_system.waitt.stepsize)
                options.min_waitts[i] = max(timing_system.waitt.min,options.min_waitts[i])
        if options.min_waitt_off <= timing_system.waitt.max:
            options.min_waitt_off = \
                round_next(options.min_waitt_off,timing_system.waitt.stepsize)
            options.min_waitt_off = max(timing_system.waitt.min,options.min_waitt_off)
        if options.max_waitt_off <= timing_system.waitt.max:
            options.max_waitt_off = \
                round_next(options.max_waitt_off,timing_system.waitt.stepsize)
            options.max_waitt_off = max(timing_system.waitt.min,options.max_waitt_off)

        options.min_waitts.sort()

        save_settings()
        self.update_parameters()

    def OnUseVariableAttenuator(self, event):
        # This field needs a separate input handler, becuase it could contradict
        # the "Collection order" field.
        enabled = (self.UseVariableAttenuator.StringSelection == "Yes")
        collection_variable_set_enabled("level",enabled)
        save_settings()
        self.update_parameters()

    def OnCollectionOrder(self,event):
        dlg = self.CollectionOrderPanel(self)
        dlg.CenterOnParent()
        dlg.Show() 

    class CollectionOrderPanel(wx.Dialog):
        def __init__ (self,parent):
            wx.Dialog.__init__(self,parent,-1,"Collection Order")
            box = wx.BoxSizer(wx.VERTICAL)
            flag = wx.ALIGN_CENTER_HORIZONTAL
            names = variables()
            self.Variables = [None]*len(names)
            self.Links = [None]*(len(names)-1)
            self.linked = wx.ArtProvider.GetBitmap(wx.ART_CROSS_MARK)
            self.unlinked = wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN)
            ## self.linked = wx.Bitmap("image.png", wx.BITMAP_TYPE_ANY)
            for i in range(0,len(names)):
                self.Variables[i] = wx.CheckBox(self,size=(160,-1))
                box.Add(self.Variables[i],flag)
                if i<len(names)-1:
                    style = wx.BORDER_NONE
                    self.Links[i] = wx.ToggleButton(self,style=style)
                    self.Links[i].Bitmap = wx.EmptyBitmapRGBA(1,1)
                    box.Add(self.Links[i],flag)
            self.Bind(wx.EVT_CHECKBOX,self.OnChange)
            self.Bind(wx.EVT_TOGGLEBUTTON,self.OnChange)

            # Leave a 5-pixel wide space around the panel.
            border = wx.BoxSizer(wx.VERTICAL)
            border.Add (box,0,wx.EXPAND|wx.ALL,5)
            self.SetSizer(border)
            self.Fit()
            
            # Periodically update the panel
            self.timer = wx.Timer(self)
            self.Bind (wx.EVT_TIMER,self.OnTimer)
            self.OnTimer()

        def OnTimer(self,event=None):
            """Periodically update the panel"""
            self.refresh()
            self.timer.Start(1000,oneShot=True) # Need to restart the Timer

        def refresh(self,event=None):
            reload_settings()
            used = {}
            i = 0
            for names in collection_variable_order():
                for j in range(0,len(names)):
                    used[names[j]] = True
                    if i<len(self.Variables):
                        self.Variables[i].Label = names[j]
                        self.Variables[i].Value = True
                    linked = j>0
                    if 0 <= i-1 < len(self.Links):
                        self.Links[i-1].Bitmap = \
                            self.linked if linked else self.unlinked
                        self.Links[i-1].Value = linked
                        self.Links[i-1].Shown = True
                    i += 1
            for name in variables():
                if not name in used:
                    if i<len(self.Variables):
                        self.Variables[i].Label = name
                        self.Variables[i].Value = False
                    if 0 <= i-1 < len(self.Links):
                        self.Links[i-1].Bitmap = wx.EmptyBitmapRGBA(1,1)
                        self.Links[i-1].Value = False
                        self.Links[i-1].Shown = False
                    i += 1
            self.Fit()

        def OnChange(self,event):
            order = []
            group = []
            for i in range(0,len(self.Variables)):
                if self.Variables[i].Value == True:
                    group += [str(self.Variables[i].Label)]
                if i<len(self.Links) and self.Links[i].Value == False:
                    if len(group)>0: order += [group]
                    group = []
            if len(group)>0: order += [group]
            collection_variable_set_order(order)
            self.refresh()

    def OnIncludeInFilename(self,event):
        dlg = self.IncludeInFilenamePanel(self)
        dlg.CenterOnParent()
        dlg.Show() 

    class IncludeInFilenamePanel(wx.Dialog):
        def __init__ (self,parent):
            wx.Dialog.__init__(self,parent,-1,"Include in Filname")
            box = wx.BoxSizer(wx.VERTICAL)
            flag = wx.ALIGN_CENTER_HORIZONTAL
            names = variables()
            self.Variables = [None]*len(names)
            for i in range(0,len(names)):
                self.Variables[i] = wx.CheckBox(self,size=(160,-1))
                box.Add(self.Variables[i],flag)
            self.Bind(wx.EVT_CHECKBOX,self.OnChange)

            # Leave a 5-pixel wide space around the panel.
            border = wx.BoxSizer(wx.VERTICAL)
            border.Add (box,0,wx.EXPAND|wx.ALL,5)
            self.SetSizer(border)
            self.Fit()

            # Periodically update the panel
            self.timer = wx.Timer(self)
            self.Bind (wx.EVT_TIMER,self.OnTimer)
            self.OnTimer()

        def OnTimer(self,event=None):
            """Periodically update the panel"""
            self.refresh()
            self.timer.Start(1000,oneShot=True) # Need to restart the Timer

        def refresh(self,event=None):
            reload_settings()
            used = {}
            i = 0
            for name in options.variable_include_in_filename:
                used[name] = True
                if i<len(self.Variables):
                    self.Variables[i].Label = name
                    self.Variables[i].Value = True
                i += 1
            for name in variables():
                if not name in used:
                    if i<len(self.Variables):
                        self.Variables[i].Label = name
                        self.Variables[i].Value = False
                    i += 1
            self.Fit()

        def OnChange(self,event):
            names = []
            for i in range(0,len(self.Variables)):
                if self.Variables[i].Value == True:
                    names += [str(self.Variables[i].Label)]
            options.variable_include_in_filename = names
            self.refresh()

    def OnWaitFor(self,event):
        dlg = self.WaitForPanel(self)
        dlg.CenterOnParent()
        dlg.Show() 

    class WaitForPanel(wx.Dialog):
        def __init__ (self,parent):
            wx.Dialog.__init__(self,parent,-1,"Wait For")
            box = wx.BoxSizer(wx.VERTICAL)
            flag = wx.ALIGN_CENTER_HORIZONTAL
            names = variables()
            self.Variables = [None]*len(names)
            for i in range(0,len(names)):
                self.Variables[i] = wx.CheckBox(self,size=(160,-1))
                box.Add(self.Variables[i],flag)
            self.Bind(wx.EVT_CHECKBOX,self.OnChange)

            # Leave a 5-pixel wide space around the panel.
            border = wx.BoxSizer(wx.VERTICAL)
            border.Add (box,0,wx.EXPAND|wx.ALL,5)
            self.SetSizer(border)
            self.Fit()

            # Periodically update the panel
            self.timer = wx.Timer(self)
            self.Bind (wx.EVT_TIMER,self.OnTimer)
            self.OnTimer()

        def OnTimer(self,event=None):
            """Periodically update the panel"""
            self.refresh()
            self.timer.Start(1000,oneShot=True) # Need to restart the Timer

        def refresh(self,event=None):
            reload_settings()
            for (i,name) in enumerate(variables()):
                self.Variables[i].Label = name
                self.Variables[i].Value = variable_wait(name)
            self.Fit()

        def OnChange(self,event):
            names = []
            for i in range(0,len(self.Variables)):
                value = self.Variables[i].Value
                name = str(self.Variables[i].Label)
                variable_set_wait(name,value)
            self.refresh()

    def OnSuspendSetup(self,event=None):
        """Bring up control panel to configure when collection is suspended"""
        from ChecklistPanel import ChecklistPanel
        dlg = ChecklistPanel(self)
        dlg.CenterOnParent()
        dlg.Show()

def collection_order_from_string(s):
    """ 'laser_on,[delay,translation_mode],repeat' ->
    [['laser_on'], ['delay', 'translation_mode'], ['repeat']]"""
    s = s.strip()
    # Define variable names
    for name in variables(): locals()[name] = name
    order = eval(s)
    if isinstance(order,basestring) or not hasattr(order,"__len__"):
        order = [order]
    order = list(order)
    for i in range(0,len(order)):
        if isinstance(order[i],basestring) or not hasattr(order[i],"__len__"):
            order[i] = [order[i]]
    for i in range(len(order)-1,-1,-1):
        for j in range(len(order[i])-1,-1,-1):
            if not isinstance(order[i][j],basestring): del order[i][j]
    for i in range(len(order)-1,-1,-1):
        if len(order[i]) == 0: del order[i]
    return order

def collection_order_to_string(order):
    """[['laser_on'], ['delay', 'translation_mode'], ['repeat']]
    -> 'laser_on,[delay,translation_mode],repeat'"""
    order = list(order) # make a copy
    for i in range(0,len(order)):
        if len(order[i]) == 1: order[i] = order[i][0]
    s = repr(order)
    if s.startswith("["): s = s[1:]
    if s.endswith("]"): s = s[:-1]
    s = s.replace("'","")
    return s
    
class DetectorPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent)

        # Controls
        e = wx.TE_PROCESS_ENTER

        self.DetectorEnabled = wx.Choice(self,size=(70,-1),choices=["Yes","No"])
        self.Bind (wx.EVT_CHOICE,self.on_input,self.DetectorEnabled)

        self.BinFactor = TextCtrl (self,size=(40,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.BinFactor)

        self.AlignmentBinFactor = TextCtrl (self,size=(40,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.AlignmentBinFactor)

        self.UseHardwareTrigger = wx.Choice(self,size=(70,-1),choices=["Yes","No"])
        self.Bind (wx.EVT_CHOICE,self.on_input,self.UseHardwareTrigger)

        self.ReadoutMode = wx.Choice(self,size=(140,-1),choices=["Frame Transfer","Bulb"])
        self.Bind (wx.EVT_CHOICE,self.on_input,self.UseHardwareTrigger)

        self.SaveRawImage = wx.Choice(self,size=(70,-1),choices=["Yes","No"])
        self.Bind (wx.EVT_CHOICE,self.on_input,self.SaveRawImage)

        self.PeriodicallyReadCCD = wx.Choice(self,size=(70,-1),choices=["Yes","No"])
        self.Bind (wx.EVT_CHOICE,self.on_input,self.PeriodicallyReadCCD)

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL
        size = (-1,-1)

        t = wx.StaticText(self,label="Enabled:",size=size)
        layout.Add (t,(0,0),flag=a)
        layout.Add (self.DetectorEnabled,(0,1),flag=a)

        t = wx.StaticText(self,label="Bin Factor (Data Collection):",size=size)
        layout.Add (t,(2,0),flag=a)
        layout.Add (self.BinFactor,(2,1),flag=a)

        t = wx.StaticText(self,label="Bin Factor (Alignment):",size=size)
        layout.Add (t,(3,0),flag=a)
        layout.Add (self.AlignmentBinFactor,(3,1),flag=a)
         
        t = wx.StaticText(self,label="Use Hardware Trigger:",size=size)
        layout.Add (t,(5,0),flag=a)
        layout.Add (self.UseHardwareTrigger,(5,1),flag=a)

        t = wx.StaticText(self,label="Readout mode:",size=size)
        layout.Add (t,(6,0),flag=a)
        layout.Add (self.ReadoutMode,(6,1),flag=a)

        t = wx.StaticText(self,label="Save Images in Raw Format:",size=size)
        layout.Add (t,(7,0),flag=a)
        layout.Add (self.SaveRawImage,(7,1),flag=a)

        t = wx.StaticText(self,label="Periodically Read CCD When Idle:",size=size)
        layout.Add (t,(8,0),flag=a)
        layout.Add (self.PeriodicallyReadCCD,(8,1),flag=a)
                
        # Leave a 10-pixel wide space around the panel.
        box = wx.BoxSizer()
        box.Add (layout,0,wx.ALL,10) 
        self.SetSizer(box)

        # Periodically refresh the panel
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Periodically update the panel"""
        if IsShownOnScreen(self):
            self.update_parameters()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update_parameters(self,event=None):
        text = "Yes" if options.xray_detector_enabled else "No"
        self.DetectorEnabled.StringSelection = text

        self.BinFactor.Value = (str(options.ccd_bin_factor))
        self.AlignmentBinFactor.Value = (str(align.ccd_bin_factor))
 
        text = "Yes" if options.ccd_hardware_trigger else "No"
        self.UseHardwareTrigger.StringSelection = text

        text = "Bulb" if options.ccd_readout_mode == "bulb" else "Frame Transfer"
        self.ReadoutMode.StringSelection = text

        text = "Yes" if options.save_raw_image else "No"
        self.SaveRawImage.StringSelection = text

        text = "Yes" if options.periodically_read_ccd else "No"
        self.PeriodicallyReadCCD.StringSelection = text

    def on_input(self, event):
        """This is called when te use switches between feilds and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        options.xray_detector_enabled = \
            (self.DetectorEnabled.StringSelection == "Yes")

        try: options.ccd_bin_factor = int(eval(self.BinFactor.Value))
        except ValueError: pass
        try: align.ccd_bin_factor = int(eval(self.AlignmentBinFactor.Value))
        except ValueError: pass

        options.ccd_hardware_trigger = \
            (self.UseHardwareTrigger.StringSelection == "Yes")

        options.ccd_readout_mode = \
            "bulb" if self.ReadoutMode.StringSelection == "Bulb" \
            else "frame transfer"

        options.save_raw_image = \
            (self.SaveRawImage.StringSelection == "Yes")

        options.periodically_read_ccd = \
            (self.PeriodicallyReadCCD.StringSelection == "Yes")

        save_settings()
        self.update_parameters()

class TemperaturePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent)

        # Controls
        e = wx.TE_PROCESS_ENTER

        self.IsEnabled = wx.Choice (self,choices=["Yes","No"])
        self.Bind (wx.EVT_CHOICE,self.on_input,self.IsEnabled)

        self.Temperatures = TextCtrl (self,size=(500,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.Temperatures)

        self.HardwareTriggered = wx.CheckBox(self,label="Hardware triggered,")
        self.Bind (wx.EVT_CHECKBOX,self.on_input,self.HardwareTriggered)

        self.Step = TextCtrl (self,size=(50,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.Step)

        self.SettlingTime = TextCtrl (self,size=(50,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.SettlingTime)

        self.Return = wx.CheckBox(self,label="After collection, return to")
        self.Bind (wx.EVT_CHECKBOX,self.on_input,self.Return)

        self.ReturnValue = TextCtrl (self,size=(50,-1),style=e)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.ReturnValue)

        self.UseStartingValue = wx.CheckBox(self,label="Use starting value")
        self.Bind (wx.EVT_CHECKBOX,self.on_input_use_starting_value,
            self.UseStartingValue)

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL
        i = 0
        t = wx.StaticText(self,label="Enabled:")
        layout.Add (t,(i,0),flag=a)
        layout.Add (self.IsEnabled,(i,1),flag=a)
        i += 1
        t = wx.StaticText(self,label="Temperatures:")
        layout.Add (t,(i,0),flag=a)
        layout.Add (self.Temperatures,(i,1),span=(1,5),flag=a)
        i += 1
        layout.Add (self.Return,(i,1),span=(1,2),flag=a)
        layout.Add (self.ReturnValue,(i,3),flag=a)
        layout.Add (self.UseStartingValue,(i,4),span=(1,2),flag=a)
        i += 1
        layout.Add (self.HardwareTriggered,(i,1),flag=a)
        t = wx.StaticText(self,label="step")
        layout.Add (t,(i,2),flag=a)
        layout.Add (self.Step,(i,3),flag=a)
        t = wx.StaticText(self,label="settling time")
        layout.Add (t,(i,4),flag=a)
        layout.Add (self.SettlingTime,(i,5),flag=a)
                
        # Leave a 10-pixel wide space around the panel.
        box = wx.BoxSizer()
        box.Add (layout,0,wx.ALL,10) 
        self.SetSizer(box)

        # Periodically refresh the panel
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Periodically update the panel"""
        if IsShownOnScreen(self):
            self.update_parameters()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update_parameters(self,event=None):
        reload_settings()
        enabled = collection_variable_enabled("temperature")
        self.IsEnabled.StringSelection = "Yes" if enabled else "No"
        values = variable_choices("temperature")
        self.Temperatures.Value = list_to_string(values)
        self.Temperatures.Enabled = enabled
        self.Return.Value = variable_return("temperature")
        self.ReturnValue.Value = "%.3f" % \
            collection_variable_return_value("temperature")
        self.ReturnValue.Enabled = variable_return("temperature") \
            and not collection_variable_return_to_starting_value("temperature")
        self.UseStartingValue.Value = \
            collection_variable_return_to_starting_value("temperature")
        self.UseStartingValue.Enabled = variable_return("temperature")
        self.HardwareTriggered.Value = temp.hardware_triggered
        self.HardwareTriggered.Enabled = enabled
        self.Step.Value = str(temp.step)
        self.Step.Enabled = temp.hardware_triggered and enabled
        self.SettlingTime.Value = "%g s" % temp.settling_time
        self.SettlingTime.Enabled = not temp.hardware_triggered and enabled

    def on_input(self,event):
        """Save changes to any field made by the user."""
        enabled = (self.IsEnabled.StringSelection == "Yes")
        collection_variable_set_enabled("temperature",enabled)

        values = string_to_list(self.Temperatures.Value)
        variable_set_choices("temperature",values)
        variable_set_return("temperature",self.Return.Value)
        text = self.ReturnValue.Value
        try: value = float(eval(text))
        except: value = nan
        collection_variable_set_return_value("temperature",value)
        temp.hardware_triggered = self.HardwareTriggered.Value
        text = self.Step.Value
        try: temp.step = float(eval(text))
        except: pass
        text = self.SettlingTime.Value
        try: temp.settling_time = float(eval(text.replace("s","")))
        except: pass

        save_settings()
        self.update_parameters()

    def on_input_use_starting_value(self,event):
        """Save changes to the "Use starting value" field made by the user."""
        collection_variable_set_return_to_starting_value("temperature",
            self.UseStartingValue.Value)
        save_settings()
        self.update_parameters()


class AlignPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)
 
        wx.StaticText (self,-1,"Auto align sample:",pos=(10,10+3))
        self.AlignmentEnabled = ComboBox(self,pos=(150,10-2),size=(70,-1),
            choices=['on','off'],style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX,self.on_input)

        # StaticText size needed because of bug in WX 2.6 or older.
        wx.StaticText (self,label="Probe depth:",pos=(10,40+3),size=(130,-1)) 
        self.Beamsize = TextCtrl (self,pos=(150,40),size=(70,-1),
            style=wx.TE_PROCESS_ENTER)
        wx.StaticText (self,label="mm  (should match vert. X-ray beam size)",
            pos=(225,40+3))
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.Beamsize)

        wx.StaticText (self,label="Start scan:",pos=(10,70+3))
        self.ScanOffset = TextCtrl (self,pos=(150,70),size=(70,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.ScanOffset)
        wx.StaticText (self,label="mm from edge",pos=(225,70+3))

        wx.StaticText (self,label="Vertical step size:",pos=(10,100+3))
        self.StepSize = TextCtrl (self,pos=(150,100),size=(70,-1),
            style=wx.TE_PROCESS_ENTER)
        wx.StaticText (self,label="mm",pos=(225,100+3))
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input,self.StepSize)

        wx.StaticText (self,label="Align at:",pos=(10,130+3))
        self.AlignAtCollectionPhis = wx.Choice (self,pos=(150,130),
            size=(130,-1),choices=["Collection Phis","Edge Phis"])
        self.Bind (wx.EVT_CHOICE,self.on_input,self.AlignAtCollectionPhis)

        self.AlignAtCollectionZs = wx.Choice (self,pos=(150+130+10,130),
            size=(130,-1),choices=["Collection Zs","Edge Zs"])
        self.Bind (wx.EVT_CHOICE,self.on_input,self.AlignAtCollectionZs)

        wx.StaticText (self,label="Interpolate within:",pos=(10,160+3))
        self.DPhi = TextCtrl (self,pos=(150,160),size=(70,-1),
            style=wx.TE_PROCESS_ENTER)
        wx.StaticText (self,label="deg",pos=(150+70+5,160+3))

        self.DZ = TextCtrl (self,pos=(150+130+10,160),size=(70,-1),
            style=wx.TE_PROCESS_ENTER)
        wx.StaticText (self,label="mm",pos=(150+130+10+70+5,160+3))

        button = wx.Button(self,label="More Options...",pos=(10,195),
            size=(130,-1))
        self.Bind (wx.EVT_BUTTON,self.more_options,button)

        self.Summary = wx.StaticText (self,pos=(10,230),size=(500,40))
        self.Status = wx.StaticText (self,pos=(10,230+45),size=(500,-1))

        self.align_button = wx.Button(self,label="Align Sample",pos=(10,300),
            size=(130,-1))
        self.align_button.SetDefault()
        self.Bind (wx.EVT_BUTTON,self.align_sample,self.align_button)
        self.cancel_button = wx.Button(self,label="Cancel",pos=(150,300),
            size=(130,-1))
        self.Bind (wx.EVT_BUTTON,self.cancel,self.cancel_button)
        self.plot_button = wx.Button(self,-1,"Plot Scan...",pos=(290,300),
            size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.plot_data,self.plot_button)
        
        # Periodically update the displayed fields.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Periodically update the panel"""
        if IsShownOnScreen(self):
            self.update_parameters(self)
            self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update(self,event=None):
        """Update status message and button states."""
        reload_settings()
        
        self.Summary.SetLabel(alignment_summary())
        self.Status.SetLabel(status.alignment_status)

        if not task.action:
           self.align_button.Enable()
           self.cancel_button.Enable(False)
        else:
           self.align_button.Enable(False)
           self.cancel_button.Enable()
        if not task.cancelled: self.cancel_button.SetLabel("Cancel")
        else: self.cancel_button.SetLabel("Cancel")
        if len(align.profile) > 0: self.plot_button.Enable()
        else: self.plot_button.Enable(False)
 
    def update_parameters(self,event=None):
        reload_settings()
        if align.enabled: self.AlignmentEnabled.Value = "on"
        else: self.AlignmentEnabled.Value = "off"
        self.Beamsize.Value = "%.3f" % align.beamsize
        self.ScanOffset.Value = "%.3f" % align.scan_offset
        self.StepSize.Value = "%.3f" % align.step
        self.AlignAtCollectionPhis.Selection = \
            0 if align.align_at_collection_phis else 1
        self.AlignAtCollectionZs.Selection = \
            0 if align.align_at_collection_zs else 1
        self.DPhi.Value = "%g" % align.intepolation_dphi
        self.DPhi.Enabled = align.align_at_collection_phis
        self.DZ.Value = "%.3f" % align.intepolation_dz
        self.DZ.Enabled = align.align_at_collection_zs

    def on_input(self, event):
        """This is called when the user switches between fields and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        align.enabled = self.AlignmentEnabled.Value == "on"
        try: align.beamsize = float(eval(self.Beamsize.Value))
        except ValueError: pass
        try: align.scan_offset = float(eval(self.ScanOffset.Value))
        except ValueError: pass
        try: align.step = float(eval(self.StepSize.Value))
        except ValueError: pass
        align.align_at_collection_phis = \
            (self.AlignAtCollectionPhis.Selection == 0)
        align.align_at_collection_zs = \
            (self.AlignAtCollectionZs.Selection == 0)
        try: align.intepolation_dphi = float(eval(self.DPhi.Value))
        except ValueError: pass
        try: align.intepolation_dz = float(eval(self.DZ.Value))
        except ValueError: pass
        save_settings()
        self.update_parameters()

    def align_sample(self,event):
        "Start alignemt scan."
        task.action = "Align Sample"

    def cancel(self,event): 
        "Abort alignment scan."
        task.cancelled = True; task.action = ""

    def plot_data(self,event):
        from Plot import Plot
        Plot(align.profile)

    def more_options(self,event):
        dlg = self.Options (self)
        dlg.CenterOnParent()
        dlg.Show() 

    class Options (wx.Dialog):
        def __init__ (self,parent):
            wx.Dialog.__init__(self,parent,-1,"Alignment Scan Options")

            layout = wx.GridBagSizer(1,1)
            a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL

            row = 0
            text = wx.StaticText (self,label="Number of X-ray pulses:")
            layout.Add(text,(row,0),flag=a,border=5)
            self.NPulses = TextCtrl(self,size=(50,-1))
            layout.Add(self.NPulses,(row,1),flag=a)

            row += 1
            text = wx.StaticText (self,label="X-ray pulses spacing [s]:")
            layout.Add(text,(row,0),flag=a,border=5)
            self.WaitT = TextCtrl(self,size=(50,-1))
            layout.Add(self.WaitT,(row,1),flag=a)

            row += 1
            text = wx.StaticText (self,label="Attenuate X-ray beam:")
            layout.Add(text,(row,0),flag=a,border=5)
            self.AttenuateXray = wx.Choice(self,size=(50,-1),choices=["Yes","No"])
            layout.Add(self.AttenuateXray,(row,1),flag=a)

            row += 1
            text = wx.StaticText (self,label="Peak search threshold [5.0]:")
            layout.Add(text,(row,0),flag=a,border=5)
            self.Threshold = TextCtrl(self,size=(50,-1))
            layout.Add(self.Threshold,(row,1),flag=a)

            row += 1
            text = wx.StaticText (self,label="Points for slope calculation [5]:")
            layout.Add(text,(row,0),flag=a,border=5)
            self.NPoints = TextCtrl(self,size=(50,-1))
            layout.Add(self.NPoints,(row,1),flag=a)

            row += 1
            text = wx.StaticText (self,label="Min. number of scan points [7]:")
            layout.Add(text,(row,0),flag=a,border=5)
            self.MinPoints = TextCtrl(self,size=(50,-1))
            layout.Add(self.MinPoints,(row,1),flag=a)

            buttons = wx.BoxSizer()
            button = wx.Button(self,wx.ID_OK)
            button.SetDefault()
            buttons.Add (button)
            buttons.AddSpacer ((10,10))
            self.Bind(wx.EVT_BUTTON,self.OnOK,button)
            button = wx.Button(self,wx.ID_CANCEL)
            buttons.Add (button) 

            # Leave a 10-pixel wide space around the panel.
            border = wx.BoxSizer(wx.VERTICAL)
            border.Add (layout,0,wx.ALL,10) 
            border.Add (buttons,0,wx.ALL,10) 
            self.SetSizer(border)
            self.Fit()

            self.update_parameters()

        def update_parameters(self,event=None):
            self.NPulses.Value = tostr(align.npulses)
            self.WaitT.Value = tostr(align.waitt)
            self.AttenuateXray.StringSelection = \
                "Yes" if align.attenuate_xray else "No"
            self.Threshold.Value = (tostr(align.threshold))
            self.NPoints.Value = (tostr(align.npoints))

            self.MinPoints.Value = (tostr(align.min_scanpoints))

        def OnOK(self,event):
            try: align.npulses = abs(int(eval(self.NPulses.Value)))
            except: pass
            try: align.waitt = timing_system.waitt.next(abs(float(eval(self.WaitT.Value))))
            except: pass
            align.attenuate_xray = (self.AttenuateXray.StringSelection == "Yes")
            try: align.threshold = abs(float(eval(self.Threshold.Value)))
            except: pass
            try:
                align.npoints = int(eval(self.NPoints.Value))
            except: pass
            if align.npoints % 2 != 1: align.npoints += 1 # must be odd number
            if align.npoints < 3: align.npoints = 3

            try: align.min_scanpoints = eval(self.MinPoints.Value)
            except: pass
            try: align.min_scanpoints = abs(int(align.min_scanpoints))
            except: pass

            save_settings()
            self.Destroy()

class TranslatePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)
 
        mode = hbox = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText (self,-1,"Translate sample:",size=(120,-1))
        hbox.Add (label,flag=wx.ALIGN_CENTER)
        choices=["off","during image","after image","during image+after image",
            "continuous","linear stage","grid scan"]
        self.TranslateMode = wx.Choice(self,choices=choices)
        hbox.Add (self.TranslateMode,flag=wx.ALIGN_CENTER)
        hbox.AddSpacer((5,5))
        self.HardwareTriggered = wx.CheckBox(self,label="Hardware Triggered")
        hbox.Add (self.HardwareTriggered,flag=wx.ALIGN_CENTER)
        self.Bind(wx.EVT_CHOICE,self.on_input)

        # Extra Parameters for translation during image
        self.duringImage = panel = wx.Panel(self)
        panel.Step = TextCtrl(panel,size=(50,-1),style=wx.TE_PROCESS_ENTER)
        panel.NSpots = TextCtrl(panel,size=(30,-1),style=wx.TE_PROCESS_ENTER)
        panel.interleave = TextCtrl(panel,size=(25,-1),style=wx.TE_PROCESS_ENTER)
        panel.single = wx.CheckBox(panel,label="1 shot per pass")
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL
        border = 2
        label = wx.StaticText(panel,label="During image step:",size=(120,-1))
        hbox.Add (label,flag=flag)
        hbox.Add (panel.Step,flag=flag)
        hbox.Add (wx.StaticText(panel,label="mm"),flag=flag,border=border)
        hbox.Add (panel.NSpots,flag=flag,border=border)
        hbox.Add (wx.StaticText(panel,label="spots, in"),flag=flag,border=border)
        hbox.Add (panel.interleave,flag=flag,border=border)
        hbox.Add (wx.StaticText(panel,label="passes"),flag=flag,border=border)
        hbox.Add (panel.single,flag=flag,border=border)
        panel.SetSizer(hbox)

        # Extra Parameters for translation after image
        self.afterImage = panel = wx.Panel(self)
        panel.NSpots = TextCtrl(panel,size=(25,-1),style=wx.TE_PROCESS_ENTER)
        panel.Step = TextCtrl(panel,size=(50,-1),style=wx.TE_PROCESS_ENTER)
        panel.after_images = TextCtrl(panel,size=(25,-1),style=wx.TE_PROCESS_ENTER)
        panel.after_series = TextCtrl(panel,size=(25,-1),style=wx.TE_PROCESS_ENTER)
        panel.interleave = TextCtrl(panel,size=(25,-1),style=wx.TE_PROCESS_ENTER)
        layout = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL
        border = 2
        label = wx.StaticText(panel,label="After image:",size=(120,-1))
        hbox.Add (label,flag=flag)
        hbox.Add (panel.NSpots,flag=flag)
        hbox.Add (wx.StaticText(panel,label="spots"),flag=flag,border=border)
        hbox.Add (panel.Step,flag=flag)
        hbox.Add (wx.StaticText(panel,label="mm step,"),flag=flag,border=border)
        hbox.Add (wx.StaticText(panel,label="every"),flag=flag,border=border)
        hbox.Add (panel.after_images,flag=flag)
        hbox.Add (wx.StaticText(panel,label="images,"),flag=flag,border=border)
        hbox.Add (wx.StaticText(panel,label="return every"),flag=flag,border=border)
        hbox.Add (panel.after_series,flag=flag)
        hbox.Add (wx.StaticText(panel,label="series, in"),flag=flag,border=border)
        hbox.Add (panel.interleave,flag=flag,border=border)
        hbox.Add (wx.StaticText(panel,label="passes"),flag=flag,border=border)
        layout.Add(hbox)
        button = wx.Button(panel,label="Plot...")
        self.Bind (wx.EVT_BUTTON,self.plot_after_image_translation,button)
        layout.Add(button)
        panel.SetSizer(layout)

        # Parameter panel for linear motor stage
        self.LinearStage = wx.Panel(self)
        self.LinearStage.Start = TextCtrl (self.LinearStage,size=(65,-1),style=wx.TE_PROCESS_ENTER)
        self.LinearStage.End = TextCtrl (self.LinearStage,size=(65,-1),style=wx.TE_PROCESS_ENTER)
        self.LinearStage.NSteps = TextCtrl (self.LinearStage,size=(45,-1),style=wx.TE_PROCESS_ENTER)
        self.LinearStage.Step = TextCtrl (self.LinearStage,size=(65,-1),style=wx.TE_PROCESS_ENTER)
        self.LinearStage.Alternate = wx.Choice(self.LinearStage,choices=["no","yes"],size=(65,-1))
        self.LinearStage.Alternate.Disable()
        self.LinearStage.AlternateComment = wx.StaticText(self.LinearStage,size=(350,-1))
        self.LinearStage.ParkPos = TextCtrl (self.LinearStage,size=(65,-1),style=wx.TE_PROCESS_ENTER)
        self.LinearStage.MoveWhenIdle = wx.Choice (self.LinearStage,choices=["no","yes"],size=(65,-1))
        self.LinearStage.StartMotion = wx.Button (self.LinearStage,label="Start",size=(65,-1))
        self.LinearStage.Stop = wx.Button (self.LinearStage,label="Stop",size=(65,-1))
        self.LinearStage.MoveTime = TextCtrl (self.LinearStage,size=(65,-1),style=wx.TE_PROCESS_ENTER)
        layout = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer()
        a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL
        box.Add (wx.StaticText(self.LinearStage,label="Travel:",size=(120,-1)),flag=a)
        box.Add (self.LinearStage.Start,flag=a)
        box.Add (wx.StaticText(self.LinearStage,label="to"),flag=a,border=5)
        box.Add (self.LinearStage.End,flag=a)
        box.Add (wx.StaticText(self.LinearStage,label="mm"),flag=a,border=5)
        box.Add (wx.StaticText(self.LinearStage,label="in"),flag=a,border=5)
        box.Add (self.LinearStage.NSteps,flag=a)
        box.Add (wx.StaticText(self.LinearStage,label="steps of"),flag=a,border=5)
        box.Add (self.LinearStage.Step,flag=a)
        box.Add (wx.StaticText(self.LinearStage,label="mm"),flag=a,border=5)
        layout.Add(box)
        box = wx.BoxSizer()
        box.Add (wx.StaticText(self.LinearStage,label="Alternate direct.:",size=(120,-1)),flag=a)
        box.Add (self.LinearStage.Alternate,flag=a)
        box.AddSpacer ((10,-1))
        box.Add (self.LinearStage.AlternateComment,flag=a)
        layout.Add(box)
        box = wx.BoxSizer()
        box.Add (wx.StaticText(self.LinearStage,label="Park pos. [mm]:",size=(120,-1)),flag=a)
        box.Add (self.LinearStage.ParkPos,flag=a)
        layout.Add(box)
        box = wx.BoxSizer()
        box.Add (wx.StaticText(self.LinearStage,label="Move when idle:",size=(120,-1)),flag=a)
        box.Add (self.LinearStage.MoveWhenIdle,flag=a)
        box.AddSpacer((5,5))
        box.Add (self.LinearStage.StartMotion,flag=a)
        box.AddSpacer((2,2))
        box.Add (self.LinearStage.Stop,flag=a)
        layout.Add(box)
        box = wx.BoxSizer()
        box.Add (wx.StaticText(self.LinearStage,label="Move time:",size=(120,-1)),flag=a)
        box.Add (self.LinearStage.MoveTime,flag=a)
        layout.Add(box)
        self.LinearStage.SetSizerAndFit(layout)
        
        # Extra Parameters for grid scan
        self.gridScan = panel = wx.Panel(self)
        panel.after_images = TextCtrl(panel,size=(30,-1),style=wx.TE_PROCESS_ENTER)
        layout = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL
        border = 2
        hbox.Add (wx.StaticText(panel,label="Translate every"),flag=flag,border=border)
        hbox.Add (panel.after_images,flag=flag)
        hbox.Add (wx.StaticText(panel,label="images"),flag=flag,border=border)
        layout.Add(hbox)
        panel.SetSizer(layout)

        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input_during_image_step,self.duringImage.Step)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input_during_image_nspots,self.duringImage.NSpots)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input_after_image_step,self.afterImage.Step)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input_after_image_nspots,self.afterImage.NSpots)
        self.Bind (wx.EVT_BUTTON,self.on_start,self.LinearStage.StartMotion)
        self.Bind (wx.EVT_BUTTON,self.on_stop,self.LinearStage.Stop)
        self.Bind (wx.EVT_CHECKBOX,self.on_input)

        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        flag = wx.ALL
        border = 8
        vbox.Add (mode,flag=flag,border=border)
        vbox.Add (self.duringImage,flag=flag,border=border)
        vbox.Add (self.afterImage,flag=flag,border=border)
        vbox.Add (self.LinearStage,flag=flag,border=border)
        vbox.Add (self.gridScan,flag=flag,border=border)
        self.SetSizer(vbox)
        
        # Periodically update the displayed fields.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Periodically update the panel."""
        if IsShownOnScreen(self):
            self.update_parameters()
            self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update(self,event=None):
        """Refresh the control panel"""
        reload_settings()
        # Called periodically on a 1-s timer.
        self.duringImage.Step.Value = "%.3f" % sample.z_step
        self.duringImage.NSpots.Value = "%d" % translation_during_image_unique_nspots()
        self.afterImage.Step.Value = "%.4f" % translation_after_image_zstep()
        self.afterImage.NSpots.Value = "%g" % translation_after_image_nspots()
        
        self.LinearStage.Start.Value = "%.3f" % sample_stage.start_position
        self.LinearStage.End.Value = "%.3f" % sample_stage.end_position
        self.LinearStage.Step.Value = "%.5f" % sample_stage.stepsize
        self.LinearStage.NSteps.Value = "%g" % sample_stage.nsteps
        
        if sample_stage.auto_reverse: self.LinearStage.Alternate.StringSelection = "yes"
        else: self.LinearStage.Alternate.StringSelection  = "no"

        self.LinearStage.ParkPos.Value = "%.3f" % sample_stage.park_position
        self.LinearStage.MoveTime.Value = time_string(translate.move_time)

    def update_parameters(self,event=None):
        """Refresh the control panel"""
        reload_settings()
        self.TranslateMode.StringSelection = translate.mode
        self.HardwareTriggered.Value = translate.hardware_triggered

        # Which parameter panels to display
        if getattr(self,"mode","") != translate.mode: # avoids flickering
            during_image,after_image,linear_stage,grid_scan = False,False,False,False
            if "after image" in translate.mode: after_image = True
            if "during image" in translate.mode: during_image = True
            if "linear stage" in translate.mode: linear_stage = True
            if "grid scan" in translate.mode: grid_scan = True
            self.duringImage.Shown = during_image
            self.afterImage.Shown  = after_image
            self.LinearStage.Shown = linear_stage
            self.gridScan.Shown = grid_scan
            self.Layout()
        self.mode = translate.mode
        
        self.duringImage.interleave.Value = str(translate.interleave_factor)
        self.duringImage.single.Value = translate.single

        self.afterImage.interleave.Value = str(translate.after_image_interleave_factor)
        self.afterImage.after_images.Value = "%d" % translate.after_images
        self.afterImage.after_series.Value = "%d" % translate.return_after_series

        self.gridScan.after_images.Value = "%d" % translate.after_images

        label = "yes" if translate.move_when_idle else "no"
        self.LinearStage.MoveWhenIdle.StringSelection = label

    def on_input(self, event):
        """This is called when the user switches between fields and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        center = sample_center()
        
        translate.mode = str(self.TranslateMode.StringSelection)
        translate.hardware_triggered = self.HardwareTriggered.Value
        
        if self.duringImage.Shown:
            try:
                translate.interleave_factor = \
                    max(int(eval(self.duringImage.interleave.Value)),1)
            except: pass
            translate.single = self.duringImage.single.Value

        if self.afterImage.Shown:
            try:
                set_translation_after_image_zstep(float(eval(self.afterImage.Step.Value)))
            except: pass
            try:
                translate.after_image_interleave_factor = \
                    max(int(eval(self.afterImage.interleave.Value)),1)
            except: pass
            try:
                translate.after_images = int(eval(self.afterImage.after_images.Value))
            except: pass
            try:
                translate.return_after_series = int(eval(self.afterImage.after_series.Value))
            except: pass
            

        if self.LinearStage.Shown:
            if event.EventObject is self.LinearStage.Start:
                try: sample_stage.start_position = float(eval(self.LinearStage.Start.Value))
                except: pass
            if event.EventObject is self.LinearStage.End:
                try: sample_stage.end_position = float(eval(self.LinearStage.End.Value))
                except: pass
            if event.EventObject is self.LinearStage.Step:
                try: sample_stage.stepsize = float(eval(self.LinearStage.Step.Value))
                except: pass
            if event.EventObject is self.LinearStage.NSteps:
                try: sample_stage.nsteps = float(eval(self.LinearStage.NSteps.Value))
                except: pass
            if event.EventObject is self.LinearStage.Alternate:
                sample_stage.auto_reverse = (self.LinearStage.Alternate.StringSelection == "yes")
            if event.EventObject is self.LinearStage.ParkPos:
                try: sample_stage.park_position = float(eval(self.LinearStage.ParkPos.Value))
                except: pass
            if event.EventObject is self.LinearStage.MoveWhenIdle:
                translate.move_when_idle = (self.LinearStage.MoveWhenIdle.StringSelection == "yes")
            if event.EventObject is self.LinearStage.MoveTime:
                translate.move_time = seconds(self.LinearStage.MoveTime.Value)

        if self.gridScan.Shown:
            try:
                translate.after_images = int(eval(self.gridScan.after_images.Value))
            except: pass


        if sample_center() != center: align.center_time = time()
        align.center_sample = param.file_basename
            
        save_settings()
        self.update_parameters()

    def on_input_during_image_step(self, event):
        """Modify the translation step size for during image translation"""
        try:
            value = float(eval(self.duringImage.Step.Value))
        except: return
        sample.z_step = value

    def on_input_during_image_nspots(self, event):
        """"""
        try:
            value = int(eval(self.duringImage.NSpots.Value))
        except: return
        translation_during_image_set_unique_nspots(value)

    def on_input_after_image_step(self, event):
        """Modify the translation step size for after image translation"""
        try: value = float(eval(self.afterImage.Step.Value))
        except: return
        set_translation_after_image_zstep(value)

    def on_input_after_image_nspots(self, event):
        """Modify the translation step size for after image translation"""
        try: value = float(eval(self.afterImage.NSpots.Value))
        except: return
        set_translation_after_image_nspots(value)

    def plot_after_image_translation(self,event):
        """Preview sample position dirunbg a time series as chart."""
        translation_after_image_plot()

    def on_start(self,event):
        """If using the linear stage, start continuous sample translation"""
        sample_stage.timer_period = wait_time(task.image_number)
        sample_stage.timer_enabled = True

    def on_stop(self,event):
        """If using the linear stage, start continuous sample translation"""
        sample_stage.timer_enabled = False


class DiagnosticsPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL

        text = wx.StaticText (self,-1,"Online Diagnostics:")
        layout.Add(text,(0,0),flag=a)
        self.DiagnosticsEnabled = ComboBox(self,size=(75,-1),
            choices=['on','off'],style=wx.CB_DROPDOWN)
        self.Bind(wx.EVT_COMBOBOX,self.on_input)
        layout.Add(self.DiagnosticsEnabled,(0,2),flag=a)

        self.Delay = wx.CheckBox(self,label="Laser to X-Ray Delay")
        layout.Add(self.Delay,(2,0),flag=a)
        button = wx.Button(self,label="Read",size=(55,-1))
        self.Bind (wx.EVT_BUTTON,self.test_delay,button)
        layout.Add(button,(2,1),flag=a)
        self.DelayValue = TextCtrl(self,style=wx.TE_READONLY,size=(75,-1))
        layout.Add(self.DelayValue,(2,2),flag=a)
        text = wx.StaticText(self,label="Min.win.:")
        layout.Add(text,(2,3),flag=a,border=1)
        self.MinWindow = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.MinWindow,(2,4),flag=a)
        text = wx.StaticText(self,label="Offset:")
        layout.Add(text,(2,5),flag=a,border=1)
        self.TimingOffset = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.TimingOffset,(2,6),flag=a)
        
        text = wx.StaticText(self,label=repr(actual_delay)+".average")
        layout.Add(text,(3,0),span=(1,8),flag=a)
        
        self.Xray = wx.CheckBox(self,label="X-Ray Pulse Intensity")
        layout.Add(self.Xray,(5,0),flag=a)
        button = wx.Button(self,label="Read",size=(55,-1))
        self.Bind (wx.EVT_BUTTON,self.test_xray,button)
        layout.Add(button,(5,1),flag=a)
        self.XrayValue = TextCtrl(self,style=wx.TE_READONLY,size=(75,-1))
        layout.Add(self.XrayValue,(5,2),flag=a)
        text = wx.StaticText(self,label="Reference:")
        layout.Add(text,(5,3),flag=a,border=1)
        self.XrayRef = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.XrayRef,(5,4),flag=a)
        text = wx.StaticText(self,label="Offset:")
        layout.Add(text,(5,5),flag=a,border=1)
        self.XrayOffset = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        self.background = self.XrayOffset.GetBackgroundColour()
        self.edited = wx.Colour(255,255,220)
        self.XrayOffset.Bind (wx.EVT_CHAR,self.on_type)
        layout.Add(self.XrayOffset,(5,6),flag=a)

        text = wx.StaticText(self,label=repr(xray_pulse))
        layout.Add(text,(6,0),span=(1,8),flag=a)

        self.XrayRecordWaveform = wx.CheckBox(self,label="Record Waveform C%s" %
            xray_trace.n)
        layout.Add(self.XrayRecordWaveform,(7,0),flag=a)

        text = wx.StaticText(self,label="Sampling Rate:")
        layout.Add(text,(7,1),flag=a,border=1)
        self.XraySamplingRate = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.XraySamplingRate,(7,2),flag=a)
        text = wx.StaticText(self,label="Time Range:")
        layout.Add(text,(7,3),flag=a,border=1)
        self.XrayTimeRange = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.XrayTimeRange,(7,4),flag=a)
        text = wx.StaticText(self,label="Offset:")
        layout.Add(text,(7,5),flag=a,border=1)
        self.XrayTimeOffset = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.XrayTimeOffset,(7,6),flag=a)

        self.Laser = wx.CheckBox(self,label="Laser Pulse Intensity")
        layout.Add(self.Laser,(9,0),flag=a)
        button = wx.Button(self,label="Read",size=(55,-1))
        self.Bind (wx.EVT_BUTTON,self.test_laser,button)
        layout.Add(button,(9,1),flag=a)
        self.LaserValue = TextCtrl(self,style=wx.TE_READONLY,size=(75,-1))
        layout.Add(self.LaserValue,(9,2),flag=a)
        text = wx.StaticText(self,label="Reference:")
        layout.Add(text,(9,3),flag=a,border=1)
        self.LaserRef = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.LaserRef,(9,4),flag=a)
        text = wx.StaticText(self,label="Offset:")
        layout.Add(text,(9,5),flag=a,border=1)
        self.LaserOffset = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.LaserOffset,(9,6),flag=a)
        
        text = wx.StaticText(self,label=repr(laser_pulse))
        layout.Add(text,(10,0),span=(1,8),flag=a)

        self.LaserRecordWaveform = wx.CheckBox(self,label="Record Waveform C%s"
            % laser_trace.n)
        layout.Add(self.LaserRecordWaveform,(11,0),flag=a)

        text = wx.StaticText(self,label="Sampling Rate:")
        layout.Add(text,(11,1),flag=a,border=1)
        self.LaserSamplingRate = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.LaserSamplingRate,(11,2),flag=a)
        text = wx.StaticText(self,label="Time Range:")
        layout.Add(text,(11,3),flag=a,border=1)
        self.LaserTimeRange = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.LaserTimeRange,(11,4),flag=a)
        text = wx.StaticText(self,label="Offset:")
        layout.Add(text,(11,5),flag=a,border=1)
        self.LaserTimeOffset = TextCtrl(self,style=wx.TE_PROCESS_ENTER,size=(75,-1))
        layout.Add(self.LaserTimeOffset,(11,6),flag=a)

        MoreButton = wx.Button(self,label="More...")
        layout.Add(MoreButton,(13,0),flag=a)
        
        # Leave a 10-pixel wide space around the panel.
        border = wx.BoxSizer()
        border.Add (layout,0,wx.ALL,10) 
        self.SetSizer(border)

        self.Bind(wx.EVT_CHECKBOX,self.on_input)
        # Call the "on_input" routine whenever the user presses Enter.
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)

        self.Bind (wx.EVT_BUTTON,self.more,MoreButton)

        # Periodically update the displayed fields.
        self.update()
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        "Called periodically every second triggered by a timer"
        if IsShownOnScreen(self):
            self.update_parameters()
            self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update(self,event=None):
        reload_settings()
        if self.XrayOffset.GetBackgroundColour() != self.edited:
            self.XrayOffset.Value =("%.4g" % diagnostics_xray_offset())

    def update_parameters(self,event=None):
        reload_settings()
        self.DiagnosticsEnabled.Value = "on" if diagnostics.enabled else "off"
        
        self.Delay.Value              = diagnostics.delay
        self.MinWindow.Value          = time_string(diagnostics.min_window)
        self.TimingOffset.Value       = time_string(diagnostics.timing_offset)
        
        self.Xray.Value               = diagnostics.xray
        self.XrayRef.Value            = "%g" % diagnostics.xray_reference
        self.XrayRecordWaveform.Value = diagnostics.xray_record_waveform
        self.XraySamplingRate.Value   = "%g" % diagnostics.xray_sampling_rate
        self.XrayTimeRange.Value      = time_string(diagnostics.xray_time_range)
        self.XrayTimeOffset.Value     = time_string(diagnostics.xray_time_offset)
        
        self.Laser.Value              = diagnostics.laser
        self.LaserRef.Value           = "%g" % diagnostics.laser_reference
        self.LaserOffset.Value        = "%g" % diagnostics.laser_offset
        self.LaserRecordWaveform.Value= diagnostics.laser_record_waveform
        self.LaserSamplingRate.Value  = "%g" % diagnostics.laser_sampling_rate
        self.LaserTimeRange.Value     = time_string(diagnostics.laser_time_range)
        self.LaserTimeOffset.Value    = time_string(diagnostics.laser_time_offset)

    def on_type(self,event):
        """Called when anything but Enter is typed in the field."""
        self.XrayOffset.SetBackgroundColour(self.edited)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip() 

    def on_input(self, event):
        """This is called when the user switches between fields and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        diagnostics.enabled = (self.DiagnosticsEnabled.Value == "on")

        diagnostics.delay = self.Delay.Value
        try: diagnostics.timing_offset = seconds(self.TimingOffset.Value)
        except: pass
        try: diagnostics.min_window = seconds(self.MinWindow.Value)
        except: pass

        diagnostics.xray = self.Xray.Value
        try: diagnostics.xray_reference = float(eval(self.XrayRef.Value))
        except: pass
        try: diagnostics_set_xray_offset(float(eval(self.XrayOffset.Value)))
        except: pass
        self.XrayOffset.SetBackgroundColour(self.background)

        diagnostics.xray_record_waveform = self.XrayRecordWaveform.Value
        try: diagnostics.xray_sampling_rate = float(eval(self.XraySamplingRate.Value))
        except: pass
        try: diagnostics.xray_time_range = seconds(self.XrayTimeRange.Value)
        except: pass
        try: diagnostics.xray_time_offset = seconds(self.XrayTimeOffset.Value)
        except: pass

        diagnostics.laser = self.Laser.Value
        try: diagnostics.laser_reference = float(eval(self.LaserRef.Value))
        except: pass
        try: diagnostics.laser_offset = float(eval(self.LaserOffset.Value))
        except: pass

        diagnostics.laser_record_waveform = self.LaserRecordWaveform.Value
        try: diagnostics.laser_sampling_rate = float(eval(self.LaserSamplingRate.Value))
        except: pass
        try: diagnostics.laser_time_range = seconds(self.LaserTimeRange.Value)
        except: pass
        try: diagnostics.laser_time_offset = seconds(self.LaserTimeOffset.Value)
        except: pass

        self.update_parameters()
        save_settings()

    def test_delay(self, event):
        "Tries to read the actual delay and displays the result"
        try: value = time_string(actual_delay.average)
        except: value = "<failed>"
        self.DelayValue.Value =(value)

    def test_xray(self, event):
        "Tries to read xray pulse intensity and displays the result"
        try: value = "%.4g" % xray_pulse.average
        except: value = "<failed>"
        self.XrayValue.Value =(value)

    def test_laser(self, event):
        "Tries to read laser pulse intensity and displays the result"
        try: value = "%.4g" % laser_pulse.average
        except: value = "<failed>"
        self.LaserValue.Value =(value)

    def more(self, event):
        "Show dialog box for more diagnostics"
        dlg = self.MoreDiagnostics (self)
        dlg.CenterOnParent()
        dlg.Show() 

    class MoreDiagnostics (wx.Dialog):
        def __init__ (self,parent):
            wx.Dialog.__init__(self,parent,-1,"More Diagnostics")

            border = wx.BoxSizer(wx.VERTICAL)

            box = wx.BoxSizer(wx.VERTICAL)
            
            from wx import grid
            self.Table = grid.Grid(self)
            nrows = max(len(diagnostics.PVs),1)
            self.Table.CreateGrid(nrows,4)
            self.Table.SetRowLabelSize(0) # Hide row labels (1,2,...).
            self.Table.SetColLabelValue(0,"Log")
            self.Table.SetColLabelValue(1,"Description")
            self.Table.SetColLabelValue(2,"Process Variable")
            self.Table.SetColLabelValue(3,"Value")
            
            for i in range(0,min(nrows,len(diagnostics.PVs))):
                if i<len(diagnostics.PVuse) and diagnostics.PVuse[i]: text = "Yes"
                else: text = "No"
                self.Table.SetCellValue(i,0,text)
                if i<len(diagnostics.PVnames):
                    self.Table.SetCellValue(i,1,diagnostics.PVnames[i])
                self.Table.SetCellValue(i,2,diagnostics.PVs[i])

            self.Table.AutoSize()
            box.Add (self.Table) 

            buttons = wx.BoxSizer()
            button = wx.Button(self,label="+",style=wx.BU_EXACTFIT)
            self.Bind(wx.EVT_BUTTON,self.add_row,button)
            buttons.Add (button) 
            size = button.GetSize()
            button = wx.Button(self,label="-",size=size)
            self.Bind(wx.EVT_BUTTON,self.delete_row,button)
            buttons.Add (button) 
            box.Add (buttons)
            # Leave a 10-pixel wide space around the panel.
            border.Add (box,0,wx.ALL,10)

            buttons = wx.BoxSizer()
            button = wx.Button(self,wx.ID_OK)
            self.Bind(wx.EVT_BUTTON,self.OnOK,button)
            button.SetDefault()
            buttons.Add (button)
            buttons.AddSpacer((10,10))
            button = wx.Button(self,wx.ID_CANCEL)
            buttons.Add (button) 
            buttons.AddSpacer((10,10))
            button = wx.Button(self,label="Test")
            self.Bind(wx.EVT_BUTTON,self.test,button)
            buttons.Add (button) 
            # Leave a 10-pixel wide space around the panel.
            border.Add (buttons,0,wx.ALL,10)
            
            self.SetSizer(border)
            self.Fit()

        def add_row(self,event):
            "Add one more row at the end of the table"
            self.Table.AppendRows(1)
            self.Table.AutoSize()
            self.Fit()

        def delete_row(self,event):
            "Remove the last row of the table"
            n = self.Table.GetNumberRows()
            self.Table.DeleteRows(n-1,1)
            self.Table.AutoSize()
            self.Fit()

        def OnOK(self,event):
            "Called if the OK button is pressed"
            diagnostics.PVuse = []
            diagnostics.PVnames = []
            diagnostics.PVs = []
            for i in range (0,self.Table.GetNumberRows()):
                PVuse = (self.Table.GetCellValue(i,0).lower() == "yes")
                PVname = str(self.Table.GetCellValue(i,1))
                PV = str(self.Table.GetCellValue(i,2))
                if PV:
                    diagnostics.PVuse += [PVuse]
                    diagnostics.PVnames += [PVname]
                    diagnostics.PVs += [PV]
            self.Destroy()
            save_settings()           

        def test(self,event):
            """Check if PVs are working b yreading their current value"""
            for i in range (0,self.Table.GetNumberRows()):
                enabled = self.Table.GetCellValue(i,0) == "Yes"
                PV = str(self.Table.GetCellValue(i,2))
                value = str(diagnostics_value(PV)) if (PV and enabled) else ""
                self.Table.SetCellValue(i,3,value)

class PumpPanel(wx.Panel):
    class Panel: "container for sub-panels"
    nmax = 1
    
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)

        # Controls
        self.Use = wx.Choice(self,choices=["yes","no"],size=(60,-1))
        self.HardwareTriggered = wx.CheckBox(self,label="Hardware Triggered")
        self.Step = TextCtrl(self,name="Increment",size=(60,-1),
            style=wx.TE_PROCESS_ENTER)
        self.Frequency = TextCtrl(self,name="Interval",size=(60,-1),
            style=wx.TE_PROCESS_ENTER)
        ##self.AtStart = wx.CheckBox(self,label="Start with the 1st image of the dataset")
        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL
        t = wx.StaticText (self,label="Use Pump:")
        layout.Add(t,(0,0),flag=a)
        layout.Add(self.Use,(0,1),flag=a)
        layout.Add(self.HardwareTriggered,(0,3),flag=a)
        t = wx.StaticText (self,label="Increment [deg]:")
        layout.Add(t,(1,0),flag=a)
        layout.Add(self.Step,(1,1),flag=a)

        t = wx.StaticText (self,label="Interval [images]:")
        layout.Add(t,(2,0),flag=a)
        layout.Add(self.Frequency,(2,1),flag=a)
        ##layout.Add(self.AtStart,(2,3),flag=a)

        # Leave a 10-pixel wide space around the panel.
        border = wx.BoxSizer()
        border.Add (layout,0,wx.ALL,10) 
        self.SetSizer(border)

        # Callbacks
        # Call the "on_input" routine whenever the user presses Enter.
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)

        self.Bind(wx.EVT_CHOICE,self.on_input)
        self.Bind(wx.EVT_COMBOBOX,self.on_input)
        self.Bind(wx.EVT_CHECKBOX,self.on_input)
        self.Bind(wx.EVT_BUTTON,self.on_run)

        # Periodically refresh the panel
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Periodically update the panel"""
        if IsShownOnScreen(self):
            self.update_parameters()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update_parameters(self):
        "Called periodically on a timer"
        self.Use.StringSelection = "yes" if pump.enabled else "no"
        self.HardwareTriggered.Value = pump.hardware_triggered
        self.Step.Value = "%g" % pump.step
        self.Step.Enabled = not pump.hardware_triggered
        self.Frequency.Value = "%d" % pump.frequency
        self.Frequency.Enabled = not pump.hardware_triggered
        ##self.AtStart.Value = pump.at_begin_of_dataset[0]        
        
    def on_input(self, event):
        pump.enabled = (self.Use.StringSelection == "yes")
        pump.hardware_triggered = self.HardwareTriggered.Value
        text = self.Step.Value
        try: pump.step = float(eval(text))
        except: pass
        text = self.Frequency.Value
        try: pump.frequency = int(eval(text))
        except: pass
        ##pump.at_begin_of_dataset[0] = self.AtStart.Value

        save_settings()
        self.update_parameters()

    def on_run(self,event):
        "Runs the entire sequence in backgound"
        pump.command_number = event.GetId()
        task.action = "Pumping Sample"

class ChopperPanel(wx.Panel):
    nrows = 8
    
    def __init__(self, parent):
        from numpy import ndarray
        wx.Panel.__init__(self,parent,-1)
 
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALIGN_CENTRE_VERTICAL|wx.ALL
        label = wx.StaticText (self,label="Variable:")
        hbox.Add(label,flag=flag)
        self.Variable = wx.Choice(self,choices=["Yes","No"])
        self.Bind(wx.EVT_CHOICE,self.on_input,self.Variable)
        hbox.Add(self.Variable,flag=flag)

        hbox.AddSpacer((10,10))
        label = wx.StaticText (self,label="Suspend collection:")
        hbox.Add(label,flag=flag)
        self.Wait = wx.Choice(self,choices=["Yes","No"])
        self.Bind(wx.EVT_CHOICE,self.on_input,self.Wait)
        hbox.Add(self.Wait,flag=flag)

        hbox.AddSpacer((20,10))
        self.Import = wx.Button(self,label="Update from EPICS")
        self.Bind(wx.EVT_BUTTON,self.on_import,self.Import)
        hbox.Add(self.Import,flag=flag)

        hbox.AddSpacer((10,10))
        self.Export = wx.Button(self,label="Send to EPICS")
        self.Bind(wx.EVT_BUTTON,self.on_export,self.Export)
        hbox.Add(self.Export,flag=flag)
        vbox.Add (hbox,flag=wx.ALL,border=10) 

        grid = wx.GridBagSizer(1,1)
        labels = ["Use","X [mm]","Y [mm]","Phase  ","Pulses","Pulse len.",
                  "Min.delay","Gate-","Gate+"]
        self.Labels = ndarray(len(labels),object)
        for i in range(0,len(labels)):
            self.Labels[i] = wx.StaticText(self,label=labels[i])
            grid.Add(self.Labels[i],(0,i),flag=flag)

        self.cells = ndarray((self.nrows,len(self.Labels)),object)
        style = wx.TE_PROCESS_ENTER
        for i in range(0,self.nrows):
            for j in range(0,len(self.Labels)):
                width = self.Labels[j].GetSize()[0]+15
                self.cells[i,j] = TextCtrl(self,size=(width,-1),style=style)
                grid.Add(self.cells[i,j],(i+1,j),flag=flag)
        self.Use,self.X,self.Y,self.Phase,self.Pulses,self.Time,self.MinDT,\
            self.Start,self.Stop = self.cells.T        

        height = self.cells[i,j].GetSize()[1]
        for i in range(0,self.nrows):
            button = wx.Button(self,label="Go To",size=(60,height),id=i)
            grid.Add(button,(i+1,len(self.Labels)),flag=flag)
            self.Bind(wx.EVT_BUTTON,self.apply_settings,button)

        self.Current = ndarray(len(labels),object)
        for i in range(0,len(labels)):
            self.Current[i] = wx.StaticText(self)
            grid.Add(self.Current[i],(self.nrows+1,i),flag=flag)
        self.Current[0].SetLabel("Now")

        vbox.Add(grid,proportion=1,flag=wx.ALL,border=10)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALIGN_CENTRE_VERTICAL|wx.ALL
        label = wx.StaticText (self,label="Modes:")
        hbox.Add(label,flag=flag)
        self.Modes = TextCtrl(self,size=(600,-1),style=style)
        self.Bind(wx.EVT_TEXT_ENTER,self.on_input,self.Modes)
        hbox.Add(self.Modes,flag=flag)
        vbox.Add(hbox,flag=wx.ALL,border=10) 

        self.SetSizer(vbox)

        # Call the "on_input" routine whenever the user presses Enter.
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)

        # Periodically update the displayed fields.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Called periodically every second triggered by a timer"""
        if IsShownOnScreen(self):
            self.update_parameters()
            self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update_parameters(self):
        """Populate user-editable fields"""
        reload_settings()
        enabled = collection_variable_enabled("chopper_mode")
        self.Variable.StringSelection = "Yes" if enabled else "No"
        self.Wait.StringSelection = "Yes" if chopper.wait else "No"

        for i in range(0,self.nrows):
            value = chopper.use[i] if i < len(chopper.use) else nan
            self.Use[i].Value =("Yes" if value else "No")
            if isnan(value): self.Use[i].Value =("")

            value = chopper.x[i] if i < len(chopper.x) else nan
            self.X[i].Value =(tostr(value).replace("nan",""))
            value = chopper.y[i] if i < len(chopper.y) else nan
            self.Y[i].Value =(tostr(value).replace("nan",""))
            value = chopper.phase[i] if i < len(chopper.phase) else nan
            self.Phase[i].Value = ("%.0fns" % (value/1e-9))
            if isnan(value): self.Phase[i].Value = ("")
            value = chopper.pulses[i] if i < len(chopper.pulses) else nan
            self.Pulses[i].Value = (tostr(value).replace("nan",""))
            value = chopper.time[i] if i < len(chopper.time) else nan
            self.Time[i].Value = (time_string(value).replace("off",""))
            value = chopper.min_dt[i] if i < len(chopper.min_dt) else nan
            self.MinDT[i].Value = (time_string(value).replace("off",""))
            value = chopper.gate_start[i] if i < len(chopper.gate_start) else nan
            self.Start[i].Value = (time_string(value).replace("off",""))
            value = chopper.gate_stop[i] if i < len(chopper.gate_stop) else nan
            self.Stop[i].Value = (time_string(value).replace("off",""))

        self.Modes.Value = list_to_string(chopper.modes)

    def update(self):
        """Updates dynamically changing fields"""
        reload_settings()
        self.Current[1].SetLabel(tostr(ChopX.value))
        self.Current[2].SetLabel(tostr(ChopY.value))
        self.Current[3].SetLabel(time_string(timing_system.hsc.delay.value,4))
        self.Current[4].SetLabel(tostr(chopper_pulses()))
        self.Current[7].SetLabel(time_string(xray_pulse.gate.start.value))
        self.Current[8].SetLabel(time_string(xray_pulse.gate.stop.value))

    def on_input(self,event):
        """This is called when the use switches between feilds and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        enabled = (self.Variable.StringSelection == "Yes")
        collection_variable_set_enabled("chopper_mode",enabled)
        chopper.wait = (self.Wait.StringSelection == "Yes")
        
        from numpy import ndarray
        values = ndarray((self.nrows,len(self.Labels)),object)
        for i in range (0,self.nrows):
            for j in range(0,len(self.Labels)):
                 values[i,j] = self.cells[i,j].GetValue()

        while len(chopper.use) < self.nrows: chopper.use += [True]
        while len(chopper.x) < self.nrows: chopper.x += [0.0]
        while len(chopper.y) < self.nrows: chopper.y += [0.0]
        while len(chopper.phase) < self.nrows: chopper.phase += [0.0]
        while len(chopper.pulses) < self.nrows: chopper.pulses += [0]
        while len(chopper.time) < self.nrows: chopper.time += [0.0]
        while len(chopper.min_dt) < self.nrows: chopper.min_dt += [0.0]
        while len(chopper.gate_start) < self.nrows: chopper.gate_start += [0.0]
        while len(chopper.gate_stop) < self.nrows: chopper.gate_stop += [0.0]

        for i in range (0,self.nrows):
            if values[i,0].capitalize() == "Yes": chopper.use[i] = True
            if values[i,0].capitalize() == "No": chopper.use[i] = False
            try: chopper.x[i] = float(eval(values[i,1]))
            except: pass
            try: chopper.y[i] = float(eval(values[i,2]))
            except: pass
            try:
                chopper.phase[i] = seconds(values[i,3])
                if chopper.phase[i] == None: chopper.phase[i] = nan
            except: pass
            try: chopper.pulses[i] = float(eval(values[i,4]))
            except: pass
            try:
                chopper.time[i] = seconds(values[i,5])
                if chopper.time[i] == None: chopper.phase[i] = nan
            except: pass
            try:
                chopper.min_dt[i] = seconds(values[i,6])
                if chopper.min_dt[i] == None: chopper.min_dt[i] = nan
            except: pass
            try:
                chopper.gate_start[i] = seconds(values[i,7])
                if chopper.gate_start[i] == None: chopper.gate_start[i] = nan
            except: pass
            try:
                chopper.gate_stop[i] = seconds(values[i,8])
                if chopper.gate_stop[i] == None: chopper.gate_stop[i] = nan
            except: pass

        chopper.modes = string_to_list(self.Modes.Value)

        save_settings()
        self.update_parameters()

    def on_import(self, event):
        """Copy parameters from 'Fast Shutter' MEDM screen"""
        import_chopper_parameters()
        self.update_parameters()

    def on_export(self, event):
        """Copy parameters to 'Fast Shutter' MEDM screen"""
        export_chopper_parameters()
        self.update_parameters()

    def apply_settings(self,event):
        "Called when 'Go To' button is pressed."
        i = event.GetId() # Row number of "Go To" button pressed
        try:
            x = float(self.X[i].GetValue())
            y = float(self.Y[i].GetValue())
            phase = seconds(self.Phase[i].GetValue())
            gate_start = seconds(self.Start[i].GetValue())
            gate_stop = seconds(self.Stop[i].GetValue())
            ChopX.value = x
            ChopY.value = y
            timing_system.hsc.delay.value = phase
            if hasattr(xray_pulse,"gate"):
                xray_pulse.gate.start.value = gate_start
                xray_pulse.gate.stop.value = gate_stop
        except ValueError: pass


def import_chopper_parameters():
    """Copy parameters from the 'Fast Shutter' MEDM screen"""
    chopper.x =     [caget("14IDB:FS%d.DO2" % i) for i in range(0,8)]
    chopper.y =     [caget("14IDB:FS%d.DO3" % i) for i in range(0,8)]
    chopper.phase = [caget("14IDB:FS%d.DO4" % i) for i in range(0,8)]
    save_settings()

def export_chopper_parameters():
    """Copy parameters to 'Fast Shutter' MEDM screen"""
    for i in range(0,min(len(chopper.x),8)):
        caput("14IDB:FS%d.DO2" % i,chopper.x[i])
    for i in range(0,min(len(chopper.y),8)):
        caput("14IDB:FS%d.DO3" % i,chopper.y[i])
    for i in range(0,min(len(chopper.phase),8)):
        caput("14IDB:FS%d.DO4" % i,chopper.phase[i])


class XrayBeamCheckPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)

        # Controls
        size = (120,-1)
        e = wx.TE_PROCESS_ENTER
        self.BeamcheckEnabled = ComboBox(self,choices=['on','off'],size=size)
        self.Type = ComboBox(self,choices=['I0','beam position'],size=size)

        self.RunVariable = wx.Choice(self,size=size,style=e)
        self.Next = wx.StaticText(self)

        self.Comment = wx.StaticText(self,size=(620,45))

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL

        size = (-1,-1)
        t = wx.StaticText(self,label="Optimize during collection:",size=size)
        layout.Add(t,(0,0),flag=a)
        layout.Add(self.BeamcheckEnabled,(0,1),flag=a)

        t = wx.StaticText(self,label="Type:",size=size)
        layout.Add(t,(1,0),flag=a)
        layout.Add(self.Type,(1,1),flag=a)

        t = wx.StaticText(self,label="Run after series of:",size=size)
        layout.Add(t,(3,0),flag=a)
        layout.Add(self.RunVariable,(3,1),flag=a)
        layout.Add(self.Next,(3,2),flag=a)

        layout.Add(self.Comment,(8,0),span=(1,4),flag=a)
        
        # Leave a 10-pixel wide space around the panel.
        border = wx.BoxSizer()
        border.Add(layout,0,wx.ALL,10) 
        self.SetSizer(border)
        
        self.Bind(wx.EVT_COMBOBOX,self.on_input)
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)
        self.Bind (wx.EVT_CHOICE,self.on_input)

        self.test_button = wx.Button(self,label="Test",pos=(10,300),
            size=(100,-1))
        self.test_button.SetDefault()
        self.Bind (wx.EVT_BUTTON,self.run_test,self.test_button)

        self.run_button = wx.Button(self,label="Run Now",pos=(120,300),
            size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.run_now,self.run_button)

        self.cancel_button = wx.Button(self,label="Cancel",pos=(230,300),
            size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.cancel,self.cancel_button)

        # Periodically refresh the panel
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Periodically update the panel"""
        if IsShownOnScreen(self):
            self.update_parameters()
            self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update_parameters(self):
        """Refresh the control panel"""
        reload_settings()
        self.BeamcheckEnabled.Value = "on" if xraycheck.enabled else "off"
        self.Type.Value = xraycheck.type
        
        if self.RunVariable.StringSelection != xraycheck.run_variable:
            self.RunVariable.StringSelection = xraycheck.run_variable
        if self.RunVariable.Items != collection_variables():
            self.RunVariable.Items = collection_variables()

        nexttime = xraycheck.last + xraycheck.interval
        text = "at "+strftime("%H:%M",localtime(nexttime))
        if nexttime<time(): text = "immediately"
        text = " (Next: "+text+")"
        self.Next.Label = text
                
    def update(self,event=None):
        """Refresh the control panel"""
        reload_settings()
        comment = xraycheck.comment
        date = strftime("%d %b %y %H:%M",localtime(xraycheck.last))
        if comment: comment = date+": "+comment
        self.Comment.Label = comment
        self.Comment.Size = 620,45 
        
        if not task.action:
           self.test_button.Enable()
           self.run_button.Enable()
           self.cancel_button.Disable()
        else:
           self.test_button.Disable()
           self.run_button.Disable()
           self.cancel_button.Enable()
        if task.cancelled: self.cancel_button.Label = "Cancelled"
        else: self.cancel_button.Label = "Cancel"
 
    def on_input(self, event):
        """This is called when the user switches between fields and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        xraycheck.enabled = (self.BeamcheckEnabled.Value == "on")
        xraycheck.type = self.Type.Value

        xraycheck.run_variable = str(self.RunVariable.StringSelection)

        save_settings()
        self.update_parameters()

    def run_test(self,event):
        """Measure the mirror settings needed to optimize the flux,
        but do not apply the new settings."""
        # Called when the 'Run Now' button is pressed
        task.action = "X-Ray Beam Check - Test"
        self.update()

    def run_now(self,event):
        """Measure the mirror settings needed to optimize the flux,
        and apply the new settings."""
        # Called when the 'Tweak Now' button is pressed"
        task.action = "X-Ray Beam Check"
        self.update()

    def cancel(self,event): 
        "Called when the 'Cancel' button is pressed"
        task.cancelled = True; task.action = ""


class LaserBeamCheckPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)

        # Controls
        size = (100,-1)
        style = wx.TE_PROCESS_ENTER
        self.BeamcheckEnabled = ComboBox(self,choices=['on','off'],size=size)

        self.CheckOnly = wx.CheckBox(self,label="check only")

        self.Interval = TextCtrl(self,size=size,style=style)
        self.OnlyAtBeginning = ComboBox(self,choices=['yes','no'],size=size)
        self.RetractSample = ComboBox(self,choices=['yes','no'],size=size)
        self.Attenuator = TextCtrl(self,size=size,style=style)
        self.RepRate = TextCtrl(self,size=size,style=style)
        self.Average = TextCtrl(self,size=size,style=style)
        self.MinSignalNoise = TextCtrl(self,size=size,style=style)

        self.BeamProfile = BeamProfile(self,size=(295,245))

        self.Comment = wx.StaticText(self,size=(620,45))

        self.test_button = wx.Button(self,label="Test",size=(100,-1))
        self.run_button = wx.Button(self,label="Run Now",size=(100,-1))
        self.run_button.SetDefault()
        self.cancel_button = wx.Button(self,label="Cancel",size=(100,-1))
        self.park_button = wx.Button(self,label="Park Position...",size=(100,-1))

        self.ParkPosSummary = wx.StaticText(self,size=(270,45))

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL

        # Parameter 'size' needed because of bug in WX 2.6 or earlier.
        size = (200,-1)
        t = wx.StaticText (self,label="Re-center during collection:",size=size)
        layout.Add(t,(0,0),flag=a)
        layout.Add(self.BeamcheckEnabled,(0,1),flag=a)

        layout.Add(self.CheckOnly,(1,1),flag=a)

        t = wx.StaticText (self,label="Repeat every:",size=size)
        layout.Add(t,(2,0),flag=a)
        layout.Add(self.Interval,(2,1),flag=a)

        t = wx.StaticText (self,label="Only at start of time series:",size=size)
        layout.Add(t,(3,0),flag=a)
        layout.Add(self.OnlyAtBeginning,(3,1),flag=a)

        t = wx.StaticText (self,label="Retract sample:",size=size)
        layout.Add(t,(4,0),flag=a)
        layout.Add(self.RetractSample,(4,1),flag=a)

        t = wx.StaticText (self,label="Attenuator (VNFilter):",size=size)
        layout.Add(t,(5,0),flag=a)
        layout.Add(self.Attenuator,(5,1),flag=a)

        t = wx.StaticText (self,label="Repetition rate:",size=size)
        layout.Add(t,(6,0),flag=a)
        layout.Add(self.RepRate,(6,1),flag=a)

        t = wx.StaticText (self,label="Average count:",size=size)
        layout.Add(t,(7,0),flag=a)
        layout.Add(self.Average,(7,1),flag=a)

        t = wx.StaticText (self,label="Min. signal/noise:",size=size)
        layout.Add(t,(8,0),flag=a)
        layout.Add(self.MinSignalNoise,(8,1),flag=a)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add (layout)
        hbox.AddSpacer((10,10))
        hbox.Add (self.BeamProfile)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add (hbox)
        vbox.AddSpacer((2,2))
        vbox.Add (self.Comment)
        
        buttonbox = wx.BoxSizer(wx.HORIZONTAL)
        buttonbox.Add (self.test_button)
        buttonbox.AddSpacer((5,5))
        buttonbox.Add (self.run_button)
        buttonbox.AddSpacer((5,5))
        buttonbox.Add (self.cancel_button)
        buttonbox.AddSpacer((5,5))
        buttonbox.Add (self.park_button)
        buttonbox.AddSpacer((5,5))
        buttonbox.Add (self.ParkPosSummary)

        vbox.Add (buttonbox)

        # Leave a 10-pixel wide space around the panel.
        border = wx.BoxSizer()
        border.Add (vbox,0,wx.ALL,10) 
        self.SetSizer(border)
        
        self.Bind(wx.EVT_COMBOBOX,self.on_input)
        self.Bind(wx.EVT_CHECKBOX,self.on_input)
        self.Bind(wx.EVT_TEXT_ENTER,self.on_input)

        self.Bind(wx.EVT_BUTTON,self.run_test,self.test_button)
        self.Bind(wx.EVT_BUTTON,self.run_now,self.run_button)
        self.Bind(wx.EVT_BUTTON,self.cancel,self.cancel_button)
        self.Bind(wx.EVT_BUTTON,self.change_park_pos,self.park_button)

        # Periodically update the window.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Called periodically every second triggered by a timer"""
        if IsShownOnScreen(self):
            self.update_parameters()
            self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer.

    def update_parameters(self):
        """Refreshes the control panel"""
        reload_settings()
        self.BeamcheckEnabled.Value = "on" if lasercheck.enabled else "off"

        self.CheckOnly.Value = lasercheck.check_only
        
        self.Interval.Value = (time_string(lasercheck.interval))

        nexttime = lasercheck.last + lasercheck.interval
        text = "at "+strftime("%H:%M",localtime(nexttime))
        if nexttime<time(): text = "immediately"
        text = " (Next: "+text+")"
        
        if lasercheck.at_start_of_time_series: self.OnlyAtBeginning.Value = ("yes")
        else: self.OnlyAtBeginning.Value = ("no")
        self.RetractSample.Value = ("yes" if lasercheck.retract_sample else "no")

        self.Attenuator.Value = ("%g deg" % lasercheck.attenuator)
        self.RepRate.Value = ("%g Hz" % lasercheck.reprate)
        self.Average.Value = ("%g" % lasercheck.naverage)
        self.MinSignalNoise.Value = ("%g" % lasercheck.signal_to_noise)
        self.ParkPosSummary.SetLabel (laser_beamcheck_park_summary()
            if lasercheck.retract_sample else "")
        self.ParkPosSummary.SetSize((290,45))

    def update(self,event=None):
        """Update field that change not triggered by user input"""
        reload_settings()
        # Called periodically one a 1-s timer if panel is shown.

        comment = lasercheck.comment
        date = strftime("%d %b %y %H:%M",localtime(lasercheck.last))
        if comment: comment = date+": "+comment
        else: comment = "Laser beam position never measured so far."
        self.Comment.SetLabel(comment) 
        self.Comment.SetSize((620,45)) 
        
        if not task.action:
            self.test_button.Enable()
            self.run_button.Enable()
            self.cancel_button.Disable()
        else:
            self.test_button.Disable()
            self.run_button.Disable()
            self.cancel_button.Enable()
        if task.cancelled: self.cancel_button.SetLabel("Cancelled")
        else: self.cancel_button.SetLabel("Cancel")

        if lasercheck.last > self.BeamProfile.last_updated:
            self.BeamProfile.Refresh()
 
    def on_input(self, event):
        """This is called when the user switches between fields and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        lasercheck.enabled = (self.BeamcheckEnabled.GetValue() == "on")

        lasercheck.check_only = self.CheckOnly.Value

        value = seconds(self.Interval.GetValue())
        if value != None: lasercheck.interval = value

        lasercheck.at_start_of_time_series = (self.OnlyAtBeginning.GetValue() == "yes")

        lasercheck.retract_sample = (self.RetractSample.GetValue() == "yes")
 
        value = self.Attenuator.GetValue().replace("deg","")
        try: lasercheck.attenuator = float(eval(value))
        except ValueError: pass

        value = self.RepRate.GetValue().replace("Hz","")
        try: lasercheck.reprate = float(eval(value))
        except ValueError: pass

        value = self.Average.GetValue()
        try: lasercheck.naverage = int(eval(value))
        except ValueError: pass
        
        value = self.MinSignalNoise.GetValue()
        try: lasercheck.signal_to_noise = float(eval(value))
        except ValueError: pass
        
        save_settings()
        self.update_parameters()

        """Measure the laser beam position and log it, but do not apply
        any beamsteering corrections"""
        # Called when the 'Test' button is pressed
        task.action = "Laser Beam Check - Test"

    def run_test(self,event):
        """Measure the laser beam position and log it, but do not apply
        any beamsteering corrections"""
        # Called when the 'Test' button is pressed
        task.action = "Laser Beam Check - Test"

    def run_now(self,event):
        """Measure the laser beam position and log it and apply
        beamsteering corrections"""
        # Called when the 'Run Now' button is pressed
        task.action = "Laser Beam Check"

    def cancel(self,event): 
        "Called when the 'Cancel' button is pressed"
        task.cancelled = True; task.action = ""

    def change_park_pos(self,event): 
        "Called when the 'Park Position' button is pressed"
        dlg = self.ParkPositions (self)
        dlg.CenterOnParent()
        dlg.Show() 

    class ParkPositions (wx.Dialog):
        Nmax = 5 # maximum number of motors
        
        def __init__ (self,parent):
            wx.Dialog.__init__(self,parent,-1,"Park Positions")

            motors = ["-","DetZ","Phi","DiffX","DiffY","DiffZ"]

            layout = wx.GridBagSizer(1,1)
            a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL

            layout.Add(wx.StaticText(self,label="Motor",size=(90,-1)),(0,0),flag=a)
            layout.Add(wx.StaticText(self,label="Beamcheck",size=(90,-1)),(0,1),flag=a)
            layout.Add(wx.StaticText(self,label="Collection",size=(90,-1)),(0,2),flag=a)
            layout.Add(wx.StaticText(self,label="Current",size=(90,-1)),(0,3),flag=a)
            
            self.Motors = [None]*self.Nmax
            self.Positions = [None]*self.Nmax
            self.SamplePositions = [None]*self.Nmax
            self.CurrentPositions = [None]*self.Nmax
            e = wx.TE_PROCESS_ENTER
            for i in range(0,self.Nmax):
                self.Motors[i] = ComboBox (self,choices=motors)
                layout.Add(self.Motors[i],(i+1,0),flag=a)
                self.Positions[i] = TextCtrl(self,size=(90,-1),style=e)
                layout.Add(self.Positions[i],(i+1,1),flag=a)
                self.SamplePositions[i] = TextCtrl(self,size=(90,-1),style=e)
                layout.Add(self.SamplePositions[i],(i+1,2),flag=a)
                self.CurrentPositions[i] = wx.StaticText(self,size=(90,-1))
                layout.Add(self.CurrentPositions[i],(i+1,3),flag=a)

            self.UseCurrentPark = wx.Button(self,label="Use Current",size=(90,-1))
            self.GoToPark = wx.Button(self,label="Go To",size=(90,-1))
            self.UseCurrentSample = wx.Button(self,label="Use Current",size=(90,-1))
            self.GoToSample = wx.Button(self,label="Go To",size=(90,-1))
            self.Cancel = wx.Button(self,label="Cancel",size=(90,-1))

            layout.Add(self.UseCurrentPark,(self.Nmax+2,1),flag=a)
            layout.Add(self.GoToPark,(self.Nmax+3,1),flag=a)
            layout.Add(self.UseCurrentSample,(self.Nmax+2,2),flag=a)
            layout.Add(self.GoToSample,(self.Nmax+3,2),flag=a)
            layout.Add(self.Cancel,(self.Nmax+3,3),flag=a)

            # Leave a 10-pixel wide space around the panel.
            border = wx.BoxSizer(wx.VERTICAL)
            border.Add (layout,0,wx.ALL,10) 
            self.SetSizer(border)
            self.Fit()
 
            # Callbacks
            self.Bind(wx.EVT_COMBOBOX,self.on_input)
            self.Bind(wx.EVT_TEXT_ENTER,self.on_input)

            self.Bind(wx.EVT_BUTTON,self.use_current_park,self.UseCurrentPark)
            self.Bind(wx.EVT_BUTTON,self.goto_park,self.GoToPark)
            self.Bind(wx.EVT_BUTTON,self.use_current_sample,self.UseCurrentSample)
            self.Bind(wx.EVT_BUTTON,self.goto_sample,self.GoToSample)
            self.Bind(wx.EVT_BUTTON,self.cancel,self.Cancel)

            # Periodically update the displayed fields.
            self.timer = wx.Timer(self)
            self.Bind (wx.EVT_TIMER,self.OnTimer)
            self.OnTimer()

        def OnTimer(self,event=None):
            """Called periodically every second triggered by a timer"""
            if IsShownOnScreen(self):
                self.update_parameters()
                self.update()
            self.timer.Start(1000,oneShot=True) # Need to restart the Timer

        def update_parameters(self,event=None):
            """Refresh all fields"""
            reload_settings()
            for i in range(0,self.Nmax):
                if i < len(lasercheck.park_motors):
                    self.Motors[i].Value = (lasercheck.park_motors[i])
                    if i < len(lasercheck.park_positions): pos = lasercheck.park_positions[i]
                    else: pos = nan
                    self.Positions[i].Value = (tostr(pos))
                    if i < len(lasercheck.sample_position): pos = lasercheck.sample_position[i]
                    else: pos = nan
                    self.SamplePositions[i].Value = (tostr(pos))
                else:
                    self.Motors[i].Value = ("-")
                    self.Positions[i].Value = ("-")
                    self.SamplePositions[i].Value = ("-")
            self.update()

        def update(self,event=None):
            "Refresh dynamically changing fields"
            Nmotors = min(len(lasercheck.park_motors),len(lasercheck.park_positions))
            for i in range(0,self.Nmax):
                if i < Nmotors:
                    pos = self.motor_pos(lasercheck.park_motors[i])
                    self.CurrentPositions[i].SetLabel(tostr(pos))
                else: self.CurrentPositions[i].SetLabel("-")

            if not task.action:
               self.GoToPark.Enable()
               self.GoToSample.Enable()
               self.Cancel.Disable()
            else:
               self.GoToPark.Disable()
               self.GoToSample.Disable()
               self.Cancel.Enable()
            if task.cancelled: self.Cancel.SetLabel("Cancelled")
            else: self.Cancel.SetLabel("Cancel")

        @staticmethod
        def motor_pos(name):
            "Current position of a motor given by name"
            try:
                motor = eval(name)
                return motor.value
            except: return nan
 
        def on_input(self, event):
            """This is called when the user switches between fields and controls
            using Tab or the mouse, or presses Enter in a text entry. This does
            necessarily indicate that any value was changed. But it is a good
            opportunity the process any changes."""
            park_motors = []
            park_position = []
            sample_position = []
            for i in range(0,self.Nmax):
                motor = self.Motors[i].GetValue()
                try: park = float(eval(self.Positions[i].GetValue()))
                except: park = self.motor_pos(motor)
                try: sample = float(eval(self.SamplePositions[i].GetValue()))
                except: sample = self.motor_pos(motor)
                if motor != "-" and motor != "":
                     park_motors += [motor]
                     park_position += [park]
                     sample_position += [sample]
            lasercheck.park_motors = park_motors
            lasercheck.park_positions = park_position
            lasercheck.sample_position = sample_position
            save_settings()
            self.update_parameters()

        def use_current_park(self,event):
            "Use current motor positions as parking positions"
            laser_beamcheck_remember_park_pos()
            self.update_parameters()
            
        def goto_park(self,event):
            "Drive motors to specified parking positions"        
            task.action = "Laser Beam Check - Retract Sample"
            self.update()

        def use_current_sample(self,event):
            "Use current motor positions as parking positions"
            laser_beamcheck_remember_sample_pos()
            self.update_parameters()
            
        def goto_sample(self,event):
            "Drive motors to specified parking positions"        
            task.action = "Laser Beam Check - Return Sample"
            self.update()

        def cancel(self,event): 
            "Called when the 'Cancel' button is pressed"
            task.cancelled = True; task.action = ""


class TimingPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)

        # Controls
        size = (100,-1)
        e = wx.TE_PROCESS_ENTER
        self.IsEnabled = ComboBox(self,choices=['on','off'],size=size)

        self.Interval = TextCtrl(self,size=size,style=e)
        self.Next = wx.StaticText(self)
        self.OnlyAtBeginning = ComboBox(self,choices=['yes','no'],size=size)
        self.RetractSample = TextCtrl(self,style=e,size=size)
        self.SampleMotor = ComboBox(self,choices=["SampleX","SampleY","SampleZ",""],size=size)
        self.MinIntensity = TextCtrl(self,style=e,size=size)

        self.Comment = wx.StaticText(self,size=(620,45))

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL

        size = (-1,-1)
        t = wx.StaticText (self,label="Recalibrate during collection:",size=size)
        layout.Add(t,(0,0),flag=a)
        layout.Add(self.IsEnabled,(0,1),flag=a)

        t = wx.StaticText (self,label="Repeat every:",size=size)
        layout.Add(t,(2,0),flag=a)
        layout.Add(self.Interval,(2,1),flag=a)
        layout.Add(self.Next,(2,2),flag=a)

        t = wx.StaticText (self,label="Only at start of time series:",size=size)
        layout.Add(t,(3,0),flag=a)
        layout.Add(self.OnlyAtBeginning,(3,1),flag=a)

        t = wx.StaticText (self,label="Retract sample by:",size=size)
        layout.Add(t,(4,0),flag=a)
        layout.Add(self.RetractSample,(4,1),flag=a)

        t = wx.StaticText (self,label="Using motor:",size=size)
        layout.Add(t,(5,0),flag=a)
        layout.Add(self.SampleMotor,(5,1),flag=a)

        t = wx.StaticText (self,label="Minimum Intensity:",size=size)
        layout.Add(t,(6,0),flag=a)
        layout.Add(self.MinIntensity,(6,1),flag=a)

        layout.Add(self.Comment,(8,0),span=(1,4),flag=a)
        
        # Leave a 10-pixel wide space around the panel.
        border = wx.BoxSizer()
        border.Add (layout,0,wx.ALL,10) 
        self.SetSizer(border)
        
        self.Bind(wx.EVT_COMBOBOX,self.on_input)
        # Call the "on_input" routine whenever the user presses Enter.
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)

        self.test_button = wx.Button(self,label="Test",pos=(10,300),
            size=(100,-1))
        self.test_button.SetDefault()
        self.Bind (wx.EVT_BUTTON,self.run_test,self.test_button)

        self.run_button = wx.Button(self,label="Run Now",pos=(120,300),
            size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.run_now,self.run_button)

        self.cancel_button = wx.Button(self,label="Cancel",pos=(230,300),
            size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.cancel,self.cancel_button)

        # Periodically update the displayed fields.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Called periodically every second triggered by a timer"""
        if IsShownOnScreen(self):
            self.update_parameters()
            self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update(self,event=None):
        """Refresh the control panel"""
        reload_settings()

        last = strftime("%d %b %y %H:%M",localtime(timingcheck.last))
        nexttime = timingcheck.last + timingcheck.interval
        next = "at "+strftime("%H:%M",localtime(nexttime))
        if nexttime<time(): next = "immediately"
        text = " (Last %s, next %s)" % (last,next)
        self.Next.Label = text
        
        self.Comment.SetLabel(timingcheck.comment) 
        self.Comment.SetSize((620,45)) 
        
        if not task.action:
           self.test_button.Enable()
           self.run_button.Enable()
           self.cancel_button.Disable()
        else:
           self.test_button.Disable()
           self.run_button.Disable()
           self.cancel_button.Enable()
        if task.cancelled: self.cancel_button.Label = "Cancelled"
        else: self.cancel_button.Label = "Cancel"
        if task.action: self.timer.Start(1000,oneShot=True)
 
    def update_parameters(self):
        """Refresh the control panel"""
        reload_settings()
        self.IsEnabled.Value = "on" if timingcheck.enabled else "off"
        
        self.Interval.Value = time_string(timingcheck.interval)

        self.OnlyAtBeginning.Value = \
            "yes" if timingcheck.at_start_of_time_series else "no"
        self.RetractSample.Value = "%g mm" % timingcheck.retract_sample
        self.SampleMotor.Value = timingcheck.sample_motor
        self.MinIntensity.Value = "%g%%" % (timingcheck.min_intensity*100)
        
    def on_input(self, event):
        """This is called when the user switches between fields and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        timingcheck.enabled = (self.IsEnabled.Value == "on")

        value = seconds(self.Interval.Value)
        if value != None: timingcheck.interval = value

        timingcheck.at_start_of_time_series = (self.OnlyAtBeginning.Value == "yes")

        value = self.RetractSample.Value.replace("mm","")
        try: timingcheck.retract_sample = float(eval(value))
        except ValueError: pass

        timingcheck.sample_motor = self.SampleMotor.Value

        value = self.MinIntensity.Value.replace("%","/100.0")
        try: timingcheck.min_intensity = float(eval(value))
        except ValueError: pass
        
        save_settings()
        self.update_parameters()

    def on_sample(self,event):
        "Called when the 'Retract Sample' button is pressed"

    def run_test(self,event):
        """Measurre the timing error, but do not take any corrective action"""
        # Called when the 'Test' button is pressed"
        task.action = "Timing Check - Test"
        self.update()

    def run_now(self,event):
        """Measure the timing error and recalibrate T=0 if needed"""
        # Called when the 'Run Now' button is pressed"
        task.action = "Timing Check"
        self.update()

    def cancel(self,event): 
        "Called when the 'Cancel' button is pressed"
        task.cancelled = True; task.action = ""


class SamplePhotoPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)

        # Controls
        size = (100,-1)
        style = wx.TE_PROCESS_ENTER
        self.SamplePhotoEnabled = ComboBox(self,choices=['on','off'],size=size)
        self.Phis = TextCtrl(self,size=size,style=style)

        self.Image = Image(self,size=(295,245))

        self.test_button = wx.Button(self,label="Test",size=(100,-1))
        self.acquire_button = wx.Button(self,label="Acquire Now",size=(100,-1))

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL

        # Parameter 'size' needed because of bug in WX 2.6 or earlier.
        size = (200,-1)
        t = wx.StaticText (self,label="Take sample photos:",size=size)
        layout.Add(t,(0,0),flag=a)
        layout.Add(self.SamplePhotoEnabled,(0,1),flag=a)

        t = wx.StaticText (self,label="At Phi:",size=size)
        layout.Add(t,(1,0),flag=a)
        layout.Add(self.Phis,(1,1),flag=a)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add (layout)
        hbox.AddSpacer((10,10))
        hbox.Add (self.Image)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add (hbox)

        buttonbox = wx.BoxSizer(wx.HORIZONTAL)
        buttonbox.Add (self.test_button)
        buttonbox.AddSpacer((5,5))
        buttonbox.Add (self.acquire_button)

        vbox.Add (buttonbox)

        # Leave a 10-pixel wide space around the panel.
        border = wx.BoxSizer()
        border.Add (vbox,0,wx.ALL,10) 
        self.SetSizer(border)
        
        self.Bind(wx.EVT_COMBOBOX,self.on_input)
        self.Bind(wx.EVT_CHECKBOX,self.on_input)
        # Call the "on_input" routine whenever the user presses Enter.
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)

        self.Bind (wx.EVT_BUTTON,self.run_test,self.test_button)
        self.Bind (wx.EVT_BUTTON,self.acquire_image,self.acquire_button)

        # Periodically update the window.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        "Called periodically every second triggered by a timer"
        if IsShownOnScreen(self):
            self.update_parameters()
            self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer.

    def update_parameters(self):
        """Refresh the control panel"""
        reload_settings()
        self.SamplePhotoEnabled.Value = "on" if sample_photo.enabled else "off"
        self.Phis.Value = str(sample_photo.phis).strip("[](),")

    def update(self,event=None):
        """Update fields that change, not triggered by user input"""
        reload_settings()
        # Called periodically one a 1-s timer if panel is shown.
        self.Image.Image = sample_photo_current_image()
        
    def on_input(self, event):
        """This is called when the user switches between fields and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        sample_photo.enabled = (self.SamplePhotoEnabled.Value == "on")
        phis = self.Phis.Value
        if not "," in phis: phis += ","
        try: phis= eval(phis)
        except: phis = [0]
        sample_photo.phis = phis

        save_settings()
        self.update_parameters()

    def run_test(self,event):
        """Measure the laser beam position and log it, but do not apply
        any beamsteering corrections"""
        # Called when the 'Test' button is pressed
        task.action = "Sample Photo - Test"

    def acquire_image(self,event):
        """Measure the laser beam position and log it and apply
        beamsteering corrections"""
        # Called when the 'Acquire' button is pressed
        task.action = "Sample Photo"

    def cancel(self,event): 
        """Called when the 'Cancel' button is pressed"""
        task.cancelled = True; task.action = ""


class CheckListPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self,parent,-1)
 
        y = 10; x = 10
        self.IDs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.IDt = wx.StaticText (self,label="Insertion Devices",
            pos=(x,y+3))
        y += 24; x = 10
        self.FEs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.FEt = wx.StaticText (self,label="Frontend shutter",
            pos=(x,y+3))
        y += 24; x = 10
        self.WBSs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.Bind (wx.EVT_BUTTON,self.white_beam_slits_setup,self.WBSs)
        self.WBSt = wx.StaticText (self,label="White beam slits",
            pos=(x,y+3))
        y += 24; x = 10
        self.HLSs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.HLSt = wx.StaticText (self,label="Heatload chopper",
            pos=(x,y+3))
        y += 24; x = 10
        self.XIAFs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.XIAFt = wx.StaticText (self,label="XIA Filters",
            pos=(x,y+3))
        y += 24; x = 10
        self.XIASs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.XIASt = wx.StaticText (self,label="XIA Shutter",
            pos=(x,y+3))
        y += 24; x = 10
        self.MSSs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.MSSt = wx.StaticText (self,label="Millisecond shutter",
            pos=(x,y+3))
        y += 24; x = 10
        self.HSSs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.HSSt = wx.StaticText (self,label="High-speed chopper",
            pos=(x,y+3))
        y += 24; x = 10
        self.SSs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.Bind (wx.EVT_BUTTON,self.sample_slits_setup,self.SSs)
        self.SSt = wx.StaticText (self,label="Sample JJ slits",
            pos=(x,y+3))
        y += 24; x = 10
        self.TMODEs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.TMODEt = wx.StaticText (self,label="Laser trigger mode",
            pos=(x,y+3))
        y += 24; x = 10
        self.ATTs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.ATTt = wx.StaticText (self,label="Laser Attenuators",
            pos=(x,y+3))
        y += 24; x = 10
        self.LSHUTs = wx.Button(self,pos=(x,y),size=(20,18)); x+=30
        self.LSHUTt = wx.StaticText (self,label="Laser Shutter",
            pos=(x,y+3))
        
        button = wx.Button(self,label="Update",pos=(10,300),size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.update_checklist,button)
        
    def update_checklist(self,event=None):
        """Update the checklist."""
        red = wx.Colour(255,0,0); green = wx.Colour(0,255,0)
        yellow = wx.Colour(255,255,0)
        gray = wx.Colour(180,180,180)

        U23gap = U23.value; U27gap = U27.value
        state = "U23 at %.3f mm, U27 at %.3f mm" % (U23gap,U27gap)
        OK = abs(U23gap-checklist.U23)<0.05 and abs(U27gap-checklist.U27)<0.05
        bad = (U23gap > 29 and U27gap > 29)
        if not OK:
            state += " (expecting %.3f, %.3f mm)" % (checklist.U23,checklist.U27)
        if OK: self.IDs.SetBackgroundColour(green)
        elif bad: self.IDs.SetBackgroundColour(red)
        else: self.IDs.SetBackgroundColour(yellow)
        self.IDt.SetLabel("Insertion Devices: "+state)

        state = "open" if xray_safety_shutters_open.value else "closed"
        if not xray_safety_shutters_enabled.value: state += ", no permit"
        if "closed" in state and options.wait_for_beam:
            state += ", will open automatically"
        OK = (state == "open")
        bad = (("closed" in state and not options.wait_for_beam) \
            or "no permit" in state)
        if OK: self.FEs.SetBackgroundColour(green)
        elif bad: self.FEs.SetBackgroundColour(red)
        else: self.FEs.SetBackgroundColour(yellow)
        self.FEt.SetLabel("Frontend shutter: "+state)

        slhg = tofloat(caget("14IDA:Slit1Hsize.VAL"))
        slvg = tofloat(caget("14IDA:Slit1Vsize.VAL"))
        state = "%.3g mmh x %.3g mmv" % (slhg,slvg)
        OK = abs(slhg-checklist.wbshg) < 0.005 and (slvg-checklist.wbsvg) < 0.005
        bad = (slvg <= 0 or slhg <= 0)
        if not OK: state += " (expecting %.3f mmh x %.3f mmv)" \
            % (checklist.wbshg,checklist.wbsvg)
        if OK: self.WBSs.SetBackgroundColour(green)
        elif bad: self.WBSs.SetBackgroundColour(red)
        else: self.WBSs.SetBackgroundColour(yellow)
        self.WBSt.SetLabel("White beam slits: "+state)

        pos = tofloat(caget("14IDA:m5.VAL"))
        slots = {-3.0:"3 mm",-0.5:"1.5 mm x 1",7.0:"1.5 mm x 12",10:"Full Beam"}
        if pos in slots: slot = slots[pos]
        else: slot = "?"
        rpm = tofloat(caget("14IDA:LA2000_SPD.TINP"))
        f = rpm / 60
        state = "%g Hz, slot: %s (pos %g mm)" % (f,slot,pos)
        OK = (pos == -0.5 and abs(f - 82.3) < 0.1)
        bad = (pos > 0 or abs(f - 82.3) >= 0.1)
        if OK: self.HLSs.SetBackgroundColour(green)
        elif bad: self.HLSs.SetBackgroundColour(red)
        else: self.HLSs.SetBackgroundColour(yellow)
        self.HLSt.SetLabel("Heatload chopper: "+state)

        UAg = tofloat(caget("14IDB:DAC1_2.VAL"))
        UTi = tofloat(caget("14IDB:DAC1_3.VAL"))
        state = ""
        if UAg < 2.5: state += "Ag 75 um"
        if UTi < 2.5: state += "+ Ti 75 um"
        state = state.strip("+ ")
        if state == "": state = "no filter inserted"
        OK = (UAg == 5.0 and UTi == 5.0)
        if OK: self.XIAFs.SetBackgroundColour(green)
        else: self.XIAFs.SetBackgroundColour(red)
        self.XIAFt.SetLabel("XIA Filters: "+state)

        state_code = caget("14IDB:xiaStatus.VAL")
        if state_code == 1: state = "open"
        elif state_code == 0: state = "closed"
        else: state = "unkonwn"
        OK = (state == "open")
        if OK: self.XIASs.SetBackgroundColour(green)
        else: self.XIASs.SetBackgroundColour(red)
        self.XIASt.SetLabel("XIA Shutter: "+state)

        U = caget("14IDB:DAC1_1.VAL")
        if U == 0 and timing_system.mson.value == 1:
            f = 1/timing_system.waitt.value
            if timing_sequencer.running: state = "continuously pulsed at %g Hz" % f
            else: state = "pulsed on demand"
        elif U == 0 and timing_system.mson.value == 0:
            state = "closed, pulsed operation disabled"
        elif U == 5: state = "always open"
        else: state = "control voltage "+str(U)+"V"
        OK = (state == "pulsed on demand")
        if OK: self.MSSs.SetBackgroundColour(green)
        else: self.MSSs.SetBackgroundColour(red)
        self.MSSt.SetLabel("Millisecond shutter: "+state)

        def dist((x1,y1),(x2,y2)): return sqrt((x2-x1)**2+(y2-y1)**2)

        npulses = chopper_pulses()
        i = chopper_mode_current()
        pos = (x,y) = (ChopX.value,ChopY.value)
        bypass = array([25.0,29.554])
        if dist(pos,bypass) < 0.5: mode = "bypass"
        elif not isnan(npulses): mode = "selecting %g pulses" % npulses
        else: mode = "unknown mode (%.3f, %.3f mm)" % (x,y)
        if not isnan(i):
            dx = x - chopper.x[i]
            dy = y - chopper.y[i]
            dt = timing_system.hsc.delay.value - chopper.phase[i]
        else: dx,dy,dt = nan,nan,nan
        if abs(dx) > 0.001: mode += ", X error %g mm" % dx
        if abs(dy) > 0.001: mode += ", Y error %g mm" % dy
        if abs(dt) >= 3e-9: mode += ", phase error "+time_string(dt)
        OK = not isnan(npulses) and not abs(dx) > 0.020 and not abs(dy) > 0.010\
             and not abs(dt) > 3e-9
        bad = (mode == "bypass")
        if OK: self.HSSs.SetBackgroundColour(green)
        elif bad: self.HSSs.SetBackgroundColour(red)
        else: self.HSSs.SetBackgroundColour(yellow)
        self.HSSt.SetLabel("High-speed chopper: "+mode)

        (slhg,slvg) = (shg.value,svg.value)
        state = "%.3f mmh x %.3f mmv" % (slhg,slvg)
        OK = (abs(slhg-checklist.shg)<=0.001 and abs(slvg-checklist.svg)<=0.001)
        bad = (slhg < 0.01 or slvg < 0.01)
        if not OK: state += " (expecting %g mmh x %g mmv)" % \
            (checklist.shg,checklist.svg)
        if OK: self.SSs.SetBackgroundColour(green)
        elif bad: self.SSs.SetBackgroundColour(red)
        else: self.SSs.SetBackgroundColour(yellow)
        self.SSt.SetLabel("Sample JJ slits: "+state)

        f = 1/timing_system.waitt.value
        running = timing_sequencer.running
        if running: state = "running at at %g Hz" % f
        elif running == 1: state = "stopped"
        else: state = "?"
        OK = ("running" in state)
        if timing_system.laseron.value == 0: state += " when enabled (currently disabled)"
        if OK: self.TMODEs.SetBackgroundColour(green)
        else: self.TMODEs.SetBackgroundColour(red)
        if variable_choices("laser_on") == [False]:
            self.TMODEs.SetBackgroundColour(gray)
        self.TMODEt.SetLabel("Laser trigger mode: "+state)

        T1 = trans1.value # in Laser Lab
        T2 = trans.value # in X-ray hutch
        OK = (T1 == 1.0 and T2 >= 0.1)
        bad = (T1 < 0.02 or T2 < 0.02)
        if not isnan(T1): T1 = "%.3g%% transm." % (T1*100)
        else: T1 = "offline"
        if not isnan(T2): T2 = "%.3g%% transm." % (T2*100)
        else: T2 = "offline"
        state = "Laser Lab: "+T1+", X-ray hutch: "+T2
        if OK: self.ATTs.SetBackgroundColour(green)
        elif bad: self.ATTs.SetBackgroundColour(red)
        else: self.ATTs.SetBackgroundColour(yellow)
        if variable_choices("laser_on") == [False]: self.ATTs.SetBackgroundColour(gray)
        self.ATTt.SetLabel("Laser attenuators: "+state)

        val = caget("14IDB:B1Bi0.VAL")
        if val == 0: state = "open"
        elif val == 1: state = "closed"
        else: state = "?"
        OK = (state == "open")
        bad = (state == "closed" and not options.open_laser_safety_shutter)
        if state == "closed" and options.open_laser_safety_shutter:
            state += " (will open automatically)"
        if OK: self.LSHUTs.SetBackgroundColour(green)
        elif bad: self.LSHUTs.SetBackgroundColour(red)
        else: self.LSHUTs.SetBackgroundColour(yellow)
        if variable_choices("laser_on") == [False]: self.LSHUTs.SetBackgroundColour(gray)
        self.LSHUTt.SetLabel("Laser shutter: "+state)

    def white_beam_slits_setup(self,event):
        "Modify nominal settings for the JJ sample slits"
        dlg = wx.TextEntryDialog(self,"Settings for data collection "\
            "(mmh x mmv)","White Beam Slits","")
        dlg.Value = ("%.3f,%.3f" % (checklist.wbshg,checklist.wbsvg))
        OK = (dlg.ShowModal() == wx.ID_OK)
        if not OK: return 
        try: checklist.wbshg,checklist.wbsvg = eval(dlg.GetValue())
        except: return
        save_settings()

    def sample_slits_setup(self,event):
        "Modify nominal settings for the JJ sample slits"
        dlg = wx.TextEntryDialog(self,"Settings for data collection "\
            "(mmh x mmv)","Sample JJ Slits","")
        dlg.Value = ("%.3f,%.3f" % (checklist.shg,checklist.svg))
        OK = (dlg.ShowModal() == wx.ID_OK)
        if not OK: return 
        try: checklist.shg,checklist.svg = eval(dlg.GetValue())
        except: return
        save_settings()


class BeamProfile(wx.ScrolledWindow):
    "Display the Laser beam profile. Needed by LaserCheckPanel."
    
    def __init__(self,parent,**options):
        wx.ScrolledWindow.__init__(self,parent,**options)
        self.Bind (wx.EVT_PAINT, self.OnPaint)
        self.last_updated = 0

    def OnPaint (self,event):
        """Called by WX whenever the contents of the window
        needs re-rendering. E.g. when the window is brought to front,
        uncovered, restored from minimized state."""
        from PIL import Image
        global lasercheck_image

        dc = wx.PaintDC(self)
        self.PrepareDC(dc)

        if not lasercheck_image:
            try: lasercheck_image = Image.open(lasercheck.last_image)
            except IOError: pass
        if lasercheck_image:
            w,h = lasercheck_image.size
            image = wx.EmptyImage(w,h)
            image.SetData(lasercheck_image.tobytes())
            # Scale the image to fit into the window.
            W,H = self.GetClientSize()
            scalefactor = min(float(W)/w,float(H)/h)
            w = round(w*scalefactor); h = round(h*scalefactor)
            image = image.Scale(w,h)
            dc.DrawBitmap (wx.BitmapFromImage(image),0,0)
        else:
            w,h = self.GetClientSize()

        self.last_updated = time()

        # Draw the FWHM with dimensions box around the beam center,
        # horizontal and vertcal beam projections or sections on the left and
        # bottom edge of the image

        if len(lasercheck.zprofile)==0 or len(lasercheck.xprofile)==0: return

        # Draw a crosshair marking the nominal beam center.
        crosshair_color = wx.Colour(255,0,255)
        l = 0.05 # crosshair size in mm
        x = xvals(lasercheck.zprofile); y = xvals(lasercheck.xprofile)
        xscale = w/(x[-1]-x[0]); xoffset = -x[0]/(x[-1]-x[0])*w
        yscale = -1/(y[0]-y[-1])*h; yoffset = y[-1]/(y[0]-y[-1])*h + h
        dc.SetPen (wx.Pen(crosshair_color,0))
        dc.DrawLines ([(-l/2*xscale+xoffset,yoffset),(+l/2*xscale+xoffset,yoffset)])
        dc.DrawLines ([(xoffset,-l/2*yscale+yoffset),(xoffset,+l/2*yscale+yoffset)])        
        
        # Draw horizontal profile at the bottom edge of the image.
        profile_color = wx.Colour(255,0,255)
        dc.SetPen (wx.Pen(profile_color,0))
        x = xvals(lasercheck.zprofile); y = yvals(lasercheck.zprofile)
        ymax = max(y)
        if ymax == 0: ymax = 1
        xscale = w/(x[-1]-x[0]); xoffset = -x[0]*xscale
        yscale = -0.35 * h/ymax; yoffset = h
        lines = []
        for i in range(0,len(x)-1):
            if not isnan(y[i]) and not isnan(y[i+1]):
                p1 = x[i]  *xscale+xoffset, y[i]  *yscale+yoffset
                p2 = x[i+1]*xscale+xoffset, y[i+1]*yscale+yoffset
                lines += [(p1[0],p1[1],p2[0],p2[1])]
        dc.DrawLineList(lines)
    
        # Draw vertical profile at the left edge of the image.
        x = xvals(lasercheck.xprofile); y = yvals(lasercheck.xprofile)
        ymax = max(y)
        if ymax == 0: ymax = 1
        xscale = h/(x[-1]-x[0]); xoffset = -x[0]*xscale
        yscale = 0.35 * w/ymax; yoffset = 0
        lines = []
        for i in range(0,len(x)-1):
            if not isnan(y[i]) and not isnan(y[i+1]):
                p1 = y[i]  *yscale+yoffset, x[i]  *xscale+xoffset
                p2 = y[i+1]*yscale+yoffset, x[i+1]*xscale+xoffset
                lines += [(p1[0],p1[1],p2[0],p2[1])]
        dc.DrawLineList(lines)

        # Draw a box around center of the beam, with the size of the FWHM.
        FWHM_color = wx.Colour(255,0,0)
        from beam_profiler import FWHM,CFWHM
        width,height = FWHM(lasercheck.zprofile),FWHM(lasercheck.xprofile)
        cx,cy = CFWHM(lasercheck.zprofile),CFWHM(lasercheck.xprofile)

        x = xvals(lasercheck.zprofile); y = xvals(lasercheck.xprofile)
        xscale = w/(x[-1]-x[0]); xoffset = -x[0]*xscale
        yscale = -1/(y[0]-y[-1])*h; yoffset = y[-1]/(y[0]-y[-1])*h + h

        x1,y1 = (cx-width/2)*xscale+xoffset,(cy-height/2)*yscale+yoffset
        x2,y2 = (cx+width/2)*xscale+xoffset,(cy+height/2)*yscale+yoffset
        lines = [(x1,y1),(x2,y1),(x2,y2),(x1,y2),(x1,y1)]
        dc.SetPen (wx.Pen(FWHM_color,0))
        dc.DrawLines (lines)

        # Draw a vertical and horizontal line throught the center.
        center_color = wx.Colour(128,128,255)
        dc.SetPen (wx.Pen(center_color,0))
        dc.DrawLines ([(cx*xscale+xoffset,h),(cx*xscale+xoffset,0)])
        dc.DrawLines ([(0,cy*yscale+yoffset),(w,cy*yscale+yoffset)])

        # Annotate the lines.
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetPointSize(10)
        dc.SetFont(font)
        dc.SetTextForeground(center_color)

        if abs(cx) < 1: label = "%+.0f um" % (cx*1000)
        else: label = "%+.3f mm" % cx
        x,y = cx*xscale+xoffset,0.875*h
        tw,th = dc.GetTextExtent(label)
        dc.DrawRotatedText (label,x+2,y-th/2,0)

        if abs(cy) < 1: label = "%+.0f um" % (cy*1000)
        else: label = "%+.3f mm" % cy
        x,y = 0.175*w,cy*yscale+yoffset
        tw,th = dc.GetTextExtent(label)
        dc.DrawRotatedText (label,x-th/2,y+2,-90)        

    
class Image(wx.ScrolledWindow):
    """Display a photo of the sample. Needed by SamplePhotoPanel."""
    
    def __init__(self,parent,**options):
        wx.ScrolledWindow.__init__(self,parent,**options)
        from PIL import Image
        self.PIL_image = Image.new('RGB',(1360,1024))
        self.Bind (wx.EVT_PAINT, self.OnPaint)        

    def OnPaint (self,event):
        """Called by WX whenever the contents of the window
        needs re-rendering. E.g. when the window is brought to front,
        uncovered, restored from minimized state."""
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)

        w,h = self.Image.size
        image = wx.EmptyImage(w,h)
        image.SetData(self.Image.tobytes())
        # Scale the image to fit into the window.
        W,H = self.ClientSize
        scalefactor = min(float(W)/w,float(H)/h)
        w = round(w*scalefactor); h = round(h*scalefactor)
        image = image.Scale(w,h)
        dc.DrawBitmap (wx.BitmapFromImage(image),0,0)

    def SetImage(self,image):
        """Current image in Python Image Library format"""
        if image != self.PIL_image:
            self.PIL_image = image
            self.Refresh()
    def GetImage(self): return self.PIL_image
    Image = property(GetImage,SetImage)


class Autorecovery (wx.Dialog):
    def __init__ (self,parent,operation,motor_names,positions):
        wx.Dialog.__init__(self,parent,title="Lauecollect: Restore Settings?")

        self.motor_names = motor_names
        self.positions = positions

        border = wx.BoxSizer(wx.VERTICAL)

        comment = "The following settings did not get restored during "\
        "the last %r operation. Restore them now?" % operation
        text = wx.StaticText (self,label=comment,size=(400,30))
        border.Add (text,0,wx.ALL,10) # Leave a 10-pixel wide space

        motors = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL|wx.ALL

        N = len(motor_names)
        self.CurrentVal = [None]*N; self.OldVal = [None]*N
        self.Buttons = [None]*N
        for i in range(0,N):
            motor_name = motor_names[i]
            position = positions[i]
            motor = eval(motor_name)
            unit = getattr(motor,"unit","")
            text = wx.StaticText (self,label=motor_name)
            motors.Add(text,(i,0),flag=a)
            text = wx.StaticText(self,label="from")
            motors.Add(text,(i,2),flag=a)
            self.CurrentVal[i] = wx.StaticText(self)
            motors.Add(self.CurrentVal[i],(i,4),flag=a)
            text = wx.StaticText(self,label="to")
            motors.Add(text,(i,6),flag=a)
            value = "%.3g" % position if unit != "s" else time_string(position)
            self.OldVal[i] = TextCtrl(self,size=(50,-1),value=value)
            motors.Add(self.OldVal[i],(i,8),flag=a)
            text = wx.StaticText(self,label=unit if unit != "s" else "")
            motors.Add(text,(i,9),flag=a)
            self.Buttons[i] = wx.Button(self,id=i,label="Restore",
                style=wx.BU_EXACTFIT)
            self.Bind(wx.EVT_BUTTON,self.restore,self.Buttons[i])
            motors.Add(self.Buttons[i],(i,11),flag=a)
 
        border.Add (motors,0,wx.ALL,10) # Leave a 10-pixel wide space

        buttons = wx.BoxSizer()
        self.RestoreAll = wx.Button(self,label="Restore All",id=wx.ID_OK)
        self.RestoreAll.SetDefault()
        self.Bind(wx.EVT_BUTTON,self.restore_all,self.RestoreAll)
        buttons.Add (self.RestoreAll)
        buttons.AddSpacer ((10,10))
        self.Cancel = wx.Button(self,id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON,self.cancel,self.Cancel)
        buttons.Add (self.Cancel) 

        border.Add (buttons,0,wx.ALL,10) # Leave a 10-pixel wide space
        self.SetSizer(border)
        self.Fit()

        self.Bind (wx.EVT_CLOSE,self.OnClose)
        
        # Periodically update the displayed fields.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()

    def OnTimer(self,event=None):
        """Periodically update the panel"""
        self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def update(self,event=None):
        """Display the current motor positions"""
        reload_settings()
        all_restored = True
        for i in range(0,len(self.motor_names)):
            motor_name = self.motor_names[i]
            position = self.positions[i]
            motor = eval(motor_name)
            unit = getattr(motor,"unit","")
            value = motor.value
            s = "%.3g" % value if unit != "s" else time_string(value)
            self.CurrentVal[i].SetLabel(s)
            error = abs(value - position)
            if unit == "mm" and error < 0.002: restored = True
            elif unit == "deg" and error < 0.001*position: restored = True
            elif unit == "s" and error < 0.001*position: restored = True
            elif error == 0: restored = True
            else: restored = False
            self.Buttons[i].SetLabel("Done" if restored else "Restore")
            self.Buttons[i].Enable(True if not restored else False)
            all_restored  = all_restored and restored
        self.RestoreAll.Enable(True if not all_restored else False)
        self.Cancel.SetLabel("Cancel" if not all_restored else "Done")

    def restore(self,event):
        "Restore a single motor"
        i = event.GetId()
        motor_name = self.motor_names[i]
        position = self.positions[i]
        motor = eval(motor_name)
        motor.value = position

    def restore_all(self,event):
        "Restore all motors in the list"
        for i in range(0,len(self.motor_names)):
            motor_name = self.motor_names[i]
            position = self.positions[i]
            motor = eval(motor_name)
            motor.value = position

    def OnClose(self,event):
        "Called when the window is closed"
        clear_autorecovery_restore_point()
        self.Destroy()

    def cancel(self,event):
        "Called when Done button is pressed"
        clear_autorecovery_restore_point()
        self.Destroy()

def image_info():
    "Info about next image"
    status = ""
    i = image_number = task.image_number
    if i > nimages(): return "Dataset complete"
    status += ("Image %s of %s: %s, " 
        % (i,nimages_to_collect(),basename(filename(i))))
    for name in collection_variables():
        value = collection_variable_value(name,image_number)
        value = variable_formatted_value(name,value)
        name = name.replace("laser_on","laser")
        name = name.replace("delay","")
        name = name.replace("chopper_mode","")
        name = name.replace("temperature","temp.")
        if name: status += name+" "
        status += value+", "
    status += "%gx%g pulses, " % (npulses(i),chopper_pulses(i))
    status = status.strip(", ")
    return status

def acquisition_status():
    """Short status report about current acquisition"""
    if task.action and options.wait_for_beam and xray_safety_shutters_open.value == False:
        status = ""
        if not xray_safety_shutters_enabled.value: status += "Remote shutter disabled. "
        status += "Waiting for remote shutter to open."
        return status
    elif task.action and not beam_ok():
        from checklist import checklist as my_checklist
        return "Waiting because %s..." % my_checklist.test_failed
    elif task.action in ["Collect Dataset","Single Image",""]:
        image_number = timing_system.image_number.count
        if task.action == "Collect Dataset":
            status = "Collecting %s of %s: " % (image_number,nimages_to_collect())
            status += basename(filename(image_number))+", "
        elif task.action == "Single Image":
            status = "Acquiring image: "
            for name in collection_variables():
                ##value = variable_value(name)
                value = collection_variable_value(name,image_number)
                value = variable_formatted_value(name,value)
                name = name.replace("laser_on","laser")
                name = name.replace("delay","")
                name = name.replace("chopper_mode","")
                name = name.replace("temperature","temp.")
                if name == "angle": name = Spindle.name
                if name: status += name+" "
                status += value+", "
        else:
            status = "Current settings: "
            for name in collection_variables():
                value = variable_value(name)
                value = variable_formatted_value(name,value)
                name = name.replace("laser_on","laser")
                name = name.replace("delay","")
                name = name.replace("chopper_mode","")
                name = name.replace("temperature","temp.")
                if name == "angle": name = Spindle.name
                if name: status += name+" "
                status += value+", "
        n = timing_system.image_number.count
        if n > 0: status += "image %d, " % n
        n = timing_system.pass_number.count
        if n > 0: status += "pass %d, " % n
        n = timing_system.pulses.count
        if n > 0: status += "%d pulses, " % n
        if task.comment: status += task.comment+", "
        status = status.strip(", ")
        return status
    elif task.action == "Align Sample": return alignment_status()
    elif task.action.startswith("X-Ray Beam Check"):
        return task.action+" - "+xraycheck.comment
    elif task.action.startswith("Laser Beam Check"):
        return task.action+" - "+lasercheck.comment
    elif task.action.startswith("Timing Check"):
        return task.action+" - "+timingcheck.comment
    else: return task.action

def diagnostics_status():
    """Short summary"""
    if not diagnostics.enabled: return ""
    diag = ""
    if task.action == "Collect Dataset":
        ldiag = ""
        if diagnostics.delay and laser_on(task.image_number):
            dt = timing_diagnostics_delay(task.image_number)
            if not isnan(dt): ldiag += time_string(dt)+", "
        if diagnostics.laser and laser_on(task.image_number):
            offset = diagnostics.laser_offset
            ref = diagnostics.laser_reference
            laser = (laser_pulse.average - offset) / (ref - offset)
            if not isnan(laser): ldiag += ("%.3g%%, " % (laser*100))
        if ldiag: diag += "laser "+ldiag
        if diagnostics.xray:
            offset = diagnostics_xray_offset()
            ref = diagnostics.xray_reference
            xray = (xray_pulse.average - offset) / (ref - offset)
            if not isnan(xray): diag += ("X-ray %.4g%%, " % (xray*100))
    else:
        ldiag = ""
        if diagnostics.delay and laser_on(task.image_number):
            dt = timing_diagnostics_delay(task.image_number)
            if not isnan(dt): ldiag += time_string(dt)+", "
        if diagnostics.laser and laser_on(task.image_number):
            offset = diagnostics.laser_offset
            ref = diagnostics.laser_reference
            laser = (laser_pulse.value - offset) / (ref - offset)
            if not isnan(laser): ldiag += ("%.3g%%, " % (laser*100))
        if ldiag: diag = "laser "+ldiag
        if diagnostics.xray:
            offset = diagnostics_xray_offset()
            ref = diagnostics.xray_reference
            xray = (xray_pulse.value - offset) / (ref - offset)
            if not isnan(xray): diag += ("X-ray %.4g%%, " % (xray*100))
        if diag: diag = "last "+diag
    diag = diag.strip(", ")
    return diag

def autorecovery():
    """In case 'lauecollect' crashed during a beam check, prompt the user
    at start up to restore the motor positions"""
    filename = settingsdir()+"/lauecollect_autorecovery.py"
    if not exists(filename): return
    lines = file(settingsdir()+"/lauecollect_autorecovery.py").readlines()
    operation = "?"
    motor_names = [] ; positions = []
    for line in lines:
        words = line.split(" =")
        if words[0] == "operation": operation = words[1].strip(" '\"\n")
        else:
            motor_names += [words[0].split(".")[0]]
            positions += [float(eval(words[1]))]

    motor_names2 = [] ; positions2 = []
    for i in range(0,len(motor_names)):
        motor_name = motor_names[i]
        position = positions[i]
        motor = eval(motor_name)
        unit = getattr(motor,"unit","")
        error = abs(motor.value - position)
        if unit == "mm" and error < 0.001: continue
        if unit == "deg" and error < 0.001*position: continue
        if unit == "s" and error < 0.001*position: continue
        if error == 0: continue
        motor_names2 += [motor_name]
        positions2 += [position]
    motor_names = motor_names2 ; positions = positions2
    if len(motor_names) == 0: clear_autorecovery_restore_point(); return
        
    dlg = Autorecovery(win,operation,motor_names,positions)
    dlg.CenterOnParent()
    dlg.Show()

def check_for_autorecovery():
    """Was something left in a messy state (cancelled?, crashed?)"""
    if task.autorecovery_needed: autorecovery()
    task.autorecovery_needed = False

def test_autorecovery():
    "for testing"
    generate_autorecovery_restore_point("Beamcheck",("MirrorV","MirrorH",
        "ChopX","ChopY","shg","svg","tmode","waitt","lxd","laseron"))


def IsShownOnScreen(win):
    """Returns 'True' if the window is physically visible on the screen,
    i.e. it is shown and all its parents up to the toplevel window are
    shown as well.
    This is procedure is a member function of 'Window' in wxPython 2.8,
    but not included in wxPython 2.6 (which is used at BioCARS).
    Works under Windows with 2.8, but not under Linux with 2.6"""
    if not win.IsShown(): return False
    if type(win.Parent) == wx.Notebook:
        if win.Parent.CurrentPage != win: return False
    if win.Parent != None: return IsShownOnScreen(win.Parent)
    else: return True


def data_collection_thread():
    "This thread runs the data collection in background."
    task.action = ""
    while task.run_background_threads:
        if task.cancelled: task.action = ""
        if task.action == "Single Image": single_image()
        if task.action == "Collect Dataset": collect_dataset()
        if task.action == "Align Sample": align_sample()
        if task.action == "Pumping Sample": run_pump_command(pump.command_number)
        if task.action == "X-Ray Beam Check":
            run_xray_beam_check(apply_correction=True)
        if task.action == "X-Ray Beam Check - Test":
            run_xray_beam_check(apply_correction=False)
        if task.action == "Laser Beam Check": laser_beamcheck()
        if task.action == "Laser Beam Check - Test":
            laser_beamcheck(apply_correction=False)
        if task.action == "Laser Beam Check - Retract Sample":
            laser_beamcheck_goto_park_pos()
        if task.action == "Laser Beam Check - Return Sample":
            laser_beamcheck_goto_sample_pos()
        if task.action == "Timing Check": run_timing_check()
        if task.action == "Timing Check - Test":
            run_timing_check(apply_correction=False)
        if task.action == "Sample Photo": sample_photo_acquire()
        if task.action == "Sample Photo - Test": sample_photo_acquire(test=True)
        task.action = ""
        task.cancelled = False
        task.finish_series = False
        task.last_image = None
        sleep(1)

# Initialize status variables
class status: "Container for status variables"
status.image_info = ""
status.acquisition_status = ""
status.diagnostics_status = ""
status.time_info = ""
status.alignment_status = ""
status.first_image_number = 1

def status_thread():
    """This updates status info in background."""
    while task.run_background_threads:
        status.image_info = image_info()
        sleep(0.20)
        status.acquisition_status = acquisition_status()
        sleep(0.20)
        status.diagnostics_status = diagnostics_status()
        sleep(0.20)
        status.alignment_status = alignment_status()
        sleep(0.20)
        if not task.action:
            status.first_image_number = first_image_number()
            sleep(0.20)
        if diagnostics.enabled and diagnostics.xray:
            if hasattr(xray_pulse,"gate"):
                diagnostics.xray_gate_start = xray_pulse.gate.start.value
                diagnostics.xray_gate_stop = xray_pulse.gate.stop.value
        sleep(0.20)

def time_remaining_thread():
    "This thread estimates collection time in background."
    while task.run_background_threads:
        if options.estimate_collection_time: status.time_info = time_info()
        else: status.time_info = ""
        sleep(4)

def periodically_read_ccd_thread():
    """Force the MAR CCD dectory to be read periodically when idle.
    This is intended to improve the stability of the CCD image offset.
    We observed that the readout offset of the image drifts when startings
    to read the detector after is has been idle (continuous clearing)
    for a while.
    """
    start_time = 0
    while task.run_background_threads:
        sleep(0.2)
        if not options.periodically_read_ccd: continue
        if task.action in ["Collect Dataset","Single Image"]: continue
        acq_time = acquisition_time(task.image_number)
        if ccd.state() == "idle" and time() > start_time+acq_time:
            ccd.start()
            start_time = time()
        integ_time = integration_time(task.image_number)
        if ccd.state() == "integrating" and time() > start_time+integ_time:
            ccd.readout_raw()


"""This is to run the modules as a stanalong program.
This code is only executed when the file is passed a run-time argument to
the Python interpreter."""
if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging
    from tempfile import gettempdir
    logfile = gettempdir()+"/LauecollectPanel.log"
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)-7s %(message)s",
        filename=logfile,
    )
    launch()
