' ------------------------------------------------ 
' --------------- PVT_250Hz_FastReturn.ab -----------------
' ------------------------------------------------ 
'
'
'velocity is ~150 mm/ms
'

DGLOBAL(3)=1'mode of operation
 DGLOBAL(0)=0'time offset to synchronize
 DGLOBAL(1)=0'counter for computing <PMCD(Z)>

'User input (Z_0, PumpA_step)
 Z_0=12.949999999999999'slot 0 position -> 13.000 on 12/14/14
 DZ=0.60999999999999999'slot separation
 Nslots=41
PumpA_step=1
DT=0.0040507596666666664'~250 Hz



DT=0.99999841199999995*DT'oscillator correction
 Z_mid=Z_0-0.5*( Nslots-1)*DZ'mid-point of the stroke
 Z_N=Z_0-( Nslots-0.5)*DZ' end-point of the stroke
Vn=-1*DZ/DT'velocity of sample cell


'SETGAIN <Axis>, <GainKp>, <GainKi>, <GainKpos>, <GainAff>
'SETGAIN sets all 4 parameters synchronously
SETGAIN 2:1780000, 10000,100,56200 
SETPARM 2: GainVff, 2371 

DIM PrintString AS STRING(80)

'Initial setup for Z axis
 IF AXISFAULT(2)<>0 THEN
FAULTACK 2'Make sure any fault state is cleared.
END IF
ENABLE 2
DIM homed AS INTEGER
homed=(AXISSTATUS(2) >> 1) BAND 1
IF NOT homed THEN'make sure axis is homeds
HOME 2
 END IF
MOVEABS 2:Z_N 'Go to starting position
WAIT MOVEDONE 2

DOUT:0::1, 0:0'Ensure digital output is low when starting

'Find current position of PumpA
 PumpA_0=PCMD(4)

'Set up for PVT calls
 ABS'Positions specified in absolute coordinates
PVT_INIT  @1 
 HALT

WHILE DIN:0::( 1,0)=0'wait for clk pulse 
 DWELL 0.00025000000000000001
WEND

SCOPETRIG

DWELL 0.192'Find DWELL time needed to phase the start of the Z motion

j=0
PVT 2: Z_N, 0,4: PumpA_0, 0 @0.001 |DOUT 0:1, 0,1 
WHILE DGLOBAL(3)>0'insert IF statements to select mode; mode 0 ends  motion
 PumpA_pos=PumpA_0+j*PumpA_step
T_0=15*DT+j*57*DT+DGLOBAL(0)'57 -> 4.33 Hz
FOR i=-1TO Nslots+1
Zi=Z_0-i*DZ
Ti=T_0+i*DT
IF i=-1
THEN
PVT 2:(Zi-DZ/2),0,4: PumpA_pos, 0 @Ti |DOUT 0:1, 0,1 
ELSEIF i=Nslots+1
THEN
PVT 2:(Zi+DZ/2),0,4: PumpA_pos, 0 @Ti |DOUT 0:1, 0,1 
IF j=0 THEN
DGLOBAL(1)=0'reset PLL counter
 END IF
ELSE
PVT 2: Zi, Vn,4: PumpA_pos, 0 @Ti |DOUT 0:1, 1,1 

END IF
NEXT i

'FORMAT PrintString, "%d,%.3f,%.3f,%.3f,%.3f\n",
'INTV:j,DBLV:T_1,DBLV:T_2,DBLV:T_3,DBLV:T_4
'PRINT PrintString
'FORMAT PrintString, "%d,%.3f,%.3f,%.3f,%.3f\n",
'INTV:j,DBLV:Z_1,DBLV:Z_2,DBLV:Z_3,DBLV:Z_4
'PRINT PrintString


'correct phase every 64 repeats (if err > 5 um)

IF(j<>0)AND(j/64-FLOOR(j/64))=0
THEN
pos_err=DGLOBAL(2)-Z_mid
IF ABS(pos_err)>0.0030000000000000001
THEN'divide pos_err by Vmax -> 616 mm/s during back stroke
 DGLOBAL(0)=DGLOBAL(0)+pos_err/616
END IF
DGLOBAL(1)=0
FORMAT PrintString,"%d,%.3f,%.5f\r",
INTV:j,DBLV:pos_err,DBLV:DGLOBAL(0)
PRINT PrintString
END IF

'FORMAT PrintString, "%d\n", INTV:j
'PRINT PrintString
 j=j+1
WEND
MOVEABS 2:Z_0 'Go to first slot
