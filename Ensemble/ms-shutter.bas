' This program operates the millisecond shutter in a mode
' where is opens and closed depending on the voltage level of input 0
' and operates in pulse mode triggered by input 1.

' Friedrich Schotte, APS, 18 Oct 2008 - 5 Nov 2018

' When the level of input 0 is TTL high the shutter is always in open position.
' When level at input 0 is TTL low the motor toggles between to closed positions
' if a TTL rising edge on input 1 is detected.
' When the level on input 0 is high the input 1 is ignored.

HEADER
INCLUDE "StringLibHeader.basi"
'DEFINE Ethernet 2 'COM channel 2 = Ethernet Socket 1
'The parameter InetSock1Flags needs to be 0x1 (TCP server)
'The port number is given by the parameter InetSock1Port (default: 8000)
END HEADER

DECLARATIONS
GLOBAL Version AS STRING="3.2"' rotated by 180deg to avoid bad spot in vacuum seal
GLOBAL open_pos,closed_pos,closed_pos2
GLOBAL open_close_speed,pulsed_speed AS DOUBLE
GLOBAL open_close_acc_ramp,pulsed_acc_ramp AS DOUBLE
GLOBAL timed_open AS INTEGER
GLOBAL opening_time as INTEGER
GLOBAL trigger_enabled AS INTEGER
GLOBAL open_close_enabled AS INTEGER'pulse the shutter on external trigger
 GLOBAL Command AS STRING'command buffer needed by Handle_Ethernet()
 GLOBAL opened AS INTEGER'last time at which shutter openend in ms
 GLOBAL closed AS INTEGER'last time at which shutter closed in ms
 GLOBAL time_opened AS INTEGER' time since the shutter openend in ms
GLOBAL open_timed AS INTEGER'is the shutter currently open by a timer?
 GLOBAL pulse_count AS INTEGER'number of pulsed operations
END DECLARATIONS

 PROGRAM
'Initialize global variables
 timed_open=0' mode: 1 = after a trigger open for a certain duration
trigger_enabled=1'pulse the shutter on external trigger
 open_close_enabled=1'open close digital input enabled
 pulse_count=0'number of pulsed operations

DIM bits AS INTEGER' axis status bits
DIM home_cyle_complete AS INTEGER' axis status bits
DIM current_pos AS INTEGER
DIM dt AS DOUBLE
DIM level0,level1,last_level1,rising_edge1 AS INTEGER' digital input states
DIM msg AS STRING
SETPARM 1023:UserString0,"ms-shutter.ab" 

' Found marginal closed position to be at 9.0 deg and 18.54 deg.
' Friedrich Schotte, Philip Anfinrud 17 Oct 2008
' opening range 9.54 deg, opening position: 13.77 deg
' speed: (18.54 - 9.0 ) / 5 ms = 1908 deg / s 
' Acceleration 2,250,000 steps/s2 = 202,500 deg/s2 
SETPARM 1023: msShut_ext, DefaultRampRate,2250000 ' in steps/s2 (changed AccelDecelRate to DefaultRampRate)
' Acceleration  ramp needed:
' s = v2/2a = (1908 deg/s)2/(2*405,000 deg/s2) = 4.49 deg, rounded to 4.5 deg
closed_pos=181.22'normal closed position in open/close mode 
 open_pos=189.99000000000001
' alternating closed position used only in pulsed mode
closed_pos2=198.75999999999999

' Timing for pulsed open mode
pulsed_speed=1908' top speed in deg/s
pulsed_acc_ramp=4.5' angle over which the motor accelerates in deg

' Timing for open/close mode
' opening range 9.0 deg to 18.54 deg: 9.54 deg
' speed: (18.54 - 9.0 ) / 5 ms = 1908 deg / s
dt=0.0080000000000000002' total operation time in s
open_close_speed=2*(open_pos-closed_pos)/dt' top speed in counts/s
open_close_acc_ramp=(open_pos-closed_pos)/2' angle over which the motor accelerates

msShut_ext