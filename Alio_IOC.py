# -*- coding: utf-8 -*-
"""
Caproto IOC for the ALIO

Using python 3.7
"""
# Check accleration calcs for ALIO

from caproto.server import pvproperty, PVGroup, ioc_arg_parser, run
from textwrap import dedent
from caproto import ChannelType, AlarmSeverity
from logging import error,warn # for debugging, removed info
import math,time
from Alio_driver import alio

kHz_clock=1.01268992539 # ms (DT)

class param: "Container for data collection parameters"
param.first_hole_x = 0
param.first_hole_y = 0
param.first_hole_z = 0
param.second_hole_x = 0
param.second_hole_y = 0
param.second_hole_z = 0
param.third_hole_x = 0
param.third_hole_y = 0
param.third_hole_z = 0
param.y_step_size = 0.2 # mm
param.z_step_size = 0.2 # mm
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
param.scan_type = 0
param.laser = 'Xray only'
param.rows = 1

class options: " "

class errors: " "
errors.number_of_data_points = ""
errors.rows = ""

def save_settings():
    f = open('alio_ioc_settings.py', 'w')
    for obj in param,options:
        for name in dir(obj):
            if name.startswith("__"):continue
            line = "%s.%s = %r\n" % (obj.__name__,name,getattr(obj,name))
            line = line.replace("-1.#IND","nan") # Needed for Windows Python
            line = line.replace("1.#INF","inf") # Needed for Windows Python
            f.write(line)

def load_settings():
    """Reload last saved parameters."""
    try:
        for line in open('alio_ioc_settings.py').readlines():
            try: exec(line)
            except: warn("ignoring line %r in settings" % line)
    except: print("No settings file!!!")

load_settings()   

