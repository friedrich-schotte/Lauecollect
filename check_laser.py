#!/usr/bin/env python
"""
Monitor status of ns laser during data collection
Author: Friedrich Schotte
Date created: 10/27/2017
Date last modified: 10/27/2017
"""
__version__ = "1.0.2"
from logging import debug,info,warn,error

def check_laser_loop():
    from sleep import sleep
    import traceback
    info("Initializing...")
    try:
        while True:
            try: check_laser()
            except Exception,msg:
                error("%s" % msg)
                traceback.print_exc()
            sleep(3)
    except KeyboardInterrupt: pass

def check_laser():
    """Play an alret sound if the laser signal is below threshold"""
    amplitude = laser_amplitude()
    info("%.3f" % amplitude)
    if amplitude < 0.1: alert()

def alert():
    from sound import play_sound
    play_sound("chimes")

def laser_amplitude():
    """Peak signal in V, typical 0.250 V"""
    from numpy import nan
    t,U = last_laser_waveform()
    if len(U) > 0: amplitude = max(U)
    else: amplitude = nan
    return amplitude

def last_laser_waveform():
    """time and voltage"""
    from lecroy_scope_waveform import read_waveform
    from os.path import exists
    file = last_laser_waveform_file()
    if exists(file):
        debug("last laser waveform: %s" % file)
        t,U = read_waveform(file)
        t,U = t[-1],U[-1]
    else: t,U = [],[]
    return t,U

def last_laser_waveform_file():
    file = last_image()
    file = file.replace("/xray_images/","/laser_traces/")
    file = file.replace(".mccd","_01_laser.trc")
    return file

def last_image():
    from os.path import exists,dirname
    filename = logfile()
    if exists(filename):
        f = file(filename)
        f.seek(-512,2)
        t = f.read(512)
        line = ([""]+t.strip("\n").split("\n"))[-1]
        image_file = ([""]+line.split("\t")[1:2])[-1]
    else:
        debug("%s not found" % filename)
        image_file = ""
    if image_file: image_file = dirname(filename)+"/xray_images/"+image_file
    return image_file

def logfile():
    """Current collection logfile"""
    import lauecollect
    from normpath import normpath
    lauecollect.load_settings()
    file = normpath(lauecollect.logfile())
    return file

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s")
    ##print('check_laser_loop()')
    check_laser_loop()
