' ------------------------------------------------ 
' ------- Ensemble_SAXS.ab version 1.4 ------------
' ------------------------------------------------ 
'
'

DIM PrintString AS STRING(80)
DGLOBAL(0)=0'Is this necessary?

Plane 1
RECONCILE 2,4,6

T_offset=0'0.65 'time offset in units of DT; centers msShut_ext opening on x-ray pulse

'Timing parameters (rescale DT to approximately match the source frequency)
 DT=0.0010126899166666666'~1000 Hz; 275th subharmonic of P0
'DT = 0.9999943*DT 'correction to match APS frequency
'DT = 0.999998412*DT 'oscillator correctison relative to Ramsey RF (351.93398 MHz)
'DT = 1.0002307*DT 'oscillator correction for DG535
 DT=1.0000034*(1.0055228571428572)*DT'FPGA internal oscillator; 0.9999962 for Pico24

'Sample cell parameters
 Nslots=41
DZ=0.60999999999999999'slot separation
 Z_1=-11.44' at APS; slot 1 position w/ cooling water set to 5 Celsius.
Z_1=-11.6' at NIH
Z_start=Z_1-DZ
Z_end=Z_start+( Nslots+1)*DZ' end-point of the stroke
Z_mid=Z_start+0.5*( Nslots+1)*DZ'mid-point of the stroke
 Z_v=DZ/(4*DT)'velocity of sample cell in fly-thru mode (~150 mm/s)
 Z_vmax=1.5*(Nslots+1)*DZ/(60*DT)'Z velocity at midpoint of return stroke (mm/s)

'Axis Z parameters
'SETGAIN <Axis>, <GainKp>, <GainKi>, <GainKpos>, <GainAff>
'SETGAIN sets all 4 parameters synchronously
SETGAIN 2:1780000, 10000,56.200000000000003,56200 'original settings
SETPARM 2: GainVff, 0 'original setting
'SETGAIN Z, 1780000, 7500, 133, 5620 'New settings
'SETPARM Z, GainVff, 3162

'Millisecond shutter parameters; determined at BioCARS in Feb 2015
'SETGAIN msShut_ext, 180900, 2621, 59, 260700
'SETPARM msShut_ext, GainVff, 5932

'Find current position of Z, msShut, and PumpA
 Z_pos=PCMD(2)
msShut_current=PCMD(6)
PumpA_pos=PLANEPOS(4)
PumpA_step=0.10000000000000001'uL

'Set up ms shutter parameters; ensure msShut is set to the nearest closed state.
 msShut_open=9.9900000000000002'Angle at center of opening
 msShut_step=8.7699999999999996'Step angle to open/close the shutter
 msShut_close1=msShut_open-msShut_step
msShut_close2=msShut_open+msShut_step
IF msShut_current<msShut_open THEN
msShut_pos1=msShut_close1
ELSE
msShut_pos1=msShut_close2
END IF

DOUT:0::1, 0'Ensure all bits of digital output are low when starting

'Set up for PVT calls
 ABS'Positions specified in absolute coordinates
PVT_INIT  @1 
 VELOCITY ON
HALT

'Wait for start of pulse pattern to synchronize start of motion
 WHILE DIN:0::( 1,0)=0'wait for next low-to-high transition.
 DWELL 0.00025000000000000001
WEND
DWELL 0.029999999999999999'wait till after burst is over (30 ms is more than enough.
 WHILE DIN:0::( 1,0)=0'wait for next low-to-high transition.
 DWELL 0.00025000000000000001
WEND

'query DIN(X,1,0) every 2 ms to determine the mode of operation (msShut_Enable, PumpA_Enable, and N_mode)
 STARTSYNC 2
SYNC
msShut_Enable=DIN:0::( 1,0)
SYNC
PumpA_Enable=DIN:0::( 1,0)
N_mode=0
FOR i=0 TO 3
SYNC
N_mode=N_mode+DIN:0::( 1,0)*2^i
NEXT i
Last_Mode=N_mode

'Synchronize start (timing is mode dependent).

IF N_mode>0 AND N_mode<6 THEN
T_0=(252)*DT
Scope_Dwell_Time=0.19
ELSEIF N_mode>5 THEN
N_step=N_mode-6
'T_0 = (1056+12)*DT
 T_0=12*((1+2^N_step)*41+7)*DT
