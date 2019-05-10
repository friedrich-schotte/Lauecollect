'	EnsembleEPAQ_PP.ab
'	Anfinrud 2019.02.27

' Player-Piano Control of High-Speed Diffractometer via PVT commands
'
' PVT commands are queued in a FIFO buffer of length 16. Use HALT to 
' hold off execution of the PVT commands until a START command is issued.
' To ensure the FIFO buffer is not overwritten, the 14th PVT command 
' automatically triggers a START. Hence, to properly synchronize
' the motion, the START command must be issued before the 14th PVT 
' command is queued in the FIFO buffer. 
'
' In AeroBasic, arrays are indexed from 0 to N, i.e., A(1) has two elements
'
'INCLUDE "PP.abi": Peristaltic Pump Look-up Table -> GLOBAL PP(9,499)
'	The first dimension, specified by PP_index, selects the pumping speed.
'	When PP_index = 0, pump is linear (50 equal steps per 50-step period).
'	When PP_index > 0, pump is nonlinear (N unequal steps per 50-step period).
'	The number of subdivisions per 50 step period is given by:
'		SS_array() AS INTEGER = {50,500,250,100,50,20,10,5,2,1}
'
'INCLUDE "Environment_parameters.abi"
'	GLOBAL A_array() AS DOUBLE = {{}}
'	GLOBAL DT_array() AS DOUBLE = {}
'	GLOBAL scale_factor_array() AS DOUBLE = {}
'
'Program Control parameters
'	IGLOBAL(0): setting to 0 initiates orderly exit of this program
'	IGLOBAL(1): setting to 1 Triggers Digital Oscilloscope
'	IGLOBAL(2): PP_index (0: linear; 1-9: nonlinear options)
'	IGLOBAL(3): Verbose Logging (1: ON)
'
'Integer and Double status indicators
'	IGLOBAL(4): N_count for last correction
'	DGLOBAL(0): scale_factor
'	DGLOBAL(1): DT
'	DGLOBAL(2): Tcorr_sum
'	DGLOBAL(3): T_synch

'E_index: Environment Index (0: NIH; 1: APS; 2: LCLS)
'E_index is saved in and accessed from non-volatile memory (UserInteger0)
'E_index = GETPARM(UserInteger0)

HEADER
INCLUDE "Environment_parameters.basi"
INCLUDE "PP.basi"
END HEADER

DECLARATIONS
GLOBAL E_index AS INTEGER
GLOBAL Z_mid AS DOUBLE
GLOBAL N_count AS INTEGER
'Nz_array specifies mode-specific pulse separation in DT units
 GLOBAL Nz_array()AS INTEGER={4,12,24,48,96,24,48,96}
'Np_array specifies mode-specific period in DT units
 GLOBAL Np_array()AS INTEGER={264,624,1152,2208,4320,1056,2016,3936}

'Synch() variables
 GLOBAL PumpA_Enable AS INTEGER
GLOBAL N_mode AS INTEGER
GLOBAL N_delay AS INTEGER
GLOBAL AIN_Volt AS DOUBLE
GLOBAL PCMD_Z AS DOUBLE
GLOBAL VCMD_Z AS DOUBLE
GLOBAL Zerr AS DOUBLE
GLOBAL T_sync AS DOUBLE
GLOBAL Tcorr AS DOUBLE
GLOBAL Tcorr_sum AS DOUBLE
GLOBAL scale_factor AS DOUBLE
GLOBAL DT_start AS DOUBLE
GLOBAL DT AS DOUBLE
GLOBAL T_ref AS DOUBLE

'PrintLog() variables
 GLOBAL PrintString AS STRING(96)'max # characters for PRINT is 96	
 GLOBAL PumpA_Enable_last AS INTEGER
GLOBAL N_mode_last AS INTEGER
GLOBAL N_delay_last AS INTEGER

END DECLARATIONS

 PROGRAM 
DIM PumpA_pos AS DOUBLE
DIM Npp AS INTEGER
DIM PP_index AS INTEGER
DIM Ti AS DOUBLE

'Write program name in UserString0
SETPARM 1023:UserString0,"EnsembleEPAQ_PP.ab" 

