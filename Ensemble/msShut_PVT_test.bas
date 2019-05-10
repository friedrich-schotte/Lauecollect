HEADER
INCLUDE "Environment_parameters.basi"
END HEADER

DECLARATIONS
GLOBAL E_index AS INTEGER
GLOBAL AIN_Volt AS DOUBLE
GLOBAL Tcorr AS DOUBLE
GLOBAL scale_factor AS DOUBLE
GLOBAL DT_start AS DOUBLE
GLOBAL DT AS DOUBLE

'PrintLog() variables
 GLOBAL PrintString AS STRING(96)'max # characters for PRINT is 96	

END DECLARATIONS

 PROGRAM 
DIM Ti AS DOUBLE

'Write program name in UserString0 (identifies program loaded)
SETPARM 1023:UserString0,"msShut_PVT.ab" 

'Read E_index(Environment index): (0: NIH; 1: APS; 2: LCLS)
 E_index=GETPARM(1023:UserInteger0) 

'Initialize IGLOBAL Interactive Control Parameters
 IGLOBAL(0)=1'1: program is running; 0: terminates program
IGLOBAL(1)=1'1 triggers digital oscilloscope one time


'Set up scope parameters
'SCOPEBUFFER 5000
'SCOPETRIGPERIOD 1	' -4 (-2) corresponds to 4 (2) kHz

IF E_index=1 THEN
'APS
 ELSE'NIH, LCLS
SETGAIN 6:161500, 3598,91.269999999999996,72990,0,0,0,0,0 'NIH 90 Hz
 END IF

'Select Environment-dependent parameters
 scale_factor=scale_factor_array(E_index)
DGLOBAL(0)=scale_factor
DT_start=DT_array(E_index)
DT=DT_start*scale_factor
DGLOBAL(1)=DT
msShut_open=msShut_open_array(E_index)
msShut_step=msShut_step_array(E_index)
msShut_atten=56'NIH/LCLS attenuated position (in degrees)
 msShut_close1=msShut_open-msShut_step
msShut_close2=msShut_open+msShut_step

ABS'Positions specified in absolute coordinates
WAIT MODE MOVEDONE 
 msShut_pos=msShut_close1
MOVEABS 6:msShut_pos:10000 
PVT_INIT  @1 
VELOCITY ON
HALT

N_count=0
STARTSYNC-1'set SYNCH interval to 0.5 ms
'Ensure input is 0 before starting.

WHILE IGLOBAL(0)>0'enter IGLOBAL(0) = 0 to exit loop
 SYNC
N_loop=0
N_PVT=0

'wait for next low-to-high transition
 AIN_Volt=AIN:6::( 1)
WHILE AIN_Volt<0.59999999999999998
SYNC
AIN_Volt=AIN:6::( 1)
WEND
'Calculate offset_Z from AIN_Volt
 offset_Z=A_array(E_index,3)*AIN_Volt^3
+A_array(E_index,2)*AIN_Volt^2
+A_array(E_index,1)*AIN_Volt
+A_array(E_index,0)


'wait for next low-to-high transition.
 WHILE AIN:6::( 1)<0.59999999999999998
IF N_count>0 THEN
Ttemp=0.001*TIMER()
IF Ttemp>(Ti-0.002)THEN
IF(N_loop BAND 3)=3 THEN
N_PVT=N_PVT+1
PVT 6: msShut_pos, 0 @Ttemp+0.002 
END IF
N_loop=N_loop+1
END IF

END IF
SYNC
WEND
AIN_Volt=AIN:6::( 1)
IF N_count=0 THEN CLEARTIMER END IF
Ttrig=0.001*TIMER()

'calculate time offset from AIN
 Ti_offset=(0.026239999999999999*AIN_Volt^3
-0.11626*AIN_Volt^2
+0.37006*AIN_Volt
-0.53064)/470

SYNC'0.5 ms after trigger

'Acquire scope trace when IGLOBAL(1)=1
 IF IGLOBAL(1)=1 THEN
SCOPETRIG
IGLOBAL(1)=0
END IF
'Determine next msShut positions for modes 0 and 1
 IF msShut_pos>msShut_close1 THEN
msShut_pos0=msShut_close1
msShut_pos1=msShut_close1
ELSE
msShut_pos0=msShut_close2
msShut_pos1=msShut_open
END IF

SYNC'1.0 ms after trigger

'Queue PVT commands for START time and for offset time 
 Ti=Ttrig+0.002
PVT 6: msShut_pos, 0 @Ti 
Ti=Ti+0.001-Ti_offset
PVT 6: msShut_pos, 0 @Ti 

SYNC'1.5 ms after trigger

'Determine mode of operation and queue next PVT command
 shut_mode=X 1,1)