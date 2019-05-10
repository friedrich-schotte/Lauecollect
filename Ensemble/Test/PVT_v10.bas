' ------------------------------------------------ 
' ------- PVT_PLL_Translation.ab -----------------
' ------------------------------------------------ 
'
'

DIM PrintString AS STRING(80)
DGLOBAL(0)=0'Is this necessary?

'Sample cell parameters
 Nslots=41
DZ=0.60999999999999999'slot separation
 Z_1=-11.6'-11.42 for slot 1 position w/ cooling water set to 5 Celsius.
Z_start=Z_1-DZ
Z_end=Z_start+( Nslots+1)*DZ' end-point of the stroke
Z_mid=Z_start+0.5*( Nslots+1)*DZ'mid-point of the stroke

'Timing parameters (rescale DT to approximately match the source frequency)
 DT=0.0010126899166666666'~1000 Hz; 275th subharmonic of P0
'DT = 0.999998412*DT 'oscillator correction relative to Ramsey RF (351.93398 MHz)
'DT = 1.0002307*DT 'oscillator correction for DG535
 DT=0.99999700000000002*(1.0055228571428572)*DT'FPGA internal oscillator


'Axis Z parameters
'SETGAIN <Axis>, <GainKp>, <GainKi>, <GainKpos>, <GainAff>
'SETGAIN sets all 4 parameters synchronously
'SETGAIN Z, 1780000, 10000, 56.2, 56200 original settings
SETGAIN 2:1780000, 10000,56.200000000000003,56200 
SETPARM 2: GainVff, 0 
 V_z=DZ/(4*DT)'velocity of sample cell (~150 mm/s)
 Vmax=626'Z velocity at midpoint of return stroke (mm/s)

'Millisecond shutter parameters
SETGAIN 5:370600, 12480,137.90000000000001,74580 
SETPARM 5: GainVff, 316.80000000000001 
 msShut_open=11.77'Angle at center of opening
 msShut_step=9.2699999999999996'Step angle to open/close the shutter

'Find current position of Z, msShut, and PumpA
 Z_pos=PCMD(2)
msShut_current=PCMD(5)
PumpA_pos=PCMD(4)

'Ensure the msShut_pos is set to the nearest closed state.
 IF(msShut_current-msShut_open)>msShut_step/2 THEN
msShut_closed=msShut_open+msShut_step
ELSE
msShut_closed=msShut_open-msShut_step
END IF

DOUT:0::1, 0'Ensure all bits of digital output are low when starting

'Set up for PVT calls
 ABS'Positions specified in absolute coordinates
PVT_INIT  @1 
 VELOCITY ON
HALT

WHILE DIN:0::( 1,0)=0'wait for next low-to-high transition.
 DWELL 0.00025000000000000001
WEND
DWELL 0.029999999999999999'wait till after burst is over (30 ms is more than enough.
 WHILE DIN:0::( 1,0)=0'wait for clk pulse 
 DWELL 0.00025000000000000001
WEND
STARTSYNC 2'query DIN(X,1,0) every 2 ms to measure the pulse width (N_mode)
 Zpos=PCMD(2)
msShut_current=PCMD(5)
SYNC
msShut_Enable=DIN:0::( 1,0)
SYNC
PumpA_Enable=DIN:0::( 1,0)
N_mode=0
FOR i=0 TO 2
SYNC
N_mode=N_mode+DIN:0::( 1,0)*2^i
NEXT i

Scope_Dwell_Time=0.20000000000000001
T_0=(266)*DT'Time to synchronize start (mode dependent).
 IF N_mode=3 THEN
T_0=(1070)*DT
Scope_Dwell_Time=1
END IF

PVT 2: Z_pos, 0,4: PumpA_pos, 0,5: msShut_current, 0 @0.001 |DOUT 0:1, 0,1 
PVT 2: Z_end, 0,4: PumpA_pos, 0,5: msShut_closed, 0 @( T_0-60*DT) |DOUT 0:1, 0,1 
PVT 2: Z_start, 0,4: PumpA_pos, 0,5: msShut_closed, 0 @T_0 |DOUT 0:1, 0,1 
START

DWELL Scope_Dwell_Time'Delay to synchronize scope near the start of the scan.
 SCOPETRIG

j=0
WHILE DGLOBAL(0)>-1'enter DGLOBAL(0) = -1 to exit loop
 WHILE DIN:0::( 1,0)=0'wait for clk pulse 
 DWELL 0.00025000000000000001