Scope_Dwell_Time=1
END IF

'Move motors into position to start.
PVT 2: Z_pos, 0,4: PumpA_pos, 0,6: msShut_current, 0 @0.001 |DOUT 0:1, 0,1 
PVT 2: Z_end, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @( T_0-60*DT) |DOUT 0:1, 0,1 
PVT 2: Z_start, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @T_0 |DOUT 0:1, 0,1 
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
msShut_current=PCMD(6)
SYNC
msShut_Enable=DIN:0::( 1,0)
SYNC
PumpA_Enable=DIN:0::( 1,0)
N_mode=0
FOR i=0 TO 3
SYNC
N_mode=N_mode+DIN:0::( 1,0)*2^i
NEXT i

IF N_mode=2 THEN'Fly-thru mode	
 IF msShut_current<msShut_open THEN
msShut_pos1=msShut_close1
ELSE
msShut_pos1=msShut_close2
END IF
IF msShut_Enable THEN
msShut_pos2=msShut_open
ELSE
msShut_pos2=msShut_pos1
END IF
'open msShut
'PVT Z Z_start+0.25*DZ,0.5*Z_v msShut_ext msShut_pos1,0 PumpA PumpA_pos,0 TIME (T_0+8*DT) DOUT X,1,4,15
'PVT Z Z_start+0.111*DZ,0.333*Z_v msShut_ext msShut_pos1,0 PumpA PumpA_pos,0 TIME (T_0+4*DT) DOUT X,1,4,15
'PVT Z Z_start+0.444*DZ,0.666*Z_v msShut_ext msShut_pos1,0 PumpA PumpA_pos,0 TIME (T_0+8*DT) DOUT X,1,4,15
PVT 2: Z_start, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @( T_0+4*DT) |DOUT 0:1, 4,15 
PVT 2:Z_start+0.25*DZ,0.5*Z_v,4: PumpA_pos, 0,6: msShut_pos1, 0 @( T_0+8*DT) |DOUT 0:1, 4,15 
 FOR i=1 TO Nslots
Zi=Z_start+i*DZ
Ti=T_0+(4*i+8)*DT
PVT 2: Zi, Z_v,4: PumpA_pos, 0,6: msShut_pos2, 0 @Ti |DOUT 0:1, 3,15 
NEXT i
'close msShut; move to Z_end; return to Z_start.
PVT 2:Zi+0.75*DZ,0.5*Z_v,4: PumpA_pos, 0,6: msShut_pos1, 0 @( Ti+4*DT) |DOUT 0:1, 0,15 
PVT 2: Z_end, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @ T_0+( 180)*DT |DOUT 0:1, 0,15 
 PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
'PVT Z Z_start+0.1*DZ,-1*Z_v TIME T_0+236*DT DOUT X,1,0,15	
PVT 2: Z_start, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @T_0+240*DT |DOUT 0:1, 0,15 
 T_0=T_0+240*DT'252*DT -> 3.92 Hz; 240*DT -> 4.1 Hz

ELSEIF N_mode>5 THEN'Stepping mode
 IF msShut_current<msShut_open THEN
msShut_pos1=msShut_close1
msShut_pos3=msShut_close2
msShut_Vmax=msShut_step/(4*DT)
ELSE
msShut_pos1=msShut_close2
msShut_pos3=msShut_close1
msShut_Vmax=-1*msShut_step/(4*DT)
END IF
IF msShut_Enable THEN
msShut_pos2=msShut_open
ELSE
msShut_Vmax=0
msShut_pos2=msShut_pos1
msShut_pos3=msShut_pos1
END IF
N_step=N_mode-6
PVT 2: Z_start+DZ, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @( T_0+12*DT) |DOUT 0:1, 1,15 
FOR i=1 TO Nslots
Zi=Z_start+i*DZ
Ti=T_0+12*(1+2^N_step)*i*DT
'Move to slot and stop; open then close msShut; move to next slot and stop; open then close msShut
PVT 2: Zi, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @( Ti-6*DT) |DOUT 0:1, 1,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,6: msShut_pos2, msShut_Vmax @Ti |DOUT 0:1, 3,15 
PVT 2: Zi+0.5*DZ, 75,4: PumpA_pos, 0,6: msShut_pos3, 0 @( Ti+6*DT) |DOUT 0:1, 1,15 
PVT 2: Zi+DZ, 0,4: PumpA_pos, 0,6: msShut_pos3, 0 @( Ti+12*DT) |DOUT 0:1, 1,15 
 temp=msShut_pos3
