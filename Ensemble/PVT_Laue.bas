'PVT_Laue uses PVT commands to translate the sample cell between 
'XYZ coordinates speciried in Center-of-Mass_Coordinates.abi. 
'It opens the millisecond shutter at intervals of 108*DT, where DT is the
'time for 1 revolution of the high-speed chopper. The first x-ray pulse
'in the sequence arrives 12*DT after the rising edge of the Ensemble 
'trigger. After the scan, the stage returns to its starting position.
'
'Usage: update XYZ coordinates in "Center-of-Mass_Coordinates.abi"
'
HEADER
INCLUDE "PVT_Laue_Parameters.basi"
END HEADER

 PROGRAM 
'Center_of_Mass_Coordinates.abi contains Mode, N_period, Number of crystals, and XYZ coordinates
'Mode
'N_period: integer multiple of DT defines period between x-ray pulses
'N_repeat: number of times repeated
'N_xtal: number of crystals
'XYZ(3,N_crystal) 'XYZ coordinates of crystals (center of mass)

'msShut_close1 = -0.3
'msShut_open = 9.7
'msShut_close2 = 19.7

DT=0.0010126899166666666
scale_factor=0.99999020000000005
DT=DT*scale_factor

ABS
PLANE 1
XPOS=PFBK(0)
YPOS=PFBK(1)
ZPOS=PFBK(2)
'SPOS = PFBK(msShut_ext)
PVT_INIT  @1 
 VELOCITY ON
HALT
Ti=0.001
'PVT X XPOS,0 Y YPOS,0 Z ZPOS,0 msShut_ext SPOS,0 TIME Ti
PVT 0: XPOS, 0,1: YPOS, 0,2: ZPOS, 0 @Ti 

WHILE DIN:0::( 1,1)=0'wait for next low-to-high transition.
 DWELL 0.00025000000000000001
WEND
START

SCOPEBUFFER 1200
SCOPETRIGPERIOD 1' -4 (-2) corresponds to 4 (2) kHz
SCOPETRIG

FOR j=0 TO N_repeat
FOR i=1 TO(N_xtal-1)
Ti=Ti+24*DT
Xi=XYZ(i,0)
Yi=XYZ(i,1)
Zi=XYZ(i,2)
'PVT X Xi,0 Y Yi,0 Z Zi,0 msShut_ext SPOS,0 TIME Ti
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0 @Ti 
 Ti=Ti+( N_period-24-12)*DT
'PVT X Xi,0 Y Yi,0 Z Zi,0 msShut_ext SPOS,0 TIME Ti
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0 @Ti 
 Ti=Ti+12*DT
'IF SPOS < msShut_open THEN
'	SPOS = msShut_close2
'ELSE
'	SPOS = msShut_close1
'END IF
'PVT X Xi,0 Y Yi,0 Z Zi,0 msShut_ext SPOS,0 TIME Ti
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0 @Ti 
 NEXT j
NEXT i

Ti=Ti+72*DT
'PVT X XPOS,0 Y YPOS,0 Z ZPOS,0 msShut_ext SPOS,0 TIME Ti
PVT 0: XPOS, 0,1: YPOS, 0,2: ZPOS, 0 @Ti 

END PROGRAM 
