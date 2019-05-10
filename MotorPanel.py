#!/usr/bin/env python
"""General motor control panel.
Friedrich Schotte, 31 Oct 2013 - 7 Jul 2017"""

__version__ = "1.3" # multiple rows
import wx
from EditableControls import TextCtrl,ComboBox
from logging import debug,info,warn,error

class MotorWindow(wx.Frame):
    """Motors"""
    def __init__(self,motors,title="Motors"):
        """motors: list of EPICS_motor objects
        If a nested list, each sublist is packed into a row.
        """
        # Make sure "motors" is a nested list.
        if motors and not hasattr(motors[0],"__len__"): motors = [motors]
        
        wx.Frame.__init__(self,parent=None,title=title)
        sizer = wx.GridBagSizer(1,1)
        for i,motor_group in enumerate(motors):
            for j,motor in enumerate(motor_group):
                panel = MotorPanel(self,motor)
                sizer.Add (panel,(i,j),flag=wx.ALL,border=5)
            
        self.SetSizer(sizer)
        self.Fit()
        self.Show()


class MotorPanel(wx.Panel):
    """Motor"""
    name = "MotorPanel"
    
    def __init__(self,parent,motor,refresh_period=1.0):
        wx.Panel.__init__(self,parent)
        self.motor = motor
        self.refresh_period = refresh_period
        
        # Controls
        self.MotorName = wx.StaticText(self,size=(100,-1),style=wx.ALIGN_CENTRE)
        self.background = self.MotorName.BackgroundColour
        self.Unit = wx.StaticText(self,size=(100,-1),style=wx.ALIGN_CENTRE)
        self.Value = wx.StaticText(self,size=(100,-1),style=wx.ALIGN_CENTRE)
        self.CommandValue = TextCtrl(self,size=(100,-1),style=wx.TE_PROCESS_ENTER)
        self.TweakValue = ComboBox(self,size=(50,-1),style=wx.TE_PROCESS_ENTER)

        left = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK)
        right = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD)

        self.TweakDownButton = wx.BitmapButton(self,bitmap=left)
        self.TweakUpButton = wx.BitmapButton(self,bitmap=right)

        self.EnableButton = wx.ToggleButton(self,label="Enabled",size=(70,-1))
        w,h = self.EnableButton.Size
        self.HomeButton = wx.ToggleButton(self,label="Homed",size=(w,h))

        self.Bind(wx.EVT_CONTEXT_MENU,self.OnConfigureMenu,self.MotorName)
        self.Bind(wx.EVT_CONTEXT_MENU,self.OnConfigureMenu,self.Unit)
        self.Bind(wx.EVT_CONTEXT_MENU,self.OnSetValueMenu,self.Value)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterCommandValue,self.CommandValue)
        self.Bind(wx.EVT_CONTEXT_MENU,self.OnSetValueMenu,self.CommandValue)
        self.Bind(wx.EVT_COMBOBOX,self.OnEnterTweakValue,self.TweakValue)
        self.Bind(wx.EVT_TEXT_ENTER,self.OnEnterTweakValue,self.TweakValue)
        self.Bind(wx.EVT_CONTEXT_MENU,self.OnTweakMenu,self.TweakValue)
        self.Bind(wx.EVT_BUTTON,self.OnTweakDown,self.TweakDownButton)
        self.Bind(wx.EVT_BUTTON,self.OnTweakUp,self.TweakUpButton)
        self.Bind(wx.EVT_TOGGLEBUTTON,self.OnEnable,self.EnableButton)
        self.Bind(wx.EVT_TOGGLEBUTTON,self.OnHome,self.HomeButton)

        # Layout
        controls = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_HORIZONTAL|wx.ALIGN_CENTRE_VERTICAL
        e = wx.EXPAND

        controls.Add(self.MotorName,(0,0),span=(1,3),flag=a|e)
        controls.Add(self.Unit,(1,0),span=(1,3),flag=a|e)
        controls.Add(self.Value,(2,0),span=(1,3),flag=a|e)
        controls.Add(self.CommandValue,(3,0),span=(1,3),flag=a|e)
        controls.Add(self.TweakDownButton,(4,0),flag=a|e)
        controls.Add(self.TweakValue,(4,1),flag=a|e)
        controls.Add(self.TweakUpButton,(4,2),flag=a|e)
        controls.Add(self.EnableButton,(5,1),flag=a)
        controls.Add(self.HomeButton,(6,1),flag=a)

        # Leave a 10 pixel wide border.
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(controls,flag=wx.ALL,border=5)
        self.SetSizer(box)
        self.Fit()

        # Initialization
        self.CommandValue.Enabled = False
        self.TweakDownButton.Enabled = False
        self.TweakUpButton.Enabled = False
        self.EnableButton.Enabled = False
        self.HomeButton.Enabled = False

        # Refresh
        self.attributes = ["name","unit","value","command_value",
            "moving","enabled","homed","homing"]
        from numpy import nan
        self.values = dict([(n,nan) for n in self.attributes])
        self.values["name"] = ""
        self.values["unit"] = ""
        self.old_values = {}
        
        from threading import Thread
        self.refresh_thread = Thread(target=self.refresh_background,
            name=self.name+".refresh")
        self.refreshing = False

        from wx.lib.newevent import NewEvent
        self.EVT_THREAD = NewEvent()[1]
        self.Bind(self.EVT_THREAD,self.OnUpdate)
        self.thread = Thread(target=self.keep_updated,name=self.name)
        self.thread.start()

    def keep_updated(self):
        """Periodically refresh the displayed settings."""
        from time import time,sleep
        while True:
            try:
                t0 = time()
                while time() < t0+self.refresh_period: sleep(0.1)
                if self.Shown:
                    self.update_data()
                    if self.data_changed: 
                        event = wx.PyCommandEvent(self.EVT_THREAD.typeId,self.Id)
                        # call OnUpdate in GUI thread
                        wx.PostEvent(self.EventHandler,event)
            except wx.PyDeadObjectError: break

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
        from numpy import nan
        self.old_values = dict(self.values) # make a copy
        for n in self.attributes: self.values[n] = self.getattr(self.motor,n,nan)

    from numpy import nan
    @staticmethod
    def getattr(object,attribute,default_value=nan):
        """Get a propoerty of an object
        attribute: e.g. 'value' or 'member.value'"""
        try: return eval("object."+attribute)
        except Exception,msg:
            import traceback
            error("%s.%s: %s" % (object,attribute,msg))
            for line in traceback.format_exc().split("\n"): error(line)
            return default_value

    @property
    def data_changed(self):
        """Did the last 'update_data' change the data to be plotted?"""
        changed = (self.values != self.old_values)
        return changed

    def OnUpdate(self,event=None):
        """Periodically refresh the displayed settings."""
        self.refresh_status()

    def refresh_status(self,event=None):
        """Update the controls with current values"""
        from numpy import nan,isnan
        unit          = self.values["unit"]
        value         = self.values["value"]
        command_value = self.values["command_value"]
        enabled       = self.values["enabled"]
        moving        = self.values["moving"]
        homed         = self.values["homed"]
        homing        = self.values["homing"]

        self.MotorName.Label = self.values["name"]
        self.Unit.Label = "[%s]" % unit if unit else ""
        self.Value.Label = "%.4f" % value if not isnan(value) else ""
        self.Value.BackgroundColour = \
            (128,128,255) if moving == True else self.background
        ##self.CommandValue.BackgroundColour = \
        ##    (128,128,255) if moving else self.background
        self.CommandValue.Value = "%.4f" % command_value \
            if not isnan(command_value) else ""
        self.CommandValue.Enabled = (enabled == True)
        choices = ["%.4f" % x for x in self.tweak_values]
        if self.TweakValue.Items != choices: self.TweakValue.Items = choices
        self.TweakValue.Value = "%.4f" % self.tweak_value
        self.TweakDownButton.Enabled = (enabled == True)
        self.TweakUpButton.Enabled = (enabled == True)

        self.EnableButton.Value = bool(enabled)
        self.EnableButton.Label = \
            "Stop" if moving == True else \
            "Enable" if isnan(enabled) else \
            "Enabled" if enabled == True else \
            "Disabled"
        self.EnableButton.BackgroundColour = \
            (255,0,0) if moving == True else \
            self.background if enabled == True else \
            (255,0,0) if enabled == False else \
            self.background
        self.EnableButton.Enabled = \
            True if moving == True else \
            not isnan(enabled)

        self.HomeButton.Value = bool(homing)
        self.HomeButton.BackgroundColour = \
            self.background if isnan(homed) or (enabled != True) else \
            (255,255,0) if homing == True else \
            (0,255,0) if homed == True else (255,0,0)
        self.HomeButton.Label = \
            "Home" if isnan(homed) else \
            "Homing" if homing == True else \
            "Homed" if homed == True else \
            "Home"
        self.HomeButton.Enabled = (enabled == True)

    def OnEnterCommandValue(self,event):
        """Set the voltage to a specific value."""
        text = self.CommandValue.Value
        try: value = float(eval(text))
        except Exception,details:
            ##debug("%s: %s" % (text,details))
            self.refresh(); return
        ##debug("self.motor.command_value = %r" % value)
        self.motor.command_value = value
        self.refresh()

    def OnSetValueMenu(self,event):
        """Bring up a menu to set the position without moving the motor"""
        menu = wx.Menu()
        menu.Append (1,"Set...","Set the  position without moving the motor")
        self.Bind (wx.EVT_MENU,self.OnSetValue,id=1)
        # Display the menu. If an item is selected then its handler will
        # be called before 'PopupMenu' returns.
        self.PopupMenu(menu)
        menu.Destroy()
        
    def OnSetValue(self,event):
        """Set the position without moving the motor"""
        dlg = wx.TextEntryDialog(self,"New position",
            "Set the position without moving the motor","")
        dlg.Value = "%.4f" % self.motor.command_value
        OK = (dlg.ShowModal() == wx.ID_OK)
        if not OK: return
        text = dlg.Value
        try: value = float(eval(text))
        except Exception,details:
            ##debug("Set Value %s: %s" % (text,details))
            self.refresh(); return
        self.motor.offset = -self.motor.sign*self.motor.dial + value
        self.refresh()
         
    def OnEnterTweakValue(self,event):
        """Set the voltage to a specific value."""
        text = self.TweakValue.Value
        try: value = float(eval(text))
        except: self.refresh(); return
        self.tweak_value = value
        self.refresh()

    def OnTweakMenu(self,event):
        """Bring up a menu to set the position without moving the motor"""
        menu = wx.Menu()
        menu.Append (1,"Choices...","Edit the choices for tweak values")
        self.Bind (wx.EVT_MENU,self.OnTweakValues,id=1)
        # Display the menu. If an item is selected then its handler will
        # be called before 'PopupMenu' returns.
        self.PopupMenu(menu)
        menu.Destroy()
        
    def OnTweakValues(self,event):
        """Edit the choices for tweak values"""
        dlg = wx.TextEntryDialog(self,"Tweak values",
            "Choices for tweak values","")
        dlg.Value = ",".join(["%.4f" % x for x in self.tweak_values])
        OK = (dlg.ShowModal() == wx.ID_OK)
        if not OK: return
        text = dlg.Value
        try: values = eval(text)
        except Exception,details:
            debug("Set Value %s: %s" % (text,details))
            self.refresh(); return
        try: values = [float(x) for x in values]
        except Exception,details:
            debug("Set Value %s: %s" % (text,details))
            self.refresh(); return
        self.tweak_values = values
        self.refresh()

    def OnTweakDown(self,event):
        """"""
        self.motor.command_value -= self.tweak_value
        self.refresh()

    def OnTweakUp(self,event):
        """"""
        self.motor.command_value += self.tweak_value
        self.refresh()

    def OnEnable(self,event):
        """Enable the motor if t hebutton is toggled on,
        disable th emotor if the butto is toggled off."""
        if self.EnableButton.Label == "Stop":
            print "Stop"
            print self.motor.moving
            self.motor.moving = False
            print self.motor.moving
        else: self.motor.enabled = self.EnableButton.Value
        self.refresh()

    def OnHome(self,event):
        """Start a home run, if the button is toggled on.
        Cancel a home run, if is is toggled off."""
        self.motor.homing = self.HomeButton.Value
        self.refresh()

    def OnConfigureMenu(self,event):
        """Bring up a menu to set the position without moving the motor"""
        menu = wx.Menu()
        menu.Append (1,"More...","Configure motor parameters")
        self.Bind (wx.EVT_MENU,self.OnConfigure,id=1)
        # Display the menu. If an item is selected then its handler will
        # be called before 'PopupMenu' returns.
        self.PopupMenu(menu)
        menu.Destroy()
        
    def OnConfigure(self,event):
        """Configure motor parameters"""
        dlg = ConfigurationPanel(self)
        dlg.CenterOnParent()
        dlg.Show()

    def get_tweak_value(self):
        from DB import dbget
        value = dbget("motor_panel.%s.tweak_value" % self.motor.name)
        try: value = float(value)
        except ValueError: value = 1.0
        return value
    def set_tweak_value(self,value):
        from DB import dbput
        return dbput("motor_panel.%s.tweak_value" % self.motor.name,str(value))
    tweak_value = property(get_tweak_value,set_tweak_value)

    def get_tweak_values(self):
        from DB import dbget
        values = dbget("motor_panel.%s.tweak_values" % self.motor.name)
        try: values = eval(values)
        except: values = [1.0]
        try: values = [float(x) for x in values]
        except: pass
        return values
    def set_tweak_values(self,values):
        from DB import dbput
        return dbput("motor_panel.%s.tweak_values" % self.motor.name,str(values))
    tweak_values = property(get_tweak_values,set_tweak_values)


