#!/bin/env python
"""
CA Strip Chart
by Valentyn Stadnytskyi and Friedrich Shotte
23 May 2018 - Oct 26 2018
last updated: March 18 2019

The strip chart interacts with Channel Archiver to receive all archived data.
After the data is received, it uses channel access to update its' circular buffers.

2.0.2 -
3.0.0 - the code is competable with python 2.7 and 3.7
3.0.1 - fixed competability with wxPython 3 and 4
"""

__version__ = "3.0.1"


from optparse import OptionParser
from time import time, sleep,localtime,strftime,clock

import numpy as np
import sys
from struct import unpack
import wx
#import StringIO
from pdb import pm
import traceback

import PIL
import io

import matplotlib
matplotlib.use('WxAgg')
##import matplotlib.pyplot as plt
##from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FCW
##from matplotlib.figure import Figure
#SMALL_SIZE = 8
#matplotlib.rc('font', size=SMALL_SIZE)
#matplotlib.rc('axes', titlesize=SMALL_SIZE)

from logging import error,warn,info,debug
if sys.version_info[0] ==3:
    #from persistent_property3 import persistent_property #Python 3.7 competable library
    from _thread import start_new_thread #Python 3.7 competable library
else:
    #from persistent_property import persistent_property
    from thread import start_new_thread
    import autoreload
    
from persistent_property3 import persistent_property 