WEND
STARTSYNC 2'query DIN(X,1,0) every 2 ms to measure the pulse width (N_mode)
 Zpos=PCMD(2)
msShut_current=PCMD(5)
SYNC
msShut_Enable=DIN:0::( 1,0)
SYNC
PumpA_Enable=DIN:0::( 1,0)
N_mode=0
FOR i=0 TO 2
SYNC
N_mode=N_mode+DIN:0::( 1,0)*2^i
NEXT i

IF N_mode=2 THEN
PumpA_step=1.8'1.8 deg is 1 step		
msShut_current=PCMD(5)
IF(msShut_current-msShut_open)>msShut_step/2 THEN
msShut_pos1=msShut_open+msShut_step
ELSE
msShut_pos1=msShut_open-msShut_step
END IF
msShut_pos2=msShut_pos1
IF msShut_Enable THEN
msShut_pos2=msShut_open
END IF
'open msShut
PVT 2: Z_start, V_z,4: PumpA_pos, 0,5: msShut_pos1, 0 @( T_0+20*DT) |DOUT 0:1, 0,1 
 FOR i=1 TO Nslots
Zi=Z_start+i*DZ
Ti=T_0+(4*i+20)*DT
PVT 2: Zi, V_z,4: PumpA_pos, 0,5: msShut_pos2, 0 @Ti |DOUT 0:1, 3,1 
NEXT i
'close msShut; move to Z_end; return to Z_start.
PVT 2:Zi+0.75*DZ,0.5*V_z,4: PumpA_pos, 0,5: msShut_pos1, 0 @( Ti+4*DT) |DOUT 0:1, 0,1 
PVT 2: Z_end, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @ T_0+( 192)*DT |DOUT 0:1, 0,1 
 PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
PVT 2: Z_start, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @T_0+252*DT |DOUT 0:1, 0,1 
T_0=T_0+252*DT'252*DT -> 3.92 Hz

ELSEIF N_mode=3 THEN
PumpA_step=1.8
IF(msShut_current-msShut_open)>msShut_step/2 THEN
msShut_pos1=msShut_open+msShut_step
msShut_pos3=msShut_open-msShut_step
msShut_Vmax=-1.5*msShut_step/(4*DT)
ELSE
msShut_pos1=msShut_open-msShut_step
msShut_pos3=msShut_open+msShut_step
msShut_Vmax=1.5*msShut_step/(4*DT)
END IF
msShut_pos2=msShut_open
IF msShut_Enable=0 THEN
msShut_Vmax=0
msShut_pos2=msShut_pos1
msShut_pos3=msShut_pos1
END IF
FOR i=1 TO Nslots-1 STEP 2
Zi=Z_start+i*DZ
Ti=T_0+24*i*DT
'Move to slot and stop; open then close msShut; move to next slot and stop; open then close msShut
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @( Ti-12*DT) |DOUT 0:1, 1,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @( Ti-4*DT) |DOUT 0:1, 1,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos2, msShut_Vmax @Ti |DOUT 0:1, 3,15 
PVT 2: Zi+0.156, 66,4: PumpA_pos, 0,5: msShut_pos3, 0 @( Ti+4*DT) |DOUT 0:1, 1,15 
PVT 2: Zi+DZ, 0,4: PumpA_pos, 0,5: msShut_pos3, 0 @( Ti+12*DT) |DOUT 0:1, 1,15 
PVT 2: Zi+DZ, 0,4: PumpA_pos, 0,5: msShut_pos3, 0 @( Ti+20*DT) |DOUT 0:1, 1,15 
PVT 2: Zi+DZ, 0,4: PumpA_pos, 0,5:msShut_pos2,-1*msShut_Vmax @( Ti+24*DT) |DOUT 0:1, 3,15 
PVT 2: Zi+DZ+0.156, 66,4: PumpA_pos, 0,5: msShut_pos1, 0 @( Ti+28*DT) |DOUT 0:1, 1,15 
 NEXT i
i=41
Zi=Z_start+i*DZ
Ti=T_0+24*i*DT
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @( Ti-12*DT) |DOUT 0:1, 1,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @( Ti-4*DT) |DOUT 0:1, 5,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos2, msShut_Vmax @Ti |DOUT 0:1, 3,15 
PVT 2: Zi+0.156, 66,4: PumpA_pos, 0,5: msShut_pos3, 0 @( Ti+4*DT) |DOUT 0:1, 1,15 
T_0=T_0+1056*DT
PVT 2: Z_end, 0,4: PumpA_pos, 0,5: msShut_pos3, 0 @( T_0-60*DT) |DOUT 0:1, 0,15 
PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
PVT 2: Z_start, 0,4: PumpA_pos, 0,5: msShut_pos3, 0 @T_0 |DOUT 0:1, 0,15 
'1056*DT -> 0.935 Hz

