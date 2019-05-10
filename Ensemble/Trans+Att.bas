' This program is to translate the sample for a Laue crystallography experiment
' synchronously to an exteranl trigger signal.
' The maximum trigger needed rate is 82 Hz, the translation step 150 um.
' The tranlations is trigger by a rising edge at the digital input 0.

' LCLS combined X-ray shutter and attenuator operation:

' When the level of input "close/open" is TTL high the shutter in open position.
' If it is low in closed or attenuated position.
' When level "full/atten." input is TTL high the attenuator is inserted.
' Otherwise, it is in closed position.
' Input "close/open" high overrides input "full/atten." high.

' Setup: 
' FPGA X-ray shut. -> Breakout box, Digital input 1 -> Ensemble X Opto-In Pin 3
' FPGA X-ray att.  -> Breakout box, Digital input 2 -> Ensemble X Opto-In Pin 4

' Author: Friedrich Schotte, 18 Apr 2013 - 31 Jan 2016
' 31 Jan 2016 merged "SampleTranslation.ab" and "Attenuator.ab"

HEADER
INCLUDE "StringLibHeader.basi"
'DEFINE UNIT 1 'position unit in multiples of of mm (if um use 0.001)
' Global string registers
'DEFINE PROGRAM_NAME 0 
' Global integer register numbers.
'DEFINE TRIGGER_ENABLED 0 
'DEFINE AUTO_RETURN 1 'automatically return to start at end of travel
'DEFINE AUTO_REVERSE 2 'automatically return to start at end of travel
'DEFINE TIMER_ENABLED 3 'Move stage on a timer?
'DEFINE TRIGGER_COUNT 4 'number of trigger events detected
'DEFINE NSTEPS 6 'number of X,Y,Z coordinates to use
'DEFINE STEP_COUNT 7 'current position number
'DEFINE TIMER_VALUE 8 'current value of timer in units of ms
'DEFINE TIMER_COUNT 9 'current value of timer in units of ms
'DEFINE NAXES 10 'how many axes to use?
' Global double register numbers.
'DEFINE VERSION 0 
'DEFINE TIMER_PERIOD 4 'timer period in ms  
'DEFINE X0 5 'first position X in mm
'DEFINE Y0 X0+1 'first position Y in mm
'DEFINE Z0 X0+2 'first position Z in mm
END HEADER

 PROGRAM 
' Initialize X-ray shutter/attenuator
DIM open_pos,closed_pos,attenuated_pos AS DOUBLE
DIM open_close_speed AS DOUBLE
DIM current_pos AS DOUBLE
DIM open_level,att_level AS INTEGER' digital input states
DIM last_open_level,last_att_level AS INTEGER
DIM msshut_bits AS INTEGER' axis status bits
DIM home_cyle_complete AS INTEGER' axis status bits

SETPARM 6: DefaultRampRate, 500000 ' in deg/s2
attenuated_pos=56
closed_pos=63' normal closed position in open/close mode in deg
open_pos=70' in deg
open_close_speed=7200' top speed in deg/s

FAULTACK 6' Make sure fault state is cleared
ENABLE 6' turn the drive on
' With and incremental encoder, after power on, in order for the controller
' to know the absolute angle of the motor it needs to find the "reference" mark 
' of the encoder. The HOME command rotates the motor until the the marker input
' open_level goes high, then stops there and resets the encoder accumulator count to
' zero.
' The program check first if a home run has already been performed, and does
' it only if it has not been done before.
msshut_bits=AXISSTATUS(6)
home_cyle_complete=(msshut_bits >> 1) BAND 1
IF home_cyle_complete=0 THEN
HOME 6
END IF
open_level=DIN:0::( 1,1)'Close/open input (0 = closed, 1 = open)
 att_level=DIN:0::( 1,2)'Annuator input (0 = closed, 1 = attenuated)
 IF open_level=1 THEN
MOVEABS 6:open_pos:open_close_speed 
ELSEIF att_level=1 THEN
MOVEABS 6:attenuated_pos:open_close_speed 
ELSE
MOVEABS 6:closed_pos:open_close_speed 
END IF
last_open_level=open_level
last_att_level=att_level

' Initialize Sample Translation
DIM last_level AS INTEGER'digital input state
 DIM trigged_step AS INTEGER'Was last move done on external trigger?
'DIM x1 as DOUBLE, y1 as DOUBLE, z1 as DOUBLE 'current position
 DIM i AS INTEGER' current position number