class ClientGUI(wx.Frame):

    def __init__(self):
        self.create_GUI()

    def create_GUI(self):
    #This function creates buttons with defined position and connects(binds) them with events that
        #This function creates buttons with defined position and connects(binds) them with events that

        #####Global start variable####
        self.local_time = time()
        self.draw_flag = True
        self.smooth_factor = 1
        self.redraw_timer_value = 400.0

        self.frequency = 1 #this is actually frequency, not time
        self.time_list = [10*self.frequency,30*self.frequency,60*self.frequency,60*2*self.frequency,60*5*self.frequency,
                          60*10*self.frequency,60*30*self.frequency,60*60*self.frequency,
                          60*2*60*self.frequency,60*6*60*self.frequency,60*12*60*self.frequency,60*24*60*self.frequency]



        self.time_range = 60

        self.txt_font_size = 10
        self.arg2 = 10

        self.environment = 0 #APS is 0, NIH is 1; localhost is 2
        self.DicObjects = {} #this is a dictionary with all different objects in GUI

        ##Create Frame ans assign panel
        frame = wx.Frame.__init__(self, None, wx.ID_ANY, "CA Strip Chart", pos = (0,0))

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


        aboutMenu = wx.Menu()
        about_item[0]= aboutMenu.Append(wx.ID_ANY,  'About')
        self.Bind(wx.EVT_MENU, self._on_client_about, about_item[0])


        menubar.Append(fileMenu, '&File')

        menubar.Append(aboutMenu, '&About')


        self.SetMenuBar(menubar)



        self.Centre()
        self.Show(True)
        ###########################################################################
        ###MENU ENDS###
        ###########################################################################


        sizer = wx.GridBagSizer(5, 1)

        self.live_checkbox = wx.CheckBox(self.panel, id=wx.ID_ANY, label="Live", style=0, validator=wx.DefaultValidator, name='LiveCheckBoxNameStr')
        sizer.Add( self.live_checkbox, pos=(0, 0), flag=wx.TOP|wx.LEFT, border=5)
        self.live_checkbox.SetValue(False)
        self.live_checkbox.Enable()

        text5 = wx.StaticText(self.panel, label="time")
        sizer.Add(text5, pos=(0, 1), flag=wx.TOP|wx.LEFT, border=5)
        self.time_dropdown_list = ['10 s','30 s', '1 min', '2 min', '5 min' , '10 min' , '30 min','1 hr','2 hr','6 hr', '12 hr', '24 hr']#, 'max']
        self.time_choice = wx.Choice(self.panel,choices = self.time_dropdown_list)
        sizer.Add(self.time_choice, pos=(0,2), span = (1,1), flag=wx.LEFT|wx.TOP, border=5)
        self.time_choice.Bind(wx.EVT_CHOICE, self._on_change_time_press)
        self.time_choice.SetSelection(1)

        self.PV_names = ['NIH:TEMP.RBV',
                         'NIH:TEMP.VAL',
                         'NIH:SAMPLE_FROZEN_OPT_RGB.MEAN',
                         'NIH:CHILLER.RBV',
                         'NIH:CHILLER.VAL',
                         'NIH:SAMPLE_FROZEN_OPT_RGB.STDEV',
                         'NIH:SAMPLE_FROZEN_OPT2.MEAN',
                         'NIH:TEMP.I',
                         'NIH:TEMP.P',
                         'NIH:CHILLER.fault_code',
                         'NIH:Pressure_Upstream',
                         'NIH:Pressure_Downstream',
                         'NIH:OASIS_DL.RBV',
                         'NIH:OASIS_DL.VAL',
                         'NIH:OASIS_DL.FLT',
                         'NIH:SAMPLE_FROZEN_OPTICAL.MEAN',
                         'NIH:SAMPLE_FROZEN_OPTICAL2.MEAN',
                         'NIH:SAMPLE_FROZEN_OPTICAL.STDEV',
                         'NIH:SAMPLE_FROZEN_XRAY.SPOTS',
                         ]
        self.PV_choice = wx.Choice(self.panel,choices = self.PV_names)
        sizer.Add(self.PV_choice, pos=(1,0), span = (1,3), flag=wx.LEFT|wx.TOP, border=5)
        self.PV_choice.SetSelection(1)

        self.graph_number = ['0','1','2','3']
        self.graph_choice = wx.Choice(self.panel,choices = self.graph_number)
        sizer.Add(self.graph_choice, pos=(1,4), span = (1,1), flag=wx.LEFT|wx.TOP, border=5)
        self.graph_choice.Bind(wx.EVT_CHOICE, self._on_plotting_choice)
        self.graph_choice.SetSelection(1)





        self.live_checkbox.SetValue(False)
        sizer.AddGrowableCol(2)

        self.panel.SetSizer(sizer)

        self.bitmapfigure = wx.StaticBitmap(self.panel)#, bitmap=bmp1)

        sizer.Add(self.bitmapfigure, pos=(2,0), span=(8,6), flag = wx.EXPAND)#,
        debug('after add bitmapfigure')
        self.Centre()
        self.Show(True)
        self.panel.SetSizer(sizer)
        self.Layout()
        self.panel.Layout()
        #self.Fit()

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.redraw_timer.Start(self.redraw_timer_value)
        stripchart.draw()

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
        for i in range(len(stripchart)):
            i.kill
        self.Close()

    def _on_change_ip_press(self,event):
        info("Dropdown IP menu: selected %s , New IP address : %r" % (self.ip_dropdown_list[1][self.IP_choice.GetSelection()],self.ip_dropdown_list[0][self.IP_choice.GetSelection()]))
        client.ip_address_server =  self.ip_dropdown_list[0][self.IP_choice.GetSelection()]
        self.live_checkbox.SetValue(False)
        self.live_checkbox.Disable()

    def _on_plotting_choice(self,event):
        PV = self.PV_names[self.PV_choice.GetSelection()]
        graph = int(self.graph_number[self.graph_choice.GetSelection()])
        try:
            stripchart[graph].kill()
        except:
            error(traceback.format_exc())
        stripchart.replace(position = graph, PV = PV)
        if stripchart.stripchart[graph].running == False:
            stripchart.stripchart[graph].running = True

    def _on_change_time_press(self,event):
        self.time_list = [10,30,60,60*2,60*5,60*10,60*30,60*1*60,2*60*60,6*60*60,12*60*60,24*60*60]
        self.time_range =  self.time_list[self.time_choice.GetSelection()]
        info('self time_range selected %r' % (self.time_range))

        if self.time_range == 10:
            self.smooth_factor = 1
            self.redraw_timer.Start(self.redraw_timer_value)
        elif self.time_range == 30:
            self.smooth_factor = 1
            self.redraw_timer.Start(self.redraw_timer_value)
        elif self.time_range == 1*60:
            self.smooth_factor = 1
            self.redraw_timer.Start(self.redraw_timer_value*1.2)
        elif self.time_range == 2*60:
            self.smooth_factor = 1
            self.redraw_timer.Start(self.redraw_timer_value*5)
        elif self.time_range == 5*60:
            self.smooth_factor = 1
            self.redraw_timer.Start(self.redraw_timer_value*10)
        elif self.time_range == 10*60:
            self.smooth_factor = 1
            self.redraw_timer.Start(self.redraw_timer_value*10)
        elif self.time_range == 0.5*3600:
            self.smooth_factor = 1
            self.redraw_timer.Start(self.redraw_timer_value*20)
        else:
            self.smooth_factor = 1
            self.redraw_timer.Start(self.redraw_timer_value*20)
        stripchart.draw()

    def _on_command_list_select(self,event):

        info('commands from the list selected')



    def _set_response(self,response_arg):
        self.local_time = response_arg[1]
        self.DicObjects['server time'].SetLabel(strftime("%Y-%m-%d %H:%M:%S", localtime(self.local_time)))


    def method_result(self,method = 'window'):
        if method == 'window':
            self.DicObjects['result'].SetLabel(str(self.result))


    def _on_server_comm(self,event):
        pass

    def _on_save_file_press(self,event):
        #msgpack_packb([time(),], default=m.encode)
        np.savetxt('CA_strip_chart'+str(time())+stripchart.PV+'.csv',np.transpose(buffer.buffer), delimiter=',' , fmt='%1.4e')

    def mthd_buttons(self, event):
        """
        This method is an event handler. It cross refences the event Id and an Id stored in a dictionary to determine what to do.
        """
        self.live_checkbox.SetValue(True)
        self.live_checkbox.Enable()


