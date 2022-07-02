import wx
import matplotlib.pyplot as plt
from epics import PV, caget# Get rid of caput?
from Alio_driver import alio
from epics.wx.wxlib import PVText, PVFloatCtrl, PVEnumChoice

__version__="0.3.0"

# Add help
# Add button to write values to FPGA. I wish!
# Fix ramp up distance of X and Y
# Shouldn't the step size include the accel/decel distance?
# Calc freqency.
# Set DG535 A to 0?
# Add button to select scanning mode. Grid/Zig zag (2Hz), Grid/line by line, Capilary
# Add option to select how many time points will be collected at each position?
# Add option to select how many shots per detector image
# Create tabs in the interface: Control and options. Move accel, settle to options. Add limit for stepping mode?
# Be able to scan in any direction.
# Define which laser is used? This will set limits on some parameters such as rep rate.
# Add status collecting
# Check log file
        
#def error(x,y,z):
#    """Test if a point is on the plane defined by the three primary points"""
#    a1=param.second_hole_x-param.first_hole_x
#    b1=param.second_hole_y-param.first_hole_y
#    c1=param.second_hole_z-param.first_hole_z
#    a2=param.third_hole_x-param.first_hole_x
#    b2=param.third_hole_y-param.first_hole_y
#    c2=param.third_hole_z-param.first_hole_z
#    a=b1*c2-b2*c1
#    b=a2*c1-a1*c2
#    c=a1*b2-b1*a2
#    d=(-a*param.first_hole_x-b*param.first_hole_y-c*param.first_hole_z)
#    #print "Should be zero if on the plane: %s" % (a*x+b*y+c*z+d)
#    return a*x+b*y+c*z+d
    