'Read E_index(Environment index): (0: NIH; 1: APS; 2: LCLS)
 E_index=GETPARM(1023:UserInteger0) 

'Initialize IGLOBAL Interactive Control Parameters
 IGLOBAL(0)=1'1: program is running; 0: terminates program
IGLOBAL(1)=1'1 triggers digital oscilloscope one time
IGLOBAL(2)=3'2 sets pump stepsize to ~0.2 uL/stroke
IGLOBAL(3)=0'1 sets logging to Verbose 
IGLOBAL(4)=0'N_count for last change in scale_factor 

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
'SETGAIN Z, 238400, 7352, 126.3, 45550,0,0,0,0,0 'NIH 210 Hz (calculated)
'SETGAIN Z, 273400, 7241, 108.5, 45550,0,0,0,0,0 'NIH 240 Hz (calculated)
'SETGAIN Z, 308400, 6142, 81.57, 45550,0,0,0,0,0 'NIH 270 Hz (calculated)
 IF E_index=1 THEN'APS
SETGAIN 0:611920, 7046,47.200000000000003,337851,0,3162,0,0,0 'APS EasyTune [1]
SETGAIN 0:326700, 3827,47.990000000000002,334800,0,0,0,1407,0 
SETGAIN 1:396431, 5139,53.100000000000001,213795,0,5620,0,0,0 'APS EasyTune [1]
'SETGAIN Z, 166800, 2395, 58.8, 63427,0,562,0,0,0 'APS EasyTune [1]
SETGAIN 2:181902, 3392,76.400000000000006,61291,0,562,0,0,0 'APS EasyTune [2]
'SETGAIN Z, 185358, 3323, 73.4, 61724,0,562,0,0,0 'APS EasyTune [3]
 ELSE'NIH, LCLS
SETGAIN 0:326700, 3827,47.990000000000002,334800,0,0,0,1407,0 
SETGAIN 1:195000, 3237,68,207200,0,0,0,2912,0 
'SETGAIN Z, 273400, 7241, 108.5, 45550,0,0,0,0,0
SETGAIN 2:171200, 5639,134.90000000000001,64170,0,0,0,1148,0 'NIH 110 Hz
SETGAIN 5:645618, 8110,51.5,464278,0,0,0,0,0 
 END IF

'Select Environment-dependent parameters
 scale_factor=scale_factor_array(E_index)
DGLOBAL(0)=scale_factor
DT_start=DT_array(E_index)
DT=DT_start*scale_factor
DGLOBAL(1)=DT

'Number of time steps for return stroke
 N_return=72

'Position parameters
'N_steps = 5+39+2 '5 for LZ offset; 39 for 40 x-ray shots; 2 for acceleration/deceleration
 DZ=-0.5'The full stroke equals (DZ*N_steps) 
 Z_start=12.5'Z_stop - DZ*N_steps 'Stroke starts at this position	
 Z_stop=-10.5'Stroke stops at this position 
 Z_mid=0.5*(Z_start+Z_stop)'mid-point of the stroke
'Zvmax_RS = 1.5*(Z_start-Z_stop)/(N_return*DT)'peak velocity during return stroke.

'Initialize conditions
 Zi=Z_start
Ti=0.001
LZi=0
Npp=0
N_count=-1

Plane 1
'check for "Motion Active" before executing RECONCILE
 WHILE(PLANESTATUS(0) BAND 1)<>0 OR(PLANESTATUS(1) BAND 1)<>0
P_status=PLANESTATUS(1)
DWELL 0.0050000000000000001
WEND
RECONCILE 2,4,5
ABS'Positions specified in absolute coordinates
WAIT MODE MOVEDONE 
LINEAR 2:Zi @10 
LINEAR 5:LZi @10 
 PumpA_pos=PCMD(4)
LINEAR 4:200*CEIL((PumpA_pos-0.01)/200) @40 'Move PumpA to the next largest multiple of 200 before terminating program.	
HOME 4
PumpA_pos=PCMD(4)
PVT_INIT  @1 
VELOCITY ON
HALT
PVT 2: Zi, 0,4: PumpA_pos, 0,5: LZi, 0 @Ti 

