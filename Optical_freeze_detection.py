"""
Optical Freeze detector

Authors: Valentyn Stadnytskyi
Date created: 26 Feb 2018
Date last modified: 26 Feb 2018
"""
__version__ = "1.0"
from CAServer import casput,casdel
from optical_image_analyser import image_analyser

def run():
    from time import sleep
    while True:
        temp = is_frozen()
        casput("NIH:SAMPLE_FROZEN_OPT.VAL",temp)
        sleep(1)

def is_frozen():
    """checks if sample is frozen"""
    ret = image_analyser.is_frozen()
    return ret


        
if __name__ == "__main__":
    print('Time Start: %r' % str(datetime.now()))
    camera = Camera("WideFieldCamera") #'WideFieldCamera' #MicrofluidicsCamera #MicroscopeCamera
    Optical_freeze_detector = image_analyser()
    print('Optical_freeze_detector.set_background_image()')
    print('Optical_freeze_detector.get_difference_image()')
    print('Optical_freeze_detector.is_frozen()')
    print("Optical_freeze_detector.plot()")
    print("Optical_freeze_detector.plot_difference()")

    print('oasis_chiller_set_point(%r)' % temperature_controller.command_value)
    print('run()')