msShut_pos3=msShut_pos1
msShut_pos1=temp
msShut_Vmax=-1*msShut_Vmax
NEXT i
'T_0 = T_0 + 1056*DT
 T_0=T_0+12*((1+2^N_step)*41+6)*DT
PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
PVT 2: Z_start, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @T_0 |DOUT 0:1, 0,15 
'1056*DT -> 0.935 Hz

ELSEIF N_mode>=4 AND N_mode<=7 THEN'Exotic Modes (16, 32, 64, and 128 ms time delays)
 IF N_mode=4 THEN
N_steps=206
ELSEIF N_mode=5 THEN
N_steps=154
ELSE
N_Steps=138
END IF
N_exotic=N_mode-3


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

N=N_mode-3
slot=0
FOR i=1 TO N_steps
R=(2^N-1)/(3*2^N-1)
R1=(i-2^N-1)/(3*2^N-1)'Slot position
 R2=(i+1-2^N-1)/(3*2^N-1)'Next Slot position
 R3=(i-1)/(3*2^N-1)'Laser trigger
 R4=(i-2^( N+1)-1)/(3*2^N-1)'X-ray trigger
 DIFF1=ABS(R1-FLOOR(R1))-0.001
DIFF2=ABS(R2-FLOOR(R2))-0.001
DIFF3=R3-FLOOR(R3)+0.001
DIFF4=R4-FLOOR(R4)+0.001
IF(DIFF1>R)THEN
slot=slot+1
Z_dir=1
ELSE
slot=slot-1
Z_dir=-1
END IF

L=0
IF(DIFF3<R)AND(slot<42)THEN
L=1
END IF
X=0
IF(DIFF4<R)AND(slot<42)THEN
X=1
END IF
S=slot
IF slot>42 THEN
S=42
END IF
IF(Z_dir=1)AND(DIFF2>R)THEN
Z_vel=1
ELSEIF(Z_dir=-1)AND(DIFF2<R)THEN
Z_vel=-1
ELSE
Z_vel=0
END IF
IF S=42 THEN Z_vel=0
END IF

'FORMAT PrintString, "%d,%d,%d,%d,%d\r",INTV:i,INTV:S,INTV:Z_vel,INTV:L,INTV:X
'PRINT PrintString

Zi=Z_start+S*DZ
Ti=T_0+4*i*DT

'Move to slot and stop; open then close msShut; move to next slot and stop; open then close msShut
PVT 2: Zi, Z_V*Z_vel,4: PumpA_pos, 0,6: msShut_pos1, 0 @Ti |DOUT 0:1, 1,15 

NEXT i


T_0=T_0+( N_steps+15)*4*DT
'PVT Z Z_end,0 msShut_ext msShut_pos3,0 PumpA PumpA_pos,0 TIME (T_0-60*DT) DOUT X,1,0,15
 PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
PVT 2: Z_start, 0,4: PumpA_pos, 0,6: msShut_pos3, 0 @T_0 |DOUT 0:1, 0,15 
'1056*DT -> 0.935 Hz

ELSEIF N_mode=0 THEN'Idle mode
 IF(msShut_current-msShut_open)>msShut_step/2 THEN
msShut_pos1=msShut_open+msShut_step
msShut_pos3=msShut_open-msShut_step
msShut_Vmax=-1*msShut_step/(4*DT)
ELSE
msShut_pos1=msShut_open-msShut_step
msShut_pos3=msShut_open+msShut_step
msShut_Vmax=msShut_step/(4*DT)
END IF
msShut_pos2=msShut_open
IF msShut_Enable=0 THEN
msShut_Vmax=0
msShut_pos2=msShut_pos1
msShut_pos3=msShut_pos1
END IF

