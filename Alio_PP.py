from os import getcwd,makedirs
from os.path import exists,dirname,basename,getmtime
from logging import info,error,warn # for debugging
import wxversion; wxversion.select("2.8")
import wx
import matplotlib.pyplot as plt
import math
from id14 import *
from alio import *

# Plot motion profile
# Add help
# Hightlight things in read that exceed some limit. velecity is exceded.
# Add button to write values to FPGA
# Fix ramp up distance of X and Y
# Calc freqency.

kHz_clock=1.0126899 # ms (DT)

class param: "Container for data collection parameters"
param.first_hole_x = 0
param.first_hole_y = 0
param.first_hole_z = 0
param.last_hole_x = 0
param.last_hole_y = 0
param.last_hole_z = 0
param.step_size = 0.2 # mm
param.acceleration = 200 # mm/s2
param.repetition_period = 48 # ~ms
param.settle_period = 2
param.continuous = 1
param.translate_x = 0
param.translate_y = 0
param.translate_z = 0
param.velocity = 0
param.acceleration_time = 0
param.acceleration_distance = 0
param.settling_time_at_speed = 0
param.settling_distance_at_speed = 0
param.time_to_first_xray_pulse = 0
param.number_of_data_points = 0
param.distance_of_actual_data_collection = 0
param.total_distance_of_translation = 0
param.time_to_reach_half_the_return_distance =0
param.max_velocity_on_return = 0
param.total_time_to_return = 0
param.total_time_of_translation = 0
param.full_cycle_clock_ticks = 0
param.measure_length = 0

class options:"Container for data collection parameters"

def save_settings():
    global settings_file_timestamp
    filename = settings_file()
    save_settings_to_file(filename)
    settings_file_timestamp = getmtime(filename)

settings_file_timestamp = 0

def save_settings_to_file(filename):
    if not exists(dirname(filename)): makedirs(dirname(filename))
    f = file(filename,"w")

    for obj in param,options:
        for name in dir(obj):
            if name.startswith("__"):continue
            line = "%s.%s = %r\n" % (obj.__name__,name,getattr(obj,name))
            line = line.replace("-1.#IND","nan") # Needed for Windows Python
            line = line.replace("1.#INF","inf") # Needed for Windows Python
            f.write(line)

def load_settings(filename=None):
    """Reload last saved parameters."""
    if filename == None: filename = settings_file()
    if not exists(filename): return
    for line in file(filename).readlines():
        try: exec(line)
        except: warn("ignoring line %r in settings" % line)

def settings_file():
    """Where to save to the default settings"""
    filename = settingsdir()+"/alio.py"
    return filename

def settingsdir():
    """In which directory to save to the settings file"""
    return module_dir()+"/settings"

def module_dir():
    "directory of the current module"
    from os.path import dirname
    module_dir = dirname(module_path())
    if module_dir == "": module_dir = "."
    return module_dir

def module_path():
    "full pathname of the current module"
    from sys import path
#    from os import getcwd
#    from os.path import basename,exists
    from inspect import getfile
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

def translation_range():
    param.translate_x=param.last_hole_x-param.first_hole_x
    param.translate_y=param.last_hole_y-param.first_hole_y
    param.translate_z=param.last_hole_z-param.first_hole_z

def velocity():
    try: param.velocity=param.step_size/(param.repetition_period*kHz_clock)*1000
    except:
        print "Velocity calc error" #Should put an error in the log file.    
    
def acceleration_time():
    param.acceleration_time=param.velocity/param.acceleration

def acceleration_distance():
    param.acceleration_distance=param.acceleration*param.acceleration_time**2 / 2

def settling_time_at_speed():
    param.settling_time_at_speed=param.settle_period*param.repetition_period*kHz_clock/1000

def settling_distance_at_speed():
    param.settling_distance_at_speed=param.settling_time_at_speed*param.velocity