def calculate_parameters():
    if param.scan_type == 'No translation':
        param.translate_x=0
        param.translate_y=0
        param.translate_z=0
    
        param.rows=0
        try: 
            param.velocity=0
        except: print("Velocity calc error") #Should put an error in the log file.    
        param.acceleration_time=0
        param.acceleration_distance=0
        param.settling_time_at_speed=0
        param.settling_distance_at_speed=0
        param.time_to_first_xray_pulse =0
     
        try: param.number_of_data_points = 0
        except ZeroDivisionError as e: print("Number of data points error: %s" % e)
        param.distance_of_actual_data_collection = 0
        param.total_distance_of_translation=0
        param.time_to_reach_half_the_return_distance=0
        param.max_velocity_on_return=0
        param.total_time_to_return=0
        try: param.total_time_of_translation=0
        except ZeroDivisionError: pass
        param.full_cycle_clock_ticks=0
        param.measure_length=0
    elif param.scan_type == 'Flythru-single row':
        param.translate_x=param.second_hole_x-param.first_hole_x
        param.translate_y=param.second_hole_y-param.first_hole_y
        param.translate_z=param.second_hole_z-param.first_hole_z
    
        param.rows=(param.third_hole_y-param.second_hole_y)/param.z_step_size
        try: 
            param.velocity=param.z_step_size/(param.repetition_period*kHz_clock)*1000
        except: print("Velocity calc error") #Should put an error in the log file.    
        param.acceleration_time=param.velocity/param.acceleration
        param.acceleration_distance=param.acceleration*param.acceleration_time**2 / 2
        param.settling_time_at_speed=param.settle_period*param.repetition_period*kHz_clock/1000
        param.settling_distance_at_speed=param.settling_time_at_speed*param.velocity
        time_to_first_xray_pulse_initial=param.acceleration_time+param.settling_time_at_speed
        time_to_first_xray_pulse_divided_by_12=time_to_first_xray_pulse_initial*1000/12
        time_to_first_xray_pulse_rounded_up=math.ceil(float(time_to_first_xray_pulse_divided_by_12))
        param.time_to_first_xray_pulse =time_to_first_xray_pulse_rounded_up*12
     
        distance_of_actual_data_collection_initial=param.translate_z-param.settling_distance_at_speed
        # We might be able to remove this -1. I think this was to be safe so that we were not collecting during the deceleration
        #try: param.number_of_data_points = (distance_of_actual_data_collection_initial/param.velocity)/(param.repetition_period*kHz_clock/1000)-1
        try: param.number_of_data_points = (distance_of_actual_data_collection_initial/param.velocity)/(param.repetition_period*kHz_clock/1000)+1
        except ZeroDivisionError as e: print("Number of data points error: %s" % e)
        param.distance_of_actual_data_collection = (param.number_of_data_points-1)*param.repetition_period*kHz_clock*param.velocity/1000
        param.total_distance_of_translation=param.translate_z+2*param.acceleration_distance
        #print(param.total_distance_of_translation,param.acceleration)
        param.time_to_reach_half_the_return_distance=math.sqrt(param.total_distance_of_translation/param.acceleration)
        param.max_velocity_on_return=param.acceleration*param.time_to_reach_half_the_return_distance
        param.total_time_to_return=param.time_to_reach_half_the_return_distance*2
        try: param.total_time_of_translation=param.acceleration_time*2+param.translate_z/param.velocity+param.total_time_to_return
        except ZeroDivisionError: pass
        #full_cycle_clock_ticks_initial=param.total_time_of_translation/(param.repetition_period*kHz_clock/1000)
        # Had trouble with the osc syncing at one point so I had to add in one more clock cycle. Seems to work now. Could make this an option.
        full_cycle_clock_ticks_initial=param.total_time_of_translation/(param.repetition_period*kHz_clock/1000)+1
        param.full_cycle_clock_ticks=math.ceil(full_cycle_clock_ticks_initial)
        param.measure_length=param.full_cycle_clock_ticks*param.repetition_period
    elif param.scan_type == 'Stepping-single row':
        param.translate_x=param.second_hole_x-param.first_hole_x
        param.translate_y=param.second_hole_y-param.first_hole_y
        param.translate_z=param.second_hole_z-param.first_hole_z    
        param.rows=(param.third_hole_y-param.second_hole_y)/param.y_step_size
        
        time_to_reach_half_the_step_size=math.sqrt(param.z_step_size/param.acceleration)
        param.velocity=param.acceleration*time_to_reach_half_the_step_size
        param.acceleration_time=param.velocity/param.acceleration
        param.acceleration_distance=param.acceleration*param.acceleration_time**2
        param.settling_time_at_speed=param.settle_period*param.repetition_period*kHz_clock/1000
        param.settling_distance_at_speed=param.settling_time_at_speed*param.velocity
        param.time_to_first_xray_pulse=param.repetition_period-12
        distance_of_actual_data_collection_initial=param.translate_z-param.settling_distance_at_speed
        param.number_of_data_points = param.translate_z/param.z_step_size+1        
        param.distance_of_actual_data_collection = param.translate_z
        param.total_distance_of_translation=param.translate_z+param.z_step_size
        param.time_to_reach_half_the_return_distance=math.sqrt(param.total_distance_of_translation/param.acceleration)
        param.max_velocity_on_return=param.acceleration*param.time_to_reach_half_the_return_distance
        param.total_time_to_return=param.time_to_reach_half_the_return_distance*2
        try: param.total_time_of_translation=param.acceleration_time*2+param.translate_z/param.velocity+param.total_time_to_return
        except ZeroDivisionError: pass
        #full_cycle_clock_ticks_initial=param.total_time_of_translation/(param.repetition_period*kHz_clock/1000)
        # Had trouble with the osc syncing at one point so I had to add in one more clock cycle. Seems to work now. Could make this an option.
        full_cycle_clock_ticks_initial=param.total_time_of_translation/(param.repetition_period*kHz_clock/1000)+1
        param.full_cycle_clock_ticks=math.ceil(full_cycle_clock_ticks_initial)
        param.measure_length=param.full_cycle_clock_ticks*param.repetition_period


    save_settings()