#################################################################################
########### Plotting
#################################################################################
    def on_redraw_timer(self, event):
        debug('on_redraw_timer')
        
        if self.live_checkbox.IsChecked() and not stripchart.drawing: #plot only if the live checkbox is checked
            #start_new_thread(self.draw,(event,))
            start_new_thread(stripchart.draw,())
            #stripchart.draw()
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
        """
        shows the bitmap generated in the
        """
        def buf2wx (buf):
            import PIL
            image = PIL.Image.open(buf)
            width, height = image.size
            return wx.Bitmap.FromBuffer(width, height, image.tobytes())
        def buf2wx_3020(buf):
            import PIL
            image = PIL.Image.open(buf)
            width, height = image.size
            return wx.BitmapFromBuffer(width, height, image.tobytes())

##        try:
##                self.figurebuf1 = self.draw_figure1(self.dic_lst)
##            except:
##                error(traceback.format_exc())
##            try:
##                self.figurebuf2 = self.draw_figure2(self.dic_lst)
##            except:
##                error(traceback.format_exc())
        if wx.__version__[0] == '3':
            self.bitmapfigure.SetBitmap(buf2wx_3020(stripchart.figurebuf))
        elif wx.__version__[0] == '4':
            self.bitmapfigure.SetBitmap(buf2wx(stripchart.figurebuf))

        #self.bitmap1.SetPosition((0,0))
        #self.bitmap2.SetPosition((500,0))

        #self.Refresh()

        self.panel.Layout()
        self.panel.Fit()
        #self.panel.Refresh()
        self.Layout()
        self.Fit()


