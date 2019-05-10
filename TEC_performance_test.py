"""
Optical Freeze detector agent

Authors: Valentyn Stadnytskyi
Date created: 26 Feb 2018
Date last modified: 25 May 2018

-added retract -> iglobal =1 -> insert sequence that waits for previous one
to be executed first
"""
__version__ = "1.7"



from CAServer import casput,casdel, casget
from CA import caget
from datetime import datetime
from thread import start_new_thread
from pdb import pm
import os

from Ensemble_client import ensemble
from time import sleep,time
from thread import start_new_thread
from persistent_property import persistent_property
from temperature_controller import temperature_controller
from logging import debug,info,warn,error


if __name__ == "__main__":
    pass
