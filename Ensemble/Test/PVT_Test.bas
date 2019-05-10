STARTSYNC-1' -1 sets period to 500 us 
WHILE DIN:0::( 1,0)=0
SYNC
WEND

'SCOPETRIGPERIOD -2 '500 us period
 SCOPETRIG
DWELL 0.0030000000000000001
'Generate pulse before generating the trajectory.
DOUT:0::1, 0:1
DOUT:0::1, 0:0

'WAIT MODE MOVEDONE
'VELOCITY OFF
 ABS'Positions specified in absolute coordinates.
PVT_INIT  @1 



Z0=12.6'starting Z position
 DZ=0.60960000000000003'slot separation
 DT=0.012149999999999999'Delta time
 Nslots=41
Nrepeats=8

Nsteps=0

HALT

FOR j=0 TO Nrepeats-1
FOR i=0 TO Nslots-1
IF i<21
THEN Zi=Z0-2*i*DZ
ELSE Zi=Z0-(2*(Nslots-i)-1)*DZ
END IF
Ti1=(2*j*Nslots+2*i+1)*DT
Ti2=(2*j*Nslots+2*i+2)*DT
PVT 2: Zi, 0 @Ti1 
PVT 2: Zi, 0 @Ti2 
Nsteps=Nsteps+1
NEXT i
'Generate pulse after loading each round trip.
DOUT:0::1, 0:1
DOUT:0::1, 0:0
 NEXT j

'START


DIM PrintString AS STRING(80)
FORMAT PrintString,"%d\n",INTV:Nsteps
PRINT PrintString
'FAULTACK Z
