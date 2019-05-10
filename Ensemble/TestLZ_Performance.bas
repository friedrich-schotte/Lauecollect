 PROGRAM 
ABS
PVT_INIT  @1 
VELOCITY ON
HALT
SCOPEBUFFER 1200
SCOPETRIGPERIOD-4' -4 (-2) corresponds to 4 (2) kHz
SCOPETRIG

DT=0.071999999999999995
DLZ=2.25
Ti=0.001
LZi=0

'Ti = Ti + DT
PVT 5: LZi, 0 @Ti 
 Ti=Ti+DT
LZi=LZi+DLZ
PVT 5: LZi, 0 @Ti 
Ti=Ti+10*DT
'LZi = LZi + DLZ
PVT 5: LZi, 0 @Ti 
'Ti = Ti + DT
'PVT LZ LZi,0 TIME Ti
'Ti = Ti + DT
'LZi = LZi + DLZ
'PVT LZ LZi,0 TIME Ti
'Ti = Ti + DT
'PVT LZ LZi,0 TIME Ti
 Ti=Ti+4*DT
LZi=LZi-DLZ
PVT 5: LZi, 0 @Ti 

START
END PROGRAM 
