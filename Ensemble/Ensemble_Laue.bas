' Ensemble_Laue.ab  version 1.0.0
'
'SET UP: 
'	Connect 'sample trans' to Digital Input 0
'	Connect 'X det trig' to Digital Input 1
'	Connect 'ms shutter' to Digital Input 2 (not yet implemented)
'	Connect Digital Output 0 to the laser shutter (LCLS)
'	Specify E_index (0: NIH; 1: APS; 2: LCLS) --- see first assignment below DIM statements
'	The rising edge of the 'X det trig' pulse should be phased to occur at the mid-point between x-ray pulses

DECLARATIONS
GLOBAL PrintString AS STRING(80)
END DECLARATIONS

 PROGRAM 

DIM i AS INTEGER,O_mode AS INTEGER,M AS INTEGER,E_index AS INTEGER
DIM DT_array(2)AS DOUBLE'Period of Base frequency (in seconds)
 DIM Period_array()AS INTEGER={12,12,8}'period between x-ray pulses in units of DT (0:NIH, 1:APS, 2:LCLS)
 DIM Open_array()AS DOUBLE={70,9.6999999999999993,70}'Shutter open (0:NIH, 1:APS, 2:LCLS)
 DIM Close_array()AS DOUBLE={63,19.699999999999999,63}'Shutter close (0:NIH, 1:APS, 2:LCLS)
 DIM Xo AS DOUBLE,Yo AS DOUBLE,Zo AS DOUBLE'Starting position

' Specify Environment Index and whether the digital oscilloscope should be set to operate
E_index=0'Environment index (0: NIH; 1: APS; 2: LCLS ---Specify appropriate E_INDEX BEFORE LAUNCHING THIS PROGRAM!)
 D_Scope=0'[1/0] Enables/Disables Digital Oscilloscope
Trig_delay=5.5'trigger propagation delay in units of DT (trig to DIO delay is 4.5 +/- 0.3 ms on oscilloscope)

'Initialize DT array 
 DT_array(0)=(1.0055257142857144)*0.024304558/24'0: NIH base period  (0.0010183 based on internal oscillator for Pico23)							
DT_array(1)=0.0010126899166666666'1: APS base period  (0.0010127 275th subharmonic of P0)
DT_array(2)=0.0010416666666666667'2: LCLS base period (0.0010417 inverse of 8*120 = 960 Hz)

'Select Environment-dependent parameters
 DT=DT_array(E_index)
msShut_open=open_array(E_index)
msShut_close=close_array(E_index)
msShut_atten=56'NIH/LCLS attenuated position (in degrees)
 M_offset=Period_array(E_index)/2-Trig_delay

DGLOBAL(0)=1.01'version number
 DGLOBAL(1)=-1' Set to Operating_mode while executing; used for handshaking
DGLOBAL(2)=-1' O_mode (0: close; 1: open; 2: open Npts times on trigger; 3: synchronous (NIH/APS); 4: LCLS edge finding; 5: LCLS data collection) 
IGLOBAL(3)=24' M is number of base periods per step interval (NIH/APS: 24 for edge scan; 108 for data collection; LCLS: 96)
IGLOBAL(6)=45' Number of (x,y,z) coordinates
IGLOBAL(10)=3' Number of axes (x,y,z)
'Would prefer DGLOBAL(3) be M
'Would prefer DGLOBAL(4) be Npts
'Can eliminate IGLOBAL(10)

CALL TEST_PARAMETERS()'Generate coordinates to simulate edge finding operation

DOUT:0::1, 0'Ensure all bits of digital output are low when starting

Plane 1'PVT commands execute on Plane 1; Motion Composer commands execute on Plane 0
 ABS'Positions specified in absolute coordinates
 VELOCITY ON'Required to connect successive PVT commands	

WHILE DGLOBAL(2)>-2'enter DGLOBAL(2) = -2 to exit loop in orderly fashion

DOUT:0::1, 2'Set bit 1 HIGH during setup for PVT commands

' Update operating parameters
O_mode=DGLOBAL(2)
M=IGLOBAL(3)'DGLOBAL(3)
 Npts=IGLOBAL(6)'DGLOBAL(4)
 Xo=DGLOBAL(5)
Yo=DGLOBAL(6)
Zo=DGLOBAL(7)
T_0=(M+M_offset)*DT'Time after trigger to properly synchronize sequence

RECONCILE 0,1,2,6'Reconcile PVT positions in Plane 1 with Motion Composer

'Ensure diffractometer is in the starting position before triggering a new sequence
PVT_INIT  @1 
PVT 0: Xo, 0,1: Yo, 0,2: Zo, 0,6: msShut_close, 0 @0.024 ' Allow 24 ms to move into position.
 START
WAIT MOVEDONE 0,1,2,6

'Set up digital oscilloscope parameters
 IF D_Scope=1 THEN
SCOPETRIGPERIOD 1' 1 ms per point
SCOPEBUFFER CEIL(M*( Npts+2)*DT*1000)
SCOPETRIG
END IF

PVT_INIT  @1 
DOUT:0::1, 0'Set DOUT LOW to indicate end of setup; wait for trigger...
'DOUT bit 1 was found to be HIGH for 26 ms, of which 24 ms is specified to move into position (Xo,Yo,Zo).

'Start motion sequence after detecting rising edge of Digital Input Bit 1
 WHILE DIN:0::( 1,1)=1'wait till Digital Input Bit 1 is LOW 
 DWELL 0.00025000000000000001
