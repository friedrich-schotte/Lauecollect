'Laue data collection using_PVT commands
'	
'PVT commands translate the sample cell between 
'XYZ coordinates specified in Laue_PVT_Parameters.abi. 
'It opens the millisecond shutter twice during each period of 
'288*DT, where DT is the time for 1 revolution of the high-speed
'chopper. The first x-ray pulse arrives 180*DT after the rising 
'edge of the AIN(X,1) trigger, and the second arrives at 288*DT. 
'After the scan, the stage returns to its starting position.
'
'Usage: update parameters in "Laue_PVT_parameters.abi" then launch
'
HEADER
INCLUDE "Laue_PVT_parameters.basi"
'Laue_PVT_parameters.abi contains:
'	N_mode: 0, hops from xtal to xtal; 1, remains on xtal
'	N_move: number of DT periods allocated to execute move
'	N_period: period to acquire pair of x-ray images 
'	N_repeat: Number of image pairs acquired per xtal
'	N_xtal: number of crystals
'	XYZ(3,N_crystal): XYZ coordinates (xtal center of mass)
INCLUDE "Environment_parameters.basi"
END HEADER

 PROGRAM 
DIM E_index AS INTEGER
DIM N_move AS INTEGER=48
DIM N_period AS INTEGER=288' for N_mode = 0, integer multiple of 48

'Write program name in UserString0 (identifies program loaded)
SETPARM 1023:UserString0,"Laue_PVT.ab" 

'Read E_index(Environment index): (0: NIH; 1: APS; 2: LCLS)
 E_index=GETPARM(1023:UserInteger0) 

'Initialize IGLOBAL Interactive Control Parameters
 IGLOBAL(0)=1'1: program is running; 0: terminates program
IGLOBAL(1)=1'1 triggers digital oscilloscope 

'SETGAIN <Axis>, <GainKp>, <GainKi>, <GainKpos>, <GainAff>[, <GainKd1>, <GainKpi>, <GainKp1>, <GainVff>, <GainPff>]
'SETGAIN X, 160000, 1344, 34.4, 341000,0,0,0,0,0 'NIH 20 Hz
'SETGAIN X, 182000, 1485, 33.42, 301300,0,0,0,459.6,0 'NIH 25 Hz
'SETGAIN X, 243400, 2429, 40.89, 336700,0,0,0,459.6,0 'NIH 30 Hz
'SETGAIN X, 290400, 3861, 54.46, 349400,0,0,0,459.6,0 'NIH 35 Hz
'SETGAIN X, 326700, 3827, 47.99, 334800,0,0,0,1407,0 'NIH 40 Hz
'SETGAIN X, 365700, 6179, 69.21, 341700,0,0,0,1407,0 'NIH 45 Hz
'SETGAIN Y, 141000, 1703, 49.45, 199300,0,0,0,945.5,0 'NIH 30 Hz
'SETGAIN Y, 195000, 3237, 68, 207200,0,0,0,2912,0 'NIH 40 Hz
'SETGAIN Y, 249700, 5101, 83.69, 211700,0,0,0,4259,0 'NIH 50 Hz
'SETGAIN Y, 297000, 6466, 89.16, 207400,0,0,0,1924,0 'NIH 60 Hz
'SETGAIN Z, 85080, 1866, 89.83, 59450,0,0,0,626,0 'NIH 60 Hz
'SETGAIN Z, 122600, 3387, 113.1, 63910,0,0,0,1114,0 'NIH 80 Hz
'SETGAIN Z, 139300, 4107, 120.8, 64230,0,0,0,1056,0 'NIH 90 Hz
'SETGAIN Z, 171200, 5639, 134.9, 64170,0,0,0,1148,0 'NIH 110 Hz
'SETGAIN msShut_ext, 104500, 2167, 84.92, 72680,0,0,0,101,0 'NIH 60 Hz

IF E_index=1 THEN'APS
SETGAIN 0:611920, 7046,47.200000000000003,337851,0,3162,0,0,0 'APS EasyTune [1]
SETGAIN 1:396431, 5139,53.100000000000001,213795,0,5620,0,0,0 'APS EasyTune [1]
'SETGAIN Z, 166800, 2395, 58.8, 63427,0,562,0,0,0 'APS EasyTune [1]
SETGAIN 2:181902, 3392,76.400000000000006,61291,0,562,0,0,0 'APS EasyTune [2]
'SETGAIN Z, 185358, 3323, 73.4, 61724,0,562,0,0,0 'APS EasyTune [3]
 ELSE'NIH, LCLS
