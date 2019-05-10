 PROGRAM 
'Insert.ab  moves X by - DX and then Y by -DY to insert the capillary 
'into the cooling stream of the temperature controller.
'When this program launches, UserString1 becomes "Insert.ab"
'
'(UserString0 for task 1; UserString1 for auxiliary task)
SETPARM 1023:UserString1,"Insert.ab" 

'Control parameters
 DX=3'incremental move in X [mm]
 DY=11'incremental move in Y [mm]

ABS
RAMP MODE RATE 
RAMP RATE 1:5000 
RAMP RATE 0:500 
WAIT MODE MOVEDONE 

MOVEINC 0:-1*DX:200 'return X first
MOVEINC 1:-1*DY:200 'lower Y last

END PROGRAM 
