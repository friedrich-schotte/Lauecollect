#!/usr/bin/env python
"""
DI-245 Data Acquisition monitor (Application level code)
by Valentyn Stadnytskyi
created: Oct 2017
last update: Nov 11, 2017
"""
import matplotlib
matplotlib.use('WxAgg')
import socket
from optparse import OptionParser
from numpy import nan
from time import time , sleep,localtime,strftime,clock
import matplotlib.pyplot as plt
import numpy as np
import sys
from struct import unpack
import wx
import StringIO
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from pdb import pm
import traceback

from msgpack import packb as msgpack_packb , unpackb as msgpack_unpackb
import msgpack_numpy as m

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FCW
from matplotlib.figure import Figure
SMALL_SIZE = 8
matplotlib.rc('font', size=SMALL_SIZE)
matplotlib.rc('axes', titlesize=SMALL_SIZE)
import logging
from logging import error,warn,info,debug
from tempfile import gettempdir
logging.basicConfig(filename=gettempdir()+'/di_245_AL.log',
                    level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

__version__ = "1.0.6" # Friedrich Schotte: logfile directory
#This version has major revision.
#I have updated circular buffer client to be uploaded from the circular_buffer.py module
#cleaned the code

from circular_buffer_LL import client as CircularBuffer

class ClientSocket(object): 

    def __init__(self,ip_addrs_input = '164.54.161.34'):
        self.server = None
        self.parser = OptionParser()
        self.parser.add_option("-z", action="store", dest="data")
        self.options, self.args = self.parser.parse_args()
        self.ip_address_server = ip_addrs_input
    
    def _connect(self):
        try:
            debug("Creating socket")
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            debug("Connecting to %r on port 9900" % self.ip_address_server)
            from CA import caget
            try:
                port = int(caget('NIH:DI245.SOCKET')[1])
                ip_address = caget('NIH:DI245.SOCKET')[0]
            except:
                error(traceback.format_exc())
                port = nan
                
            self.server.connect((self.ip_address_server, port))
            debug("Connection success!")
        except socket.error, msg:
            error("Failed to create and connect. Error code: %s , Error message : %r" % (str(msg[0]), msg[1]))
            
            
    def _send(self,command_str):
        command = command_str.split(",")
        debug('command %r,buffer.pointerC %r, clock %r' % (command,buffer.pointerC , clock()))
        
        if len(command[0]) == 0:
            msg_out =msgpack_packb([-1], default=m.encode)
        elif command[0] == "1":
            frame.live_checkbox.SetValue(False)
            msg_out = msgpack_packb([int(command[0])], default=m.encode)
        elif command[0] == "2":
            frame.live_checkbox.SetValue(False)
            msg_out = msgpack_packb([int(command[0])], default=m.encode)
        elif command[0] == "3": 
            if len(commmand) >=2:
                msg_out = msgpack_packb([int(command[0]),int(command[1])], default=m.encode)
            else:
                msg_out = msgpack_packb([int(command[0]),int(1)], default=m.encode)
        elif command[0] == "4":
            msg_out = msgpack_packb([int(command[0])], default=m.encode)
        elif command[0] == "5":   
            msg_out = msgpack_packb([int(command[0]),int(buffer.pointerC)], default=m.encode)
            debug('msg_out %r' % msg_out)
        elif command[0] == "6":
            msg_out = msgpack_packb([int(command[0])], default=m.encode)    
        elif command[0] == "7":
            msg_out = msgpack_packb([int(command[0])], default=m.encode)    
        else:
            msg_out = msgpack_packb([int(command[0])], default=m.encode)         
        self.server.sendall(msg_out)
    
    def _receive(self):
        length = int(self.server.recv(256))
        sleep(0.01)
        flag = True
        if length != 0:
            data = ''
            amount_received = len(data)
            while len(data) < length:
                data += self.server.recv(length - len(data))
                sleep(0.01)
            debug("Received response: pickled data arrived")
            flag = False

        self.response_arg =  msgpack_unpackb(data, object_hook=m.decode) 
    
    def _server_close(self):
        self.server.close() 
        
        
        
def smooth(x,y, box_pts):
    box = np.ones(box_pts)/box_pts
    y_smooth = np.convolve(y, box, mode='same')
    x_smooth = np.convolve(x, box, mode='same')
    return x_smooth, y_smooth
        
class ClientGUI(wx.Frame):
 
    def __init__(self):
        self.create_GUI()
                     
    def create_GUI(self):
    #This function creates buttons with defined position and connects(binds) them with events that
        #This function creates buttons with defined position and connects(binds) them with events that
        
        #####Global start variable####
        self.local_time = time()
        self.AirT_cjc = -2.
        self.OasisT_cjc = -2.
        self.smooth_factor = 1
        self.calib = [1,0,1,0]
        self.frequency = 40 #this is actually frequency, not time
        self.time_list = [10*self.frequency,30*self.frequency,60*self.frequency,60*2*self.frequency,60*5*self.frequency,
                          60*10*self.frequency,60*30*self.frequency,3600*1*self.frequency,3600*2*self.frequency,
                          3600*6*self.frequency,3600*12*self.frequency,len(buffer.buffer[0,:])]

        self.time_range = 10*self.frequency
        
        self.txt_font_size = 10
        self.arg2 = 10
        
        self.environment = 0 #APS is 0, NIH is 1; localhost is 2
        self.DicObjects = {} #this is a dictionary with all different objects in GUI
        
        ##Create Frame ans assign panel
        frame = wx.Frame.__init__(self, None, wx.ID_ANY, "Monitor (DI-245)", pos = (0,0))
        
        self.panel = wx.Panel(self, wx.ID_ANY, style=wx.BORDER_THEME,size = (400,70), pos = (0,0))
        

        ###########################################################################
        ##MENU STARTS: for the GUI
        ###########################################################################
        file_item = {}
        about_item = {}
        self.calib_item = {}
        self.opt_item = {}
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        file_item[2] = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
        self.Bind(wx.EVT_MENU, self.OnQuit, file_item[2])
        
        
        calibMenu = wx.Menu()
        self.calib_item[0]= calibMenu.Append(wx.NewId(),  "Calibrate" ,"")
        self.Bind(wx.EVT_MENU, self._on_server_comm, self.calib_item[0])
        
        
        optMenu = wx.Menu()
        self.opt_item[0]= optMenu.Append(wx.NewId(),  '(0) Init DL')
        self.opt_item[1]= optMenu.Append(wx.NewId(),  '(1) Close DL')
        self.opt_item[2]= optMenu.Append(wx.NewId(),  '(2) CA Broadcast')
        self.opt_item[6]= optMenu.Append(wx.NewId(),  '(6) Perform calibration')
        self.opt_item[7]= optMenu.Append(wx.NewId(),  '(7) Get calibration')
        self.Bind(wx.EVT_MENU, self._on_server_comm, self.opt_item[0])
        self.Bind(wx.EVT_MENU, self._on_server_comm, self.opt_item[1])
        
        aboutMenu = wx.Menu()
        about_item[0]= aboutMenu.Append(wx.ID_ANY,  'Client About')
        about_item[1]= aboutMenu.Append(wx.ID_ANY,  'Server About')
        self.Bind(wx.EVT_MENU, self._on_client_about, about_item[0])
        self.Bind(wx.EVT_MENU, self._on_server_about, about_item[1])
        
        menubar.Append(fileMenu, '&File')
        menubar.Append(calibMenu, '&Calibration')
        
        menubar.Append(optMenu, '&Options')
        menubar.Append(aboutMenu, '&About')
        
        
        self.SetMenuBar(menubar)
        
        
        
        self.Centre()
        self.Show(True)
        ###########################################################################
        ###MENU ENDS###
        ###########################################################################

        
        sizer = wx.GridBagSizer(5, 2)
        
        text4 = wx.StaticText(self.panel, label="Server IP")
        sizer.Add(text4, pos=(0, 0), flag=wx.TOP|wx.LEFT, border=5)
        
        self.ip_dropdown_list = [['164.54.161.34','128.231.5.78','127.0.0.1'],['APS','NIH','localhost']] 
        self.IP_choice = wx.Choice(self.panel,choices = self.ip_dropdown_list[1][:])
        self.IP_choice.SetSelection(self.environment)
        self.IP_choice.Bind(wx.EVT_CHOICE, self._on_change_ip_press)
        sizer.Add(self.IP_choice, pos=(0, 1), span=(1, 1), flag=wx.TOP|wx.EXPAND, border=5) 
        
        
        self.flashingText = wx.StaticText(self.panel)
        self.flashingText.SetLabel('Ready')    
        sizer.Add(self.flashingText, pos=(0, 3), flag=wx.TOP|wx.LEFT, border=5)
        
        self.DicObjects[4]  = wx.Button(self.panel, label="Start")
        sizer.Add(self.DicObjects[4] , pos=(0, 4), flag=wx.TOP|wx.RIGHT, border=5)
        self.DicObjects[4].Bind(wx.EVT_BUTTON, self.mthd_buttons)
        
        
        self.live_checkbox = wx.CheckBox(self.panel, id=wx.ID_ANY, label="Live", style=0, validator=wx.DefaultValidator, name='LiveCheckBoxNameStr')
        sizer.Add( self.live_checkbox, pos=(1, 0), flag=wx.TOP|wx.LEFT, border=5)
        self.live_checkbox.SetValue(False)
        self.live_checkbox.Disable()
        
        self.DicObjects['server time'] = wx.StaticText(self.panel)
        self.DicObjects['server time'].SetLabel('')
        sizer.Add(self.DicObjects['server time'], pos=(1, 1), flag=wx.TOP|wx.LEFT, border=5)
        self.DicObjects['server time'].SetLabel('Press Start Button')
        text5 = wx.StaticText(self.panel, label="time")
        sizer.Add(text5, pos=(1, 3), flag=wx.TOP|wx.LEFT, border=5)
        self.time_dropdown_list = ['10 s','30 s', '1 min', '2 min', '5 min' , '10 min' , '30 min' , '1 h' , '2 h', '6 h' , '12 h','max']#, 'max']   
        self.time_choice = wx.Choice(self.panel,choices = self.time_dropdown_list)
        sizer.Add(self.time_choice, pos=(1,4), span = (4,5), flag=wx.LEFT|wx.TOP, border=5)
        self.time_choice.Bind(wx.EVT_CHOICE, self._on_change_time_press)
        self.time_choice.SetSelection(1)
        self.live_checkbox.SetValue(False)
        sizer.AddGrowableCol(2)
        
        self.panel.SetSizer(sizer)
    
        self.dpi = 100
        self.figure = Figure((4, 6), dpi=self.dpi)
        self.axes0 = self.figure.add_subplot(411)
        self.axes1 = self.figure.add_subplot(412)
        self.axes2 = self.figure.add_subplot(413)
        self.axes3 = self.figure.add_subplot(414)
        self.canvas = FCW(self, -1, self.figure)
        gsizer = wx.BoxSizer(wx.VERTICAL)
        gsizer.Add(self.panel, 0)
        gsizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(gsizer)
        self.Fit()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.redraw_timer.Start(1000)
        self.draw(None)

    def _on_client_about(self,event):
        "Called from the Help/About"
        from os.path import basename
        from inspect import getfile
        filename = getfile(lambda x: None)
        info = basename(filename)+" version: "+__version__+"\n"+__doc__
        dlg = wx.MessageDialog(self,info,"About",wx.OK|wx.ICON_INFORMATION)
        dlg.CenterOnParent()
        dlg.ShowModal()
        dlg.Destroy()    
    
    def _on_server_about(self,event):
        wx.MessageBox('This is information about the server', 'Server Info', 
        wx.OK | wx.ICON_INFORMATION)       
    
    
    def OnQuit(self, event):
        self.Close()     

    def _on_change_ip_press(self,event):
        info("Dropdown IP menu: selected %s , New IP address : %r" % (self.ip_dropdown_list[1][self.IP_choice.GetSelection()],self.ip_dropdown_list[0][self.IP_choice.GetSelection()]))
        client.ip_address_server =  self.ip_dropdown_list[0][self.IP_choice.GetSelection()]
        self.live_checkbox.SetValue(False)
        self.live_checkbox.Disable()
        
    def _on_change_time_press(self,event):
        self.time_list = [10*self.frequency,30*self.frequency,60*self.frequency,60*2*self.frequency,60*5*self.frequency,60*10*self.frequency,60*30*self.frequency,3600*1*self.frequency,3600*2*self.frequency,3600*6*self.frequency,3600*12*self.frequency,len(buffer.buffer[0,:])]
        self.time_range =  self.time_list[self.time_choice.GetSelection()]
        if self.time_range >= len(buffer.buffer[0,:]):
            self.time_range = self.time_list[len(self.time_list)-1]
            self.time_choice.SetSelection(len(self.time_list)-1)
        info('self time_range selected %r' % (self.time_range))
           
        if self.time_range == 10*self.frequency:
            self.smooth_factor = 1
            self.redraw_timer.Start(1000) 
        elif self.time_range == 30*self.frequency:
            self.smooth_factor = 1
            self.redraw_timer.Start(1000) 
        elif self.time_range == 1*60*self.frequency:
            self.smooth_factor = 20  
            self.redraw_timer.Start(1000) 
        elif self.time_range == 2*60*self.frequency:
            self.smooth_factor = 30      
            self.redraw_timer.Start(1000) 
        elif self.time_range == 5*60*self.frequency:
            self.smooth_factor = 60  
            self.redraw_timer.Start(1000)            
        elif self.time_range == 10*60*self.frequency:
            self.smooth_factor = 60   
            self.redraw_timer.Start(1000)            
        elif self.time_range == 0.5*3600*self.frequency:
            self.smooth_factor = 60
            self.redraw_timer.Start(1000)
        elif self.time_range == 3600*self.frequency:
            self.smooth_factor = 300
            self.redraw_timer.Start(3000)
        elif self.time_range == 2*3600*self.frequency:
            self.smooth_factor = 600
            self.redraw_timer.Start(4000)
        elif self.time_range == 6*3600*self.frequency:
            self.smooth_factor = 1800
            self.redraw_timer.Start(5000)
        elif self.time_range == 12*3600*self.frequency:
            self.smooth_factor = 7200
            self.redraw_timer.Start(5000)
        elif self.time_range > 12*3600*self.frequency:
            self.smooth_factor = 12*1800
            self.redraw_timer.Start(10000)
        else:
            self.smooth_factor = 1
        self.draw(None)
        
    def _on_command_list_select(self,event):
    
        info('commands from the list selected')
        # self._create_button(0,'Echo (0)',(step_h*0+step_h_zero,step_v*0+step_v_zero),'mthd_buttons')
        # self._create_button(1,'Close Server (1)',(step_h*0+step_h_zero,step_v*1+step_v_zero),'mthd_buttons')
        # self._create_button(2,'Broadcast burst (2)',(step_h*0+step_h_zero,step_v*2+step_v_zero),'mthd_buttons')
        # self._create_button(3,'Get mean(N) (3)',(step_h*0+step_h_zero,step_v*3+step_v_zero),'mthd_buttons')
        # self._create_button(4,'All buffer (4)',(step_h*0+step_h_zero,step_v*4+step_v_zero),'mthd_buttons')
        # self._create_button(5,'Update buffer (5)',(step_h*0+step_h_zero,step_v*5+step_v_zero),'mthd_buttons')
        # self._create_button(6,'Plot (6)',(step_h*0+step_h_zero,step_v*6+step_v_zero),'_on_button_plot')
        # self._create_button(7,'Save to file (7)',(step_h*0+step_h_zero,step_v*7+step_v_zero),'_on_save_file_press') 

        
    def _set_response(self,response_arg):
        self.local_time = response_arg[1]
        self.DicObjects['server time'].SetLabel(strftime("%Y-%m-%d %H:%M:%S", localtime(self.local_time)))
        

    def method_result(self,method = 'window'):
        if method == 'window':
            self.DicObjects['result'].SetLabel(str(self.result))
    
    def help_button(self,event):
        info('Help button was pressed')
    
    def _on_button_plot(self,event):
        info('plot button pressed')
        self.draw(event)
    
    def _on_server_comm(self,event): 
        # self.calib_item[0]= calibMenu.Append(wx.NewId(),  "Calibrate" ,"")
        # self.opt_item[0]= optMenu.Append(wx.NewId(),  'Echo Server')
        # self.opt_item[1]= optMenu.Append(wx.NewId(),  'Close Server')
        
        try:
            if event.GetId() == self.calib_item[0].GetId():
                command = 6
            elif event.GetId() == self.opt_item[0].GetId():
                command = 0
            elif event.GetId() == self.opt_item[1].GetId():
                command = 1    
            flag = True
        except:
            error(traceback.format_exc())
            flag = False
        if event == 7:
            command = 7
            flag = True
        info('sending command = %r' %(command))
        if flag:
            client._connect()
            client._send(str(command))
            sleep(0.005)
            client._receive()
            client.server.close()  
            info('Command processed: %r'% client.response_arg[0])
            info('server time: %r' % client.response_arg[1])
            info('arg1: %r' % client.response_arg[2])
            info('arg2: %r' % client.response_arg[3])
            if command == 6:
                self.calib = client.response_arg[2]
            if command == 7:
                self.calib = client.response_arg[2]              
            self._set_response(client.response_arg) 
            
    def _on_save_file_press(self,event):
        #msgpack_packb([time(),], default=m.encode)
        np.savetxt('DI_245_circular_buffer'+str(time())+'.csv',np.transpose(buffer.buffer), delimiter=',' , fmt='%1.4e')  
        
    def mthd_buttons(self, event):
        """
        This method is an event handler. It cross refences the event Id and an Id stored in a dictionary to determine what to do. 
        """
        if event == 'change_ip':
            pass        
        else:
            self.flashingText.SetLabel('Pulling')
            info('Event ID %r'  % event.GetId())
            raw_commands = '0'
            for i in self.DicObjects.keys():
                if event.GetId() == self.DicObjects[i].GetId():
                    raw_commands = str(i)
                if i == 3:
                    raw_commands = raw_commands +',' + str(self.arg2)

            print('raw_commands %r'  % raw_commands)
            
            client._connect()
            client._send(raw_commands)
            
            sleep(0.005)
            client._receive()
            client.server.close()  

                
            if client.response_arg[0] == 0:
                print('Command processed:',client.response_arg[0])
                print('server time:', client.response_arg[1])
                print('arg1:', client.response_arg[2])
                print('arg2:', client.response_arg[3])
                self._set_response(client.response_arg)
                
            elif client.response_arg[0] == 1:
                print("Server has been shut down")
                self._set_response(client.response_arg)
            
            
            elif client.response_arg[0] == 2: 
                print('Command processed:',client.response_arg[0])
                print('server time:', client.response_arg[1])
                print('arg1:', client.response_arg[2])
                print('arg2:', client.response_arg[3])
                self._set_response(client.response_arg)
                
            elif client.response_arg[0] == 3:  
                print('Command processed:',client.response_arg[0])
                print('server time:', client.response_arg[1])
                print('arg1:', client.response_arg[2])
                print('arg2:', client.response_arg[3])
                self._set_response(client.response_arg)
                self._update_readings(client.response_arg)
            elif client.response_arg[0] == 4: 
                print('test')
                print('Command processed:',client.response_arg[0])
                print('server time:', client.response_arg[1])
                print('arg1:', client.response_arg[2])
                print('arg2:', client.response_arg[3])
                buffer.get_all(int(client.response_arg[2]),client.response_arg[3])
                self._set_response(client.response_arg)
                self._on_server_comm(7)
                self.live_checkbox.SetValue(True)
                self.live_checkbox.Enable()
                
            elif client.response_arg[0] == 5:
                print('Command processed:',client.response_arg[0])
                print('server time:', client.response_arg[1])
                print('arg1:', client.response_arg[2])
                print('arg2:', client.response_arg[3])
                print('client.response_arg[2]' , client.response_arg[2])
                buffer.get_update(int(client.response_arg[2]),client.response_arg[3])
                self._set_response(client.response_arg)
                
            elif client.response_arg[0] == 6:
                print('Command processed:',client.response_arg[0])
                print('server time:', client.response_arg[1])
                print('arg1:', client.response_arg[2])
                print('arg2:', client.response_arg[3])
                self.calib = client.response_arg[2]
                self._set_response(client.response_arg) 
                

            elif client.response_arg[0] == 7:
                print('Command processed:',client.response_arg[0])
                print('server time:', client.response_arg[1])
                print('arg1:', client.response_arg[2])
                print('arg2:', client.response_arg[3])
                self.calib = client.response_arg[2]
                print('self.calib')
                print('calibration %r' % self.calib)
                self._set_response(client.response_arg)
                
                
            else:
                print('Command processed:',client.response_arg[0])
                print('server time:', client.response_arg[1])
                print('arg1:', client.response_arg[2])
                print('arg2:', client.response_arg[3])
                self._set_response(client.response_arg)
            
        self.flashingText.SetLabel('Ready')    
        
    
#################################################################################
########### Plotting
#################################################################################
    def on_redraw_timer(self, event):
        if self.live_checkbox.IsChecked(): #plot only if the live checkbox is checked
            self.flashingText.SetLabel('Pulling')
            client._connect()
            client._send('5')
            sleep(0.005)
            client._receive()
            client._server_close() 
            buffer.get_update(client.response_arg[2],client.response_arg[3])
            self._set_response(client.response_arg)
            self.draw(event)    
            self.flashingText.SetLabel('Ready')
        
    def smooth(self, y, step = 1): #this is a smoothing function that helps speed up plotting
        if step == 1:
            y_out = y
        else:
            y_out = np.zeros(len(y)/step)
            for i in range(len(y_out)):
                if i == 0:
                    y_out[i] = np.mean(y[0:int((1)*step)])
                elif i == len(y_out)-1:
                    y_out[i] = np.mean(y[int((i)*step):])
                else:
                    y_out[i] = np.mean(y[int((i)*step):int((i+1)*step)])    
        return y_out
    
    def draw(self,event):
        #print(self.time_range,self.frequency)
        x = self.smooth(np.arange(-self.time_range/self.frequency, 0, 1.0/self.frequency),self.smooth_factor)
        
        self.axes0.cla()
        self.axes1.cla()
        self.axes2.cla()
        self.axes3.cla()

        
        plot_from = buffer.pointerC-self.time_range
        plot_to = buffer.pointerC

        if buffer.pointerC>self.time_range:
            y1 =  self.smooth(((buffer.buffer[0,plot_from:plot_to]-8192.))*(5.0/2**13)/self.calib[0],self.smooth_factor)
            y2 =  self.smooth(((buffer.buffer[1,plot_from:plot_to]-8192.))*(5.0/2**13)/self.calib[1],self.smooth_factor)
            y3 =  self.smooth(((108.364-88.0461)/2.0**13)*(buffer.buffer[2,plot_from:plot_to]-2.0**13)+88.0461+0.2,self.smooth_factor)
            y4 =  self.smooth((buffer.buffer[3,plot_from:plot_to]-8192.)*0.036621+100. + self.calib[3],self.smooth_factor)
   
        else: 
            y = np.concatenate((buffer.buffer[0,plot_from:],buffer.buffer[0,0:plot_to]))
            y1 = self.smooth(((y-8192.)/8192.)*(5.0/2**13)/self.calib[0],self.smooth_factor)
            y = np.concatenate((buffer.buffer[1,plot_from:],buffer.buffer[1,0:plot_to]))
            y2 = self.smooth(((y-8192.)/8192.)*(5.0/2**13)/self.calib[0],self.smooth_factor)
            y = np.concatenate((buffer.buffer[2,plot_from:],buffer.buffer[2,0:plot_to]))
            y3 = self.smooth(((108.364-88.0461)/2.0**13)*(y-2.0**13)+88.0461+0.2,self.smooth_factor)
            y = np.concatenate((buffer.buffer[3,plot_from:],buffer.buffer[3,0:plot_to]))
            y4 = self.smooth((y-8192.)*0.036621+100. + self.calib[3],self.smooth_factor)
        from numpy import nan
        for i in range(len(y1)):
            if y1[i] == 0:
                y1[i] = nan
            if y2[i] == 0:
                y2[i] = nan
            if y3[i] == 0:
                y4[i] = nan
            if y4[i] == 0:
                y4[i] = nan
            
        
        try:
            self.axes0.plot(x,y1,'-b', label = 'Upstream')
            self.axes1.plot(x,y2,'-g', label = 'Downstream')
            self.axes2.plot(x,y3,'-r')
            self.axes3.plot(x,y4,'-r')

            self.axes0.set_title('Pressure upstream')
            self.axes1.set_title('Pressure downstream')
            self.axes2.set_title('Pressure barometric')
            self.axes3.set_title('Temperature')
            self.axes3.set_xlabel("time, seconds")

            self.axes0.set_xticklabels([])
            self.axes1.set_xticklabels([])
            self.axes2.set_xticklabels([])
            
            self.axes0.set_xlim([np.min(x),np.max(x)])
            self.axes1.set_xlim([np.min(x),np.max(x)])
            self.axes2.set_xlim([np.min(x),np.max(x)])
            self.axes3.set_xlim([np.min(x),np.max(x)])
        except:
            error(traceback.format_exc())
            
        try:
            self.axes0.set_ylim([np.nanmin(y1)-np.nanabs(np.nanmin(y1))*0.02,np.nanmax(y1)+np.nanabs(np.nanmax(y1))*0.02])
            self.axes1.set_ylim([np.nanmin(y2)-np.nanabs(np.nanmin(y2))*0.02,np.nanmax(y2)+np.nanabs(np.nanmax(y2))*0.02])
            self.axes2.set_ylim([np.nanmin(y3)-np.nanabs(np.nanmin(y3))*0.02,np.nanmax(y3)+np.nanabs(np.nanmax(y3))*0.02])
            self.axes3.set_ylim([np.nanmin(y4)-np.nanabs(np.nanmin(y4))*0.02,np.nanmax(y4)+np.nanabs(np.nanmax(y4))*0.02])
        except Exception,e:
            error(traceback.format_exc())
            
        self.axes0.grid()
        self.axes1.grid()
        self.axes2.grid()
        self.axes3.grid()

        divider = 5 #this is a tick divider, meaning how many ticks we have in plots. 5 tick = 6 div is a good choice
        step = (np.max(x)-np.min(x))/divider
        range_lst = []
        for i in range(divider+1):
            range_lst.append(np.min(x)+step*i)
        label_lst = []

        if self.time_choice.GetSelection() == 0 or self.time_choice.GetSelection() == 1 or self.time_choice.GetSelection() == 2 or self.time_choice.GetSelection() == 3:
            time_format = '%M:%S'
        elif self.time_choice.GetSelection() == 4 or self.time_choice.GetSelection() == 5 or self.time_choice.GetSelection() == 6:
            time_format = '%H:%M'    
        else: 
            time_format = '%H:%M:%S'   
        for i in range(len(range_lst)-1):
            label_lst.append(strftime(time_format, localtime(self.local_time+range_lst[i])))
        i=i+1    
        label_lst.append(strftime('%H:%M:%S' , localtime(self.local_time+range_lst[i])))

            
        self.axes3.set_xticklabels(label_lst)
        self.axes0.set_xticks(range_lst)
        self.axes1.set_xticks(range_lst)
        self.axes2.set_xticks(range_lst)
        self.axes3.set_xticks(range_lst)
        self.axes3.set_xlabel("local time")

        

        self.canvas.Refresh()
        self.canvas.Update()
        self.canvas.draw()
        
        
    
        
        
# Run the main program
if __name__ == "__main__":
    logging.basicConfig(filename = gettempdir()+'/di_245_client.log',
                        level=logging.DEBUG,
                        format="%(asctime)s %(levelname)s: %(message)s")
        
    #Create an instance with a ring buffer
    buffer = CircularBuffer(size = (4,10000))#4320000))
    
    #start the socket
    client = ClientSocket()
    
    #Create the GUI frane and show it
    app = wx.App()
    frame = ClientGUI()
    frame.Show()
    
    #Start main GUI loop
    #app.MainLoop()   
