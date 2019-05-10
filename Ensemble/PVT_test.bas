 PROGRAM 
'Set up for PVT calls

motor=2'(0,1,2 -> X,Y,Z)

Plane 1
RECONCILE 2
Z_pos=PCMD(2)
RECONCILE 0
X_pos=PCMD(0)
RECONCILE 1
Y_pos=PCMD(1)


ABS'Positions specified in absolute coordinates
PVT_INIT  @1 
 VELOCITY ON
HALT

Scope_Trigger_Delay=0
SCOPETRIGPERIOD-4' 0.25 ms per point (4 kHz)
SCOPEBUFFER 1000
SCOPETRIG

Ti=0.001
DT=0.012

DX=0.10000000000000001
DY=0.20000000000000001
DZ=0.59999999999999998

IF motor=0 THEN
PVT 0: X_pos, 0 @Ti 
PVT 0: X_pos+DX, 0 @Ti+DT 
PVT 0: X_pos+DX, 0 @Ti+2*DT 
PVT 0: X_pos+2*DX, 0 @Ti+3*DT 
PVT 0: X_pos+2*DX, 0 @Ti+4*DT 
PVT 0: X_pos, 0 @Ti+10*DT 
END IF

IF motor=1 THEN
PVT 1: Y_pos, 0 @Ti 
PVT 1: Y_pos+DY, 0 @Ti+DT 
PVT 1: Y_pos+DY, 0 @Ti+2*DT 
PVT 1: Y_pos+2*DY, 0 @Ti+3*DT 
PVT 1: Y_pos+2*DY, 0 @Ti+4*DT 
PVT 1: Y_pos, 0 @Ti+10*DT 
END IF

IF motor=2 THEN
PVT 2: Z_pos, 0 @Ti 
PVT 2: Z_pos+DZ, 0 @Ti+DT 
PVT 2: Z_pos+DZ, 0 @Ti+2*DT 
PVT 2: Z_pos+2*DZ, 0 @Ti+3*DT 
PVT 2: Z_pos+2*DZ, 0 @Ti+4*DT 
PVT 2: Z_pos, 0 @Ti+10*DT 
END IF

START
DWELL 0.5
 PROGRAM STOP 1 
END PROGRAM 


