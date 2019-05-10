'RasterScan uses PVT commands to translate the sample cell within a 
'plane normal to the microscope camera, with Z being the fast axis.
'It opens the millisecond shutter at intervals of 24*DT, where DT is the
'time for 1 revolution of the high-speed chopper. The first x-ray pulse
'in the sequence arrives 48*DT after the rising edge of the Ensemble 
'trigger, which is assumed to be coincident with an x-ray pulse. 
'After the scan, the stage returns to its starting position.
'
'Usage: enter NR, NC, NT, NP, and DZ in "RasterScan_parameters.abi"
'DZ is the step size in mm. The number of rows (NR) and number of 
'columns (NC) should be odd. The number of heat-load chopper revolutions
'before starting the scan is given by NT, and the time between pulses
'is given by NP.
'

HEADER
INCLUDE "RasterScan_parameters.basi"
END HEADER

 PROGRAM 
DIM ROW AS INTEGER,COL AS INTEGER,SGN AS INTEGER
DIM PrintString AS STRING(120)
pi=3.1415926000000001
msShut_close1=-0.29999999999999999
msShut_open=9.6999999999999993
msShut_close2=19.699999999999999
DT=0.0010126899166666666
DX=DZ*SIN(pi/6)'pi/6 radians = 30 deg
 DY=DZ*COS(pi/6)
ZV=DZ/( NP*12*DT)

XPOS=PFBK(0)
YPOS=PFBK(1)
ZPOS=PFBK(2)
SPOS=PFBK(6)

SCOPEBUFFER 700
SCOPETRIGPERIOD 1' -4 (-2) corresponds to 4 (2) kHz

PLANE 1
PVT_INIT  @1 
VELOCITY ON
HALT

'Specify starting position and time.
 Ti=0.0001
PVT 0: XPOS, 0,1: YPOS, 0,2: ZPOS, 0,6: SPOS, 0 @Ti 


'Wait for trigger (next low-to-high transition)
 WHILE DIN:0::( 1,0)=0
DWELL 0.00025000000000000001
WEND

SCOPETRIG
START

'Specify arrival of first x-ray pulse at 48*DT.
 Ti=Ti+( NT*12-6.5)*DT

SGN=1
FOR ROW=-(NR-1)/2TO(NR-1)/2
Xi=XPOS+ROW*DX
Yi=YPOS-ROW*DY
FOR COL=-(NC-1)/2TO(NC-1)/2
Ti=Ti-9*DT
Zi=ZPOS+SGN*( COL-9/( NP*12))*DZ
PVT 0: Xi, 0,1: Yi, 0,2: Zi, ZV,6: SPOS, 0 @Ti 
FORMAT PrintString,"%d,%d,%.3f,%.3f,%.3f\r",
INTV:ROW,INTV:COL,DBLV:Zi,DBLV:ZV,DBLV:Ti
PRINT PrintString
Ti=Ti+18*DT
Zi=ZPOS+SGN*( COL+9/( NP*12))*DZ
IF SPOS<msShut_open THEN
SPOS=msShut_close2
ELSE
SPOS=msShut_close1
END IF
PVT 0: Xi, 0,1: Yi, 0,2: Zi, ZV,6: SPOS, 0 @Ti 
FORMAT PrintString,"%d,%d,%.3f,%.3f,%.3f\r",
INTV:ROW,INTV:COL,DBLV:Zi,DBLV:ZV,DBLV:Ti
PRINT PrintString
Ti=Ti+( NP*12-9)*DT
NEXT COL
SGN=-1*SGN
ZV=-1*ZV
NEXT ROW
'reposition ms shutter to its starting position.
 Ti=Ti+((NT-NP)*12+9)*DT
PVT 0: XPOS, 0,1: YPOS, 0,2: ZPOS, 0,6: SPOS, 0 @Ti 

END PROGRAM 
