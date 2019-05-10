DECLARATIONS
GLOBAL PrintString AS STRING(96)'max # characters for PRINT is 96
 GLOBAL PumpA_Enable AS INTEGER
GLOBAL PumpA_Enable_last AS INTEGER
GLOBAL N_mode AS INTEGER
GLOBAL N_mode_last AS INTEGER
GLOBAL N_loop AS INTEGER
GLOBAL N_trigger AS INTEGER
GLOBAL N_control AS INTEGER
GLOBAL Volt1 AS DOUBLE
GLOBAL T_offset AS DOUBLE
GLOBAL T_shift AS DOUBLE=-0.25
GLOBAL Z_error AS DOUBLE
END DECLARATIONS

 PROGRAM 

N_trigger=-1
IGLOBAL(0)=1
WHILE IGLOBAL(0)>0'enter IGLOBAL(0) = 0 to exit loop	
 N_trigger=N_trigger+1
STARTSYNC 1'corresponds to 1 ms clock ticks per SYNC
 Call Synch()
FOR j=1 TO 50 SYNC NEXT j'4 ms
WEND
END PROGRAM 

FUNCTION Synch()
DIM N_temp AS INTEGER
DIM j AS INTEGER
'wait for next low-to-high transition
 N_loop=0
Volt1=AIN:0::( 1)
DOUT:0::0, 4'marks time of start
WHILE Volt1<0.59999999999999998
SYNC
Volt1=AIN:0::( 1)
N_loop=N_loop+1
WEND
DOUT:0::0, 3'marks time of trigger pulse
HALT
'Calculate offset_Z from Volt1
 T_offset=0.044299999999999999*Volt1^3
-0.17499999999999999*Volt1^2
+0.64629999999999999*Volt1
-T_shift'adding 0.25 starts motion 0.25 ms earlier

'Record msShut_Enable 4 ms later
 SYNC
SYNC
SYNC
SYNC
'msShut_Enable = 0
'IF (AIN(X,1) > 1.60) THEN msShut_Enable = 1 END IF

'Record PumpA_Enable 3 ms later
 SYNC
SYNC
SYNC
PumpA_Enable=0
IF(AIN:0::( 1)>1.6000000000000001)THEN
PumpA_Enable=1
END IF

'Read 4 bits that define mode (every 3 ms)
 N_temp=0
FOR i=0 TO 3
SYNC
SYNC
SYNC
IF(AIN:0::( 1)>1.6000000000000001)THEN
N_temp=N_temp+2^i
END IF
NEXT i
N_mode=N_temp

'Read 6 bits that define delay (every 3 ms)
 N_temp=0
FOR i=0 TO 5
SYNC
SYNC
SYNC
IF(AIN:0::( 1)>1.6000000000000001)THEN
N_temp=N_temp+2^i
END IF
NEXT i
N_control=N_temp
DOUT:0::0, 2'marks when bit pattern is read
'4 ms from rising edge to trigger detection
'37 ms from trigger detection to finish reading bit pattern

END FUNCTION