def send_to_alio():
    """Sends calculated values to Alio"""

    if param.scan_type=='Flythru-single row':
        alio.speed=param.velocity
        alio.accel=param.acceleration_time*1000 # Needs to be converted to msec
        alio.z_step_size=param.translate_z+param.acceleration_distance*2
        alio.x_step_size=param.translate_x
        alio.y_step_size=param.translate_y
        alio.z_starting=param.first_hole_z-param.acceleration_distance
        alio.x_starting=param.first_hole_x
        alio.y_starting=param.first_hole_y
        alio.steps_expected=1
    elif param.scan_type=='Stepping-single row':
        alio.speed=100
        alio.accel=10
        alio.z_step_size=param.z_step_size
        alio.x_step_size=param.translate_x/param.number_of_data_points
        alio.y_step_size=param.translate_y/param.number_of_data_points
        alio.z_starting=param.first_hole_z
        alio.x_starting=param.first_hole_x
        alio.y_starting=param.first_hole_y
        alio.steps_expected=round(param.number_of_data_points,4)
    else:
        print("Not a valid scan type")
        
        
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

def starting_position():
    try:
        time_z=param.translate_z/param.velocity
        vel_x=param.translate_x/time_z
        dis_x=vel_x*param.acceleration_time
        vel_y=param.translate_y/time_z
        dis_y=vel_y*param.acceleration_time
        print(dis_x, param.first_hole_x-dis_x, dis_y, param.first_hole_y-dis_y,param.first_hole_z-param.acceleration_distance)
        alio.x=(param.first_hole_x-dis_x)
        alio.y=(param.first_hole_y-dis_y)
        alio.z=(param.first_hole_z-param.acceleration_distance)
    except: print("Velocity Error")

    while not alio.in_position(): time.sleep(0.1)

class ALIO_IOC(PVGroup):
    """
    Alio IOC
    """
    # modes = [
    #     'scan1D_flythru',
    #     'flythru-48-100',
    # ]
    async def CMD(self, instance, value):
        #if value in self.modes:
        print(value.lower(),value.lower() in param.scan_type.lower())
        if value.lower() in param.scan_type.lower():
            ''' Currently just checks if scan type is similar. Flythru vs flythru
                Could check number of data points if needed '''
        # May want to add an option in GUI so that this mode can be confirmed
            # Could force a recalculation just in case something is wrong
            await self.points(value)
            await ioc.CMD_RBV.write(value)
            print(str(value))
        else:
            await ioc.CMD_RBV.write('')
            print("Does not match scan type")

    async def ACQ(self, instance, value):
        if value==1:
            send_to_alio()
            starting_position()
            alio.mode=1 # Enable XYZ scanning with triggers
            await ioc.ACQ_RBV.write(value)
        if value==0:
            #Stop Alio motion
            alio.mode=0 # Disable
            await ioc.ACQ_RBV.write(0)
                        
