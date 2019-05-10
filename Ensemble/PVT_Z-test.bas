 PROGRAM 

PLANE 1
RECONCILE 0,2
ABS'Positions specified in absolute coordinates
WAIT MODE MOVEDONE 
 Zstart=12
MOVEABS 2:Zstart:10 

Ti=0.001
DZ=-0.5
DT=0.001
ZV=DZ/(48*DT)
Zi=Zstart

SCOPEBUFFER 1200
SCOPETRIGPERIOD 1' -4 (-2) corresponds to 4 (2) kHz
SCOPETRIG

PVT_INIT  @1 
VELOCITY ON
HALT
PVT 2: Zi, 0 @Ti 

WHILE IGLOBAL(0)>-1'enter IGLOBAL(0) = -1 to exit loop
 Ti=Ti+8*DT
Zi=Zi+DZ
PVT 2: Zi, ZV @Ti 
Ti=Ti+2112*DT
Zi=Zi+44*DZ
PVT 2: Zi, ZV @Ti 
Ti=Ti+8*DT
Zi=Zi+DZ
PVT 2: Zi, 0 @Ti 
Ti=Ti+72*DT
Zi=Zi-46*DZ
PVT 2: Zi, 0 @Ti 
IGLOBAL(3)=0
WEND

Ti=Ti+1
PVT 2:0, 0 @Ti 
'START
 IGLOBAL(0)=0

END PROGRAM 
