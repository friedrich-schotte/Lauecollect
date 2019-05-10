DECLARATIONS
GLOBAL PrintString AS STRING(120)
GLOBAL msShut_Enable AS INTEGER
GLOBAL PumpA_Enable AS INTEGER
GLOBAL N_mode AS INTEGER
GLOBAL N_delay AS INTEGER
GLOBAL scale_factor AS DOUBLE
GLOBAL msShut_Enable_last AS INTEGER
GLOBAL PumpA_Enable_last AS INTEGER
GLOBAL N_mode_last AS INTEGER
GLOBAL N_delay_last AS INTEGER
GLOBAL scale_factor_last AS DOUBLE
GLOBAL T_corr AS DOUBLE
GLOBAL T_corr_sum AS DOUBLE
GLOBAL Z_error_range AS INTEGER
GLOBAL DIN_array(160)AS INTEGER
GLOBAL T_offset AS DOUBLE
GLOBAL N_count AS INTEGER
GLOBAL DT AS DOUBLE
GLOBAL Zpos AS DOUBLE
GLOBAL Zvmax_RS AS DOUBLE
END DECLARATIONS

 PROGRAM 
IGLOBAL(4)=1'1: Verbose logging
DZ=-0.5'The full stroke is defined to be (DZ*N_steps) 
 N_steps=46'5 for LZ offset; 39 for 40 x-ray shots; 2 for acceleration/deceleration
Z_stop=-10.5'Stroke stops at this position 
 Z_start=Z_stop-DZ*N_steps'Stroke starts at this position	
 N_return=72'Number of time steps for return stroke
 DT=(1.0055257142857144)*0.024304558/24
Z_mid=0.5*(Z_start+Z_stop)'mid-point of the stroke
 Zvmax_RS=1.5*(Z_start-Z_stop)/(N_return*DT)'peak velocity during return stroke.
 Zi=Z_start
Ti=0.001
N_count=0

Plane 1
RECONCILE 2
ABS'Positions specified in absolute coordinates
WAIT MODE MOVEDONE 
LINEAR 2:Zi @10 
PVT_INIT  @1 
 VELOCITY ON
HALT
PVT 2: Zi, 0 @Ti 

IGLOBAL(0)=0
CALL Synch()

'	FOR i = 0 TO 160
'		FORMAT PrintString, "%d\r",INTV:DIN_array(i)
'		PRINT PrintString
'	NEXT i


WHILE IGLOBAL(0)>-1'enter IGLOBAL(0) = -1 to exit loop
 CALL Synch()
STARTSYNC 12
Zi=Z_stop
Ti=Ti+192*DT
PVT 2: Zi, 0 @Ti 

'Phase correction
 IF N_count>0 THEN
Ti=Ti+0.5*( Zpos-Z_mid)/Zvmax_RS
END IF

'Return Stroke
 Zi=Z_start
Ti=Ti+72*DT
PVT 2: Zi, 0 @Ti 
IF N_count=0 THEN
SYNC
CLEARTIMER
START
END IF
CALL Print_Log()
'		FORMAT PrintString, "%.2f\r",
'			DBLV:T_offset
'		PRINT PrintString
N_count=N_count+1
WEND

Ti=Ti+1000*DT
PVT 2:0, 0 @Ti 

IGLOBAL(0)=0'when -1, exit program
 WHILE(PLANESTATUS(0) BAND 1)<>0 OR(PLANESTATUS(1) BAND 1)<>0
P_status=PLANESTATUS(1)
DWELL 0.0050000000000000001
WEND
RECONCILE 2

END PROGRAM 

FUNCTION Synch()
DIM N_temp AS INTEGER
'Decode mode parameters from trigger pulse train
 STARTSYNC-1'corresponds to 0.5 ms clock ticks per SYNC 
 WHILE DIN:0::( 1,0)=0'wait for next low-to-high transition. 
 SYNC
WEND
T_offset=(AIN:0::( 1)-2.0150000000000001)/1.8899999999999999

'Insert two SYNC pulses to phase the DIN(X,1,0) acquisition
 SYNC
SYNC

T_current=TIMER()

'Record msShut_Enable 3 ms later
 FOR j=0 TO 5 SYNC NEXT j'4.0 ms
msShut_Enable=DIN:0::( 1,0)

'Record PumpA_Enable 3 ms later
 FOR j=0 TO 5 SYNC NEXT j' 3 ms
PumpA_Enable=DIN:0::( 1,0)

'Read 4 bits that define mode (every 3 ms)
 N_temp=0
FOR i=0 TO 3
FOR j=0 TO 5 SYNC NEXT j
N_temp=N_temp+DIN:0::( 1,0)*2^i
NEXT i
N_mode=N_temp

'Record Zpos immediately after N_mode
 Zpos=PCMD(2)-T_offset*Zvmax_RS/1000

'Read 6 bits that define delay (every 3 ms)
 N_temp=0
FOR i=0 TO 5
FOR j=0 TO 5 SYNC NEXT j
N_temp=N_temp+DIN:0::( 1,0)*2^i
NEXT i
N_delay=N_temp

END FUNCTION

FUNCTION Print_Log()
IF N_Count=0 THEN
PRINT"T_current[ms], msShut_Enable, PumpA_Enable, N_Mode, N_Delay, T_offset, Zpos\r"
CLEARTIMER

ELSEIF(msShut_Enable<>msShut_Enable_last)
OR(PumpA_Enable<>PumpA_Enable_last)
OR(N_mode<>N_mode_last)
OR(N_delay<>N_delay_last)
OR(scale_factor<>scale_factor_last)
OR(IGLOBAL(4)=1)THEN
FORMAT PrintString,"%d,%d,%d,%d,%d,%.3f,%.3f\r",
INTV:T_current,
INTV:msShut_Enable,
INTV:PumpA_Enable,
INTV:N_mode,
INTV:N_delay,
DBLV:T_offset,
DBLV:Zpos
PRINT PrintString
msShut_Enable_last=msShut_Enable
PumpA_Enable_last=PumpA_Enable
N_mode_last=N_mode
N_delay_last=N_delay
scale_factor_last=scale_factor
END IF
END FUNCTION
