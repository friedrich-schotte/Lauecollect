#!/usr/bin/env python
"""
Setup panel for diffractomter.
Friedrich Schotte, 28 Feb 2013 - 12 Jun 2015
"""
from diffractometer import diffractometer
import wx
from EditableControls import TextCtrl,ComboBox
__version__ = "1.0.2"

class DiffractometerSetup (wx.Dialog):
    """Configures Diffractometer"""
    def __init__ (self,parent=None):
        wx.Dialog.__init__(self,parent,-1,"Diffractometer Setup")
        # Controls
        style = wx.TE_PROCESS_ENTER

        self.Configuration = ComboBox (self,size=(175,-1),style=style,
            choices=["BioCARS Diffractometer","NIH Diffractometer","LCLS Diffractometer"])
        self.Apply = wx.Button(self,label="Apply",size=(75,-1))
        self.Save = wx.Button(self,label="Save",size=(75,-1))

        self.X = ComboBox (self,size=(160,-1),style=style,
            choices=["GonX","SampleX"])
        self.Y = ComboBox (self,size=(160,-1),style=style,
            choices=["GonY","SampleY"])
        self.Z = ComboBox (self,size=(160,-1),style=style,
            choices=["GonZ","SampleZ"])
        self.Phi = ComboBox (self,size=(160,-1),style=style,
            choices=["Phi","SamplePhi"])

        self.XYType = ComboBox (self,size=(160,-1),style=style,
            choices=["rotating","stationary"])

        self.RotationCenterX = TextCtrl (self,size=(160,-1),style=style)
        self.RotationCenterY = TextCtrl (self,size=(160,-1),style=style)

        self.XScale = TextCtrl (self,size=(160,-1),style=style)
        self.YScale = TextCtrl (self,size=(160,-1),style=style)
        self.ZScale = TextCtrl (self,size=(160,-1),style=style)
        self.PhiScale = TextCtrl (self,size=(160,-1),style=style)

        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_COMBOBOX,self.OnEnter)
        self.Configuration.Bind (wx.EVT_COMBOBOX,self.OnSelectConfiguration)
        self.Save.Bind (wx.EVT_BUTTON,self.OnSave)
        self.Apply.Bind (wx.EVT_BUTTON,self.OnApply)

        # Layout
        layout = wx.BoxSizer()
        vbox = wx.BoxSizer(wx.VERTICAL)
        
        config = wx.BoxSizer(wx.HORIZONTAL)
        flag = wx.ALIGN_CENTER
        config.Add (self.Configuration,flag=flag)
        config.Add (self.Apply,flag=flag)
        config.Add (self.Save,flag=flag)
        vbox.Add (config,flag=wx.EXPAND|wx.ALL)
        
        grid = wx.FlexGridSizer(cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        
        label = "X Translation:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.X,flag=flag)
        label = "Y Translation:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Y,flag=flag)
        label = "Z Translation:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Z,flag=flag)
        label = "Phi Rotation:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Phi,flag=flag)
        label = "XY Translation Type:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.XYType,flag=flag)
        
        label = "Rotation Center X:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.RotationCenterX,flag=flag)
        label = "Rotation Center Y:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.RotationCenterY,flag=flag)

        label = "X Scale Factor:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.XScale,flag=flag)
        label = "Y Scale Factor:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.YScale,flag=flag)
        label = "Z Scale Factor:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.ZScale,flag=flag)
        label = "Phi Scale Factor:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.PhiScale,flag=flag)

        # Leave a 10-pixel wide space around the panel.
        vbox.Add (grid,flag=wx.EXPAND|wx.ALL)
        layout.Add (vbox,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()
        self.Show()

        self.update()

    def update(self,Event=0):
        self.X.Value = diffractometer.x_motor_name
        self.Y.Value = diffractometer.y_motor_name
        self.Z.Value = diffractometer.z_motor_name
        self.Phi.Value = diffractometer.phi_motor_name
        self.XYType.Value = \
            "rotating" if diffractometer.xy_rotating else "stationary"

        self.RotationCenterX.Value = "%.4f mm" % \
            diffractometer.rotation_center_x
        self.RotationCenterY.Value = "%.4f mm" % \
            diffractometer.rotation_center_y

        self.XScale.Value = str(diffractometer.x_scale)
        self.YScale.Value = str(diffractometer.y_scale)
        self.ZScale.Value = str(diffractometer.z_scale)
        self.PhiScale.Value = str(diffractometer.phi_scale)

        self.Configuration.Value = self.current_configuration

        # Reschedule "update".
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(2000,oneShot=True)

    def get_current_configuration(self):
        from DB import dbget
        return dbget("diffractometer.current_configuration")
    def set_current_configuration(self,value):
        from DB import dbput
        dbput("diffractometer.current_configuration",value)
    current_configuration = property(get_current_configuration,
        set_current_configuration)

    def OnEnter(self,event):
        diffractometer.x_motor_name = str(self.X.Value) 
        diffractometer.y_motor_name = str(self.Y.Value) 
        diffractometer.z_motor_name = str(self.Z.Value)
        diffractometer.phi_motor_name = str(self.Phi.Value) 
        diffractometer.xy_rotating = True if self.XYType.Value == "rotating" else False

        value = self.RotationCenterX.Value.replace("mm","")
        try: diffractometer.rotation_center_x = float(eval(value))
        except: pass

        value = self.RotationCenterY.Value.replace("mm","")
        try: diffractometer.rotation_center_y = float(eval(value))
        except: pass

        try: diffractometer.x_scale = float(eval(self.XScale.Value))
        except: pass
        try: diffractometer.y_scale = float(eval(self.YScale.Value))
        except: pass
        try: diffractometer.z_scale = float(eval(self.ZScale.Value))
        except: pass
        try: diffractometer.phi_scale = float(eval(self.PhiScale.Value))
        except: pass
        self.update()

    def OnSelectConfiguration(self,event):
        self.current_configuration = str(self.Configuration.Value)
        ##print "current configuration: % r" % self.current_configuration

    def OnEnterConfiguration(self,event):
        self.current_configuration = str(self.Configuration.Value)
        ##print "current configuration: % r" % self.current_configuration

    def OnSave(self,event):
        ##print "save_configuration %r" % self.current_configuration
        save_configuration(self.current_configuration)

    def OnApply(self,event):
        ##print "load_configuration %r" % self.current_configuration
        load_configuration(self.current_configuration)
        self.update()

configuration_parameters = [
    "x_motor_name","y_motor_name","z_motor_name","phi_motor_name",
    "x_scale","y_scale","z_scale","phi_scale",
    "xy_rotating","rotation_center_x","rotation_center_y"]

def save_configuration(name):
    """name: 'NIH Diffractometer' or 'BioCARS Diffractometer'"""
    from DB import dbput
    for par in configuration_parameters:
        dbput("diffractometer/"+name+"."+par,repr(getattr(diffractometer,par)))
    
def load_configuration(name):
    """name: 'NIH Diffractometer' or 'BioCARS Diffractometer'"""
    from DB import dbget
    for par in configuration_parameters:
        par_name = "diffractometer/"+name+"."+par
        str_value = dbget(par_name)
        try: value = eval(str_value)
        except Exception,message:
            print("%s: %s: %s" % (par_name,str_value,message))
            continue
        setattr(diffractometer,par,value)


if __name__ == '__main__': # for testing
    from pdb import pm
    app = wx.App(redirect=False)
    win = DiffractometerSetup()
    app.MainLoop()
