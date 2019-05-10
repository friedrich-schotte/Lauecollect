' ------------------------------------------------ 
' --------------- PVT_even_odd.ab -----------------
' ------------------------------------------------ 
'
' This program moves in a repetitive staircase
' fashion. 
'
'synchronize at 12.28 mm
'velocity is 75 mm/ms at 12.28 mm
'

DGLOBAL(0)=0'time offset to synchronize
 DGLOBAL(1)=0'counter for computing <PMCD(Z)>

Z_0=12.539999999999999'starting Z position
 DZ=0.60999999999999999'slot separation
 DT=0.024304558'Staircase Period
 DT=0.99999841199999995*DT
Z_synch=Z_0-0.29999999999999999'Vmax between slots 1 and 0

Nslots=41

'SETGAIN <Axis>, <GainKp>, <GainKi>, <GainKpos>, <GainAff>
'SETGAIN sets all 4 parameters synchronously
SETGAIN 2:1780000, 10000,100,56200 
SETPARM 2: GainVff, 2371 

DIM PrintString AS STRING(80)

'Initial setup
 IF AXISFAULT(2)<>0 THEN
FAULTACK 2'Make sure any fault state is cleared.
END IF
ENABLE 2
DIM homed AS INTEGER
homed=(AXISSTATUS(2) >> 1) BAND 1
IF NOT homed THEN'make sure axis is homeds
HOME 2
 END IF
MOVEABS 2:Z_0 'Got to starting position
WAIT MOVEDONE 2

ABS'Positions specified in absolute coordinates.s
PVT_INIT  @1 
 HALT

WHILE DIN:0::( 1,0)=0'wait for clk pulse 
 DWELL 0.00025000000000000001
WEND
DWELL 0.97199999999999998'0.971, 0.980 with Task 1 only


j=0
WHILE 1
FOR i=0 TO Nslots-1
PumpA_pos=j*1.8
T_0=j*43*DT+DGLOBAL(0)
Zi=Z_0-i*DZ
Ti1=T_0+( i+0.40000000000000002)*DT+DGLOBAL(0)
Ti2=T_0+( i+1)*DT+DGLOBAL(0)
IF i=40
THEN
PVT 2: Zi, 0 @Ti1 |DOUT 0:1, 0,1 
PVT 2: Zi, 0,4: PumpA_pos, 0 @Ti2 |DOUT 0:1, 1,1 
ELSE
PVT 2: Zi, 0 @Ti1 |DOUT 0:1, 0,1 
PVT 2: Zi, 0 @Ti2 |DOUT 0:1, 1,1 
END IF
NEXT i

'correct phase every 64 repeats (if err > 5 um)
 j=j+1
'IF (j/64 - FLOOR(j/64)) = 0
'	THEN
'		pos_err = DGLOBAL(2)-Z_synch
'		IF ABS(pos_err) > 0.003
'			THEN 
'				offset = pos_err/75
'				DGLOBAL(0) = DGLOBAL(0)+ pos_err/75
'		END IF
'		DGLOBAL(1) = 0
'END IF

'FORMAT PrintString, "%d\n", INTV:j
'PRINT PrintString
 WEND
