 PROGRAM 
'Freeze_Intervention.ab sequentially moves Y by +DY then X by +DX 
'to extract the capillary from the cooling stream of the temperature
'controller. After Wait_Time seconds, the capillary returns to its 
'original position.
'While this program runs, UserString1 becomes "Freeze_Intervention.ab"
'
'(UserString0 for task 1; UserString1 for auxiliary task)
SETPARM 1023:UserString1,"Freeze_Intervention.ab" 

ABS
'SCOPEBUFFER 1200
'SCOPETRIGPERIOD 1	' -4 (-2) corresponds to 4 (2) kHz
'SCOPETRIG

'Control parameters
 DX=3'incremental move in X [mm]
 DY=11'incremental move in Y [mm]

Wait_Time=10

RAMP MODE RATE 
RAMP RATE 1:5000 
RAMP RATE 0:500 
WAIT MODE MOVEDONE 

MOVEINC 1:DY:200 'raise Y first
MOVEINC 0:DX:200 
DWELL Wait_Time

MOVEINC 0:-1*DX 'return X first
MOVEINC 1:-1*DY 'lower Y last

SETPARM 1023:UserString1,"" 

END PROGRAM 
