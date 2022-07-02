"""Aerotech Ensemble Motion Controller
Author: Friedrich Schotte
Date created: 2019-08-15
Date lst modified: 2019-08-15
"""
__version__ = "2.0"
from logging import debug,info,warn,error

class Ensemble_Simulator(object):
    name = "ensemble_simulator"
    naxes = 7
    from sim_motor import sim_motor as motor
    
    axes = [motor(name="%s.axis%d" % (name,axis+1))
        for axis in range(0,naxes)]

ensemble_simulator = Ensemble_Simulator()


if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=format)
    self = ensemble_simulator

