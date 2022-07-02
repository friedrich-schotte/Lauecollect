import wx
from ms_shutter import ms_shutter
from numpy import nan,isnan

"""
Grapical User Interface for the sample translation stage.
Friedrich Schotte, APS, 21 Oct 2008 - 25 Jun 2013
"""

class TranslationPanel (wx.Frame):
    "Grapical user interface for linear translation stage"
    version = "2.8.1"

    def __init__(self):
        wx.Frame.__init__(self,parent=None,title="Millisecond shutter")

        self.shutter = ms_shutter
        self.moving = False

        # Highlight an Edit control if its contents have been modified
        # but not applied yet by hitting the Enter key.
        self.edited = wx.Colour(255,255,220)

        self.unused_color = wx.Colour(180,180,180)
        
        # Controls
        panel = wx.Panel(self)
        self.Address = wx.TextCtrl (panel,size=(280,-1),style=wx.TE_PROCESS_ENTER)

        self.Pos = wx.TextCtrl (panel,size=(60,-1),style=wx.TE_PROCESS_ENTER)

        self.PulseCount = wx.TextCtrl (panel,size=(60,-1),style=wx.TE_PROCESS_ENTER)

        cb3=wx.CHK_3STATE|wx.CHK_ALLOW_3RD_STATE_FOR_USER
        self.DriveEnabled = wx.CheckBox (panel,label="On",style=cb3)
        self.DriveDisabled = wx.CheckBox (panel,label="Off",style=cb3)

        self.TriggerEnabled  = wx.CheckBox (panel,label="Enabled",style=cb3)

        choices = ["Single Shot","Timed","-"]
        self.OpeningMode = wx.Choice (panel,choices=choices)
        self.OpeningTimeLabel = wx.StaticText(panel,label="Opening Time:")
        self.OpeningTime = wx.TextCtrl (panel,size=(60,-1),
            style=wx.TE_PROCESS_ENTER)
        self.fg_color = self.OpeningTime.GetForegroundColour()

        self.OpenCloseEnabled  = wx.CheckBox (panel,label="Enabled",style=cb3)
        self.OpenCloseStatus = wx.StaticText(panel)

        self.Version = wx.StaticText(panel,size=(250,-1))
        self.Status = wx.StaticText(panel,size=(250,-1))

        self.OpenButton = wx.Button (panel,label="Open",size=(120,-1))
        self.bkg_color = self.OpenButton.GetBackgroundColour()
        self.CloseButton = wx.Button (panel,label="Close",size=(120,-1))
        RefreshButton = wx.Button (panel,label="Refresh")
        self.AutoRefresh = wx.CheckBox (panel,label="Auto Refesh")

        # Callbacks
        self.Bind (wx.EVT_TEXT,self.OnEnterAddress,self.Address)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterAddress,self.Address)

        self.Pos.Bind(wx.EVT_CHAR,self.OnEditPosition)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterPosition,self.Pos)

        self.PulseCount.Bind(wx.EVT_CHAR,self.OnEditPulseCount)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterPulseCount,self.PulseCount)

        self.Bind (wx.EVT_CHECKBOX,self.OnEnableDrive,self.DriveEnabled)
        self.Bind (wx.EVT_CHECKBOX,self.OnDisableDrive,self.DriveDisabled)

        self.Bind (wx.EVT_CHECKBOX,self.OnEnableTrigger,self.TriggerEnabled)

        self.Bind  (wx.EVT_CHOICE,self.OnChangeOpeningMode,self.OpeningMode)
        self.OpeningTime.Bind (wx.EVT_CHAR,self.OnEditOpeningTime)
        self.Bind (wx.EVT_TEXT_ENTER,self.OnEnterOpeningTime,self.OpeningTime)

        self.Bind (wx.EVT_CHECKBOX,self.OnEnableOpenClose,self.OpenCloseEnabled)

        self.Bind (wx.EVT_BUTTON,self.OnOpen,self.OpenButton)
        self.Bind (wx.EVT_BUTTON,self.OnClose,self.CloseButton)
        self.Bind (wx.EVT_BUTTON,self.OnRefresh,RefreshButton)
        self.Bind (wx.EVT_CHECKBOX,self.OnAutoRefresh,self.AutoRefresh)

        # Layout
        layout = wx.GridBagSizer(1,1)
        a = wx.ALIGN_CENTRE_VERTICAL

        text = "Rotary X-ray shutter driven by Aerotech servo motor controller"
        layout.Add (wx.StaticText(panel,label=text),(0,0),span=(1,2),flag=wx.ALL)

        layout.Add (wx.StaticText(panel,label="Address:"),(1,0),flag=a)
        layout.Add (self.Address,(1,1),flag=a)
        
        layout.Add (wx.StaticText(panel,label="Orientation [deg]:"),(2,0),flag=a)
        layout.Add (self.Pos,(2,1),flag=a)

        layout.Add (wx.StaticText(panel,label="Pulse count:"),(3,0),flag=a)
        layout.Add (self.PulseCount,(3,1),flag=a)

        layout.Add (wx.StaticText(panel,label="Holding current:"),(4,0),flag=a)
        box = wx.BoxSizer()
        box.Add (self.DriveEnabled)
        box.AddSpacer(5)
        box.Add (self.DriveDisabled)
        layout.Add (box,(4,1),flag=a)

        layout.Add (wx.StaticText(panel,label="Pulsed Open digital input:"),(5,0),flag=a)
        box = wx.BoxSizer()
        box.Add (self.TriggerEnabled)
        layout.Add (box,(5,1),flag=a)

        layout.Add (wx.StaticText(panel,label="Operation Mode:"),(6,0),flag=a)
        box = wx.BoxSizer()
        box.Add (self.OpeningMode)
        box.AddSpacer(10)
        box.Add (self.OpeningTimeLabel)
        box.AddSpacer(10)
        box.Add (self.OpeningTime)
        layout.Add (box,(6,1),flag=a)

        layout.Add (wx.StaticText(panel,label="Open/Close digital input:"),(7,0),flag=a)
        box = wx.BoxSizer()
        box.Add (self.OpenCloseEnabled,flag=a)
        box.AddSpacer(10)
        box.Add (self.OpenCloseStatus,flag=a)
        layout.Add (box,(7,1),flag=a)

        layout.Add (wx.StaticText(panel,label="Soloist program version:"),(8,0),flag=a)
        layout.Add (self.Version,(8,1),flag=a)

        layout.Add (wx.StaticText(panel,label="Connection status:"),(9,0),flag=a)
        layout.Add (self.Status,(9,1),flag=a)

        box = wx.BoxSizer()
        box.Add (self.OpenButton,flag=a)
        box.Add (self.CloseButton,flag=a|wx.ALL,border=5)
        box.Add (RefreshButton,flag=a|wx.ALL,border=15)
        box.Add (self.AutoRefresh,flag=a)
        layout.Add (box,(10,0),span=(1,2),flag=a)

        # Leave a 10 pixel wide border.
        border = wx.BoxSizer()
        border.Add (layout,flag=wx.ALL,border=10)
        panel.SetSizer(border)
        panel.Fit()
        self.Fit()

        # Initialization
        self.Address.SetValue(self.shutter.address)
        self.mark_inactive()
        self.Version.SetLabel("(unknown)")
        self.Status.SetLabel("(unknown)")

        self.Show()

    def show_settings(self):
        "Updates the controles and indicators with current values"
        pos = self.shutter.position
        self.Pos.SetForegroundColour(self.fg_color)
        # Make sure not to override pending changes.
        if self.Pos.GetBackgroundColour() != self.edited:
            text = "%g" % pos
            if self.Pos.GetValue() != text: self.Pos.SetValue(text)

        count = self.shutter.pulse_count
        self.PulseCount.SetForegroundColour(self.fg_color)
        # Make sure not to override pending changes.
        if self.PulseCount.GetBackgroundColour() != self.edited:
            text = "%d" % count
            if self.PulseCount.GetValue() != text: self.PulseCount.SetValue(text)

        enabled = self.shutter.drive_enabled
        self.DriveEnabled.Set3StateValue(enabled)
        self.DriveDisabled.Set3StateValue(not enabled)

        enabled = self.shutter.trigger_enabled
        self.TriggerEnabled.Set3StateValue(enabled)

        self.OpeningMode.Clear()        
        self.OpeningMode.AppendItems(["Single Shot","Timed"])        
        if self.shutter.timed_open: text = "Timed"
        else: text = "Single Shot"
        self.OpeningMode.SetStringSelection(text)

        if text == "Single Shot": color = self.unused_color
        else: color = self.fg_color
        self.OpeningTimeLabel.SetForegroundColour(color)
        self.OpeningTime.SetForegroundColour(color)
        # Make sure not to override pending changes.
        if self.OpeningTime.GetBackgroundColour() != self.edited:
            value = self.shutter.opening_time
            text = "%.3f s" % value
            if self.OpeningTime.GetValue() != text:
                self.OpeningTime.SetValue(text)

        enabled = self.shutter.open_close_input_enabled
        self.OpenCloseEnabled.Set3StateValue(enabled)

        level = ms_shutter.open_close_input_level
        if enabled:
            if level > 0: text = "(high: open)"
            else: text = "(low: closed)"
        else:
            if level > 0: text = "(high)"
            else: text = "(low)"
        self.OpenCloseStatus.SetLabel(text)
        if enabled:
            if level > 0: self.OpenCloseStatus.SetForegroundColour(wx.RED)
            else: self.OpenCloseStatus.SetForegroundColour(wx.GREEN)
        else: self.OpenCloseStatus.SetForegroundColour(wx.BLACK)

        self.Version.SetLabel(self.shutter.firmware_version)

        open = abs(pos - self.shutter.open_position) < 1.0
        if open: self.OpenButton.SetBackgroundColour(wx.RED)
        else: self.OpenButton.SetBackgroundColour(self.bkg_color)
        if open: self.CloseButton.SetLabel("Open")
        else: self.CloseButton.SetLabel("open")
        
        closed = abs(pos - self.shutter.closed_position) < 3.0 \
            or abs(pos - self.shutter.alternate_closed_position) < 3.0
        if closed: self.CloseButton.SetBackgroundColour(wx.GREEN)
        else: self.CloseButton.SetBackgroundColour(self.bkg_color)
        if closed: self.CloseButton.SetLabel("Closed")
        else: self.CloseButton.SetLabel("Close")

    def mark_inactive(self):
        """Bring the controls and indicators in a state showing that
        they are not valid"""
        self.Pos.SetValue("-")
        self.Pos.SetForegroundColour(self.unused_color)
        self.PulseCount.SetValue("-")
        self.PulseCount.SetForegroundColour(self.unused_color)
        # Gray out checkboxes by setting the state to a value of 2.
        self.DriveEnabled.Set3StateValue(2)   
        self.DriveDisabled.Set3StateValue(2)       
        self.TriggerEnabled.Set3StateValue(2)         
        self.OpeningMode.Clear()        
        self.OpeningMode.AppendItems(["Single Shot","Timed","-"])        
        self.OpeningMode.SetStringSelection("-")
        self.OpeningTime.SetValue("-")
        self.OpeningTimeLabel.SetForegroundColour(self.unused_color)
        self.OpeningTime.SetForegroundColour(self.unused_color)
        self.OpenCloseEnabled.Set3StateValue(2)

        self.OpenCloseStatus.SetLabel("")

        self.OpenButton.SetBackgroundColour(self.bkg_color)
        self.CloseButton.SetBackgroundColour(self.bkg_color)

    def OnEnterAddress(self,event):
        "Called when typing in the address field."
        self.shutter.address = self.Address.GetValue()

    def OnEditPosition(self,event):
        "Called when typing in the position field."
        self.Pos.SetBackgroundColour(self.edited)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip() 

    def OnEnterPosition(self,event):
        "Called when typing Enter in the position field."
        if self.shutter.open_close_input_enabled:
            title = "Confirm"
            message = "The shutter is currently controller by the Open/Close digital input.\n"
            message += "Do you want to disable the Open/Close digital input?"
            dlg = wx.MessageDialog (self,message,title,wx.OK|wx.CANCEL)
            OK = (dlg.ShowModal() == wx.ID_OK)
            dlg.Destroy()
            if not OK: return
            self.shutter.open_close_input_enabled = False
        self.Pos.SetBackgroundColour(wx.WHITE)
        text = self.Pos.GetValue()
        try: pos = float(text)
        except: self.OnAutoRefresh(); return
        self.shutter.position = pos
        self.moving = True
        self.OnAutoRefresh()

    def OnEditPulseCount(self,event):
        "Called when typing in the position field."
        self.PulseCount.SetBackgroundColour(self.edited)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip() 

    def OnEnterPulseCount(self,event):
        "Called when typing Enter in the position field."
        self.PulseCount.SetBackgroundColour(wx.WHITE)
        text = self.PulseCount.GetValue()
        try: count = int(text)
        except: self.OnAutoRefresh(); return
        self.shutter.pulse_count = count
        self.OnAutoRefresh()

    def OnEnableDrive(self,event):
        "Turn on the holding current."
        self.shutter.drive_enabled = True
        self.refresh()

    def OnDisableDrive(self,event):
        "Turn off the holding current."
        self.shutter.drive_enabled = False
        self.refresh()

    def OnEnableTrigger(self,event):
        "Turn on the holding current."
        if self.shutter.trigger_enabled: self.shutter.trigger_enabled = False
        else: self.shutter.trigger_enabled = True
        self.refresh()

    def OnChangeOpeningMode(self,event):
        selection = self.OpeningMode.GetStringSelection()
        if selection == "Single Shot": self.shutter.timed_open = False
        elif selection == "Timed": self.shutter.timed_open = True
        else: print "Opening mode: %r?" % selection

    def OnEditOpeningTime(self,event):
        "Called when typing in the 'Opening Time' field."
        self.OpeningTime.SetBackgroundColour(self.edited)
        # Pass this event on to further event handlers bound to this event.
        # Otherwise, the typed text does not appear in the window.
        event.Skip() 

    def OnEnterOpeningTime(self,event):
        "Called when typing Enter in the 'Opeing Time' field."
        self.OpeningTime.SetBackgroundColour(wx.WHITE)
        text = self.OpeningTime.GetValue()
        try: value = float(text.strip(" s"))
        except: self.OnAutoRefresh(); return
        self.shutter.opening_time = value
        self.OnAutoRefresh()

    def OnEnableOpenClose(self,event):
        "Turn on the holding current."
        if self.shutter.open_close_input_enabled: self.shutter.open_close_input_enabled = False
        else: self.shutter.open_close_input_enabled = True
        self.refresh()

    def OnOpen(self,event=None):
        """Rotate shutter to open position"""
        if self.shutter.open_close_input_enabled and self.shutter.open_close_input_level == 0:
            title = "Confirm"
            message = "The shutter is currently closed because the Open/Close digital input is <low>.\n"
            message += "Do you want to disable the Open/Close digital input?"
            dlg = wx.MessageDialog (self,message,title,wx.OK|wx.CANCEL)
            OK = (dlg.ShowModal() == wx.ID_OK)
            dlg.Destroy()
            if not OK: return
            self.shutter.open_close_input_enabled = False
        self.shutter.position = self.shutter.open_position
        self.refresh()

    def OnClose(self,event=None):
        """Rotate shutter to closed position"""
        if self.shutter.open_close_input_enabled and self.shutter.open_close_input_level == 1:
            title = "Confirm"
            message = "The shutter is currently open because the Open/Close digital input is <high>.\n"
            message += "Do you want to disable the Open/Close digital input?"
            dlg = wx.MessageDialog (self,message,title,wx.OK|wx.CANCEL)
            OK = (dlg.ShowModal() == wx.ID_OK)
            dlg.Destroy()
            if not OK: return
            self.shutter.open_close_input_enabled = False
        self.shutter.position = self.shutter.closed_position
        self.refresh()

    def OnRefresh(self,event=None):
        "Check whether the network connection is OK."
        # Reset pending status of entered new position 
        self.Pos.SetBackgroundColour(wx.WHITE)
        self.refresh()

    def OnAutoRefresh(self,event=None):
        "Called if Auto Refresh check box is checked or unchecked."
        # Relaunch this procedure after 500 ms as long as the "Auto Refesh"
        # box is checked.
        if self.AutoRefresh.GetValue() == True or self.moving:
            self.refresh()
            self.moving = self.shutter.moving
            self.timer = wx.Timer(self)
            self.Bind (wx.EVT_TIMER,self.OnAutoRefresh)
            self.timer.Start(500,oneShot=True)

    def refresh(self):
        self.Status.SetLabel("checking...")
        status = self.shutter.status
        self.Status.SetLabel(status)
        if status != "OK":
            self.AutoRefresh.SetValue(False)
            self.mark_inactive()
            return
        self.show_settings()

if __name__ == '__main__': 

    app = wx.GetApp() if wx.GetApp() else wx.App()

    panel = TranslationPanel()
    app.MainLoop()