SCOPEBUFFER 1000
SCOPETRIGPERIOD 1' -4 (-2) corresponds to 4 (2) kHz 
PP_index=IGLOBAL(2)'0 is linear; 1-9 is nonlinearPP_index = IGLOBAL(2) '0 is linear; 1-9 is nonlinear	
CALL Synch()'ensures subsequent Synch() starts prior to start bit

WHILE IGLOBAL(0)>0'enter IGLOBAL(0) = 0 to exit loop	
 N_count=N_count+1
CALL Synch()'read bit pattern; calculate Tcorr, DT
 CALL Print_Log()
Ti=Ti+Tcorr'apply timing correction
 Nx=Nz_array(N_mode)'Time between x-ray pulses in units of DT

IF N_mode<5 THEN'Flythru-4, -12, -24, -48, -96
 ZV=DZ/( Nx*DT)
Ti=Ti+12*DT
IF N_mode=0 THEN Ti=Ti-4*DT END IF
Zi=Zi+DZ
PVT 2: Zi, ZV @Ti 
Ti=Ti+44*Nx*DT
Zi=Zi+44*DZ
PVT 2: Zi, ZV @Ti 
Ti=Ti+12*DT
IF N_mode=0 THEN Ti=Ti-4*DT END IF
Zi=Zi+DZ
Call Startup()
ELSEIF N_mode>4 THEN'Stepping Modes
 Ti=Ti+24*DT
Zi=Zi+6*DZ
FOR i=1 TO 20
PVT 2: Zi, 0 @Ti 
IF i=1 THEN CALL Startup()END IF
Ti=Ti+Nx*DT
PVT 2: Zi, 0 @( Ti-12*DT) 
Zi=Zi+DZ
PVT 2: Zi, 0 @Ti 
Ti=Ti+Nx*DT
PVT 2: Zi, 0 @( Ti-12*DT) 
Zi=Zi+DZ
NEXT i
END IF

'Return Stroke
 IF PumpA_Enable=1 THEN
PVT 2: Zi, 0,4: PumpA_pos, 0,5: LZi, 0 @Ti 
Ti=Ti+N_return*DT
Zi=Z_start
LZi=-1*ZV*10^(N_delay/8-5)'LZ position for L_delay				
 IF(Npp>=SS_array(PP_index))OR(PP_index<>IGLOBAL(2))THEN
PumpA_pos=50*FLOOR((PumpA_pos+0.01)/50)+50
Npp=1
ELSE
PumpA_pos=50*FLOOR((PumpA_pos+0.01)/50)+PP(PP_index,Npp)
Npp=Npp+1
END IF
PP_index=IGLOBAL(2)
PVT 2: Zi, 0,4: PumpA_pos, 0,5: LZi, 0 @Ti 
ELSE
PVT 2: Zi, 0,5: LZi, 0 @Ti 
IGLOBAL(6)=SS_array(PP_index)*(PumpA_pos-50*FLOOR((PumpA_pos+0.01)/50))/50
Ti=Ti+N_return*DT
Zi=Z_start
LZi=-1*ZV*10^(N_delay/8-5)'LZ position for L_delay
PVT 2: Zi, 0,5: LZi, 0 @Ti 
 END IF

WEND

'Orderly exit

'Wait for motion to complete before executing RECONCILE 
 WHILE(PLANESTATUS(0) BAND 1)<>0 OR(PLANESTATUS(1) BAND 1)<>0
P_status=PLANESTATUS(1)
DWELL 0.0050000000000000001
WEND

RECONCILE 2,5

Ti=Ti+3000*DT
PumpA_pos=200*CEIL((PumpA_pos+0.01)/200)
PVT 2:0, 0,4: PumpA_pos, 0,5:0, 0 @Ti 
START

END PROGRAM 

FUNCTION Startup()
IF N_count=0 THEN
SYNC
CLEARTIMER
START
END IF
END FUNCTION

FUNCTION Synch()
DIM N_temp AS INTEGER
DIM offset_Z AS DOUBLE
DIM Tsigma AS DOUBLE=5.9999999999999997e-007'1.0e-6
DIM Nsigma AS DOUBLE=20

