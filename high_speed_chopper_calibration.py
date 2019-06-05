"""
Author: Friedrich Schotte
Date created: 2019-05-29
Date last modified: 2019-05-30
"""
__version__ = "1.0" 

from configuration import configuration
from time import sleep
conf = configuration("Julich_chopper_modes")
descriptions = conf.descriptions
X = conf.positions[0]
Y = conf.positions[1]
Phi = conf.positions[2]
S_1 = descriptions.index("S-1")

def update():
    new_Y = Y[:]
    new_Phi = Phi[:]
    for N in range(3,25+1):
        if "S-%d" % N in descriptions:
            row = descriptions.index("S-%d" % N)
            new_Y[row] = Y[S_1] - N*0.0377+0.035
            new_Phi[row] = Phi[S_1] + N*2.744e-9
    Y[:] = new_Y 
    Phi[:] = new_Phi 

    new_X = X[:]
    for row in range(0,len(X)):
        if descriptions[row] != "Bypass":
            new_X[row] = X[S_1]
    X[:] = new_X 

print("update()")