def time_to_first_xray_pulse():
    time_to_first_xray_pulse_initial=param.acceleration_time+param.settling_time_at_speed
    #print time_to_first_xray_pulse_initial
    time_to_first_xray_pulse_divided_by_12=time_to_first_xray_pulse_initial*1000/12
    #print time_to_first_xray_pulse_divided_by_12
    time_to_first_xray_pulse_rounded_up=math.ceil(float(time_to_first_xray_pulse_divided_by_12))
    #print time_to_first_xray_pulse_rounded_up
    param.time_to_first_xray_pulse =time_to_first_xray_pulse_rounded_up*12
 
def distance_of_actual_data_collection():
    distance_of_actual_data_collection_initial=param.translate_z-param.settling_distance_at_speed
    #print distance_of_actual_data_collection_initial
    # We might be able to remove this -1. I think this was to be safe so that we were not collecting during the deceleration
    try: param.number_of_data_points = (distance_of_actual_data_collection_initial/param.velocity)/(param.repetition_period*kHz_clock/1000)-1
    except ZeroDivisionError: pass
    #print param.number_of_data_points
    param.distance_of_actual_data_collection = param.number_of_data_points*param.repetition_period*kHz_clock*param.velocity/1000

def total_distance_of_translation():
    param.total_distance_of_translation=param.translate_z+2*param.acceleration_distance
    
def time_to_reach_half_the_return_distance():
    param.time_to_reach_half_the_return_distance=math.sqrt(param.total_distance_of_translation/param.acceleration)
    
def max_velocity_on_return():
    param.max_velocity_on_return=param.acceleration*param.time_to_reach_half_the_return_distance
    
def total_time_to_return():
    param.total_time_to_return=param.time_to_reach_half_the_return_distance*2
    
def total_time_of_translation():
    try: param.total_time_of_translation=param.acceleration_time*2+param.translate_z/param.velocity+param.total_time_to_return
    except ZeroDivisionError: pass

def full_cycle_clock_ticks():
    full_cycle_clock_ticks_initial=param.total_time_of_translation/(param.repetition_period*kHz_clock/1000)
    #print full_cycle_clock_ticks_initial
    param.full_cycle_clock_ticks=math.ceil(full_cycle_clock_ticks_initial)
    
def measure_length():
    param.measure_length=param.full_cycle_clock_ticks*param.repetition_period
    
def update_plot():
    ad=param.acceleration_distance
    sdap=param.settling_distance_at_speed
    v=param.velocity
    doadc=param.distance_of_actual_data_collection
    rv=param.max_velocity_on_return
    #plt.plot([0,ad,ad+sdap,ad+sdap+ad],[0,v,v,0],color='g')
    plt.plot([0,ad],[0,v],'r') # Acceleration
    plt.plot([ad,ad+sdap],[v,v],'b') # Settling time
    plt.plot([ad+sdap,ad+sdap+doadc],[v,v],'g') # Actual data collection
    plt.plot([ad+sdap+doadc,ad+sdap+doadc+ad],[v,0],'r') # Deceleration
    plt.plot([ad+sdap+doadc+ad,(ad+sdap+doadc+ad)/2],[0,-rv],'r') # Return acceleration
    plt.plot([(ad+sdap+doadc+ad)/2,0],[-rv,0],'r') # Return deceleration
    plt.plot()
    plt.show()
    
class AlioWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__ (self,None,-1,"Alio PP")
        self.SetSize((640,400)) 

        main_page = wx.BoxSizer(wx.VERTICAL)

        grid=wx.FlexGridSizer(7,7,0,0)
        self.input=wx.Panel(self)
        
        # Add a button to save the current position
        self.title=wx.StaticText(self.input,-1," Position of first hole (X,Y,Z) ")
        self.firstX=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.firstY=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.firstZ=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.units=wx.StaticText(self.input,-1," mm ")
        #button = wx.Button(self.GonPanel,label="Save current",pos=(x,y),size=(90,-1)); x+=100
        button = wx.Button(self.input,label="Save current",size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.define_first_save,button)
        button2 = wx.Button(self.input,label="Go To",size=(80,-1))
        self.Bind (wx.EVT_BUTTON,self.define_first_goto,button2)
        grid.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.firstX),(self.firstY),(self.firstZ),\
        (self.units,0,wx.ALIGN_CENTER_VERTICAL),(button),(button2)])
        
        # Add a button to save the current position
        self.title=wx.StaticText(self.input,-1," Position of last hole (X,Y,Z) ")
        self.lastX=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.lastY=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.lastZ=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.units=wx.StaticText(self.input,-1," mm ")
        button = wx.Button(self.input,label="Save current",size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.define_last_save,button)
        button2 = wx.Button(self.input,label="Go To",size=(80,-1))
        self.Bind (wx.EVT_BUTTON,self.define_last_goto,button2)
        #self.blank=wx.StaticText(self.input,-1,"")
        grid.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.lastX),(self.lastY),(self.lastZ),\
        (self.units,0,wx.ALIGN_CENTER_VERTICAL),(button),(button2)])
       
        self.title=wx.StaticText(self.input,-1," Step size ")
        self.step_size=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.units=wx.StaticText(self.input,-1," mm ")
        self.blank=wx.StaticText(self.input,-1,"")
        grid.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.step_size),(self.units,0,wx.ALIGN_CENTER_VERTICAL),\
        (self.blank),(self.blank),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.input,-1," Acceleration ")
        self.acceleration=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.units=wx.StaticText(self.input,-1," mm/s2 ")
        grid.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.acceleration),(self.units,0,wx.ALIGN_CENTER_VERTICAL),\
        (self.blank),(self.blank),(self.blank),(self.blank)])

        # Force this value to be an integer
        # Show what the frequency would be
        self.title=wx.StaticText(self.input,-1," Repetition Period (dt) ")
        self.title.SetToolTip(wx.ToolTip("X-ray repetition period. Inverse of frequency. Example: 48 is 20 Hz"))
        self.repetition_period=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        self.units=wx.StaticText(self.input,-1," ~ms ")
        grid.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.repetition_period),\
        (self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank),(self.blank),(self.blank)])
        
        self.title=wx.StaticText(self.input,-1," Period to settle at speed ")
        self.title.SetToolTip(wx.ToolTip("Time, after ramp up, to allow the stage to stabilize before collecting data"))
        self.settle_period=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        #self.units=wx.StaticText(self,-1," ~ms ")
        grid.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.settle_period),(self.blank),(self.blank),\
        (self.blank),(self.blank),(self.blank)])

        # Need to implement this part
        self.title=wx.StaticText(self.input,-1," Continuous (1) or Stepping (#) (NA) ")
        self.title.SetToolTip(wx.ToolTip("Use 1 for now. Stepping mode not enabled."))
        self.continuous=wx.TextCtrl(self.input,size=(80,-1),style=wx.TE_PROCESS_ENTER)
        #self.units=wx.StaticText(self,-1," ~ms ")
        grid.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.continuous),(self.blank),(self.blank),\
        (self.blank),(self.blank),(self.blank)])

        self.input.SetSizer(grid)
        self.input.Fit()

        main_page.Add(self.input)
        #line=wx.StaticLine(self,wx.ID_ANY,size=(20,-1),style=wx.LI_HORIZONTAL)
        line=wx.StaticLine(self,style=wx.LI_HORIZONTAL)
        main_page.AddSpacer(10)
        main_page.Add(line,0,wx.GROW,5)
        main_page.AddSpacer(10)
        
        grid2=wx.FlexGridSizer(7,5,0,0)
        self.output=wx.Panel(self)

        self.title=wx.StaticText(self.output,-1," Translation range (X, Y, Z) ")
        self.translate_x=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.translate_y=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.translate_z=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," mm ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.translate_x),(self.translate_y),(self.translate_z),(self.units,0,wx.ALIGN_CENTER_VERTICAL)])

        self.title=wx.StaticText(self.output,-1," Velocity ")
        self.title.SetToolTip(wx.ToolTip("Velecity at full speed. mm/s"))
        self.velocity=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," mm/s ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.velocity),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Acceleration time ")
        self.acceleration_time=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," s ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.acceleration_time),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Acceleration distance ")
        self.acceleration_distance=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," mm ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.acceleration_distance),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Settling time at speed ")
        self.settling_time_at_speed=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," s ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.settling_time_at_speed),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Settling distance at speed ")
        self.settling_distance_at_speed=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," mm ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.settling_distance_at_speed),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Time to first X-ray pulse (t0) ")
        self.time_to_first_xray_pulse=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," ms ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.time_to_first_xray_pulse),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Number of data points (N)")
        self.number_of_data_points=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY|wx.TE_RICH)
        #self.units=wx.StaticText(self.output,-1," ms ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.number_of_data_points),(self.blank),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Distance of actual data collection ")
        self.distance_of_actual_data_collection=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," mm ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.distance_of_actual_data_collection),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Total distance of translation ")
        self.total_distance_of_translation=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," mm ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.total_distance_of_translation),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Time to reach half the return distance ")
        self.time_to_reach_half_the_return_distance=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," s ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.time_to_reach_half_the_return_distance),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Max velocity on return ")
        self.max_velocity_on_return=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," mm/s ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.max_velocity_on_return),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Total time to return ")
        self.total_time_to_return=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," s ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.total_time_to_return),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Total time of translation ")
        self.total_time_of_translation=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," s ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.total_time_of_translation),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Full cycle clock ticks ")
        self.full_cycle_clock_ticks=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        #self.units=wx.StaticText(self.output,-1," s ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.full_cycle_clock_ticks),(self.blank),(self.blank),(self.blank)])

        self.title=wx.StaticText(self.output,-1," Measure length (period) ")
        self.measure_length=wx.TextCtrl(self.output,size=(80,-1),style=wx.TE_READONLY)
        self.units=wx.StaticText(self.output,-1," clock cycles ")
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.measure_length),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.blank),(self.blank)])

        self.output.SetSizer(grid2)
        self.output.Fit()
        main_page.Add(self.output)

        #line=wx.StaticLine(self,style=wx.LI_HORIZONTAL)
        #main_page.AddSpacer(10)
        #main_page.Add(line,0,wx.GROW,5)
        #main_page.AddSpacer(10)
        self.buttons=wx.Panel(self)
        self.button = wx.Button(self.buttons,label="Send to Alio",size=(100,25),pos=(5,-1))
        self.Bind (wx.EVT_BUTTON,self.send_to_alio,self.button)
        #self.button2 = wx.Button(self.buttons,label="Send to FPGA",size=(100,25),pos=(100,-1))
        #self.Bind (wx.EVT_BUTTON,self.send_to_fpga,self.button2)
        main_page.Add(self.buttons)

        self.SetSizer(main_page)