'Decode mode parameters from trigger pulse train
 STARTSYNC-1'corresponds to 0.5 ms clock ticks per SYNC

'Acquire scope trace when IGLOBAL(1)=1
 IF IGLOBAL(1)=1 AND N_Count>0 THEN
IF N_Count>0 THEN
WHILE PCMD(2)>0
SYNC
WEND
WHILE VCMD(2)<0.29999999999999999
SYNC
WEND
END IF
SCOPETRIG
IGLOBAL(1)=0
END IF

'wait for next low-to-high transition
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

'Record msShut_Enable 4 ms later
 FOR j=0 TO 7 SYNC NEXT j'4 ms
'msShut_Enable = 0
'IF (AIN(X,1) > 1.60) THEN msShut_Enable = 1 END IF

'Record PumpA_Enable 3 ms later
 FOR j=0 TO 5 SYNC NEXT j'3 ms
PumpA_Enable=0
IF(AIN:0::( 1)>1.6000000000000001)THEN PumpA_Enable=1 END IF

'Read 4 bits that define mode (every 3 ms)
 N_temp=0
FOR i=0 TO 3
FOR j=0 TO 5 SYNC NEXT j'3 ms
IF(AIN:0::( 1)>1.6000000000000001)THEN N_temp=N_temp+2^i END IF
NEXT i
N_mode=N_temp

'Record Zerr immediately after N_mode is read
 PCMD_Z=PCMD(2)
VCMD_Z=VCMD(2)
Zerr=PCMD_Z-Z_mid-offset_Z

'Record Time near mid-point of return stroke (19 ms after trigger)
 T_sync=TIMER()/1000
DGLOBAL(3)=T_sync

'Read 6 bits that define delay (every 3 ms)
 N_temp=0
FOR i=0 TO 5
FOR j=0 TO 5 SYNC NEXT j'3 ms
IF(AIN:0::( 1)>1.6000000000000001)THEN N_temp=N_temp+2^i END IF
NEXT i
N_delay=N_temp

'Calculate time correction Tcorr; rescale DT if necessary
 IF N_Count<1 THEN
Tcorr_sum=0
ELSE
IF VCMD_Z<>0 THEN
Tcorr=Zerr/VCMD_Z
IF ABS(Tcorr)<(Nsigma*Tsigma)THEN
Tcorr=0.25*Tcorr
END IF
END IF
END IF
'Tcorr = 0 
 IF N_count>10 THEN
Tcorr_sum=Tcorr_sum+Tcorr
DGLOBAL(2)=Tcorr_sum
IF ABS(Tcorr_sum)>(Nsigma*Tsigma)THEN
scale_factor=scale_factor*(1+((Nsigma-1)/Nsigma)*Tcorr_sum/(T_sync-T_ref))
DGLOBAL(0)=scale_factor
IGLOBAL(4)=N_Count
DT=scale_factor*DT_start
DGLOBAL(1)=DT
Tcorr_sum=0
T_ref=T_sync
END IF
ELSE
T_ref=T_sync
END IF

SYNC
STARTSYNC 12.5'Time delay before startup
 END FUNCTION

FUNCTION Print_Log()
FORMAT PrintString,"%.3f,%d,%d,%d,%.3f,%.3f,%.3f,%.1e\r",
DBLV:T_sync,
INTV:PumpA_Enable,
INTV:N_mode,
INTV:N_delay,
DBLV:AIN_Volt,
DBLV:PCMD_Z,
DBLV:Zerr,
DBLV:Tcorr
IF N_Count=0 THEN
PrintString="T_sync[s], PumpA_Enable, N_Mode, N_Delay, AIN_Volt, PCMD_Z, Zerr, Tcorr[s]\r"
PRINT PrintString
ELSEIF
(N_mode<>N_mode_last)
OR ABS(Tcorr)>2.0000000000000002e-005
OR IGLOBAL(3)=1
AND N_Count>1 THEN

PRINT PrintString
PumpA_Enable_last=PumpA_Enable
N_mode_last=N_mode
N_delay_last=N_delay
END IF
IF N_Count=10000 THEN IGLOBAL(3)=0 END IF
END FUNCTION