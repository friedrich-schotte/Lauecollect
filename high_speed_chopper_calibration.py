"""
Author: Friedrich Schotte
Date created: 2019-05-29
Date last modified: 2022-06-26
Revision comment: Using motor name
"""
__version__ = "1.1.1"

from configuration import configuration
from time import sleep
conf = configuration("Julich_chopper_modes")
descriptions = conf.descriptions
updated = conf.updated
X = conf.X.positions
Y = conf.Y.positions
phase = conf.phase.positions

def preview():
    calculate_new()
    t = ""
    t += "\t".join([
        "Name",
        "Updated"+" "*10,
        conf.X.name+" "*8,
        conf.Y.name+" "*8,
        conf.phase.name+" "*0,
        conf.p0_shift.name+" "*0,
    ])+"\n"
    for i in range(0,conf.nrows): 
        t += "\t".join([
            descriptions[i],
            new_updated[i],
            conf.X.formatted(new_X[i]),
            conf.Y.formatted(new_Y[i]),
            conf.phase.formatted(new_phase[i]),
            conf.p0_shift.formatted(conf.p0_shift.positions[i]),
        ])+"\n"
    return t

def update():
    calculate_new()
    Y[:] = new_Y 
    phase[:] = new_phase 
    X[:] = new_X 

def calculate_new():
    global new_updated,new_X,new_Y,new_phase,S_1
    new_updated = updated[:]
    new_Y = Y[:]
    new_phase = phase[:]
    new_X = X[:]

    S_1 = descriptions.index("S-1")

    for N in range(3,25+1):
        if "S-%d" % N in descriptions:
            row = descriptions.index("S-%d" % N)
            new_Y[row] = Y[S_1] - N*0.0377+0.035
            new_phase[row] = phase[S_1] + N*2.744e-9

    if "S-1t" in descriptions:
        row = descriptions.index("S-1t")
        new_Y[row] = Y[S_1] - 0.816

    for row in range(0,conf.nrows):
        if descriptions[row] != "Bypass":
            new_X[row] = X[S_1]

    for row in range(0,conf.nrows):
        if new_X[row] != X[row] or new_Y[row] != Y[row] or new_phase[row] != phase[row]:
            new_updated[row] = now()

def now():
    from datetime import datetime
    return str(datetime.now()).split(".")[0]

if __name__ == "__main__":
    print("print(preview())")
    print("update()")
