DIM PrintString AS STRING(80)
startsync 1000
WHILE 1
SYNC
A=EXTPOS(0)
'DWELL 1
 SYNC
B=EXTPOS(0)
FORMAT PrintString,"%d\n",INTV:(B-A)
PRINT PrintString
WEND