WEND
WHILE(DIN:0::( 1,1)=0)AND(DGLOBAL(2)>1)'wait for LOW-to-HIGH transition on Digital Input bit 1.
 DGLOBAL(1)=DGLOBAL(2)'Client can poll DGLOBAL(1) to confirm when ready for trigger
 DWELL 0.00025000000000000001
WEND

'Execute sequence.
 IF O_mode=0 THEN
PVT 6: msShut_close, 0 @0.0080000000000000002 
START'Start sets time zero
 ELSEIF O_mode=1 THEN
PVT 6: msShut_open, 0 @0.0080000000000000002 
START'Start sets time zero
 ELSEIF O_mode=2 THEN
FOR i=0 to(Npts-1)
PVT 6: msShut_close, 0 @( T_0-20*DT) 
IF i=0 THEN
START'Start sets time zero
DOUT:0::1, 2'Set bit 1 HIGH to indicate start of sequence
 END IF
PVT 6: msShut_open, 0 @( T_0-13*DT) 
PVT 6: msShut_open, 0 @( T_0-11*DT) 
PVT 6: msShut_close, 0 @( T_0-4*DT) 
T_0=T_0+M*DT
NEXT i
'set DOUT LOW to indicate end of sequence
PVT 6: msShut_close, 0 @T_0 |DOUT 0:1, 0,15 
 ELSEIF O_mode=3 THEN
FOR i=0 to(Npts-1)
Xi=DGLOBAL(i*3+5)
Yi=DGLOBAL(i*3+6)
Zi=DGLOBAL(i*3+7)
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close, 0 @( T_0-20*DT) 
IF i=0 THEN
START'Start sets time zero
DOUT:0::1, 2'Set bit 1 HIGH to indicate start of sequence
 END IF
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_open, 0 @( T_0-13*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_open, 0 @( T_0-11*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close, 0 @( T_0-4*DT) 
T_0=T_0+M*DT
NEXT i
'Return to starting position; set DOUT LOW to indicate end of sequence
PVT 0: Xo, 0,1: Yo, 0,2: Zo, 0,6: msShut_close, 0 @T_0 |DOUT 0:1, 0,15 
 ELSEIF O_mode=4 THEN
FOR i=0 to(Npts-1)
Xi=DGLOBAL(i*3+5)
Yi=DGLOBAL(i*3+6)
Zi=DGLOBAL(i*3+7)
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close, 0 @( T_0-88*DT) 
IF i=0 THEN
START'Start sets time zero
DOUT:0::1, 2'Set bit 1 HIGH to indicate start of sequence
 END IF
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_atten, 0 @( T_0-80*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_atten, 0 @( T_0-8*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close, 0 @T_0 
T_0=T_0+M*DT
NEXT i
'Return to starting position; set DOUT LOW to indicate end of sequence
PVT 0: Xo, 0,1: Yo, 0,2: Zo, 0,6: msShut_close, 0 @T_0 |DOUT 0:1, 0,15 
 ELSEIF O_mode=5 THEN
FOR i=0 to(Npts-1)
Xi=DGLOBAL(i*3+5)
Yi=DGLOBAL(i*3+6)
Zi=DGLOBAL(i*3+7)
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close, 0 @( T_0-88*DT) 
IF i=0 THEN
START'Start sets time zero
DOUT:0::1, 2'Set bit 1 HIGH to indicate start of sequence
 END IF
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_atten, 0 @( T_0-80*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_atten, 0 @( T_0-8*DT) 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close, 0 @T_0 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close, 0 @( T_0+6*DT) |DOUT 0:1, 0,1 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close, 0 @( T_0+8*DT) |DOUT 0:1, 1,1 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_open, 0 @( T_0+16*DT) |DOUT 0:1, 1,1 
PVT 0: Xi, 0,1: Yi, 0,2: Zi, 0,6: msShut_close, 0 @( T_0+24*DT) |DOUT 0:1, 0,1 
T_0=T_0+2*M*DT
NEXT i
'Return to starting position; set DOUT LOW to indicate end of sequence
PVT 0: Xo, 0,1: Yo, 0,2: Zo, 0,6: msShut_close, 0 @T_0 |DOUT 0:1, 0,15 
 END IF

WAIT MOVEDONE 0,1,2,6
DGLOBAL(2)=-1'The value -1 indicates the sequence is finished and the program is awaiting a new command
 DGLOBAL(1)=-1
FORMAT PrintString,"E_index = %d, O_mode = %d, M = %d, Npts = %d\r",INTV:E_index,INTV:O_mode,INTV:M,INTV:Npts
PRINT PrintString'Print parameters for last sequence.

'May wish to incorporate (DIN(X,1,2)=0,1) in this loop to force the ms shutter to close/open
 WHILE DGLOBAL(1)=DGLOBAL(2)
DWELL 0.001
WEND
WEND

END PROGRAM 

FUNCTION TEST_PARAMETERS()
DIM i AS INTEGER
DIM real AS DOUBLE,Xo AS DOUBLE,Yo AS DOUBLE,Zo AS DOUBLE
Xo=-0.9466
Yo=-0.44330000000000003
Zo=0.62509999999999999
FOR i=0 TO IGLOBAL(6)-1
ratio=i/15
IF ABS(FLOOR(ratio)-ratio)>0.001 THEN
y=-(1-ratio+FLOOR(ratio))*0.20000000000000001
ELSE
x=ratio*0.10000000000000001
y=0
z=ratio*0.10000000000000001
END IF
DGLOBAL(i*3+5)=Xo+x
DGLOBAL(i*3+6)=Yo+y
DGLOBAL(i*3+7)=Zo+z
NEXT i
END FUNCTION
