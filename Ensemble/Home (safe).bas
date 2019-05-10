' (!)Retract helium cone before running.
SETPARM 1023:UserString0,"Home (safe).ab" 
ACKNOWLEDGEALL
ENABLE 0,1,2,4,5
PLANE 0
RECONCILE 0,1,2,4,5
WAIT MODE MOVEDONE 
HOME 1
HOME 2
MOVEABS 1:12 
HOME 0
MOVEABS 1:0 
HOME 5
PumpA_pos=PCMD(4)
MOVEABS 4:50*CEIL(PumpA_pos/50):20 'Move PumpA to the next largest multiple of 50 before terminating program.	
HOME 4