ELSEIF N_mode=0 THEN
PumpA_step=45
PVT 2: Z_1, 0,4: PumpA_pos, 0,5: msShut_closed, 0 @( T_0+24*DT) |DOUT 0:1, 0,15 
PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
PVT 2: Z_1, 0,4: PumpA_pos, 0,5: msShut_closed, 0 @( T_0+(192)*DT) |DOUT 0:1, 4,15 
PVT 2: Z_start, 0,4: PumpA_pos, 0,5: msShut_closed, 0 @( T_0+252*DT) |DOUT 0:1, 0,15 
T_0=T_0+252*DT
ELSEIF N_mode=1 THEN
PumpA_step=1.8
IF(msShut_current-msShut_open)>msShut_step/2 THEN
msShut_pos1=msShut_open+msShut_step
msShut_pos3=msShut_open-msShut_step
msShut_Vmax=-1.5*msShut_step/(4*DT)
ELSE
msShut_pos1=msShut_open-msShut_step
msShut_pos3=msShut_open+msShut_step
msShut_Vmax=1.5*msShut_step/(4*DT)
END IF
msShut_pos2=msShut_open
IF msShut_Enable=0 THEN
msShut_Vmax=0
msShut_pos2=msShut_pos1
msShut_pos3=msShut_pos1
END IF
FOR i=1 TO Nslots
Zi=Z_start+i*DZ
Ti=T_0+24*DT
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @( Ti-12*DT) |DOUT 0:1, 1,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @( Ti-4*DT) |DOUT 0:1, 7,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos2, 0 @Ti |DOUT 0:1, 3,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos2, 0 @( Ti+160*DT) |DOUT 0:1, 3,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @( Ti+164*DT) |DOUT 0:1, 3,15 
PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
T_0=T_0+252*DT
NEXT i
PVT 2: Z_end, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @T_0-60*DT |DOUT 0:1, 0,15 
PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
PVT 2: Z_start, 0,4: PumpA_pos, 0,5: msShut_pos1, 0 @T_0 |DOUT 0:1, 0,15 


ELSE'The following ELSE code does strange things.
PVT 2: Z_start, 0,4: PumpA_pos, 0,5: msShut_closed, 0 @( T_0+24*DT) |DOUT 0:1, 4,15 
PVT 2: Z_start, 0,4: PumpA_pos, 0,5: msShut_closed, 0 @( T_0+26*DT) |DOUT 0:1, 0,15 
 T_0=T_0+1056*DT
END IF

'FORMAT PrintString, "%d,%.3f,%.3f,%.3f,%.3f\n",
'INTV:j,DBLV:T_1,DBLV:T_2,DBLV:T_3,DBLV:T_4
'PRINT PrintString
'FORMAT PrintString, "%d,%.3f,%.3f,%.3f,%.3f\n",
'INTV:j,DBLV:Z_1,DBLV:Z_2,DBLV:Z_3,DBLV:Z_4
'PRINT PrintString


' Correct phase if necessary
IF(N_mode=2)OR(N_mode=3)THEN
IF j=0 THEN
Zpos=0
Zpos_sum=0
Zpos_sumsq=0
counter=1
END IF

Zpos_sum=Zpos_sum+Zpos
Zpos_sumsq=Zpos_sumsq+Zpos^2
stdev=sqr(Zpos_sumsq/counter-( Zpos_sum/counter)^2)
pos_err=Zpos_sum/counter-Z_mid+0.434'tweaked to 0.434 to center rising edge on central slot
 counter=counter+1
IF(counter>32)AND(abs(pos_err)>2*(stdev/sqr(counter)))THEN
FORMAT PrintString,"%d,%.3f,%.5f,%.5f\r",
INTV:counter,DBLV:pos_err,DBLV:stdev,DBLV:pos_err/Vmax
PRINT PrintString
T_0=T_0-pos_err/Vmax'divide pos_err by Vmax to convert to time
 Zpos_sum=0
Zpos_sumsq=0
counter=1
END IF
END IF
'FORMAT PrintString, "%d,%.3f,%.3f,\n", INTV:N_mode,DBLV:pos_err,DBLV:stdev
'PRINT PrintString

j=j+1
WEND