#        main_page.Add(grid2)
        self.Fit()
        
        self.Bind(wx.EVT_TEXT_ENTER,self.on_input)
        self.update_parameters()
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()
        
        self.Show()      

    def OnTimer(self,event=None):
        """Periodically update the panel"""
        #self.update_parameters()
        self.on_input(self)
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def define_first_save(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""
        
        param.first_hole_x = round(GonX.value,3)
        param.first_hole_y = round(GonY.value,3)
        param.first_hole_z = round(GonZ.value,3)
        self.update_parameters()
        save_settings()

    def define_first_goto(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""
        
        GonX.value = param.first_hole_x
        GonY.value = param.first_hole_y
        GonZ.value = param.first_hole_z
        self.update_parameters()

    def define_last_save(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""
        
        param.last_hole_x = round(GonX.value,3)
        param.last_hole_y = round(GonY.value,3)
        param.last_hole_z = round(GonZ.value,3)
        self.update_parameters()
        save_settings()

    def define_last_goto(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""
        
        GonX.value = param.last_hole_x
        GonY.value = param.last_hole_y
        GonZ.value = param.last_hole_z
        self.update_parameters()

    def send_to_alio(self, event):
        """Sends calculated values to Alio"""
        
        alio.speed=param.velocity
        alio.accel=param.acceleration_time*1000 # Needs to be converted to msec
        alio.z_step_size=param.translate_z
        alio.x_step_size=param.translate_x
        alio.y_step_size=param.translate_y
        alio.z_starting=param.first_hole_z-param.acceleration_distance
        alio.x_starting=param.first_hole_x
        alio.y_starting=param.first_hole_y

    def send_to_fpga(self, event):
        """Sends calculated values to FPGA"""

        pass        
        
    def update_parameters(self):
        try:
            self.firstX.SetValue(str(param.first_hole_x))
            self.firstY.SetValue(str(param.first_hole_y))
            self.firstZ.SetValue(str(param.first_hole_z))
            self.lastX.SetValue(str(param.last_hole_x))
            self.lastY.SetValue(str(param.last_hole_y))
            self.lastZ.SetValue(str(param.last_hole_z))
            self.step_size.SetValue(str(param.step_size))
            self.acceleration.SetValue(str(param.acceleration))
            self.repetition_period.SetValue(str(param.repetition_period))
            self.settle_period.SetValue(str(param.settle_period))
            self.continuous.SetValue(str(param.continuous))
        except:
            print "Problem loading parameters"
        
    def on_input(self,event):
        try: 
            param.first_hole_x = float(eval(self.firstX.GetValue()))
            param.first_hole_y = float(eval(self.firstY.GetValue()))
            param.first_hole_z = float(eval(self.firstZ.GetValue()))
            param.last_hole_x = float(eval(self.lastX.GetValue()))
            param.last_hole_y = float(eval(self.lastY.GetValue()))
            param.last_hole_z = float(eval(self.lastZ.GetValue()))
            param.step_size = float(eval(self.step_size.GetValue()))
            param.acceleration = float(eval(self.acceleration.GetValue()))
            param.repetition_period = float(eval(self.repetition_period.GetValue()))
            param.settle_period = float(eval(self.settle_period.GetValue()))
            param.continuous = float(eval(self.continuous.GetValue()))
        except: pass

        translation_range()
        self.translate_x.SetValue(str(param.translate_x))
        #self.translate_x.SetLabel(str(param.translate_x))
        self.translate_y.SetValue(str(param.translate_y))
        self.translate_z.SetValue(str(param.translate_z))

        velocity()
        self.velocity.SetValue(str(param.velocity))

        acceleration_time()
        self.acceleration_time.SetValue(str(param.acceleration_time))
        
        acceleration_distance()
        self.acceleration_distance.SetValue(str(param.acceleration_distance))

        settling_time_at_speed()
        self.settling_time_at_speed.SetValue(str(param.settling_time_at_speed))

        settling_distance_at_speed()
        self.settling_distance_at_speed.SetValue(str(param.settling_distance_at_speed))

        time_to_first_xray_pulse()
        self.time_to_first_xray_pulse.SetValue(str(param.time_to_first_xray_pulse))

        distance_of_actual_data_collection()
        self.distance_of_actual_data_collection.SetValue(str(param.distance_of_actual_data_collection))

        total_distance_of_translation()
        self.number_of_data_points.SetValue(str(param.number_of_data_points))
        self.total_distance_of_translation.SetValue(str(param.total_distance_of_translation))

        time_to_reach_half_the_return_distance()
        self.time_to_reach_half_the_return_distance.SetValue(str(param.time_to_reach_half_the_return_distance))

        max_velocity_on_return()
        self.max_velocity_on_return.SetValue(str(param.max_velocity_on_return))
        
        total_time_to_return()
        self.total_time_to_return.SetValue(str(param.total_time_to_return))

        total_time_of_translation()
        self.total_time_of_translation.SetValue(str(param.total_time_of_translation))
        
        full_cycle_clock_ticks()
        self.full_cycle_clock_ticks.SetValue(str(param.full_cycle_clock_ticks))
        
        measure_length()
        self.measure_length.SetValue(str(param.measure_length))
        
        a=round(param.number_of_data_points,10)
        if a.is_integer():
            self.number_of_data_points.SetForegroundColour(wx.NullColor)
        else:
            self.number_of_data_points.SetForegroundColour(wx.RED)
            #print param.number_of_data_points
            
        save_settings()
        
        #update_plot()
        
def Alio_PP():
    global win
    wx.app = wx.App(redirect=False)
    win = AlioWindow()
    wx.app.MainLoop()
    
load_settings()
if __name__ == '__main__':
    #P250.value="0" # Tell ALIO to not accept triggers.
    Alio_PP()
