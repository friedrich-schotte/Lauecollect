DECLARATIONS
GLOBAL PrintString AS STRING(120)
GLOBAL PP(100)AS DOUBLE
GLOBAL Zpos AS DOUBLE
GLOBAL Z_mid AS DOUBLE
GLOBAL Zvmax_RS AS DOUBLE
GLOBAL DT_start AS DOUBLE
GLOBAL msShut_Enable AS INTEGER
GLOBAL PumpA_Enable AS INTEGER
GLOBAL N_mode AS INTEGER
GLOBAL N_delay AS INTEGER
GLOBAL N_counter AS INTEGER

END DECLARATIONS

 PROGRAM 

DIM O_mode AS INTEGER,M AS INTEGER,E_index AS INTEGER
DIM DT_array(2)AS DOUBLE'Period of Base frequency (in seconds)
 DIM scale_factor_array(2)AS DOUBLE'
DIM Period_array()AS INTEGER={12,12,8}'period between x-ray pulses in units of DT (0:NIH, 1:APS, 2:LCLS)
 DIM Open_array()AS DOUBLE={56,9.6999999999999993,56}'Shutter open (0:NIH, 1:APS, 2:LCLS)
 DIM Close_array()AS DOUBLE={63,19.699999999999999,63}'Shutter close (0:NIH, 1:APS, 2:LCLS)
 DIM msShut_step_array()AS DOUBLE={7,10,7}'Step size to move from open to close (in degrees)
 DIM Xo AS DOUBLE,Yo AS DOUBLE,Zo AS DOUBLE'Starting position

' Specify Environment Index and whether the digital oscilloscope should be set to operate
E_index=1'Environment index (0: NIH; 1: APS; 2: LCLS ---Specify appropriate E_INDEX BEFORE LAUNCHING THIS PROGRAM!)
 D_Scope=0'[1/0] Enables/Disables Digital Oscilloscope
Trig_delay=5.5'trigger propagation delay in units of DT (trig to DIO delay is 4.5 +/- 0.3 ms on oscilloscope)

'Initialize DT array 
 DT_array(0)=(1.0055257142857144)*0.024304558/24'0: NIH base period  (0.0010183 based on internal oscillator for Pico23)							
DT_array(1)=0.0010126899166666666'1: APS base period  (0.0010127 275th subharmonic of P0)
DT_array(2)=0.0010416666666666667'2: LCLS base period (0.0010417 inverse of 8*120 = 960 Hz)

'Initialize scale_factor_array (rescales DT to approximately match the source frequency)
 scale_factor_array(0)=1.000005'1.0000018 'Pico23 
scale_factor_array(1)=0.99999035999999997'APS 2017.02.26; 0.99999084 APS 2016.11.08; 0.99999525 'APS 03/07/2016
 scale_factor_array(2)=1'LCLS 

'Select Environment-dependent parameters
 DT_start=DT_array(E_index)
msShut_open=open_array(E_index)
msShut_close=close_array(E_index)
msShut_step=msShut_step_array(E_index)
msShut_atten=56'NIH/LCLS attenuated position (in degrees)
 msShut_close1=msShut_open-msShut_step
msShut_close2=msShut_open+msShut_step
M_offset=Period_array(E_index)/2-Trig_delay
scale_factor=scale_factor_array(E_index)'If time correction is positive (us), need to decrease the scale factor.

'Set operating parameters
 Z_start=11
Z_stop=-12.5
Z_mid=0.5*(Z_start+Z_stop)'mid-point of the stroke
 DZ=-0.5

'Initial conditions
 LZi=0
Npp=0
Zi=Z_start
msShut_pos=msShut_close1

CALL PP_Array()
Plane 1
RECONCILE 2

'Move to starting positions
 ABS'Positions specified in absolute coordinates
WAIT MODE MOVEDONE 
MOVEABS 2:Zi:10 
MOVEABS 5:LZi:10 
MOVEABS 6:msShut_close1 

PumpA_pos=PCMD(4)
MOVEABS 4:50*CEIL(PumpA_pos/50):20 'Move PumpA to the next largest multiple of 50 before terminating program.	
HOME 4
PumpA_pos=PCMD(4)

SCOPETRIGPERIOD-4' -4 (-2) corresponds to 4 (2) kHz
SCOPEBUFFER 2000

'Set up for PVT commands
PVT_INIT  @1 
 VELOCITY ON
HALT
Ti=0.001
DT=scale_factor*DT_start
Zvmax_RS=1.5*(Z_start-Z_stop)/(60*DT)'peak velocity during return stroke.

DGLOBAL(0)=0
'GOTO EndOfProgram
 N_delay=0
N_counter=0
PVT 2: Zi, 0,4: PumpA_pos, 0,5: LZi, 0,6: msShut_pos, 0 @Ti 
WHILE DGLOBAL(0)>-1'enter DGLOBAL(0) = -1 to exit loop
'CALL Synch()
'CALL Phase()
 M_scale=4
IF N_mode=11 THEN
M_scale=48
END IF
ZV=DZ/( M_scale*DT)
Ti=Ti+8*DT
Zi=Zi+DZ
PVT 2: Zi, ZV,4: PumpA_pos, 0,5: LZi, 0,6: msShut_pos, 0 @Ti 
Ti=Ti+3*M_scale*DT
Zi=Zi+3*DZ
PVT 2: Zi, ZV,4: PumpA_pos, 0,5: LZi, 0,6: msShut_pos, 0 @Ti 
Ti=Ti+2*M_scale*DT
Zi=Zi+2*DZ
msShut_pos=msShut_open
PVT 2: Zi, ZV,4: PumpA_pos, 0,5: LZi, 0,6: msShut_pos, 0 @Ti 
Ti=Ti+40*M_scale*DT
Zi=Zi+40*DZ
PVT 2: Zi, ZV,4: PumpA_pos, 0,5: LZi, 0,6: msShut_pos, 0 @Ti 
Ti=Ti+8*DT
Zi=Z_stop
msShut_pos=msShut_close1
PVT 2: Zi, 0,4: PumpA_pos, 0,5: LZi, 0,6: msShut_pos, 0 @Ti 