class StripChart(object):
    selected_CA_values = persistent_property('selected_CA_values', ['NIH:TEMP.RBV',
                                                                    'NIH:CHILLER.RBV',
                                                                    'NIH:TEMP.I',
                                                                    'NIH:SAMPLE_FROZEN_OPTICAL2.MEAN'])
    #selected_CA_values = persistent_property('selected_CA_values', ['','NIH:CHILLER.RBV','','NIH:SAMPLE_FROZEN_OPTICAL.MEAN'])
    class StripRecorder(object):
        def __init__(self,PV,buffersize = 120000):
            from circular_buffer_LL import server
            self.running = False
            if PV == 'NIH:TEMP.RBV':
                buffersize = 240000

            self.buffer = server(size = (2,buffersize), var_type = 'float64')
            from numpy import zeros, nan,asarray
            self.PV = PV
            self.arr = zeros((2,1)) + nan
            try:
                buff = asarray(self.get_data(PV,time()-3600*24,3600*24))
                self.buffer.append(buff)
            except:
                error(traceback.format_exc())
            if len(PV) != 0:
                self.start()
            self.drawing = False

        def start(self):
            #if sys.version_info[0] ==3:
            from CA3 import camonitor
            #else:
                #from CA import camonitor
            self.running = True
            camonitor(self.PV,callback=self.callback)

        def callback(self,pvname,value,char_value):
            from time import time
            self.arr[0,0] = time()
            self.arr[1,0] = value
            self.buffer.append(self.arr)

        def get_data(self,PV,from_t,duration_t):
            if sys.version_info[0] ==3:
                from channel_archiver3 import channel_archiver
            else:
                from channel_archiver import channel_archiver
            from numpy import asarray
            print('uploading data from CA for PV = %r' % PV)
            return asarray(channel_archiver.history(PV,from_t,from_t+duration_t))

        def kill(self):
            del self

    def __init__(self):
        self.stripchart = ['','','','']

    def add(self,position,PV = 'NIH:TEMP.RBV' , buffersize = 240000):
        self.stripchart[position] = self.StripRecorder(PV = PV,buffersize = buffersize)
        self.selected_CA_values[position] = PV

    def replace(self,position = 0, PV = 'NIH:TEMP.RBV' , buffersize = 240000):
        self.stripchart[position] = self.StripRecorder(PV = PV,buffersize = buffersize)
        self.selected_CA_values[position] = PV

    def pop(self,position):
        try:
            self.stripchart[position].kill()
        except:
            info('nothing to kill')


    def chart(self,time_range = 60):
        from matplotlib.figure import Figure
        from matplotlib import pyplot, rc
        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FCW
        SMALL_SIZE = 8
        rc('font', size=SMALL_SIZE)
        rc('axes', titlesize=SMALL_SIZE)
        from numpy import searchsorted, nanargmin, nan

        dpi = 100
        figure = Figure(figsize=(4,6),dpi = dpi)#figure((4, 6), dpi=dpi)
        axes = []
        axes.append(figure.add_subplot(411))
        axes.append(figure.add_subplot(412))
        axes.append(figure.add_subplot(413))
        axes.append(figure.add_subplot(414))

        self.draw_flag = False

        local_time = time()
        buffer = []
        x = []
        y = []
        index = 0
        for sc in self.stripchart:
            buff = sc.buffer.buffer
            pointer = sc.buffer.pointer
            debug('buff = %r, pointer = %r' %(buff.shape,pointer))
            try:
                plot_from = nanargmin(abs(buff[0] - (local_time-time_range)))
            except Exception as err:
                error(err)
                plot_from = -1
                
            if plot_from is nan:
                plot_from = 0

            plot_to = pointer
            #print('PV: %r , plot_from %r, plot_to %r and time ranfe = %r' % (sc.PV,plot_from, plot_to, self.time_range))
            if pointer>plot_from:
                x.append(buff[0,plot_from:plot_to])
                y.append(buff[1,plot_from:plot_to])
            else:
                x.append(np.concatenate((buff[0,plot_from:],buff[0,0:plot_to])))
                y.append(np.concatenate((buff[1,plot_from:],buff[1,0:plot_to])))
                
        from numpy import log10

        for index in range(len(stripchart.stripchart)):
            axes[index].cla()
            if index == 3:
                axes[index].plot(x[index],y[index],'ob', markersize = 1)
                axes[3].set_yscale('log')
            else:
                axes[index].plot(x[index],y[index],'ob', markersize = 1)
            axes[index].set_title(stripchart.stripchart[index].PV)


        axes[3].set_xlabel("time, seconds")
        for index in range(len(stripchart.stripchart)):
            axes[index].set_xticklabels([])

