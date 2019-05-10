' ------------------------------------------------ 
' --------------- SyncVsDwell.ab -----------------
' ------------------------------------------------ 
'
' This program is designed to demonstrate the
' difference between using a SYNC command and a  
' DWELL command by using STARTSYNC..SYNC 
' to create a tightly-timed loop and a DWELL to
' create a more loosely-timed delay.
'
' The SYNC command provides a delay based on a
' synchronous execution time, while the DWELL 
' command provides a delay based on the set
' execution time. These two commands are
' similar, but the SYNC command delays only
' the amount of time that remains to the next 
' synchronous execution time. The DWELL always
' delays for the entire time.
'
' The SYNC loop provides values exact to the
' second, while the DWELL loop accumulates
' fractions of seconds. This accumulation is
' caused by resources needed to execute the  
' FORMAT and PRINT commands.
'
'  ------------------------------------------------ 

DIM MyString AS STRING(96)
DIM TempValue AS DOUBLE

STARTSYNC 1000' Synchronize every millisecond.

CLEARTIMER

WHILE 1
' To demonstrate the difference between a SYNC loop and a
' DWELL loop, comment out the following SYNC line, and
' uncomment the DWELL line at the end of this program.
SYNC

TempValue=TIMER()*0.001

FORMAT MyString,"Time in Seconds: %g",DBLV:TempValue
PRINT MyString

'DWELL 1          ' Dwell for 1 second.
 WEND