class AlioWindow(wx.Frame):
    def __init__(self):
        wx.Frame.__init__ (self,None,-1,"Alio PP")
        self.SetSize((640,400))
        cw=70 # Cell width
        
        main_page = wx.BoxSizer(wx.VERTICAL)

        self.laser=PVEnumChoice(self,pv='14IDB:ALIO_LASER',size=(200,-1))
        main_page.Add(self.laser)
        
        self.scan_type=PVEnumChoice(self,pv='14IDB:ALIO_SCAN_TYPE',size=(200,-1))
        self.scan_type.SetToolTip(wx.ToolTip('Flythru-single row: 1 image per row\nStepping-single row: 1 image per row\nScan1D_flythru: 1 image per point'))
        self.scan_type_current=PV(pvname='14IDB:ALIO_SCAN_TYPE',callback=self.update_type)
        main_page.Add(self.scan_type)
        
        grid_input_positions=wx.FlexGridSizer(3,7,0,0)
        self.input_positions=wx.Panel(self)                
        self.title=wx.StaticText(self.input_positions,-1," Beginning of first row (X,Y,Z) ")
        self.firstX=PVFloatCtrl(self.input_positions,pv='14IDB:ALIO_FIRST_HOLE_X',size=(cw,-1),act_on_losefocus=True)
        self.firstY=PVFloatCtrl(self.input_positions,pv='14IDB:ALIO_FIRST_HOLE_Y',size=(cw,-1),act_on_losefocus=True)
        self.firstZ=PVFloatCtrl(self.input_positions,pv='14IDB:ALIO_FIRST_HOLE_Z',size=(cw,-1),act_on_losefocus=True)
        self.units=wx.StaticText(self.input_positions,-1," mm ")
        button = wx.Button(self.input_positions,label="Save current",size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.define_first_save,button)
        button2 = wx.Button(self.input_positions,label="Go To",size=(80,-1))
        self.Bind (wx.EVT_BUTTON,self.define_first_goto,button2)
        grid_input_positions.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.firstX),(self.firstY),(self.firstZ),\
        (self.units,0,wx.ALIGN_CENTER_VERTICAL),(button),(button2)])
        
        self.title=wx.StaticText(self.input_positions,-1," End of first row (X,Y,Z) ")
        self.secondX=PVFloatCtrl(self.input_positions,pv='14IDB:ALIO_SECOND_HOLE_X',size=(cw,-1),act_on_losefocus=True)
        self.secondY=PVFloatCtrl(self.input_positions,pv='14IDB:ALIO_SECOND_HOLE_Y',size=(cw,-1),act_on_losefocus=True)
        self.secondZ=PVFloatCtrl(self.input_positions,pv='14IDB:ALIO_SECOND_HOLE_Z',size=(cw,-1),act_on_losefocus=True)
        self.units=wx.StaticText(self.input_positions,-1," mm ")
        button = wx.Button(self.input_positions,label="Save current",size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.define_second_save,button)
        button2 = wx.Button(self.input_positions,label="Go To",size=(80,-1))
        self.Bind (wx.EVT_BUTTON,self.define_second_goto,button2)
        grid_input_positions.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.secondX),(self.secondY),(self.secondZ),\
        (self.units,0,wx.ALIGN_CENTER_VERTICAL),(button),(button2)])
       
        self.title=wx.StaticText(self.input_positions,-1," End of last row (X,Y,Z) ")
        self.thirdX=PVFloatCtrl(self.input_positions,pv='14IDB:ALIO_THIRD_HOLE_X',size=(cw,-1),act_on_losefocus=True)
        self.thirdY=PVFloatCtrl(self.input_positions,pv='14IDB:ALIO_THIRD_HOLE_Y',size=(cw,-1),act_on_losefocus=True)
        self.thirdZ=PVFloatCtrl(self.input_positions,pv='14IDB:ALIO_THIRD_HOLE_Z',size=(cw,-1),act_on_losefocus=True)
        self.units=wx.StaticText(self.input_positions,-1," mm ")
        self.third_button_save = wx.Button(self.input_positions,label="Save current",size=(100,-1))
        self.Bind (wx.EVT_BUTTON,self.define_third_save,self.third_button_save)
        self.third_button_goto = wx.Button(self.input_positions,label="Go To",size=(80,-1))
        self.Bind (wx.EVT_BUTTON,self.define_third_goto,self.third_button_goto)
        grid_input_positions.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.thirdX),(self.thirdY),(self.thirdZ),\
        (self.units,0,wx.ALIGN_CENTER_VERTICAL),(self.third_button_save),(self.third_button_goto)])

        self.input_positions.SetSizer(grid_input_positions)
        self.input_positions.Fit()
        main_page.Add(self.input_positions)

        self.input_parameters=wx.Panel(self)
        
        grid_input_parameters=wx.FlexGridSizer(4,4,0,0)

        self.title=wx.StaticText(self.input_parameters,-1," Step size (Y,Z)")
        self.y_step_size=PVFloatCtrl(self.input_parameters,pv='14IDB:ALIO_Y_STEP_SIZE', size=(80,-1), act_on_losefocus=True)
        self.z_step_size=PVFloatCtrl(self.input_parameters,pv='14IDB:ALIO_Z_STEP_SIZE', size=(80,-1), act_on_losefocus=True)
        self.units=wx.StaticText(self.input_parameters,-1," mm ")
        grid_input_parameters.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.y_step_size),(self.z_step_size),(self.units,0,wx.ALIGN_CENTER_VERTICAL)])

        self.title=wx.StaticText(self.input_parameters,-1," Acceleration ")
        self.acceleration=PVFloatCtrl(self.input_parameters,pv='14IDB:ALIO_ACCELERATION',size=(80,-1),act_on_losefocus=True)
        self.units=wx.StaticText(self.input_parameters,-1," mm/s2 ")
        grid_input_parameters.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.acceleration),(self.units,0,wx.ALIGN_CENTER_VERTICAL),(0,0)])

        # Force this value to be an integer
        # Show what the frequency would be
        self.title=wx.StaticText(self.input_parameters,-1," Repetition Period (DT) ")
        self.title.SetToolTip(wx.ToolTip("X-ray repetition period. Inverse of frequency. Example: 48 is 20 Hz"))
        self.repetition_period=PVFloatCtrl(self.input_parameters,pv='14IDB:ALIO_REPETITION_PERIOD',size=(80,-1),act_on_losefocus=True)
        self.units=wx.StaticText(self.input_parameters,-1," ms clock cycles")
        grid_input_parameters.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.repetition_period),\
        (self.units,0,wx.ALIGN_CENTER_VERTICAL),(0,0)])
        
        self.title=wx.StaticText(self.input_parameters,-1," Period to settle at speed         ")
        self.title.SetToolTip(wx.ToolTip("Time, after ramp up, to allow the stage to stabilize before collecting data"))
        self.settle_period=PVFloatCtrl(self.input_parameters,pv='14IDB:ALIO_SETTLE_PERIOD',size=(80,-1),act_on_losefocus=True)
        #self.units=wx.StaticText(self,-1," ms clock cycles")
        grid_input_parameters.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.settle_period),(0,0),(0,0)])

        self.input_parameters.SetSizer(grid_input_parameters)
        self.input_parameters.Fit()
        main_page.Add(self.input_parameters)
        
        line=wx.StaticLine(self,style=wx.LI_HORIZONTAL)
        main_page.AddSpacer(10)
        main_page.Add(line,0,wx.GROW,5)
        main_page.AddSpacer(10)
        
        grid2=wx.FlexGridSizer(20,4,0,0)
        self.output=wx.Panel(self)
        #self.output=wx.CollapsiblePane(self,label='Details')
        #self.output=cp.GetPane()

        self.title=wx.StaticText(self.output,-1," Translation range (X, Y, Z) ")
        self.translate_x=PVText(self.output,pv='14IDB:ALIO_TRANSLATION_RANGE_X', size=(90,-1), auto_units=True)
        self.translate_y=PVText(self.output,pv='14IDB:ALIO_TRANSLATION_RANGE_Y',size=(90,-1), auto_units=True)
        self.translate_z=PVText(self.output,pv='14IDB:ALIO_TRANSLATION_RANGE_Z',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.translate_x),(self.translate_y),(self.translate_z)])

        self.title=wx.StaticText(self.output,-1," Rows")
        #self.title.SetToolTip(wx.ToolTip("Velecity at full speed. mm/s"))
        self.rows=PVText(self.output,pv='14IDB:ALIO_ROWS',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.rows),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Velocity at full speed")
        self.title.SetToolTip(wx.ToolTip("Velecity at full speed. mm/s"))
        self.velocity=PVText(self.output,pv='14IDB:ALIO_VELOCITY',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.velocity),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Acceleration time ")
        self.acceleration_time=PVText(self.output,pv='14IDB:ALIO_ACCELERATION_TIME',size=(90,-1), auto_units=True)
        #self.acceleration_time=PVStaticText(self.output,pv='14IDB:ALIO_ACCELERATION_TIME',size=(90,-1))
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.acceleration_time),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Acceleration distance ")
        self.acceleration_distance=PVText(self.output,pv='14IDB:ALIO_ACCELERATION_DISTANCE',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.acceleration_distance),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Settling time at speed ")
        self.settling_time_at_speed=PVText(self.output,pv='14IDB:ALIO_SETTLING_TIME_AT_SPEED',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.settling_time_at_speed),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Settling distance at speed ")
        self.settling_distance_at_speed=PVText(self.output,pv='14IDB:ALIO_SETTLING_DISTANCE_AT_SPEED',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.settling_distance_at_speed),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Time to first X-ray pulse (t0) ")
        self.time_to_first_xray_pulse=PVText(self.output,pv='14IDB:ALIO_TIME_TO_FIRST_XRAY_PULSE',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.time_to_first_xray_pulse),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Number of data points (N)")
        self.number_of_data_points=PVText(self.output,pv='14IDB:ALIO_NUMBER_OF_DATA_POINTS',size=(90,-1),auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.number_of_data_points),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Distance of actual data collection ")
        self.distance_of_actual_data_collection=PVText(self.output,pv='14IDB:ALIO_DISTANCE_OF_ACTUAL_DATA_COLLECTION',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.distance_of_actual_data_collection),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Total distance of translation ")
        self.total_distance_of_translation=PVText(self.output,pv='14IDB:ALIO_TOTAL_DISTANCE_OF_TRANSLATION',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.total_distance_of_translation),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Time to reach half the return distance ")
        self.time_to_reach_half_the_return_distance=PVText(self.output,pv='14IDB:ALIO_TIME_TO_REACH_HALF_THE_RETURN_DISTANCE',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.time_to_reach_half_the_return_distance),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Max velocity on return ")
        self.max_velocity_on_return=PVText(self.output,pv='14IDB:ALIO_MAX_VELOCITY_ON_RETURN',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.max_velocity_on_return),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Total time to return ")
        self.total_time_to_return=PVText(self.output,pv='14IDB:ALIO_TOTAL_TIME_TO_RETURN',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.total_time_to_return),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Total time of translation ")
        self.total_time_of_translation=PVText(self.output,pv='14IDB:ALIO_TOTAL_TIME_OF_TRANSLATION',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.total_time_of_translation),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Full cycle clock ticks ")
        self.full_cycle_clock_ticks=PVText(self.output,pv='14IDB:ALIO_FULL_CYCLE_CLOCK_TICKS',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.full_cycle_clock_ticks),(0,0),(0,0)])

        self.title=wx.StaticText(self.output,-1," Measure length (period) ")
        self.measure_length=PVText(self.output,pv='14IDB:ALIO_MEASURE_LENGTH',size=(90,-1), auto_units=True)
        grid2.AddMany([(self.title,0,wx.ALIGN_CENTER_VERTICAL),(self.measure_length),(0,0),(0,0)])

        self.output.SetSizer(grid2)
        self.output.Fit()
        main_page.Add(self.output)

        self.error_message=PVText(self,pv='14IDB:ALIO_ERROR_MESSAGE',size=(90,-1))
        main_page.Add(self.error_message)

        line=wx.StaticLine(self,style=wx.LI_HORIZONTAL)
        main_page.AddSpacer(10)
        main_page.Add(line,0,wx.GROW,5)
        main_page.AddSpacer(10)
        
        self.title=wx.StaticText(self,-1,"      FPGA parameters and Status ")
        self.title.SetFont(wx.Font(wx.DEFAULT,wx.DEFAULT,wx.NORMAL,wx.BOLD))
        self.title.SetToolTip(wx.ToolTip("The parameters need to be input into the FPGA panels."))
        main_page.Add(self.title)

        self.pp_mode_panel=wx.Panel(self)
        grid3=wx.FlexGridSizer(2,5,0,5)
        
        self.t1=wx.StaticText(self.pp_mode_panel,-1," Parameters for PP Mode: ")
        self.t2=wx.StaticText(self.pp_mode_panel,-1,"period")
        self.t3=wx.StaticText(self.pp_mode_panel,-1,"N")
        self.t4=wx.StaticText(self.pp_mode_panel,-1,"DT")
        self.t5=wx.StaticText(self.pp_mode_panel,-1,"t0")
        grid3.AddMany([(self.t1),(self.t2),(self.t3,1,wx.ALIGN_CENTER_HORIZONTAL),(self.t4),(self.t5)])
        
        self.pv1=PVText(self.pp_mode_panel,pv='14IDB:ALIO_MEASURE_LENGTH',size=(50,-1))
        self.pv2=PVText(self.pp_mode_panel,pv='14IDB:ALIO_NUMBER_OF_DATA_POINTS',size=(50,-1))
        self.pv3=PVText(self.pp_mode_panel,pv='14IDB:ALIO_REPETITION_PERIOD',size=(50,-1))
        self.pv4=PVText(self.pp_mode_panel,pv='14IDB:ALIO_TIME_TO_FIRST_XRAY_PULSE',size=(50,-1))
        grid3.AddMany([(0,0),(self.pv1),(self.pv2,1,wx.ALIGN_CENTER_HORIZONTAL),(self.pv3),(self.pv4)])
        
        self.pp_mode_panel.SetSizer(grid3)

        self.pp_mode_panel.Fit()
        main_page.Add(self.pp_mode_panel)

        line=wx.BoxSizer(wx.HORIZONTAL)
        self.title=wx.StaticText(self,-1," Current Status of FPGA: ")
        line.Add(self.title)
        self.status=PVText(self,pv='14IDB:ALIO_STATUS',size=(100,-1))
        line.Add(self.status)
        main_page.Add(line)

        line=wx.StaticLine(self,style=wx.LI_HORIZONTAL)
        main_page.AddSpacer(10)
        main_page.Add(line,0,wx.GROW,5)
        main_page.AddSpacer(10)

        self.buttons=wx.Panel(self)
        #self.button_alio = wx.Button(self.buttons,label="Send to Alio",size=(100,25),pos=(5,-1))
        #self.Bind (wx.EVT_BUTTON,self.send_to_alio,self.button_alio)
        #self.button2 = wx.Button(self.buttons,label="Send to FPGA",size=(100,25),pos=(100,-1))
        #self.Bind (wx.EVT_BUTTON,self.send_to_fpga,self.button2)
        self.button_alio_enable = wx.Button(self.buttons,label="Enable Alio",size=(100,25),pos=(200,-1))
        self.Bind (wx.EVT_BUTTON,self.enable_alio,self.button_alio_enable)
        self.button_alio_disable = wx.Button(self.buttons,label="Disable Alio",size=(100,25),pos=(300,-1))
        self.Bind (wx.EVT_BUTTON,self.disable_alio,self.button_alio_disable)
        self.button_plot_motion = wx.Button(self.buttons,label="Plot motion",size=(100,25),pos=(500,-1))
        self.Bind (wx.EVT_BUTTON,self.plot_motion,self.button_plot_motion)
        main_page.Add(self.buttons)

        self.SetSizer(main_page)
        self.Fit()
        
        self.update_type()
        
        self.timer=wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.OnTimer)
        self.OnTimer()
        self.Show()      

    # Get rid of timer. Just using it for now to test GetValue
    def OnTimer(self,event=None):
        #self.step_size.put()
        #print(self.firstX.GetValue())
        self.timer.Start(1000,oneShot=True)

    def define_first_save(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""        
        self.firstX.SetValue(str(round(alio.x,3)))
        self.firstY.SetValue(str(round(alio.y,3)))
        self.firstZ.SetValue(str(round(alio.z,3)))

    def define_first_goto(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""        
        alio.x = self.firstX.GetValue()
        alio.y = self.firstY.GetValue()
        alio.z = self.firstZ.GetValue()

    def define_second_save(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""
        
        self.secondX.SetValue(str(round(alio.x,3)))
        self.secondY.SetValue(str(round(alio.y,3)))
        self.secondZ.SetValue(str(round(alio.z,3)))

    def define_second_goto(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""        
        alio.x = self.secondX.GetValue()
        alio.y = self.secondY.GetValue()
        alio.z = self.secondZ.GetValue()

    def define_third_save(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""        
        self.thirdX.SetValue(str(round(alio.x,3)))
        self.thirdY.SetValue(str(round(alio.y,3)))
        self.thirdZ.SetValue(str(round(alio.z,3)))

    def define_third_goto(self, event):
        """Reads the current position of GonX,GonY,GonZ as starting of
        translation"""        
        alio.x = self.thirdX.GetValue()
        alio.y = self.thirdY.GetValue()
        alio.z = self.thirdZ.GetValue()

#     def send_to_alio(self, event):
#         """Sends calculated values to Alio"""
        
#         alio.speed=param.velocity
#         alio.accel=param.acceleration_time*1000 # Needs to be converted to msec
#         alio.z_step_size=param.translate_z+param.acceleration_distance*2
#         alio.x_step_size=param.translate_x
#         alio.y_step_size=param.translate_y
#         alio.z_starting=param.first_hole_z-param.acceleration_distance
#         alio.x_starting=param.first_hole_x
#         alio.y_starting=param.first_hole_y
#         alio.steps_expected=param.continuous
        
#         spx=param.first_hole_x
#         spy=param.first_hole_y
#         spz=param.first_hole_z-param.acceleration_distance
#         stx=param.translate_x
#         sty=param.translate_y
#         stz=param.translate_z+param.acceleration_distance*2
#         print("\nPrint parameters for grid scanning")
#         print("Starting: %s, %s, %s" % (spx,spy,spz))
#         print("Step size: %s, %s, %s" % (stx,sty,stz))

#         rows=round((param.third_hole_y-param.second_hole_y)/param.step_size+1)
#         print(rows)
        
# #        try: Xshift_per_row=(grid.end[0]-grid.rowend[0])/(rows-1) # Download
#         try: Xshift_per_row=(param.third_hole_x-param.second_hole_x)/(rows-1)
#         except: Xshift_per_row=0
#         try: Yshift_per_row=(param.third_hole_y-param.second_hole_y)/(rows-1)
#         except: Yshift_per_row=0
#         try: Zshift_per_row=(param.third_hole_z-param.second_hole_z)/(rows-1)
#         except: Zshift_per_row=0
        
#         print("Shifts per row: %s, %s, %s\n" % (Xshift_per_row,Yshift_per_row,Zshift_per_row))

#         dir=0
#         for i in range(0,int(round(rows))):
# #            a=spx+i*Xshift_per_row
# #            b=spy+i*Yshift_per_row
# #            c=spz+i*Zshift_per_row
#             if dir==0:
#                 a=spx+i*Xshift_per_row
#                 b=spy+i*Yshift_per_row
#                 c=spz+i*Zshift_per_row
#                 print("Row/Starting Position/Error: %s/%s, %s, %s, %s" % (i,a,b,c,error(a,b,c)))
#                 print("Row/Ending Position/Error: %s/%s, %s, %s, %s" % (i,a+stx,b+sty,c+stz,error(a+stx,b+sty,c+stz)))
#                 print("")
#                 dir=1
#             elif dir==1:
#                 a=spx+i*Xshift_per_row+stx
#                 b=spy+i*Yshift_per_row+sty
#                 c=spz+i*Zshift_per_row+stz
#                 print("Row/Starting Position/Error: %s/%s, %s, %s, %s" % (i,a,b,c,error(a,b,c)))
#                 print("Row/Ending Position/Error: %s/%s, %s, %s, %s" % (i,a-stx,b-sty,c-stz,error(a-stx,b-sty,c-stz)))
#                 print("")
#                 dir=0
                  
    def send_to_fpga(self, event):
        """Sends calculated values to FPGA"""

        pass        

    def enable_alio(self, event):
        """Sets the mode on the Alio. Enables Alio to accept triggers. 
        Sets P250=1 for now but should be set to whatever value is necessary 
        for that particular scan"""
        alio.mode=1

    def disable_alio(self, event):
        """Sets the mode on the Alio. Disables Alio to accept triggers. 
        Sets P250=0."""
        alio.mode=0

    def plot_motion(self, event):
        """This is only for a simple capillary type motion"""
        ad=caget('14IDB:ALIO_ACCELERATION_DISTANCE')
        sdap=caget('14IDB:ALIO_SETTLING_DISTANCE_AT_SPEED')
        v=caget('14IDB:ALIO_VELOCITY')
        doadc=caget('14IDB:ALIO_DISTANCE_OF_ACTUAL_DATA_COLLECTION')
        rv=caget('14IDB:ALIO_MAX_VELOCITY_ON_RETURN')
        # #plt.plot([0,ad,ad+sdap,ad+sdap+ad],[0,v,v,0],color='g')
        plt.plot([0,ad],[0,v],'r', label='Acceleration')
        plt.plot([ad,ad+sdap],[v,v],'b', label='Settling time')
        plt.plot([ad+sdap,ad+sdap+doadc],[v,v],'g',label='Actual data collection')
        plt.plot([ad+sdap+doadc,ad+sdap+doadc+ad],[v,0],'c',label='Deceleration')
        plt.plot([ad+sdap+doadc+ad,(ad+sdap+doadc+ad)/2],[0,-rv],'k',label='Return acceleration')
        plt.plot([(ad+sdap+doadc+ad)/2,0],[-rv,0],'k',label='Return deceleration')
        plt.title('Capillary Motion Profile')
        plt.xlabel('Z motion (mm)')
        plt.ylabel('Velocity (mm/s)')
        plt.legend(loc='best',fontsize='x-small')
        plt.show()       
                
        # I don't think this is doing anything. Need to fix
        # a=round(param.number_of_data_points,10)
        # if a.is_integer():
        #     self.number_of_data_points.SetForegroundColour(wx.NullColour)
        # else:
        #     self.number_of_data_points.SetForegroundColour(wx.RED)
        #     #print param.number_of_data_points
            
    def update_type(self, pvname=None, value=None, **kw):
        if value==1 or value==2:
            self.thirdX.Disable()
            self.thirdY.Disable()
            self.thirdZ.Disable()
            self.third_button_save.Disable()
            self.third_button_goto.Disable()
            self.rows.Disable()
        elif value==3 or value==4:
            self.thirdX.Enable()
            self.thirdY.Enable()
            self.thirdZ.Enable()
            self.third_button_save.Enable()
            self.third_button_goto.Enable()            
            self.rows.Enable()
        else:
            self.thirdX.Enable()
            self.thirdY.Enable()
            self.thirdZ.Enable()
            self.third_button_save.Enable()
            self.third_button_goto.Enable()
            self.rows.Disable()

def Alio_PP():
    global win
    wx.app = wx.App(redirect=False)
    win = AlioWindow()
    wx.app.MainLoop()
    
if __name__ == '__main__':
    #P250.value="0" # Tell ALIO to not accept triggers.
    Alio_PP()