FOR i=1 TO Nslots-1 STEP 2
Ti=T_0+24*i*DT
PVT 6: msShut_pos1, 0 @( Ti-6*DT) |DOUT 0:1, 1,15 
PVT 6: msShut_pos2, msShut_Vmax @Ti |DOUT 0:1, 3,15 
PVT 6: msShut_pos3, 0 @( Ti+6*DT) |DOUT 0:1, 1,15 
PVT 6: msShut_pos3, 0 @( Ti+18*DT) |DOUT 0:1, 1,15 
PVT 6:msShut_pos2,-1*msShut_Vmax @( Ti+24*DT) |DOUT 0:1, 3,15 
PVT 6: msShut_pos1, 0 @( Ti+30*DT) |DOUT 0:1, 1,15 
Next i
T_0=T_0+1056*DT
PVT 6: msShut_pos1, 0 @T_0 |DOUT 0:1, 1,15 
PumpA_Pos=PLANEPOS(4)

ELSEIF N_mode=1 THEN'Single-slot mode
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
PVT 2: Zi, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @( Ti-12*DT) |DOUT 0:1, 1,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @( Ti-4*DT) |DOUT 0:1, 7,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,6: msShut_pos2, 0 @Ti |DOUT 0:1, 3,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,6: msShut_pos2, 0 @( Ti+160*DT) |DOUT 0:1, 3,15 
PVT 2: Zi, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @( Ti+164*DT) |DOUT 0:1, 3,15 
PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
T_0=T_0+252*DT
NEXT i
PVT 2: Z_end, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @T_0-60*DT |DOUT 0:1, 0,15 
PumpA_pos=PumpA_pos+PumpA_step*PumpA_Enable
PVT 2: Z_start, 0,4: PumpA_pos, 0,6: msShut_pos1, 0 @T_0 |DOUT 0:1, 0,15 


ELSE'The following ELSE code does strange things.
'PVT Z Z_start,0 msShut_ext msShut_closed,0 PumpA PumpA_pos,0 TIME (T_0+24*DT) DOUT X,1,4,15
'PVT Z Z_start,0 msShut_ext msShut_closed,0 PumpA PumpA_pos,0 TIME (T_0+26*DT) DOUT X,1,0,15
 T_0=T_0+1056*DT
END IF

'FORMAT PrintString, "%d,%.3f,%.3f,%.3f,%.3f\n",
'INTV:j,DBLV:T_1,DBLV:T_2,DBLV:T_3,DBLV:T_4
'PRINT PrintString
'FORMAT PrintString, "%d,%.3f,%.3f,%.3f,%.3f\n",
'INTV:j,DBLV:Z_1,DBLV:Z_2,DBLV:Z_3,DBLV:Z_4
'PRINT PrintString


' Correct phase if necessary
IF(Last_Mode=N_mode)AND(N_mode<>0)THEN
IF j=0 THEN
Zpos=0
Zpos_sum=0
Zpos_sumsq=0
counter=1
END IF

Zpos_sum=Zpos_sum+Zpos
Zpos_sumsq=Zpos_sumsq+Zpos^2
stdev=sqr(Zpos_sumsq/counter-( Zpos_sum/counter)^2)
pos_err=Zpos_sum/counter-Z_mid+0.434+T_offset*DT*Z_vmax'tweaked to 0.434 to center rising edge on central slot
 counter=counter+1
IF(counter>32)AND(abs(pos_err)>2*(stdev/sqr(counter)))THEN
FORMAT PrintString,"%d,%.3f,%.5f,%.5f\r",
INTV:counter,DBLV:pos_err,DBLV:stdev,DBLV:pos_err/Z_vmax
PRINT PrintString
T_correction=pos_err/Z_vmax'divide pos_err by Z_vmax to convert to time
 T_max=0.0040000000000000001
IF(T_correction>T_max)THEN
T_correction=T_max
ELSEIF(T_correction<-1*T_max)THEN
T_correction=-1*T_max
END IF
T_0=T_0-T_correction
Zpos_sum=0
Zpos_sumsq=0
counter=1
END IF
END IF

'FORMAT PrintString, "%d,%.3f,%.3f,\n", INTV:N_mode,DBLV:pos_err,DBLV:stdev
'PRINT PrintString
 Last_Mode=N_mode
j=j+1
WEND