class ConfigurationPanel(wx.Frame):
    def __init__(self,parent=None):
        wx.Frame.__init__(self,parent=parent,title="Configuration")
        panel = wx.Panel(self)

        # Controls
        style = wx.TE_PROCESS_ENTER
        self.UserValue = TextCtrl(self,size=(90,-1),style=style)
        self.DialValue = TextCtrl(self,size=(90,-1),style=style)
        self.HighLimit = TextCtrl(self,size=(90,-1),style=style)
        self.LowLimit  = TextCtrl(self,size=(90,-1),style=style)
        self.Sign = ComboBox(self,size=(90,-1),style=style,
            choices=["+1","-1"])
        self.Offset = TextCtrl(self,size=(90,-1),style=style)
        self.Speed = ComboBox (self,size=(90,-1),style=style,
            choices=["1.8","15","90"])

        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnter)
        self.Bind (wx.EVT_COMBOBOX,self.OnEnter)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterUserValue,self.UserValue)

        # Layout
        layout = wx.BoxSizer()
        grid = wx.FlexGridSizer (cols=2,hgap=5,vgap=5)
        flag = wx.ALIGN_CENTER_VERTICAL
        
        label = "User value:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.UserValue,flag=flag)
        label = "Dial value:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.DialValue,flag=flag)
        label = "High Limit:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.HighLimit,flag=flag)
        label = "Low Limit:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.LowLimit,flag=flag)
        label = "Sign:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Sign,flag=flag)
        label = "Offset:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Offset,flag=flag)
        label = "Speed:"
        grid.Add (wx.StaticText(self,label=label),flag=flag)
        grid.Add (self.Speed,flag=flag)
        # Leave a 10-pixel wide space around the panel.
        layout.Add (grid,flag=wx.EXPAND|wx.ALL,border=10)

        self.SetSizer(layout)
        self.Fit()

        self.update()

    def update(self,Event=0):
        motor = self.Parent.motor

        if hasattr(motor,"name"): self.Title = motor.name

        if hasattr(motor,"command_value"):
            self.UserValue.Value = "%.4f" % motor.command_value
        else: self.UserValue.Value = ""
        if hasattr(motor,"command_dial"):
            self.DialValue.Value = "%.4f" % motor.command_dial
        else: self.DialValue.Value = ""
        if hasattr(motor,"low_limit"):
            self.LowLimit.Value = "%.4f" % motor.low_limit
        else: self.LowLimit.Value = ""
        if hasattr(motor,"high_limit"):
            self.HighLimit.Value = "%.4f" % motor.high_limit
        else: self.HighLimit.Value = ""
        if hasattr(motor,"sign"):
           self.Sign.Value = "%+g" % motor.sign
        else: self.Sign.Value = ""
        if hasattr(motor,"offset"):
            self.Offset.Value = "%.4f" % motor.offset
        else: self.Offset.Value = ""
        if hasattr(motor,"speed"):
            self.Speed.Value = "%g" % motor.speed
        else: self.Speed.Value = ""

        # Relaunch yourself.
        self.update_timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.update,self.update_timer)
        self.update_timer.Start(2000,oneShot=True)

    def OnEnter(self,event):
        """Read back updated parameters from the configuration panel"""
        from numpy import nan,inf
        motor = self.Parent.motor

        if hasattr(motor,"command_dial"):
            try: motor.command_dial = float(eval(self.DialValue.Value))
            except: pass
        if hasattr(motor,"low_limit"):
            try: motor.low_limit = float(eval(self.LowLimit.Value))
            except: pass
        if hasattr(motor,"high_limit"):
            try: motor.high_limit = float(eval(self.HighLimit.Value))
            except: pass
        if hasattr(motor,"offset"):
            try: motor.offset = float(eval(self.Offset.Value))
            except: pass
        if hasattr(motor,"sign"):
            try: motor.sign = float(eval(self.Sign.Value))
            except: pass
        if hasattr(motor,"speed"):
            try: motor.speed = float(eval(self.Speed.Value))
            except: pass

        self.update()

    def OnEnterUserValue(self,event):
        """Change the user value without moving the motor"""
        motor = self.Parent.motor

        try: value = float(eval(self.UserValue.Value))
        except: self.update(); return

        if hasattr(motor,"offset") and hasattr(motor,"sign") and \
            hasattr(motor,"dial"):
            motor.offset = -motor.sign*motor.dial + value

        self.update()


def tofloat(x):
    from numpy import nan
    try: return float(x)
    except: return nan

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    # Needed to initialize WX library
    if not "app" in globals(): app = wx.App(redirect=False)
    from cavro_centris_syringe_pump_IOC import volume,port
    motors = [port,volume]
    window = MotorWindow(motors,title="Cavro Centris Syringe Pumps")
    app.MainLoop()
