DECLARATIONS
GLOBAL Version AS STRING="2.4"
GLOBAL res AS DOUBLE'encoder resolution in mm
 GLOBAL stepsize AS DOUBLE'increment for triggered motion (um)
 GLOBAL start_pos AS DOUBLE'turning point for triggered motion (um)
 GLOBAL end_pos AS DOUBLE'turning point for triggered motion (um)
 GLOBAL auto_return AS INTEGER'automatically return to start at end of travel
 GLOBAL auto_reverse AS INTEGER'automatically reverse direction at end of travel
 GLOBAL speed AS DOUBLE'top speed in um/s
 GLOBAL step_acceleration AS DOUBLE'for triggered operation in um/s2
 GLOBAL acceleration AS DOUBLE'for non-triggered motion in um/s2
 GLOBAL low_limit AS DOUBLE'limit switch trigger point (um)
 GLOBAL high_limit AS DOUBLE'limit switch trigger point (um)
 GLOBAL trigger_enabled AS INTEGER'move stage on external trigger
 GLOBAL timer_enabled AS INTEGER'move stage on a timer  
 GLOBAL timer_period AS INTEGER'timer period on ms
 GLOBAL last_timer AS INTEGER'last time the timer triggered a step (ms)
 GLOBAL last_level AS INTEGER'digital input state
 GLOBAL trigger_count AS INTEGER'number of trigger events detected
 GLOBAL step_count AS INTEGER'number of triggered steps operations
 GLOBAL trigged_step AS INTEGER'Was last move done on external trigger?
 GLOBAL target_position AS DOUBLE'End point of last move
END DECLARATIONS

 PROGRAM
'Initialize global variables
 stepsize=500'increment for triggered motion (um)
 start_pos=-12250'turning point for triggered motion (um)
 end_pos=12250'turning point for triggered motion (um)
 trigger_enabled=1'move stage on external trigger
 timer_enabled=0'move stage on a timer  
 timer_period=24'timer period in ms  
 speed=200000'top speed in um/s
 step_acceleration=10000000'for triggered operation in um/s2
 acceleration=step_acceleration'for non-triggered motion in um/s2 (0.25 s for full stroke)
 trigger_count=0'number of trigger events detected
 step_count=0'number of triggered steps operations
 triggered_step=0'Was last move done on external trigger?
 last_timer=0'Last time the timer triggered a step (ms)
 target_position=PCMD(2)

DIM level AS INTEGER'digital input state
 DIM bits AS INTEGER'status bits
 DIM HL AS INTEGER,LL AS INTEGER,moving AS INTEGER'high limit, low limit
 DIM t AS INTEGER,t1 AS INTEGER

WAIT MODE NOWAIT 'After a motion command, do not wait for it to complete.
RAMP MODE RATE 'The acceation ramp is determind by the RAMP RATE parameter (default)
'Use the velocity profiling mode
 IF GETMODE(3)=0 THEN
'VELOCITY ON 
 END IF
FAULTACK 2'Make sure any fault state is cleared.

' Read digital inputs (on AUX I/O connector)
last_level=DIN:0::( 1,0)
WHILE 1
do_step=0
IF trigger_enabled THEN
' Read digital inputs (on AUX I/O connector)
level=DIN:0::( 1,0)
IF level=1 AND last_level=0 THEN do_step=1 END IF
IF do_step THEN trigger_count=trigger_count+1 END IF
last_level=level
END IF
IF timer_enabled THEN
t=TIMER()
t1=t-( t/timer_period)*timer_period
IF 0<=t1 AND t1<1 AND t<>last_timer THEN
do_step=1
last_timer=t
END IF
END IF

' Operate the stage momentarily advancing one step.
IF do_step THEN
' For debugging, indicate begin of move by setting a digital output
DOUT:0::1, 1

bits=AXISSTATUS(2)
moving=(bits >> 3) BAND 1
' Ignore trigger if still busy performing the last motion,
' unless the last motion was externally triggered.
IF NOT moving or triggered_step THEN
trigger_count=trigger_count+1
IF end_pos>start_pos THEN HP=end_pos ELSE HP=start_pos END IF
IF end_pos>start_pos THEN LP=start_pos ELSE LP=end_pos END IF
HL=(bits >> 22) BAND 1
LL=(bits >> 23) BAND 1

IF NOT moving THEN
'FAULTACK Z 'Make sure any fault state is cleared.
 END IF
ENABLE 2'turn the drive on

IF stepsize>0 AND target_position+stepsize>HP+1 OR HL THEN
RAMP RATE 2:acceleration 
MOVEABS 2:LP:speed ' D position in um, F in um/s
target_position=LP
triggered_step=0
step_count=step_count+1
ELSEIF stepsize<0 AND target_position+stepsize<LP-1 OR LL THEN
RAMP RATE 2:acceleration 
MOVEABS 2:HP:speed ' D position in um, F in um/s
target_position=HP
triggered_step=0
step_count=step_count+1
ELSE
CALL MOVE_STEP()
triggered_step=1
step_count=step_count+1
END IF
END IF

' For debugging, indicate end of move by setting a digital output
DOUT:0::1, 0
END IF
WEND
END PROGRAM

' Position as function of time during a step move, relative to
' the beginning of the move.
' The step size if given by the globl variable 'stepsize', the 
' accelearion by th global variable 'step_acceleration'
FUNCTION step_position(BYVAL t AS DOUBLE)AS DOUBLE
' t: time in seconds since beginning of move
DIM a AS DOUBLE,xs AS DOUBLE,tr AS DOUBLE,x AS DOUBLE
a=step_acceleration
xs=stepsize
'Acceleration/deceleration ramp duration in seconds.
 tr=SQR(ABS(xs)/a)
IF t<=0 THEN
x=0
ELSEIF t<=tr THEN
x=a/2*t^2
ELSEIF t<=(2*tr)THEN
x=xs-a/2*(2*tr-t)^2
ELSE
x=xs
END IF
STEP_POSITION=x
END FUNCTION

' Speed as function of time during a step move, relative to
' the beginning of the move.
' The step size if given by the globl variable 'stepsize', the 
' accelearion by th global variable 'step_acceleration'
FUNCTION step_velocity(BYVAL t AS DOUBLE)AS DOUBLE
' t: time in seconds since beginning of move
DIM a AS DOUBLE,xs AS DOUBLE,tr AS DOUBLE,sign AS DOUBLE
DIM v AS DOUBLE
a=step_acceleration
xs=stepsize
'Acceleration/deceleration ramp duration in seconds.
 tr=SQR(ABS(xs)/a)
IF xs>0 THEN
sign=1
ELSE
sign=-1
END IF
IF t<=0 THEN
v=0
ELSEIF t<=tr THEN
v=a*t
ELSEIF t<=(2*tr)THEN
v=a*(2*tr-t)
ELSE
v=0
END IF
STEP_VELOCITY=v
END FUNCTION

' Move the stange bt one step defined by the global variable 'stepsize'
FUNCTION MOVE_STEP()
DIM pos AS DOUBLE,t AS DOUBLE,dt AS DOUBLE
dt=0.001' time step
ABS'Positioning mode of the task: absolute (default: incremental)
PVT_INIT  @0 
PVT  @dt 
 HALT'Hold motion FIFO queue when new moves are loaded.
 FOR t=0 TO 0.017999999999999999 STEP dt
pos=target_position+step_position(t)
vel=step_velocity(t)
PVT 2: pos, vel 
NEXT t
target_position=target_position+stepsize
START'Execute the moves queued up in the profiled motion FIFO queue.
'WAIT MOVEDONE Z
 END FUNCTION

