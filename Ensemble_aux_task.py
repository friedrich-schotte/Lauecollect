"""
Optical Freeze detector agent

Authors: Valentyn Stadnytskyi
Date created: 26 Feb 2018
Date last modified: 7 Mar 2018

Version: 1.5
-added retract -> iglobal =1 -> insert sequence that waits for previous one
to be executed first
"""
__version__ = "1.5"



from CAServer import casput,casdel
from CA import caget
from datetime import datetime
from logging import debug,info,warn,error
from thread import start_new_thread
import os
from Ensemble import ensemble
from time import sleep,time
from thread import start_new_thread


def freeze_intervention(filename = 'Freeze_Intervention.ab' ):
         ensemble.auxiliary_task_filename = filename
        
if __name__ == "__main__":
    print("freeze_intervention()")