SETGAIN 0:326700, 3827,47.990000000000002,334800,0,316,0,1407,0 
SETGAIN 1:249700, 5101,83.689999999999998,211700,0,316,0,1924,0 
SETGAIN 2:85080, 1866,89.829999999999998,59450,0,100,0,1000,0 
SETGAIN 6:161500, 3598,91.269999999999996,72990,0,0,0,0,0 'NIH 90 Hz
 END IF

'Set up scope parameters
 SCOPEBUFFER N_period*( N_xtal+2)
SCOPETRIGPERIOD 1' -4 (-2) corresponds to 4 (2) kHz

'Select Environment-dependent parameters
 scale_factor=scale_factor_array(E_index)
IF DGLOBAL(0)>0.99990000000000001 AND DGLOBAL(0)<1.0001 THEN
scale_factor=DGLOBAL(0)' reuse recent value
ELSE
DGLOBAL(0)=scale_factor
END IF
DT_start=DT_array(E_index)
DT=DT_start*scale_factor
DGLOBAL(1)=DT
msShut_open=msShut_open_array(E_index)
msShut_step=msShut_step_array(E_index)
msShut_atten=56'NIH/LCLS attenuated position (in degrees)
 msShut_close1=msShut_open-msShut_step
msShut_close2=msShut_open+msShut_step

ABS
PLANE 1

'check for "Motion Active" before executing RECONCILE
 WHILE(PLANESTATUS(0) BAND 1)<>0 OR(PLANESTATUS(1) BAND 1)<>0
P_status=PLANESTATUS(1)
DWELL 0.0050000000000000001
WEND
RECONCILE 0,1,2,6

XPOS=CMDPOS(0)
YPOS=CMDPOS(1)
ZPOS=CMDPOS(2)
SPOS=CMDPOS(6)
WAIT MODE MOVEDONE 
MOVEABS 6:msShut_close1 
PVT_INIT  @1 
VELOCITY ON
HALT
Ti=0.001
PVT 0: XPOS, 0,1: YPOS, 0,2: ZPOS, 0,6: msShut_close1, 0 @Ti 

'wait for next low-to-high transition.
 STARTSYNC-1
AIN_Volt=AIN:0::( 1)
WHILE AIN_Volt<0.59999999999999998
SYNC
AIN_Volt=AIN:0::( 1)
WEND

'Calculate offset_Z from AIN_Volt
 offset_Z=A_array(E_index,3)*AIN_Volt^3
+A_array(E_index,2)*AIN_Volt^2
+A_array(E_index,1)*AIN_Volt
+A_array(E_index,0)

'calculate time offset from offset_Z
 Ti_offset=offset_Z/470

'Acquire scope trace when IGLOBAL(1)=1
 IF IGLOBAL(1)=1 THEN
SCOPETRIG
END IF

Ti=Ti-Ti_offset-0.0057499999999999999'0.00575 properly phases the ms shutter
START
IF N_mode=0 THEN
FOR j=1 TO N_repeat
FOR i=0 TO(N_xtal-1)
Xi=XYZ(i,0)
Yi=XYZ(i,1)
Zi=XYZ(i,2)
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close1, 0 @( Ti+(N_move+6)*DT) 
Ti=Ti+N_period*DT
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close1, 0 @( Ti-114*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close2, 0 @( Ti-102*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close2, 0 @( Ti-6*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close1, 0 @( Ti+6*DT) 
NEXT i
NEXT j
ELSE
FOR i=0 TO(N_xtal-1)
Xi=XYZ(i,0)
Yi=XYZ(i,1)
Zi=XYZ(i,2)
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close1, 0 @( Ti+(N_move+6)*DT) 
Ti=Ti+180*DT
FOR j=1 TO N_repeat
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close1, 0 @( Ti-6*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close2, 0 @( Ti+6*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close2, 0 @( Ti+102*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close1, 0 @( Ti+114*DT) 
Ti=Ti+216*DT
NEXT j
Ti=Ti-108*DT
NEXT i
END IF

'Return to starting position
 Ti=Ti+56*DT
PVT 0: XPOS, 0,1: YPOS, 0,2: ZPOS, 0,6: msShut_close1, 0 @Ti 

IGLOBAL(0)=0'Reset to zero when program stops running.
 END PROGRAM 
