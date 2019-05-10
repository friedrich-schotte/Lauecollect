 PROGRAM 
ABS
PVT_INIT  @1 
VELOCITY ON
HALT
SCOPEBUFFER 1200
SCOPETRIGPERIOD-2' -4 (-2) corresponds to 4 (2) kHz
SCOPETRIG

DT=0.024
DX=0.5
Ti=0.001

Ti=Ti+DT
Xi=Xi+DX
PVT 0: Xi, 0 @Ti 
Ti=Ti+3*DT
PVT 0: Xi, 0 @Ti 
Ti=Ti+DT
Xi=Xi+DX
PVT 0: Xi, 0 @Ti 
Ti=Ti+3*DT
PVT 0: Xi, 0 @Ti 
Ti=Ti+DT
Xi=Xi+DX
PVT 0: Xi, 0 @Ti 
Ti=Ti+3*DT
PVT 0: Xi, 0 @Ti 
Ti=Ti+4*DT
Xi=Xi-3*DX
PVT 0: Xi, 0 @Ti 

START
END PROGRAM 
