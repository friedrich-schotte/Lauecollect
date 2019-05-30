"""
Author: Friedrich Schotte
Date created: 2019-05-24
Date last modified: 2019-05-29
"""
__version__ = "1.0" 

from configuration import configuration
conf = configuration("Julich_chopper_modes")
descriptions = conf.descriptions
X = conf.positions[0]
Y = conf.positions[1]
Phi = conf.positions[2]
S_1 = descriptions.index("S-1")

def update():
    for N in range(3,25+1):
        if "S-%d" % N in descriptions:
            row = descriptions.index("S-%d" % N)
            Y[row] = Y[S_1] - N*0.0377+0.035
            Phi[row] = Phi[S_1] + N*2.744e-9
print("update()")
