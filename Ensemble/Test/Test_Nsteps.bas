DIM PrintString AS STRING(80)
DIM N AS INTEGER
DIM NS AS INTEGER
DIM NR AS INTEGER
DIM NRD AS INTEGER
DIM NL AS INTEGER
DIM NB AS INTEGER

N=3
NS=2^(N+1)-3
NR=3*2^(N+1)-3
NRD=FLOOR(41/NS)
NL=NS*(41/NS-FLOOR(41/NS))
NB=FLOOR(NL>0)
'NE = MAKEINTEGER(NL>0)
'*2^(N+2)+NL+3)

FORMAT PrintString,"%d,%d,%d,%d,%d,%d,%d\r",INTV:N,INTV:NS,INTV:NR,INTV:NRD,INTV:NL,INTV:NB
PRINT PrintString