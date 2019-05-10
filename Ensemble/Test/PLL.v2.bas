' PLL

DIM PrintString AS STRING(80)
DGLOBAL(1)=0
While 1
counter=DGLOBAL(1)
WHILE DIN:0::( 1,0)=0'wait for clk pulse 
 DWELL 0.00050000000000000001
WEND
STARTSYNC 2
Zpos=PCMD(2)

j=0
FOR i=1 TO 4
SYNC
j=j+DIN:0::( 1,0)
NEXT i
DGLOBAL(3)=j

IF counter=0 THEN
Zpos_sum=0
Zpos_sumsq=0
counter=counter+1
DGLOBAL(1)=counter
ELSE
Zpos_sum=Zpos_sum+Zpos
Zpos_sumsq=Zpos_sumsq+Zpos^2
mean=Zpos_sum/counter
stdev=sqr(Zpos_sumsq/counter-( Zpos_sum/counter)^2)
DGLOBAL(2)=mean
counter=counter+1
DGLOBAL(1)=counter
END IF

DWELL 1

FORMAT PrintString,"%d,%.3f,%.3f,%.3f,%.5f\r",
INTV:counter,DBLV:Zpos,DBLV:mean,DBLV:stdev,DBLV:DGLOBAL(0)
'PRINT PrintString
 WEND