DIM level AS INTEGER'digital input state
 DIM t,dt AS INTEGER'time in milliseconds
 DIM Nt,last_Nt AS INTEGER'time in number of timer periods
 DIM do_step AS INTEGER'Start motion?
 DIM bits AS INTEGER,enabled AS INTEGER,homed AS INTEGER'Axis status bits
 DIM xp AS DOUBLE,yp AS DOUBLE,zp AS DOUBLE
DIM ox as DOUBLE,oy AS DOUBLE,oz AS DOUBLE' grid origin
DIM dx as DOUBLE,dy AS DOUBLE,dz AS DOUBLE' grid stepsize
DIM nx as INTEGER,ny AS INTEGER,nz AS INTEGER' grid size

SGLOBAL(0)="SampleTranslation"
DGLOBAL(0)=4.9000000000000004
IGLOBAL(1)=1'automatically return to start at end of travel
 IGLOBAL(2)=0'automatically reverse direction at end of travel
 IGLOBAL(0)=1'move stage on external trigger
 IGLOBAL(3)=0'move stage on a timer  
 IGLOBAL(6)=0'number of triggered steps operations
 DGLOBAL(4)=24'timer period in ms  
 IGLOBAL(4)=0'number of trigger events detected
 IGLOBAL(7)=0'number of triggered steps operations
 IGLOBAL(9)=0
IGLOBAL(10)=3' how many axes to use
IF 0 THEN' For testing only set to 1
'Initialize the coordinates to do a Y,Z grid scan.
 IGLOBAL(6)=64'number of triggered steps operations
 nz=8
dz=1
oz=-1*nz/2*dz
ny=8
dy=1
oy=-1*ny/2*dy
FOR i=0 TO IGLOBAL(6)
DGLOBAL(5+3*I)=0
DGLOBAL(6+3*I)=oy+FLOOR(i/nz)*dy
DGLOBAL(7+3*I)=oz+( i-FLOOR(i/nz)*nz)*dz
NEXT i
END IF

CLEARTIMER'Reset the timer to 0 to indicate the program uptime.             
'PLANE 0 'for coordinated moved using the LINEAR command
'ABS 'for the LINEAR command: LINEAR uses absolute coordinates.
WAIT MODE NOWAIT 'After a motion command, do not wait for it to complete.
 SCURVE 0'Set ramp portion of velocity profile to fully linear.

' Read digital inputs (on AUX I/O connector)
last_level=DIN:0::( 1,0)
last_Nt=0

WHILE 1
' X-ray shutter/Attenuator
' Read digital inputs
open_level=DIN:0::( 1,1)'Close/open input (0 = closed, 1 = open)
 att_level=DIN:0::( 1,2)'Annuator input (0 = closed, 1 = attenuated)
 IF open_level<>last_open_level OR att_level<>last_att_level THEN
IF open_level=1 THEN
MOVEABS 6:open_pos:open_close_speed 
ELSEIF att_level=1 THEN
MOVEABS 6:attenuated_pos:open_close_speed 
ELSE
MOVEABS 6:closed_pos:open_close_speed 
END IF
END IF
last_open_level=open_level
last_att_level=att_level

' Sample Translation
do_step=0
IF IGLOBAL(0)THEN
' Read digital inputs (on AUX I/O connector)
level=DIN:0::( 1,0)
'DOUT X,1,level ' Timing marker for debugging
 IF level=1 AND last_level=0 THEN
do_step=1
END IF
IF do_step THEN IGLOBAL(4)=(IGLOBAL(4)+1)END IF
last_level=level
END IF
' On the rising edge of input 1, operated the stage momentarily advancing
' one step.
IF do_step THEN
i=IGLOBAL(7)
xp=DGLOBAL(5+3*i)/1
yp=DGLOBAL(6+3*i)/1
zp=DGLOBAL(7+3*i)/1
IF xp=xp AND yp=yp AND zp=zp THEN' Ignore NaN
MOVEABS 0:xp,1:yp,2:zp ' non-coordinated move
'LINEAR X xp Y yp Z zp ' coordinated move
 END IF
i=i+1
IF i>=IGLOBAL(6)THEN
IF IGLOBAL(1)THEN
i=0
ELSE
i=IGLOBAL(6)-1
END IF
END IF
IGLOBAL(7)=i
END IF
WEND
END PROGRAM 
