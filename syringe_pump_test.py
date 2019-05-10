from syringe_pump_new import *
from sim_motor import sim_motor
P1,P2 = sim_motor("sim_syringe_pump"),sim_motor("sim_syringe_pump2")
PC = SyringePumpCombined("syringe_pump_combined",P1,P2)
self = PC # for debugging
print('PC.dV = 0; PC.V = 10')
print('P1.value = 5; P2.value=15')
print('P1.value = 50; P2.value=50')
print('(P1.value,P2.value),(PC.V_min,PC.V,PC.V_max)')
print('(P1.value,P2.value),(PC.dV_min,PC.dV,PC.dV_max)')
