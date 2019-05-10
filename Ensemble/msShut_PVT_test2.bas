DECLARATIONS
GLOBAL PrintString AS STRING(96)'max # characters for PRINT is 96	
 GLOBAL T_loop AS INTEGER
GLOBAL N_delay AS INTEGER
GLOBAL N_outlier AS INTEGER
GLOBAL N_loop_latch AS INTEGER
GLOBAL PCMD_msShut_ext AS DOUBLE
GLOBAL T0 AS DOUBLE
GLOBAL Volt0 AS DOUBLE
GLOBAL Volt1 AS DOUBLE
GLOBAL Volt2 AS DOUBLE
GLOBAL slope AS INTEGER
END DECLARATIONS

 PROGRAM 
DT=0.0010182857999999999
msShut_open=56
msShut_step=7
msShut_close1=msShut_open-msShut_step
msShut_close2=msShut_open+msShut_step

ABS'Positions specified in absolute coordinates
WAIT MODE MOVEDONE 
 msShut_pos=msShut_close1
MOVEABS 6:msShut_pos:10000 
slope=1


'Set up scope parameters
 SCOPEBUFFER 1000
SCOPETRIGPERIOD-4' -4 (-2) corresponds to 4 (2) kHz
SCOPETRIG
DWELL(0.025000000000000001)
IGLOBAL(0)=1'enable loop
 IGLOBAL(1)=1'reset max/min statistics

PVT_INIT  @0 
VELOCITY ON
'CLEARTIMER
 HALT
T_loop=0
N_outlier=0
WHILE IGLOBAL(0)>0'enter IGLOBAL(0) = 0 to exit loop
 N_loop=0

STARTSYNC 1'set SYNCH interval to 1 ms
 Volt0=AIN:6::( 0)
Volt1=Volt0
DOUT:6::0, 4
WHILE(Volt1<0.55000000000000004)OR(Volt1>2.75)
SYNC
Volt1=AIN:6::( 0)
N_loop=N_loop+1
WEND
DOUT:6::0, 3
N_loop_latch=N_loop
HALT

SYNC'1ms
SYNC'2ms
SYNC'3ms
Volt2=AIN:6::( 0)
DOUT:6::0, 2

IF(Volt0<1.6000000000000001)AND(Volt2<1.6000000000000001)THEN'trigger mode
 T_offset=0.044299999999999999*Volt1^3
-0.17499999999999999*Volt1^2
+0.64629999999999999*Volt1'trigger pulse rising edge			
 IF slope=1 THEN
msShut_pos=msShut_close2
slope=-1
ELSE
msShut_pos=msShut_close1
slope=1
END IF
midpoint=msShut_open
Ti=12*DT-2*T_offset/1000
N_delay=7
SYNC'4ms
'SYNC '5ms
 ELSEIF(Volt0<1.6000000000000001)AND(Volt2>1.6000000000000001)THEN'gating pulse rising edge
 T_offset=0.040399999999999998*Volt1^3
-0.15207000000000001*Volt1^2
+0.60602999999999996*Volt1
msShut_pos=msShut_open
IF slope=1 THEN
midpoint=msShut_open-0.5*msShut_step
slope=-1
ELSE
midpoint=msShut_open+0.5*msShut_step
slope=1
END IF
N_delay=5
Ti=8*DT-2*T_offset/1000
SYNC'4ms
ELSE'gating pulse falling edge
 T_offset=-0.043430000000000003*Volt1^3
+0.26563999999999999*Volt1^2
-0.95660999999999996*Volt1
+1.9502699999999999
IF slope=1 THEN
msShut_pos=msShut_close2
midpoint=msShut_open+0.5*msShut_step
slope=-1
ELSE
msShut_pos=msShut_close1
midpoint=msShut_open-0.5*msShut_step
slope=1
END IF
N_delay=5
Ti=8*DT-2*T_offset/1000
SYNC'4ms
SYNC'5ms
SYNC'6ms
SYNC'7ms
SYNC'8ms
END IF

PVT 6: msShut_pos, 0 @Ti |DOUT 6:0, 0 
START
DOUT:6::0, 1

FOR j=0 TO N_delay SYNC NEXT j
VCMD_msShut_ext=VCMD(6)/1000
PCMD_msShut_ext=PCMD(6)-midpoint-VCMD_msShut_ext*T_offset

IF IGLOBAL(1)=1 THEN'reset max/min statistics
 V1_max=0
V2_max=0
N_loop_min=100
T_loop=0
N_outlier=0
IGLOBAL(1)=0
CALL Print_Log()
ELSE
IF N_loop_latch<N_loop_min THEN
N_loop_min=N_loop_latch
END IF
IF Volt1>V1_max THEN
V1_max=Volt1
END IF
IF Volt2>V2_max THEN
V2_max=Volt2
END IF
IF(PCMD_msShut_ext<-0.5)OR(PCMD_msShut_ext>0.5)THEN
N_outlier=N_outlier+1
CALL Print_Log()
END IF
END IF
'DWELL 0.001 'Ensure trigger is below threshold before looping
 T_loop=T_loop+1
WEND
END PROGRAM 

FUNCTION Print_Log()
FORMAT PrintString,"%d,%d,%d,%.3f,%.3f,%.3f\r",
INTV:N_outlier,
INTV:T_loop,
INTV:N_loop_latch,
DBLV:Volt1,
DBLV:Volt2,
DBLV:PCMD_msShut_ext
IF T_loop=0 THEN
PrintString="N_outlier, T_loop, N_loop_latch, Volt1, Volt2, PCMD_msShut_ext\r"
PRINT PrintString
ELSE
PRINT PrintString
END IF
END FUNCTION
