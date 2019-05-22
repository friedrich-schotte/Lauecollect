"""
Optical Freeze detector agent

Authors: Valentyn Stadnytskyi
Date created: 26 Feb 2018
Date last modified: 1 Mar 2018
"""
__version__ = "1.0"
from CAServer import casput,casdel
from optical_image_analyser import image_analyser
from datetime import datetime
from logging import debug,info,warn,error
from thread import start_new_thread

        
def run():
    from logging import info
    info('optical freeze detector started')
    from time import sleep
    while True:
        is_fr = is_frozen()
        if is_fr:
            set_deicing(1)
        casput("NIH:SAMPLE_FROZEN_OPT.VAL",is_frozen)
        casput("NIH:SAMPLE_FROZEN_OPT.BCKG",image_analyser.background_image_flag)
        # Publish additional diagnostics
        casput("NIH:SAMPLE_FROZEN_OPT.MEAN",image_analyser.mean)
        casput("NIH:SAMPLE_FROZEN_OPT.STDEV",image_analyser.stdev)
        sleep(0.2)

def is_frozen():
    """checks if sample is frozen"""
    res = image_analyser.is_frozen()
    return res


        
if __name__ == "__main__":
    print('run()')
    import logging
    logging.basicConfig(level=logging.INFO,format="%(levelname)s: %(message)s")
