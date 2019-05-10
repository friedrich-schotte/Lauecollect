#!/bin/env python
"""Extract images from and LCLS datastream an save them in a Lauecollect
directory structure.
Setup: source /reg/g/psdm/etc/ana_env.sh

Friedrich Schotte, Jan 25, 2016 - Feb 8, 2016
"""
__version__ = "1.0.2"

from pdb import pm # for debugging
from find import find
from table import table
from sleep import sleep
from os.path import exists,dirname,basename
from shutil import copy2
from datastream import datastream,timestamp,date_time
from numimage import numimage
from logging import error,warn,info,debug
import logging

data_root = "/reg/d/psdm/xpp/xppj1216/ftc/xppopr_xppj1216/Data/MbCO"
# This is how the images are tagged in the datastram.
exp = "exp=xppj1216"
options = ":smd:live:dir=/reg/d/ffb/xpp/xppj1216/xtc"
image_detector = "rayonix:data16"
# Additional detectors to read from the data stream an add to the logfile.
detectors = [
    "XppSb2_Ipm:sum",         # X-ray pulse intensity at "Strongback 2"
    "XppSb3_Ipm:sum",         # X-ray pulse intensity at "Strongback 3"
    "XppEnds_Ipm0:channel:0", # Laser pulse intensity 
    "XppEnds_Ipm0:channel:1", # X-ray pulse intensity at sample (scattering foil)
    "XPP:TIMETOOL:FLTPOS_PS", # laser to X-ray time delay in ps
    "lxt_ttc",                # nominal laser to X-ray time delay in s
]

logging.basicConfig(level=logging.INFO, # DEBUG,INFO,WARN,ERROR
    format="%(asctime)s: %(levelname)s: %(message)s",
    filename=data_root+"/process_datastream.log") 

# Find all lauecollect log files in the data directory.
info("Checking log files...")
# Excludes files and directories which are not useful.
exclude = ["*/alignment*","*/trash*","*/backup*","*._*","*/process_datastream*"]
logfiles = find(data_root,name="*.log",exclude=exclude)
info("Found %d logfile(s)." % len(logfiles))

for logfile in logfiles:
    # Create a backup copy of the original Lauecollect log file.
    backup_file = logfile+".orig"
    if not exists(backup_file): copy2(logfile,backup_file)
    log = table(backup_file,separator="\t")
    log.add_column("run")
    log.add_column("image_event_number")
    log.add_column("image_event_id",dtype="S160")
    log.add_column("image_timestamp",dtype="S60")
    log.add_column("image_size")
    for j in range(0,12): log.add_column("event_number(%d)"%(j+1))
    for j in range(0,12): log.add_column("timestamp(%d)"%(j+1),dtype="S40")
    for j in range(0,12): log.add_column("fiducial(%d)"%(j+1))
    for d in detectors:
        for j in range(0,12): log.add_column(d+"(%d)"%(j+1))
    dir = dirname(logfile)
    event_number = {}
    event_ids = []
    for i in range(0,len(log)):
        # Find the datastream event_id based on the time stamp
        datetime = log["date time"][i]
        run = datastream.run(exp+options,timestamp(datetime+"-0800"))
        exp_run = "%s:run=%d" % (exp,run)
        if not run in event_number:
            # What is the event number for the first image in the datastream?
            event_number[run] = \
                datastream.get_event_number(exp_run+":event=rayonix,0"+options)
            # Useful data starts after the first image (which is discarded)
            event_number[run] += 1
            debug("%r: starting event number %r" % (exp_run,event_number[run]))
        log["run"][i] = run
        # Put the detector reading for the 12 events leadign up to the next
        # image into the log file, using 12 columns per detector.
        for j in range(0,12):
            event_id = exp_run+":event=%d" % event_number[run]
            log["event_number(%d)"%(j+1)][i] = event_number[run]
            log["timestamp(%d)"%(j+1)][i] = date_time(datastream.timestamp(event_id+options))
            log["fiducial(%d)"%(j+1)][i] = datastream.fiducial(event_id+options)
            for d in detectors:
                log[d+"(%d)"%(j+1)][i] = datastream.get(event_id+options,d)
            event_number[run] += 1
        log["image_event_number"][i] = event_number[run]
        log["image_timestamp"][i] = date_time(datastream.timestamp(event_id+options))
        log["image_event_id"][i] = event_id
        image_file = dir+"/xray_images/"+log["file"][i]
        # Locate the image in the datastream by its event ID and
        # save it as TIFF file by the name specified in the logfile's
        # "file" column.
        image = datastream.get(event_id+options,image_detector)
        if image is not None: 
            debug("Got image %s from %s" % (basename(image_file),event_id))
            log["image_size"][i] = len(image)
            ##numimage(image).save(image_file)
        else: log["image_size"][i] = 0
    info("updating %r" % logfile)
    log.save(logfile)
