 PROGRAM 
'Retract.ab  moves Y by +DY then X by +DX to retract the capillary 
'from the cooling stream of the temperature controller.
'When this program launches, UserString1 becomes "Retract.ab"
'
'(UserString0 for task 1; UserString1 for auxiliary task)
SETPARM 1023:UserString1,"Retract.ab" 

'Control parameters
 DX=3'incremental move in X [mm]
 DY=11'incremental move in Y [mm]

ABS
RAMP MODE RATE 
RAMP RATE 1:5000 
RAMP RATE 0:500 
WAIT MODE MOVEDONE 

MOVEINC 1:DY:200 'raise Y first
MOVEINC 0:DX:200 'offset X last

END PROGRAM 