#    async def PTS(self, instance):
#        return self.points()
        
    async def update2(self, instance, value):
        #print(instance.pvspec.attr,instance.pvspec.attr[5:].lower(),value)
        temp="param.%s = %s" % (instance.pvspec.attr[5:].lower(),value)
        #print(temp)
        exec(temp)
        save_settings()
        calculate_parameters() # Does this wait to return
        await ioc.ALIO_TRANSLATION_RANGE_X.write(param.translate_x)
        await ioc.ALIO_TRANSLATION_RANGE_Y.write(param.translate_y)
        await ioc.ALIO_TRANSLATION_RANGE_Z.write(param.translate_z)
        await ioc.ALIO_ROWS.write(param.rows)
        await ioc.ALIO_VELOCITY.write(param.velocity)
        await ioc.ALIO_ACCELERATION_TIME.write(param.acceleration_time)
        await ioc.ALIO_ACCELERATION_DISTANCE.write(param.acceleration_distance)
        await ioc.ALIO_SETTLING_TIME_AT_SPEED.write(param.settling_distance_at_speed)                                      
        await ioc.ALIO_SETTLING_DISTANCE_AT_SPEED.write(param.settling_distance_at_speed)
        await ioc.ALIO_TIME_TO_FIRST_XRAY_PULSE.write(param.time_to_first_xray_pulse)
        await ioc.ALIO_NUMBER_OF_DATA_POINTS.write(param.number_of_data_points)
        await ioc.ALIO_DISTANCE_OF_ACTUAL_DATA_COLLECTION.write(param.distance_of_actual_data_collection)
        await ioc.ALIO_TOTAL_DISTANCE_OF_TRANSLATION.write(param.total_distance_of_translation)
        await ioc.ALIO_TIME_TO_REACH_HALF_THE_RETURN_DISTANCE.write(param.time_to_reach_half_the_return_distance)
        await ioc.ALIO_MAX_VELOCITY_ON_RETURN.write(param.max_velocity_on_return)
        await ioc.ALIO_TOTAL_TIME_TO_RETURN.write(param.total_time_to_return)
        await ioc.ALIO_TOTAL_TIME_OF_TRANSLATION.write(param.total_time_of_translation)
        await ioc.ALIO_FULL_CYCLE_CLOCK_TICKS.write(param.full_cycle_clock_ticks)
        await ioc.ALIO_MEASURE_LENGTH.write(param.measure_length)
        await ioc.ALIO_ERROR_CHECK.write('')
        
    async def scan_type(self, instance, value):
        """ 0: No translation. 1: single row continous."""
        param.scan_type=value
        save_settings()
        calculate_parameters()
        #print(param.scan_type)
        await ioc.ALIO_TRANSLATION_RANGE_X.write(param.translate_x)
        await ioc.ALIO_TRANSLATION_RANGE_Y.write(param.translate_y)
        await ioc.ALIO_TRANSLATION_RANGE_Z.write(param.translate_z)
        await ioc.ALIO_ROWS.write(param.rows)
        await ioc.ALIO_VELOCITY.write(param.velocity)
        await ioc.ALIO_ACCELERATION_TIME.write(param.acceleration_time)
        await ioc.ALIO_ACCELERATION_DISTANCE.write(param.acceleration_distance)
        await ioc.ALIO_SETTLING_TIME_AT_SPEED.write(param.settling_distance_at_speed)                                      
        await ioc.ALIO_SETTLING_DISTANCE_AT_SPEED.write(param.settling_distance_at_speed)
        await ioc.ALIO_TIME_TO_FIRST_XRAY_PULSE.write(param.time_to_first_xray_pulse)
        await ioc.ALIO_NUMBER_OF_DATA_POINTS.write(param.number_of_data_points)
        await ioc.ALIO_DISTANCE_OF_ACTUAL_DATA_COLLECTION.write(param.distance_of_actual_data_collection)
        await ioc.ALIO_TOTAL_DISTANCE_OF_TRANSLATION.write(param.total_distance_of_translation)
        await ioc.ALIO_TIME_TO_REACH_HALF_THE_RETURN_DISTANCE.write(param.time_to_reach_half_the_return_distance)
        await ioc.ALIO_MAX_VELOCITY_ON_RETURN.write(param.max_velocity_on_return)
        await ioc.ALIO_TOTAL_TIME_TO_RETURN.write(param.total_time_to_return)
        await ioc.ALIO_TOTAL_TIME_OF_TRANSLATION.write(param.total_time_of_translation)
        await ioc.ALIO_FULL_CYCLE_CLOCK_TICKS.write(param.full_cycle_clock_ticks)
        await ioc.ALIO_MEASURE_LENGTH.write(param.measure_length)
        await ioc.ALIO_ERROR_CHECK.write('')

    async def laser(self, instance, value):
        """ 0: No translation. 1: single row continous."""
        param.laser=value
        save_settings()
        #print(param.laser)

    async def points(self,mode):
        xyz=[]
        x_step_size=param.translate_x/param.number_of_data_points
        y_step_size=param.translate_y/param.number_of_data_points
        for i in range(int(param.number_of_data_points)):
            xyz.append(param.first_hole_x+x_step_size*i)
            xyz.append(param.first_hole_y+y_step_size*i)
            xyz.append(param.first_hole_z+param.z_step_size*i)
        if not "scan" in mode: xyz = xyz[0:3]
        await ioc.PTS_VAL.write(xyz)
        #print(xyz)
        #self.PTS_VAL(xyz)
        #return xyz
    
    CMD_VAL = pvproperty(name='ALIO.CMD.VAL', dtype=ChannelType.STRING, put=CMD)
    CMD_RBV = pvproperty(name='ALIO.CMD.RBV', dtype=ChannelType.STRING)
    ACQ_VAL = pvproperty(value=0, name='ALIO.ACQ.VAL', put=ACQ)
    ACQ_RBV = pvproperty(value=0, name='ALIO.ACQ.RBV')
    PTS_VAL = pvproperty(value=[0.0,0.0,0.0], 
                         max_length=8000, 
                         name='ALIO.PTS.VAL', 
                         dtype=ChannelType.DOUBLE, 
                         precision=3)
    PTS_DESC = pvproperty(value=['X','Y','Z'],
                          name='ALIO.PTS.DESC',
                          dtype=ChannelType.STRING)
    e_strings=['No translation','Flythru-single row','Stepping-single row','Scan1D_stepping','Scan1D_flythru']
    ALIO_SCAN_TYPE = pvproperty(value=param.scan_type,enum_strings=e_strings, dtype=ChannelType.ENUM, put=scan_type)
    l_strings=['Xray only','ns laser', 'ps laser']
    ALIO_LASER = pvproperty(value=param.laser,enum_strings=l_strings, dtype=ChannelType.ENUM, put=laser)

    ALIO_FIRST_HOLE_X = pvproperty(value=float(param.first_hole_x), precision=3, put=update2)
    ALIO_FIRST_HOLE_Y = pvproperty(value=float(param.first_hole_y), precision=4, put=update2)
    ALIO_FIRST_HOLE_Z = pvproperty(value=float(param.first_hole_z), precision=4, put=update2)
    ALIO_SECOND_HOLE_X = pvproperty(value=float(param.second_hole_x), precision=4, put=update2)
    ALIO_SECOND_HOLE_Y = pvproperty(value=float(param.second_hole_y), precision=4, put=update2)
    ALIO_SECOND_HOLE_Z = pvproperty(value=float(param.second_hole_z), precision=4, put=update2)
    ALIO_THIRD_HOLE_X = pvproperty(value=float(param.third_hole_x), precision=4, put=update2)
    ALIO_THIRD_HOLE_Y = pvproperty(value=float(param.third_hole_y), precision=4, put=update2)
    ALIO_THIRD_HOLE_Z = pvproperty(value=float(param.third_hole_z), precision=4, put=update2)
    ALIO_Y_STEP_SIZE = pvproperty(value=float(param.y_step_size), precision=3, put=update2)
    ALIO_Z_STEP_SIZE = pvproperty(value=float(param.z_step_size), precision=3, put=update2)
    ALIO_ACCELERATION = pvproperty(value=float(param.acceleration), precision=1, put=update2)
    ALIO_REPETITION_PERIOD = pvproperty(value=int(param.repetition_period),put=update2)
    ALIO_SETTLE_PERIOD = pvproperty(value=int(param.settle_period),put=update2)
    
    ALIO_TRANSLATION_RANGE_X = pvproperty(value=float(param.translate_x),precision=3, units="mm")
    ALIO_TRANSLATION_RANGE_Y = pvproperty(value=float(param.translate_y),precision=3, units="mm")
    ALIO_TRANSLATION_RANGE_Z = pvproperty(value=float(param.translate_z),precision=3, units="mm")
    ALIO_ROWS = pvproperty(value=float(param.rows),precision=3)
    ALIO_VELOCITY = pvproperty(value=float(param.velocity),precision=3, units="mm/s")
    ALIO_ACCELERATION_TIME = pvproperty(value=float(param.acceleration_time),precision=3, units="s")
    ALIO_ACCELERATION_DISTANCE = pvproperty(value=float(param.acceleration_distance),precision=3, units="mm")
    ALIO_SETTLING_TIME_AT_SPEED = pvproperty(value=float(param.settling_distance_at_speed),precision=3, units="s")                                            
    ALIO_SETTLING_DISTANCE_AT_SPEED = pvproperty(value=float(param.settling_distance_at_speed),precision=3, units="mm")
    ALIO_TIME_TO_FIRST_XRAY_PULSE = pvproperty(value=float(param.time_to_first_xray_pulse), units="ms clock")
    ALIO_NUMBER_OF_DATA_POINTS = pvproperty(value=float(param.number_of_data_points),precision=3)
    ALIO_DISTANCE_OF_ACTUAL_DATA_COLLECTION = pvproperty(value=float(param.distance_of_actual_data_collection),precision=3, units="mm")
    ALIO_TOTAL_DISTANCE_OF_TRANSLATION = pvproperty(value=float(param.total_distance_of_translation),precision=3, units="mm")
    ALIO_TIME_TO_REACH_HALF_THE_RETURN_DISTANCE = pvproperty(value=float(param.time_to_reach_half_the_return_distance),precision=3, units="s")
    ALIO_MAX_VELOCITY_ON_RETURN = pvproperty(value=float(param.max_velocity_on_return),precision=3, units="mm/s")
    ALIO_TOTAL_TIME_TO_RETURN =pvproperty(value=float(param.total_time_to_return),precision=3, units="s")
    ALIO_TOTAL_TIME_OF_TRANSLATION = pvproperty(value=float(param.total_time_of_translation),precision=3, units="s")
    ALIO_FULL_CYCLE_CLOCK_TICKS = pvproperty(value=float(param.full_cycle_clock_ticks))
    ALIO_MEASURE_LENGTH = pvproperty(value=float(param.measure_length), units="ms clock")
    
    ALIO_ERROR_CHECK = pvproperty(value='')
    ALIO_ERROR_MESSAGE = pvproperty(value='')
    ALIO_STATUS = pvproperty(value='')
    
    @ALIO_ROWS.putter
    async def ALIO_ROWS(self,instance,value):
        #print(value,round(value,4),round(value,4).is_integer())
        #if value>=10:
        if not round(value,4).is_integer():
            errors.number_of_data_points='Not an integer number of rows. '
        else:
            errors.number_of_data_points=''

    @ALIO_NUMBER_OF_DATA_POINTS.putter
    async def ALIO_NUMBER_OF_DATA_POINTS(self,instance,value):
        #print(value,round(value,4),round(value,4).is_integer())
        #if value>=10:
        if not round(value,4).is_integer():
            errors.rows='Not an integer number of data points. '
        else:
            errors.rows=''
                 
    @ALIO_ERROR_CHECK.putter
    async def ALIO_ERROR_CHECK(self,instance,value):
        string=''
        for name in dir(errors):
            if name.startswith("__"):continue
            string=string+(getattr(errors,name))
        if len(string)==0:
            await instance.alarm.write(severity=AlarmSeverity.NO_ALARM)
            await ioc.ALIO_ERROR_MESSAGE.write('')
        else:
            await instance.alarm.write(severity=AlarmSeverity.MAJOR_ALARM)
            await ioc.ALIO_ERROR_MESSAGE.write('Error: ' + string)

if __name__ == '__main__':
    ioc_options, run_options = ioc_arg_parser(
        default_prefix='14IDB:',
        desc=dedent(ALIO_IOC.__doc__))
    ioc = ALIO_IOC(**ioc_options)
    run(ioc.pvdb, **run_options)
