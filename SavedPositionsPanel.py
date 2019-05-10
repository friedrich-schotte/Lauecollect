#!/usr/bin/env python
"""Control panel to save and motor positions.
Friedrich Schotte 13 Dec 2010 - 6 Jul 2017"""
__version__ = "1.3.7" # fixed settings lost bug

import wx
from EditableControls import TextCtrl
from numpy import ndarray,isnan
from DB import dbput,dbget
# Turn off IEEE-754 warnings in numpy 1.6+ ("invalid value encountered in...")
import numpy; numpy.seterr(invalid="ignore",divide="ignore")


class SavedPositionsPanel (wx.Frame):
    """Control panel to save and recall goniometer X,Y,Z and Phi settings."""
    
    def __init__(self,parent=None,
        title="Goniometer Saved Positions",
        name = "goniometer_saved",
        motors = [],
        motor_names = [],
        formats = [],
        nrows = 8):
        """
        name: basename of settings file
        """
        wx.Frame.__init__(self,parent=parent,title=title)

        self.name = name
        self.motors = motors
        self.motor_names = motor_names
        self.formats = formats

        for i in range(len(self.motor_names),len(self.motors)):
            self.motor_names += [self.motors[i].name]
        while len(self.formats) < len(self.motors): self.formats += ["%+6.3f"]

        panel = wx.Panel(self)

        # Leave a 5 pixel wide border.
        border_box = wx.BoxSizer(wx.VERTICAL)

        # Controls

        # Labels
        flag = wx.ALIGN_CENTRE_VERTICAL|wx.ALL
        grid = wx.GridBagSizer(1,1)
        labels = ["","Description","Updated"]
        for i in range(len(self.motors)):
            labels += ["%s\n[%s]" % (self.motor_names[i],self.motors[i].unit)]
        self.Labels = ndarray(len(labels),object)
        for i in range(0,len(labels)):
            self.Labels[i] = wx.StaticText(panel,label=labels[i],style=wx.ALIGN_CENTRE)
            grid.Add(self.Labels[i],(0,i),flag=flag)
        
        # Settings
        style = wx.TE_PROCESS_ENTER

        self.Descriptions = ndarray(nrows,object)
        for i in range(0,nrows):
            self.Descriptions[i] = TextCtrl(panel,size=(200,-1),style=style)
            grid.Add(self.Descriptions[i],(i+1,1),flag=flag)
        self.NormalBackgroundColour = self.Descriptions[0].BackgroundColour

        self.Dates = ndarray(nrows,object)
        for i in range(0,nrows):
            self.Dates[i] = TextCtrl(panel,size=(100,-1),style=style)
            grid.Add(self.Dates[i],(i+1,2),flag=flag)

        self.Positions = ndarray((nrows,len(self.motors)),object)
        for i in range(0,nrows):
            for j in range(0,len(self.motors)):
                width = max(75,self.Labels[j+3].GetSize()[0]+5)
                self.Positions[i,j] = TextCtrl(panel,size=(width,-1),style=style)
                grid.Add(self.Positions[i,j],(i+1,j+3),flag=flag)

        # Current positions
        label = wx.StaticText(panel)
        grid.Add(label,(nrows+1,1),flag=flag)
        label.Label = "Current value:"
        
        # 'Go To' Buttons
        height = self.Descriptions[0].GetSize()[1]
        for i in range(0,nrows):
            button = wx.Button(panel,label="Go To",size=(60,height),id=i)
            grid.Add(button,(i+1,0),flag=flag)
            self.Bind(wx.EVT_BUTTON,self.goto_setting,button)

        # 'Set' Buttons
        height = self.Descriptions[0].GetSize()[1]
        for i in range(0,nrows):
            button = wx.Button(panel,label="Set",size=(45,height),id=100+i)
            grid.Add(button,(i+1,len(self.motors)+3),flag=flag)
            self.Bind(wx.EVT_BUTTON,self.define_setting,button)

        self.Current = ndarray(len(motors),object)
        for i in range(0,len(self.motors)):
            self.Current[i] = wx.StaticText(panel)
            grid.Add(self.Current[i],(nrows+1,i+3),flag=flag)

        border_box.Add (grid,flag=wx.ALL,border=5)

        button = wx.Button(panel,label="Stop")
        self.Bind(wx.EVT_BUTTON,self.stop,button)
        border_box.Add (button,flag=wx.ALL|wx.ALIGN_CENTRE_HORIZONTAL,border=5)
        
        panel.SetSizer(border_box)
        panel.Fit()
        self.Fit()
        self.Show()

        self.update_settings()

        # Make sure "on_input" is called only after "update_settings".
        
        # Call the "on_input" routine whenever the user presses Enter.
        self.Bind (wx.EVT_TEXT_ENTER,self.on_input)
        # Call the "on_input" routine whenever the user navigates between
        # fields, using Enter, Tab or the mouse
        self.Bind (wx.EVT_CHILD_FOCUS,self.on_child_focus)

        # Periodically update the displayed fields.
        self.timer = wx.Timer(self)
        self.Bind (wx.EVT_TIMER,self.OnTimer)
        self.timer.Start(1000,oneShot=True)

    def OnTimer(self,event=None):
        "Called periodically every second triggered by a timer"
        self.update_settings()
        self.update()
        self.timer.Start(1000,oneShot=True) # Need to restart the Timer

    def on_input(self, event):
        """This is called when the use switches between feilds and controls
        using Tab or the mouse, or presses Enter in a text entry. This does
        necessarily indicate that any value was changed. But it is a good
        opportunity the process any changes."""
        self.save_settings()

    def on_child_focus(self,event):
        """Called whenever the user navigates between fields, using Enter,
        Tab or the mouse.
        This routine simply calls 'on_input' and the passes the event on to the
        default handler. I did not bind the CHILD_FOCUS to 'on_input' directly
        because the other events 'on_input' handles (TEXT_ENTER,COMBOBOX)
        must not be passed on to a default event handler."""
        self.on_input(event)
        # The default event handler needs to receive the event too, otherwise
        # the focus would not change.
        event.Skip()

    def update(self):
        """Update motor positions"""
        from numpy import zeros,array,average,sqrt,nanargmin

        for i in range(0,len(self.motors)):
            position = self.motors[i].value
            self.Current[i].Label = tostr(self.motors[i].value,self.formats[i])
        # Highlight the current settings
        nrows = self.Descriptions.shape[0]
        values = zeros((nrows,len(self.motors)))
        for i in range(0,nrows):
            for j in range(0,len(self.motors)):
                values[i,j] = tofloat(self.Positions[i,j].Value)
        positions = array([motor.value for motor in self.motors])
        tolerance = array([getattr(motor,"readback_slop",0)
                           for motor in self.motors])
        # Find the row that matches the actual settings
        matches = zeros(nrows,bool)
        for i in range(0,nrows):
            matches[i] = all(abs(values[i,:] - positions) < tolerance)
        # Find the row the is closest to the actual settings
        dist = zeros(nrows)
        for i in range(0,nrows):
            dist[i] = sqrt(average((values[i,:] - positions)**2))
        try: closest = nanargmin(dist)
        except ValueError: closest = 0
        ##print "closest",closest
        # Update the colors
        for i in range(0,nrows):
            if matches[i]: color = wx.Colour(150,150,255)
            elif i == closest: color = wx.Colour(200,200,255)
            else: color = self.NormalBackgroundColour
            self.Descriptions[i].BackgroundColour = color
            self.Dates[i].BackgroundColour = color
            for j in range(0,len(self.motors)): 
                self.Positions[i,j].BackgroundColour = color
            
    def update_settings(self):
        """Reload saved settings from the settings file"""
        nrows = self.Descriptions.shape[0]
        for i in range(0,nrows):
            text = dbget("%s.line%d.description" % (self.name,i))
            self.Descriptions[i].Value = text
            text = dbget("%s.line%d.updated" % (self.name,i))
            self.Dates[i].Value = text
            for j in range(0,len(self.motors)):
                value = dbget("%s.line%d.%s" % (self.name,i,self.motor_names[j]))
                self.Positions[i,j].Value = value

    def save_settings(self):
        nrows = self.Descriptions.shape[0]
        for i in range(0,nrows):
            text = self.Descriptions[i].Value
            dbput("%s.line%d.description" % (self.name,i),text)
            text = self.Dates[i].Value
            dbput("%s.line%d.updated" % (self.name,i),text)
            for j in range(0,len(self.motors)):
                value = self.Positions[i,j].Value
                resname = "%s.line%d.%s" % (self.name,i,self.motor_names[j])
                dbput(resname,value)

    def goto_setting(self,event):
        """Moved the motor to the settings in the row of the 'Go To'
        button that was pressed pressed."""
        i = event.GetId() # Row number of "Go To" button pressed
        for j in range(0,len(self.motors)):
            try:
                value = float(self.Positions[i,j].Value)
                ##print "%s.value = %r" % (self.motor_names[j],value)
                self.motors[j].value = value
            except ValueError: pass

    def define_setting(self,event):
        """Copy the current motor settings in the row of the 'Set" button
        that was pressed."""
        i = event.GetId()-100 # Row number of "Set" button pressed
        for j in range(0,len(self.motors)):
            value = tostr(self.motors[j].command_value,self.formats[j])
            self.Positions[i,j].Value = value
        from time import strftime
        date = strftime("%d %b %H:%M")
        self.Dates[i].Value = date

        self.save_settings()

    def stop(self,event):
        """To cancel any move should one hit the wrong button by mistake"""
        for j in range(0,len(self.motors)): self.motors[j].stop()


def tostr(x,format="%g"):
    """Converts a number to a string.
    This is needed to handle "not a number" and infinity properly.
    Under Windows, 'str()','repr()' and '%' format 'nan' as '-1.#IND' and 'inf'
    as '1.#INF', which is inconsistent with Linux ('inf' and 'nan').
    """
    from numpy import isnan,isinf
    try:
        if isnan(x): return "nan"
        if isinf(x) and x>0: return "inf"
        if isinf(x) and x<0: return "-inf"
        return format % x
    except TypeError: return str(x)

def tofloat(s):
    """Convert string to float and return 'not a number' in case of """
    from numpy import nan
    try: return float(s)
    except Exception: return nan


if __name__ == '__main__':
    from id14 import SampleX,SampleY,SampleZ,SamplePhi
    # Needed to initialize WX library
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False)
    panel = SavedPositionsPanel(
        title="Goniometer Saved Positions",
        name="goniometer_saved",
        motors=[SampleX,SampleY,SampleZ,SamplePhi],
        motor_names=["SampleX","SampleY","SampleZ","SamplePhi"],
        formats = ["%+6.3f","%+6.3f","%+6.3f","%+8.3f"],
        nrows=8)
    wx.app.MainLoop()
