 PROGRAM 
ABS
PVT_INIT  @1 
VELOCITY ON
HALT
SCOPEBUFFER 1200
SCOPETRIGPERIOD-2' -4 (-2) corresponds to 4 (2) kHz
SCOPETRIG

DT=0.024
DY=0.5
Ti=0.001

Ti=Ti+DT
Yi=Yi+DY
PVT 1: Yi, 0 @Ti 
Ti=Ti+3*DT
PVT 1: Yi, 0 @Ti 
Ti=Ti+DT
Yi=Yi+DY
PVT 1: Yi, 0 @Ti 
Ti=Ti+3*DT
PVT 1: Yi, 0 @Ti 
Ti=Ti+DT
Yi=Yi+DY
PVT 1: Yi, 0 @Ti 
Ti=Ti+3*DT
PVT 1: Yi, 0 @Ti 
Ti=Ti+4*DT
Yi=Yi-3*DY
PVT 1: Yi, 0 @Ti 

START
END PROGRAM 