##
        for index in range(len(stripchart.stripchart)):
            try:
                axes[index].set_xlim([local_time - time_range,local_time])
            except Exception as err:
                error(traceback.format_exc(err))

        for index in range(len(stripchart.stripchart)):
            axes[index].grid()

        divider = 5 #this is a tick divider, meaning how many ticks we have in plots. 5 tick = 6 div is a good choice
        step = (time_range)/divider
        range_lst = []
        for i in range(divider+1):
            range_lst.append(local_time-time_range+step*i)
        label_lst = []

##        if self.time_choice.GetSelection() == 0 or self.time_choice.GetSelection() == 1 or self.time_choice.GetSelection() == 2 or self.time_choice.GetSelection() == 3:
        time_format = '%H:%M:%S'
##        elif self.time_choice.GetSelection() == 4 or self.time_choice.GetSelection() == 5 or self.time_choice.GetSelection() == 6:
##            time_format = '%H:%M'
##        else:
##            time_format = '%H:%M:%S'
        for i in range(len(range_lst)-1):
            label_lst.append(strftime(time_format, localtime(range_lst[i])))
        i=i+1
        label_lst.append(strftime('%H:%M:%S' , localtime(range_lst[i])))
        from numpy import asarray

        for index in range(len(stripchart.stripchart)):
            axes[index].set_xticks(range_lst)
        axes[3].set_xticklabels(label_lst)
        axes[3].set_xlabel("local time")

        self.draw_flag = True

        figure.tight_layout()
        buf = io.BytesIO()
        debug('buf = %r' % buf)
        try:
            figure.savefig(buf, format='jpg')
        except:
            error(traceback.format_exc())
        buf.seek(0)
        return buf


    def draw(self):
        debug('draw called')
        self.drawing = True
        try:
            time_range =  frame.time_range
        except:
            time_range = 60.0
        self.figurebuf = self.chart(time_range = time_range)
        try:
            wx.CallAfter(frame.draw,(0,))
        except:
            error(traceback.format_exc())
        self.drawing = False


# Run the main program
if __name__ == "__main__":

    stripchart = StripChart()
    for i in range(4):
        PV = stripchart.selected_CA_values[i]
        stripchart.add(position = i, PV = PV , buffersize = 240000)

    #stripchart.append(StripChart(PV = 'NIH:TEMP.RBV' , buffersize = 5600))
    #stripchart.append(StripChart(PV = 'NIH:SAMPLE_FROZEN_OPT_RGB.MEAN_TOP' , buffersize = 1000))
    #stripchart.append(StripChart(PV = 'NIH:SAMPLE_FROZEN_OPT_RGB.MEAN_BOTTOM' , buffersize = 1000))
    #stripchart.append(StripChart(PV = 'NIH:SAMPLE_FROZEN_OPT_RGB.MEAN_DIFF' , buffersize = 1000))

    import logging
    from tempfile import gettempdir
    logging.basicConfig(filename=gettempdir()+'/CA_strip_chart.log',
                        level=logging.WARN, format="%(asctime)s %(levelname)s: %(message)s")
    #Create an instance with a ring buffer
    #start the socket
    #Create the GUI frane and show it
    app = wx.App(False)
    frame = ClientGUI()
    frame.Show()
    #Start main GUI loop
    app.MainLoop()
