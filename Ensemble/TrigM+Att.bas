' This program is to translate the sample for a Laue crystallography experiment
' synchronously to an external trigger signal.
' The maximum trigger rate is 82 Hz.
' The tranlations is trigger by a rising edge at the digital input 0.

' LCLS combined X-ray shutter and attenuator operation:

' When the level of input "close/open" is TTL high the shutter in open position.
' If it is low in closed or attenuated position.
' When level "full/atten." input is TTL high the attenuator is inserted.
' Otherwise, it is in closed position.
' Input "close/open" high overrides input "full/atten." high.

' Setup: 
' FPGA sample trans, -> Breakout box, Digital input 0 -> Ensemble X Opto-In Pin 2
' FPGA X-ray shut.   -> Breakout box, Digital input 1 -> Ensemble X Opto-In Pin 3
' FPGA X-ray att.   - > Breakout box, Digital input 2 -> Ensemble X Opto-In Pin 4

' Friedrich Schotte, NIH, 18 Apr 2013 - 31 Jan 2016'
' 31 Jan 2016 merged "TriggeredMotion.ab" and "Attenuator.ab"

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
' Initialize X-ray shutter/attenuator
DIM open_pos,closed_pos,attenuated_pos AS DOUBLE
DIM open_close_speed AS DOUBLE
DIM current_pos AS DOUBLE
DIM open_level,att_level AS INTEGER' digital input states

SETPARM 1023: msShut_ext, DefaultRampRate,500000 ' in deg/s2
attenuated_pos=56
closed_pos=63' normal closed position in open/close mode in deg
open_pos=70' in deg
open_close_speed=7200' top speed in deg/s

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
 DIM n_axes AS INTEGER,pos AS DOUBLE,relative_move AS INTEGER
DIM step_count AS INTEGER
DIM axis_enabled AS INTEGER,axis_nsteps AS INTEGER,divisor AS INTEGER
DIM name AS STRING,version AS DOUBLE
name=SGLOBAL(0)
IF name<>"TriggeredMotion"OR DGLOBAL(0)<>6 THEN
'Initialize global variables
 SGLOBAL(0)="TriggeredMotion"
DGLOBAL(0)=6
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
' X-ray shutter/Attenuator
' Read digital inputs
open_level=DIN:0::( 1,1)'Close/open input (0 = closed, 1 = open)
 att_level=DIN:0::( 1,2)'Annuator input (0 = closed, 1 = attenuated)
 current_pos=msShut_ext