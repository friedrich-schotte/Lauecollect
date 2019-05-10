HEADER
'DEFINE PI 3.1415926999999999 
END HEADER

 PROGRAM 
DIM DT_array(2)AS DOUBLE'Period of Base frequency (in seconds)
 DIM scale_factor_array(2)AS DOUBLE'
DIM Open_array()AS DOUBLE={56,9.6999999999999993,56}'Shutter open (0:NIH, 1:APS, 2:LCLS)
 DIM Close_array()AS DOUBLE={63,19.699999999999999,63}'Shutter close (0:NIH, 1:APS, 2:LCLS)
 DIM msShut_step_array()AS DOUBLE={7,10,7}'Step size to move from open to close (in degrees)
 DIM Xo AS DOUBLE,Yo AS DOUBLE,Zo AS DOUBLE'Starting position

E_index=0'Environment index (0: NIH; 1: APS; 2: LCLS ---Specify appropriate E_INDEX BEFORE LAUNCHING THIS PROGRAM!)

'Initialize DT array 
 DT_array(0)=(1.0055257142857144)*0.024304558/24'0: NIH base period  (0.0010183 based on internal oscillator for Pico23)							
DT_array(1)=0.0010126899166666666'1: APS base period  (0.0010127 275th subharmonic of P0)
DT_array(2)=0.0010416666666666667'2: LCLS base period (0.0010417 inverse of 8*120 = 960 Hz)

'Initialize scale_factor_array (rescales DT to approximately match the source frequency)
 scale_factor_array(0)=1.00000109'1.0000018 'Pico23 
scale_factor_array(1)=0.99999084000000005'APS 2016.11.08; 0.99999525 'APS 03/07/2016
 scale_factor_array(2)=1'LCLS 
 scale_factor=scale_factor_array(E_index)'If time correction is positive (us), need to decrease the scale factor.
 DT=DT_array(E_index)

'Define ms shutter parameters
 msShut_open=open_array(E_index)
msShut_step=msShut_step_array(E_index)
msShut_close1=msShut_open-msShut_step
msShut_close2=msShut_open+msShut_step

'Coordinates of first pixel in raster scan.
 Xo=-0.68999999999999995
Yo=0.55400000000000005
Zo=0

'Define range, resolution for raster scan
 N_row=30'even integer
 N_col=10'even integer
 DP=0.029999999999999999'pixel size

Xv=-1*DP*sin(0.52359833333333328)/(24*DT)'average velocity during step
 Yv=DP*cos(0.52359833333333328)/(24*DT)'average velocity during step
 Zv=DP/(24*DT)'velocity of Z during raster scan

' move to first pixel 
WAIT MODE MOVEDONE 
LINEAR 0:Xo,1:Yo,2:Zo 
WAIT MOVEDONE 0,1,2

Plane 1
RECONCILE 0
X_pos=PCMD(0)
RECONCILE 1
Y_pos=PCMD(1)
RECONCILE 2
Z_pos=PCMD(2)


ABS'Positions specified in absolute coordinates
PVT_INIT  @1 
 VELOCITY ON
HALT
N_pts=(24*(N_row+1)*(N_col+1)+48)/4' assuning 4 ms per point
N_pts=(200*CEIL(N_pts/200))'round to nearest 200
 SCOPETRIGPERIOD 4' 4 ms per point
SCOPEBUFFER N_pts
SCOPETRIG
DWELL 0.040000000000000001

'Move motors into position to start.
 Ti=0.001
PVT 0: X_pos, 0,1: Y_pos, 0,2: Z_pos, 0,6: msShut_close1, 0 @Ti 
Ti=Ti+48*DT
Xi=Xo
Yi=Yo
Zi=Zo-DP
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close1, 0 @Ti 
START
For i=1 TO N_row STEP 2' raster scan outboard and inboard for each i
FOR j=1 TO N_col STEP 2' raster outboard
Zi=Zi+0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2: Zi, Zv,6: msShut_close1, 0 @Ti 
Zi=Zi+0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2: Zi, Zv,6: msShut_open, 0 @Ti 
Zi=Zi+0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2: Zi, Zv,6: msShut_close2, 0 @Ti 
Zi=Zi+0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2: Zi, Zv,6: msShut_open, 0 @Ti 
NEXT j
Xi=Xi-0.5*DP*sin(0.52359833333333328)
Yi=Yi+0.5*DP*cos(0.52359833333333328)
Zi=Zi+0.5*DP
Ti=Ti+12*DT
PVT 0:Xi,2*Xv,1:Yi,2*Yv,2: Zi, Zv,6: msShut_close1, 0 @Ti 
Xi=Xi-0.5*DP*sin(0.52359833333333328)
Yi=Yi+0.5*DP*cos(0.52359833333333328)
Zi=Zi+0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0 @Ti 
FOR j=1 TO N_col STEP 2' raster inboard
Zi=Zi-0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2:Zi,(-1*Zv),6: msShut_close1, 0 @Ti 
Zi=Zi-0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2:Zi,(-1*Zv),6: msShut_open, 0 @Ti 
Zi=Zi-0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2:Zi,(-1*Zv),6: msShut_close2, 0 @Ti 
Zi=Zi-0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2:Zi,(-1*Zv),6: msShut_open, 0 @Ti 
NEXT j
Xi=Xi-0.5*DP*sin(0.52359833333333328)
Yi=Yi+0.5*DP*cos(0.52359833333333328)
Zi=Zi-0.5*DP
Ti=Ti+12*DT
PVT 0:Xi,2*Xv,1:Yi,2*Yv,2:Zi,(-1*Zv),6: msShut_close1, 0 @Ti 
Xi=Xi-0.5*DP*sin(0.52359833333333328)
Yi=Yi+0.5*DP*cos(0.52359833333333328)
Zi=Zi-0.5*DP
Ti=Ti+12*DT
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0 @Ti 

NEXT i

Ti=Ti+48*DT
PVT 0: Xo, 0,1: Yo, 0,2: Zo, 0 @Ti 
END PROGRAM 