Ti=Ti+60*DT
Zi=Z_start
LZi=-1*ZV*10^(N_delay/8-5)'LZ position for L_delay
 Npp=Npp+PumpA_Enable
PumpA_pos=50*FLOOR(Npp/100)+PP(Npp-100*FLOOR(Npp/100))
PVT 2: Zi, 0,4: PumpA_pos, 0,5: LZi, 0,6: msShut_pos, 0 @Ti 
N_counter=N_counter+1
WEND
LINEAR 4:50*CEIL(Npp/100) @20 'Move PumpA to the next largest multiple of 50 before terminating program.
LINEAR 5:0 
EndOfProgram:
END PROGRAM 

FUNCTION PP_Array()
'Estimate Peristaltic Pump position using 5th order polynomial
 DIM i AS INTEGER
FOR i=0 TO 99' Assign positions for 100 steps
v=i*24.699999999999999/99
PP(i)=1.843*v-0.0066010000000000001*v^2+0.0038279999999999998*v^3-0.00043209999999999999*v^4+1.1590000000000001e-005*v^5
NEXT i
END FUNCTION

FUNCTION Synch()
DIM N_temp AS INTEGER
'Decode mode parameters from trigger pulse train
 STARTSYNC-1'corresponds to 0.5 ms clock ticks per SYNC 
'When first starting, sychronize on second detected trigger.
 IF N_counter=0 THEN
WHILE DIN:0::( 1,0)=0'wait for low-to-high transition.
 SYNC
WEND
'Wait 30 ms before polling next low-to-high transition.
 FOR i=0 to 60
SYNC
NEXT i
END IF
WHILE DIN:0::( 1,0)=0'wait for next low-to-high transition.
 SYNC
WEND
'Record Zpos immediately after first rising edge
 Zpos=PCMD(2)
IF N_counter=1 THEN
FOR i=0 to 46'wait 23 ms to start
 SYNC
NEXT i
SCOPETRIG
'START
 END IF
SYNC
SYNC
SYNC
SYNC
SYNC
SYNC
SYNC
'Record msShut_Enable 3.5 ms after first rising edge
 msShut_Enable=DIN:0::( 1,0)
SYNC
SYNC
SYNC
SYNC
'Record PumpA_Enable 2 ms later
 PumpA_Enable=DIN:0::( 1,0)
'Read 4 bits that define mode (every 2 ms)
 N_temp=0
FOR i=0 TO 3
SYNC
SYNC
SYNC
SYNC
N_temp=N_temp+DIN:0::( 1,0)*2^i
NEXT i
N_mode=N_temp
'Read 6 bits that define delay (every 2 ms)
 N_temp=0
FOR i=0 TO 5
SYNC
SYNC
SYNC
SYNC
N_temp=N_temp+DIN:0::( 1,0)*2^i
NEXT i
N_delay=N_temp
END FUNCTION

FUNCTION Phase()
' Monitor and correct phase of motion(PLL)
IF N_counter=0 THEN
Verbose=0'If Verbose is True, then print after every stroke; else only after timing correction

T_ref=0'Time used to compute new scale_factor
 N_corr=25'Number of strokes between corrections
 Z_error_max=-10
Z_error_min=10
Sum_corrections=0
T_correction_old=0
PRINT"k, Mode, Z_error_max [um], Z_error_min [um], pos_error [um],"
PRINT"T_0 [s], scale factor, T_correction [us], Sum_corrections [us]"
PRINT"\r"
END IF


Z_error=Zpos-Z_mid
IF Z_error<Z_error_min THEN
Z_error_min=Z_error
END IF
IF Z_error>Z_error_max THEN
Z_error_max=Z_error
END IF
pos_error=0.5*(Z_error_max+Z_error_min)
T_correction=pos_error/Zvmax_RS


IF(N_counter>25)AND(N_counter/N_corr=FLOOR(N_counter/N_corr))THEN'make correction								
 T_0=T_0-T_correction
Sum_corrections=Sum_corrections+T_correction
Z_error_max=Z_error_max-pos_error-DGLOBAL(3)
Z_error_min=Z_error_min-pos_error+DGLOBAL(3)
DGLOBAL(3)=0.0040000000000000001
IF N_counter>(4*N_corr)THEN
sum_pos_error=sum_pos_error+pos_error
IF(abs(sum_pos_error)>0.050000000000000003)AND((T_0-T_ref)>300)THEN
scale_factor=scale_factor*(1-sum_pos_error/Zvmax_RS/(T_0-T_ref))
DT=scale_factor*DT_start
sum_pos_error=0
T_ref=T_0
END IF
END IF
FORMAT PrintString,"%d,%d,%.0f,%.0f,%.0f,%.1f,%.8f,%.0f,%.0f\r",
INTV:N_counter,INTV:N_mode,DBLV:1000*Z_error_max,DBLV:1000*Z_error_min,DBLV:1000*pos_error,DBLV:T_0,DBLV:scale_factor,DBLV:1000000*T_correction,DBLV:1000000*Sum_corrections

IF NOT Verbose AND T_correction<>T_correction_old THEN
PRINT PrintString
T_correction_old=T_correction
END IF
END IF

END FUNCTION
