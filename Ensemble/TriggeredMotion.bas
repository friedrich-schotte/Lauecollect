' This program is to translate the sample for a Laue crystallography experiment
' synchronously to an external trigger signal.
' The maximum trigger rate is 82 Hz.
' The tranlations is trigger by a rising edge at the digital input 0.

' Friedrich Schotte, NIH, 18 Apr 2013 - 15 Nov 2014

HEADER
INCLUDE "StringLibHeader.basi"
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
'DEFINE NAXES 10 'How many axis to use?
'DEFINE INT_ARRAY00 11 'start of interger arrays
'DEFINE AXIS_ENABLED_I 0 'Do triggered motion on this axis? order of array
'DEFINE RELATIVE_MOVE_I 1 'Interpret coordinates as incremental? order of array
'DEFINE TRIGGER_DIVISOR_I 2 'Sub-divide trigger frequency? order of array
'DEFINE AXIS_NSTEPS_I 3 'Per-axis number of steps? order of array
' Global double register numbers.
'DEFINE VERSION 0 
'DEFINE TIMER_PERIOD 4 'timer period in ms
'DEFINE POS00 5 'first position for the first axis, start of an n_axes x N array
END HEADER

DECLARATIONS
GLOBAL timer_period AS DOUBLE'timer period on ms  
END DECLARATIONS

 PROGRAM 
 DIM last_level AS INTEGER'digital input state
 DIM trigged_step AS INTEGER'Was last move done on external trigger?
'DIM x1 as DOUBLE, y1 as DOUBLE, z1 as DOUBLE 'current position
 DIM i AS INTEGER' current position number
DIM level AS INTEGER'digital input state
 DIM t,dt AS INTEGER'time in milliseconds
 DIM Nt,last_Nt AS INTEGER'time in number of timer periods
 DIM do_step AS INTEGER'Start motion?
 DIM bits AS INTEGER,enabled AS INTEGER,homed AS INTEGER'Axis status bits
 DIM n_axes AS INTEGER,pos AS DOUBLE,relative_move AS INTEGER
DIM step_count AS INTEGER
DIM axis_enabled AS INTEGER,axis_nsteps AS INTEGER,divisor AS INTEGER
DIM name AS STRING,version AS DOUBLE
name=SGLOBAL(0)
IF name<>"TriggeredMotion"OR DGLOBAL(0)<>5.0999999999999996 THEN
'Initialize global variables
 SGLOBAL(0)="TriggeredMotion"
DGLOBAL(0)=5.0999999999999996
IGLOBAL(1)=1'automatically return to start at end of travel
 IGLOBAL(2)=0'automatically reverse direction at end of travel
 IGLOBAL(0)=0'move stage on external trigger
 IGLOBAL(3)=0'move stage on a timer  
 IGLOBAL(6)=0'number of triggered steps operations
 DGLOBAL(4)=24'timer period in ms  
 IGLOBAL(4)=0'number of trigger events detected
 IGLOBAL(7)=0'number of triggered steps operations
 IGLOBAL(9)=0
IGLOBAL(10)=6'how many axes to use? 
 n_axes=IGLOBAL(10)
FOR iaxis=0 TO n_axes-1
IGLOBAL(11+0*n_axes+iaxis)=0'Use this axis?
 IGLOBAL(11+1*n_axes+iaxis)=0'Do incr. move?
 IGLOBAL(11+2*n_axes+iaxis)=1'Sub-divide trigger frequency?
 IGLOBAL(11+3*n_axes+iaxis)=0'per-axis number of steps
 NEXT isaxis
FOR i=5 to 256
DGLOBAL(i)=0
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
IGLOBAL(8)=TIMER()
IF IGLOBAL(3)THEN
t=IGLOBAL(8)
dt=DGLOBAL(4)
IGLOBAL(9)=t/dt
if IGLOBAL(9)<>last_Nt THEN do_step=1 END IF
last_Nt=IGLOBAL(9)
END IF
' On the rising edge of input 1, operated the stage momentarily advancing
' one step.
IF do_step THEN
step_count=IGLOBAL(7)
n_axes=IGLOBAL(10)
FOR iaxis=0 TO n_axes-1
i=step_count
axis_enabled=IGLOBAL(11+0*n_axes+iaxis)
IF axis_enabled THEN
divisor=IGLOBAL(11+2*n_axes+iaxis)
IF divisor=0 THEN divisor=1 END IF
IF i/divisor*divisor=i THEN
i=i/divisor
axis_nsteps=IGLOBAL(11+3*n_axes+iaxis)
IF axis_nsteps>IGLOBAL(6)THEN axis_nsteps=IGLOBAL(6)END IF
IF IGLOBAL(1)THEN i=i-i/axis_nsteps*axis_nsteps END IF
IF i<axis_nsteps THEN
pos=DGLOBAL(5+i*n_axes+iaxis)
'pos = pos: check for NaN
 IF AXISFAULT(iaxis)=0 AND pos=pos THEN
relative_move=IGLOBAL(11+1*n_axes+iaxis)
IF NOT relative_move THEN
MOVEABS iaxis:pos 
ELSE
MOVEINC iaxis:pos 
END IF
END IF
END IF
END IF
END IF
NEXT isaxis
IGLOBAL(7)=IGLOBAL(7)+1
END IF
WEND
END PROGRAM 
