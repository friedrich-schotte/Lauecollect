 PROGRAM 
ABS
PVT_INIT  @1 
VELOCITY ON
HALT
SCOPEBUFFER 600
SCOPETRIGPERIOD-4' -4 (-2) corresponds to 4 (2) kHz
SCOPETRIG

DT=0.012
DZ=0.5
Ti=0.001

Ti=Ti+DT
Zi=Zi+DZ
PVT 2: Zi, 0 @Ti 
Ti=Ti+DT
PVT 2: Zi, 0 @Ti 
Ti=Ti+DT
Zi=Zi+DZ
PVT 2: Zi, 0 @Ti 
Ti=Ti+DT
PVT 2: Zi, 0 @Ti 
Ti=Ti+DT
Zi=Zi+DZ
PVT 2: Zi, 0 @Ti 
Ti=Ti+DT
PVT 2: Zi, 0 @Ti 
Ti=Ti+4*DT
Zi=Zi-3*DZ
PVT 2: Zi, 0 @Ti 

START
END PROGRAM 
