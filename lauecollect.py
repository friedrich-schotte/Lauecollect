#!/usr/bin/env python
"""Laue Data Collection
Author: Friedrich Schotte
Date created: 2007-08-22
Date last modified: 2018-09-13
"""
from pdb import pm # for debugging
# Beamline instrumentation
from instrumentation import *
from CA import caget,caput
# General Python library functions
from numpy import nan,isnan,inf,isinf,array,sqrt,floor,ceil,log10,sin,cos,pi,\
     radians,clip,allclose,where,rint
##import numpy; numpy.seterr(all="ignore") # Turn off warning "All-NaN axis encountered" 
from time import sleep,strftime,time,localtime
from os import getcwd,remove,makedirs,listdir,chmod
from os.path import exists,dirname,basename,join,splitext,normpath,getmtime
from tempfile import gettempdir
from textfile import read,save
from sound import play_sound
from sample_alignment import sample
from sample_translation_raster import grid
from peak_integration import peak_integration_mask
from ImageViewer import show_images
from string_table import string_table
from logging import info,error,warn # for debugging
from exists import exist_files
from time_string import time_string,seconds
from thread import start_new_thread,allocate_lock
from numimage import numimage
from checklist import beam_ok

__version__ = "28.0" # Methods-based data collection: SAXS_WAXS_methods
 
DiffX = diffractometer.X
DiffY = diffractometer.Y
DiffZ = diffractometer.Z
##Phi = diffractometer.Phi
Spindle = Phi # motor for sample rotation

class param: "Container for data collection parameters"
# Set reasonable defaults
param.amin = -90.0
param.amax = 90.0
param.astep = 4.0
param.amode = "Single pass"
param.alist = range(-30,30,4)
param.ref_timepoint = nan # off
param.file_basename = "test"
param.extension = "mccd"
param.description = ""
param.logfile_filename = "test.log"
param.path = getcwd()

class options: "Container for data collection options"
# List of variable names, starting with the fastest variable to the slowest
# variable
options.collection_order = [["laser_on","delay"],["translation"],["angle"]]
options.variable_include_in_filename = ["delay","angle","laser_on","repeat",
    "repeat2","level","translation","temperature"]
options.variable_choices = {"level":[1.],"temperature":[20]}
options.variable_wait = {"level":False,"temperature":True,"repeat":False,"repeat2":False}
options.variable_return = {"level":False,"temperature":True,"repeat":False,"repeat2":False}
options.variable_return_value = {"temperature":22}
options.npulses = 1
options.npulses_off = 1
options.npasses = 1
options.npasses2 = 1
options.min_waitts = [0.304]
options.min_waitt_off = 0.097
options.max_waitt_off = 0.097
options.estimate_collection_time = False
options.wait_for_beam = False # suspend data collection during storage ring down time
options.wait_for_topup = False # suspend data collection during injection
options.open_laser_safety_shutter = False # automatically open the laser shutter
options.save_raw_image = False
options.periodically_read_ccd = False
options.use_illuminator = False # insert/retract backlight
options.ccd_bin_factor = 4 # determines image  size for data collection
options.ccd_hardware_trigger = False
options.ccd_readout_mode = "frame transfer"
options.xray_detector_enabled = True
options.xray_on = [True] # Acquire image with X-rays?
options.finish_series_variable = "delay"

class temp: "Container for temperature scan parameters"
temp.hardware_triggered = True # Ramp on backpanel TTL trigger
temp.step = 0.050        # Triggered increment in deg C
temp.settling_time = 0.0 # Extra wait time when changing temperature

class align: "Container for alignment scan parameters"
align.enabled = False    # Perform aligmnent scans?
align.step = 0.025       # alignment scan step size in mm (negative sign implied)
align.start = 0          # alignment scan starting point in mm
align.end = -0.400       # alignment scan starting point in mm
align.beamsize = 0.030   # vertical X-ray beam size
align.center_time = 0    # Time center point was defined
align.center_sample = "" # sample name at the time the sample was centered
align.profile = []       # data of last alignment scan
align.threshold = 4.0    # Peak search threshold signal to noise ratio
align.boxsize = 15       # Spot intgration box size in pixels
align.npoints = 5        # number of points to calculate slope
align.optimize = False   # use shoter scan range once the crystal shape is known
align.min_scanpoints = 7 # used when optimizing the scan range
align.last_scans_use = 8 # number of scans to use to determine the scan range
align.scan_offset = 0.060 # Start of scan range outside the crystal visual edge
align.attenuate_xray = False # Attenuate X-ray beam
align.npulses = 10       # number of pulses for each alignemnt image
align.waitt = 0.024      # X-ray pulse spacing for alignment images
align.align_at_collection_phis = False # Do aligment scan at every angle?
align.align_at_collection_zs = False   # Do aligment scan at every DiffZ if translating?
align.intepolation_dphi = 30 # Interpolate if support angles within +/-30 deg
align.intepolation_dz = 0.2  # Interpolate if support GonZs within +/-0.2 mm
align.ccd_bin_factor = 8 # determines image  size for alignment scans

class translate: "Container for sample translation parameters"
translate.mode = "off"   # Operation mode for sample translation
translate.hardware_triggered = False # Slave motion controller to timing system?
translate.interleave_factor = 1 # translate in multiple passes 
translate.single = True  # single shot per spot per pass
translate.after_image_interleave_factor = 1 # translate in multiple passes 
translate.after_images = 1 # after how many images to translate
translate.return_after_series = 1 # after how many series to return to the starting point 
translate.after_image_nspots = 1  # used if "after image" translation enabled 
translate.during_image_nspots = 1  # used if "after image" translation enabled 
translate.move_when_idle = False # Keep moving the linear stage when idle?
translate.move_time = 0.020 # time to move the sample stage in a triggered move
translate.modes = [] # for linear stage, 'Fly-thru', 'Stepping-12'

class pump: "Container for Syringe pump. parameters"
pump.enabled = False
pump.hardware_triggered = True
pump.step = 90
pump.frequency = 1 # very how many image?
pump.on = [True] # for every image

class chopper: "Container for chopper parameters"
chopper.x = [34.491,34,491,34.491,31.016,37.210,37.210,37.210]
chopper.y = [30.825,30.755,30.455,30.060,30.345,30.425,30.140]
chopper.phase = [0,0,0,0,0,0,0,0]
chopper.pulses = [1,3,1,1,1,1,1,1]
chopper.time = [1e-12,308e-9,1.54e-6,1e-12,1e-12,1e-12,1e-12,1e-12]
chopper.min_dt = [-20e-6,100e-9,150e-6,-20e-6,0,0,0,0]
chopper.gate_start = [+115e-9,-35e-9,-625e-9,+115e-9,0,0,0,0]
chopper.gate_stop = [+490e-9,+640e-9,+1200e-9,+490e-9,0,0,0,0]
chopper.use = [False,False,False,True,False,False,False,False]
chopper.wait = True # suspend data collection while chopper mode is changing?
chopper.modes = [] # if not using te time dealy to select the mode

class diagnostics: "Container for alignment scan parameters"
diagnostics.enabled = False
diagnostics.delay = False
diagnostics.xray = False
diagnostics.laser = False
diagnostics.min_window = 2e-6
diagnostics.timing_offset = 0
diagnostics.xray_reference = -122e-12
diagnostics.xray_offset_level = 0
diagnostics.xray_gate_start = -625e-9
diagnostics.xray_gate_stop = +1200e-9
diagnostics.xray_record_waveform = False
diagnostics.xray_sampling_rate = 1e9
diagnostics.xray_time_range = 5e-6
diagnostics.xray_time_offset = 0
diagnostics.laser_reference = 2.5e-9
diagnostics.laser_offset = 0
diagnostics.laser_record_waveform = False
diagnostics.laser_sampling_rate = 1e9
diagnostics.laser_time_range = 2e-6
diagnostics.laser_time_offset = 0
diagnostics.PVs = ["S:SRcurrentAI.VAL","BNCHI:BunchCurrentAI.VAL","14IDB:oxTemp",
    "14Keithley1:DMM1Ch1_raw.VAL","14Keithley1:DMM1Ch3_raw.VAL","14Keithley1:DMM1Ch4_raw.VAL"]
diagnostics.PVnames = ["ring-current[mA]","bunch-current[mA]","CryoJet[K]",
    "cooling-water-temp[C]","room-temp[C]","table-temp[C]"]
diagnostics.PVuse = [True,True,True,False,False,True]

class xraycheck: "Container for X-ray beam optimization parameters"
xraycheck.enabled = False       # Auto-tweak during data collection?
xraycheck.run_variable = "delay"# Run check when this colection variable repeats 
xraycheck.interval = 3600       # time in seconds before repeating
xraycheck.at_start_of_time_series = True
xraycheck.retract_sample = -1.5 # [mm] to spare sample from expore to X-ray beam
xraycheck.sample_motor = "DiffZ" # use "DiffZ" motor to retract the sample
xraycheck.last = 0              # last time alignment scan finished
xraycheck.min_intensity = 0.1   # do not run optimization if x-ray intensity if less than 20% of refernce
xraycheck.type = "beam position"# which type of optimization? "beam position" or "I0"
xraycheck.comment = ""          # summary of last check

class lasercheck: "Container for laser beam profiler"
lasercheck.enabled = False       # Auto-tweak during data collection?
lasercheck.check_only = False    # Measure position only, not applying correction
lasercheck.interval = 3600       # time in seconds before repeating
lasercheck.at_start_of_time_series = True
lasercheck.retract_sample = True # Move sample out of laser beam during check?
lasercheck.park_motors = ["DetZ","Phi","DiffX","DiffY"]
lasercheck.park_positions = [678.47,-35,10.35,1.725]
lasercheck.sample_position = []
lasercheck.last = 0              # Last time alignment scan finished
lasercheck.attenuator = 180.0    # VNFilterangle in deg
lasercheck.reprate = 40          # Laser trigger frequency
lasercheck.naverage = 4          # How many times to measure the beam position
lasercheck.signal_to_noise = 15. # Take no corrective action below this value.
lasercheck.comment = ""          # summary of last laser beam check
lasercheck.zprofile = []         # last recorded beam profile in X-ray beam direction 
lasercheck.xprofile = []         # last recorded beam profile orthogonal to X-ray direction 
lasercheck.last_image = ""       # pathname of last saved beam profile image

lasercheck_image = None          # last redorded beam profile image in PIL format

class timingcheck: "Container for timinig calibration parameters"
timingcheck.enabled = False       # Auto-tweak during data collection?
timingcheck.interval = 3600       # time in seconds before repeating
timingcheck.at_start_of_time_series = True
timingcheck.retract_sample = -1.0 # move sample by 1.0 mm
timingcheck.attenuator_angle = 300# VNFilter seeting in deg
timingcheck.sample_motor = "DiffY" # use "DiffZ" motor to retract the sample
timingcheck.last = 0              # last time alignment scan finished
timingcheck.min_intensity = 0.1   # do not run optimization if x-ray intensity if less than 20% of refernce
timingcheck.comment = ""          # summary of last check

class sample_photo: "Container for sample image"
sample_photo.enabled = False      # Auto-tweak during data collection?
sample_photo.phis = [0]           # List of orientations at which to take photos/
sample_photo.frequency_orientations = 1 # How often to save the image

class checklist: "Container for check list parameters"
checklist.U23 = 10.741 # operating gap of undulator
checklist.U27 = 15.848 # operating gap of undulator
checklist.wbshg = 1.000 # nom. white-beam slits horizontal gap  
checklist.wbsvg = 1.000 # nom. white-beam slits vertical gap
checklist.shg = 0.200 # nom. horizontal gap of sample JJ slits 
checklist.svg = 0.120 # nom. vertical gap  of sample JJ slits 

# Initialize status variables
class task: "Container for status variables"
task.image_number = 1
task.last_image = None # for 'Finish Time Series' option
task.cancelled = False
task.finish_series = False
task.action = ""
task.last_pulse = 0 # timestamp of the last X-ray pulse 
task.next_pulse = 0 # time to wait until before sending the next laser pulse
task.run_background_threads = False
task.comment = "" # progress info
task.autorecovery_needed = False # something left in a messy state
task.last_image_xdet_count = nan # acquisition finished after this count

def save_settings():
    """Update the default parameter file"""
    global settings_file_timestamp
    filename = settings_file()
    save_settings_to_file(filename)
    settings_file_timestamp = getmtime(filename)

def reload_settings():
    """Reload default parameters parameters if changed."""
    global settings_file_timestamp
    filename = settings_file()
    if exists(filename) and getmtime(filename) != settings_file_timestamp:
        load_settings(filename)
        settings_file_timestamp = getmtime(filename)

settings_file_timestamp = 0

def save_settings_to_file(filename):
    """Write a parameter file"""
    if not exists(dirname(filename)): makedirs(dirname(filename))
    f = file(filename,"w")

    for obj in param,options,temp,align,translate,chopper,pump,diagnostics,\
        xraycheck,lasercheck,timingcheck,sample_photo,checklist:
        for name in dir(obj):
            if name.startswith("__"): continue
            line = "%s.%s = %r\n" % (obj.__name__,name,getattr(obj,name))
            line = line.replace("-1.#IND","nan") # Needed for Windows Python
            line = line.replace("1.#INF","inf") # Needed for Windows Python
            f.write(line)

def load_settings(filename=None):
    """Reload last saved parameters."""
    if filename == None: filename = settings_file()
    if not exists(filename): return
    for line in file(filename).readlines():
        try: exec(line)
        except: warn("ignoring line %r in settings" % line)
    global Spindle
    try: Spindle = eval(param.amotor)
    except:
        warn("Resetting spindle motor from %r to Phi" % param.amotor)
        param.amotor = "Phi"; Spindle = Phi

def save_dataset_settings():
    """Generate or update a settings file in the current data collection
    directory."""
    filename = param.path+"/"+param.file_basename+".par"
    save_settings_to_file(filename)

def settings_file():
    """Where to save to the default settings"""
    filename = settingsdir()+"/lauecollect_settings.py"
    return filename

def settingsdir():
    """In which directory to save to the settings file"""
    return module_dir()+"/settings"
    
def single_image():
    """This is for quick test shots.
    Acquire a single image in the current orientation without saving it."""
    action = task.action; task.action = "Single Image"

    set_chopper(0)
    task.image_number = 0 # for status display
    start_images([0])
    acquire_image(0)
    finish_images([0])

    task.action = action

def collect_dataset():
    """Acquire all the images of a dataset, resuming a collection
    where interrupted"""
    from checklist import checklist as my_checklist

    if not exists (param.path): makedirs (param.path)
    if not exists (param.path): return

    start_dataset()

    image_numbers = collection_pass(1)
    while len(image_numbers)>0 and not task.cancelled:
        while not beam_ok() and len(image_numbers)>0 and not task.cancelled:
            task.image_number = image_numbers[0] # for GUI update
            info("Waiting because %s..." % my_checklist.test_failed)
            sleep(1)
            image_numbers = collection_pass(1)
        if task.cancelled: break
        acquire_images(image_numbers)
        image_numbers = collection_pass(task.image_number+1)

    finish_dataset()
    
    if not task.cancelled: play_sound("ding")

def start_dataset():
    """Called once at the beginning of a dataset"""
    diagnostics_start_dataset()
    collection_variables_start_dataset()

def finish_dataset():
    """Called once at the end of a dataset"""
    diagnostics_finish_dataset()
    collection_variables_finish_dataset()

def acquire_images(image_numbers):
    """Collect a series of images in hardware triggred mode.
    The actions between the images can be performed in quickly enough
    so the collection does not need to be suspended.
    image_numbers: 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    if len(image_numbers) > 0:
        align_sample_if_needed_for_phi(angle(image_numbers[0]))
        if xray_beam_check_before(image_numbers[0]):
            run_xray_beam_check(apply_correction=True)

        task.image_number = image_numbers[0] # for progress report

        set_collection_variables(image_numbers[0],wait=True)

        start_images(image_numbers)

        for image_number in image_numbers:
            if task.cancelled: break
            if not image_number <= nimages_to_collect(): break
            set_collection_variables(image_number,wait=False)
            acquire_image(image_number)
            if task.cancelled or not beam_ok(): break

        finish_images(image_numbers)

def start_images(image_numbers):
    """This is run at the beginning of 'collect_dataset' or 'single_image'.
    image_numbers: list of 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    prepare_images(image_numbers)
    acquisition_start(image_numbers)    
    
def prepare_images(image_numbers):
    """Perform all the setup, without starting the acquisition.
    image_numbers: list of 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    from threading import Thread
    threads = []
    threads += [Thread(target=logfile_start_images,args=(image_numbers,))]
    threads += [Thread(target=diagnostics_start_images,args=(image_numbers,))]
    threads += [Thread(target=temperature_controller_start_images,args=(image_numbers,))]
    threads += [Thread(target=motion_controller_start_images,args=(image_numbers,))]
    threads += [Thread(target=timing_system_start_images,args=(image_numbers,))]
    threads += [Thread(target=xray_detector_start_images,args=(image_numbers,))]
    for thread in threads: thread.start()
    for thread in threads: thread.join()

def prepare_images_serial(image_numbers):
    """Perform all the setup, without starting the acquisition.
    image_numbers: list of 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    logfile_start_images(image_numbers)
    diagnostics_start_images(image_numbers)
    temperature_controller_start_images(image_numbers)
    motion_controller_start_images(image_numbers)
    timing_system_start_images(image_numbers)
    xray_detector_start_images(image_numbers)

def motion_controller_start_images(image_numbers):
    """Configure motion controller
    image_numbers: list of 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    if "after image" in translate.mode:
        XYZ = array([translation_after_image_xyz(i) for i in image_numbers])
        triggered_motion.xyz = XYZ
        triggered_motion.waitt = timing_system.waitt.next(wait_time(image_numbers[0]))
        triggered_motion.armed = True

def timing_system_start_images(image_numbers):
    """Set up the trigger pulse generation for a series of images
    image_numbers: list of 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    debug("Lauecollect: timing system setup...")
    
    timing_sequencer.queue_active = False # hold off exection till all is set up
    timing_system.image_number.count = 0
    timing_system.pass_number.count = 0
    timing_system.pulses.count = 0

    debug("Lauecollect: Compiling parameters for timing system...")
    my_delays      = [delay(i) for i in image_numbers]
    my_laser_on    = [laser_on(i) for i in image_numbers]
    my_ms_on       = [1]*len(image_numbers)
    my_image_numbers=list(image_numbers)
    debug("Lauecollect: Compiling parameters for timing system done.")

    Ensemble_SAXS.acquire(
        delays=my_delays,
        laser_on=my_laser_on,
        ms_on=my_ms_on,
        image_numbers=my_image_numbers,
    )

def xray_detector_start_images(image_numbers):
    """Configure X-ray area detector
    image_numbers: list of 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    if options.xray_detector_enabled:
        filenames = [filename(i) for i in image_numbers]
        show_images(filenames)
        ccd.bin_factor = options.ccd_bin_factor
        ccd.acquire_images(image_numbers,filenames)

def acquisition_start(image_numbers):
    """Start imitng system after all subsystem are initialized"""
    if len(image_numbers) > 0:
        if not "linear stage" in translate.mode:
            filenames = [filename(i) for i in image_numbers]

            xdet_on = timing_sequencer.xdet_on
            progress("X-ray detector continuously triggered: %r" % xdet_on)

            # If the X-ray detector is not continuously triggered...
            if not xdet_on: xdet_count = timing_system.xdet_count.count+2 # discard first dummy image

            timing_sequencer.acquisition_start()

            progress("Timing system: Waiting for acquisition to start...")
            while not timing_system_acquiring() and not task.cancelled: sleep(0.01)
            progress("Timing system: Acquisition started.")
            
            if xdet_on: xdet_count = timing_system.xdet_count.count+1

            from rayonix_detector_continuous_1 import ccd
            progress("First image %r, xdet_count=%r" % (basename(filenames[0]),xdet_count))
            ccd.acquire_images_triggered(filenames,start=xdet_count)

            task.last_image_xdet_count = xdet_count+len(image_numbers)-1
        else:
            progress("Timing system: Starting acquisition...")
            Ensemble_SAXS.acquisition_start(image_numbers[0])
            while not timing_sequencer.queue_active and not task.cancelled:
                sleep(0.05)
            
            task.last_image_xdet_count = nan

def timing_system_acquiring():
    """Has the timing system started acquiring data?"""
    return  timing_system.image_number.count > 0 \
        or timing_system.pass_number.count > 0 

def finish_images(image_numbers):
    """This is run at the end of 'collect_dataset' or 'single_image'         
    image_numbers: list of 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    timing_system_finish_images(image_numbers)
    diagnostics_finish_images(image_numbers)
    xray_detector_finish_images(image_numbers)
    temperature_controller_finish_images(image_numbers)
    logfile_finish_images(image_numbers)
    save_dataset_settings()

def timing_system_finish_images(image_numbers):
    """Stop trigger pulse generation"""
    if "linear stage" in translate.mode:
        Ensemble_SAXS.acquisition_cancel()
    else: timing_sequencer.acquisition_cancel()

def xray_detector_finish_images(image_numbers):
    if options.xray_detector_enabled:
        if task.cancelled or not beam_ok(): ccd.cancel_acquisition()

def acquire_image(image_number):
    """Follow the data collection for one image"""
    debug("acquire image %r..." % image_number)
    task.image_number = image_number # for reporting progress

    start_image(image_number)
    wait_for_image(image_number)
    finish_image(image_number)
    
    debug("acquire image %r done" % image_number)

def start_image(image_number):
    """This is run before each image"""
    temperature_controller_start_image(image_number)
    diagnostics_start_image(image_number)
    
def finish_image(image_number):
    """This is run after each image"""
    diagnostics_finish_image(image_number)

def wait_for_image(image_number):
    """Follow the data collection for one image"""
    while not completed_image(image_number) and not task.cancelled and beam_ok():
        sleep(0.002)

def exec_delayed(time,command):
    """Execute a command on background after a certain delay
    time: seconds
    command: string, executable Python code"""
    from thread import start_new_thread
    start_new_thread(exec_delayed_background,(time,command))

def exec_delayed_background(time,command):
    """Execute a command after a certain delay
    time: seconds
    command: string, executable Python code"""
    sleep(time)
    exec(command)

def completed_image(image_number):
    return timing_system_completed_image(image_number)

def timing_system_completed_image(image_number):
    ##debug("completed image %d? current image number %r" %
    ##    (image_number,timing_system.image_number.count))
    if timing_system.image_number.count > image_number: completed = True
    elif not timing_sequencer.queue_active: completed = True
    else: completed = False
    ##debug("completed image %d? %r" % (image_number,completed))
    return completed

def wait_for_beam():
    """In case the storage ring is down suspend the data collection.s"""
    while not beam_ok() and not task.cancelled: sleep(1)

# Temperature controller

def temperature(image_number):
    """Which temperature to set while acquiring this image?"""
    return collection_variable_value("temperature",image_number)

def dT(image_number):
    """How much does temperature change while acquiring this image?
    iamge_number: 1-based index"""
    i = image_number
    if i <= nimages()-1: dT = temperature(i+1)-temperature(i)
    elif i >= 2: dT = temperature(i)-temperature(i-1)
    else: dT = 0
    return dT

def dTs(image_numbers): return [dT(i) for i in image_numbers]

def temp_inc(image_number):
    """How many temperature increments while acquiring this image?"""
    i = image_number
    dT = temperature(i+1)-temperature(i)
    temp_inc = int(rint(abs(dT)/temp.step))
    return temp_inc

def temp_incs(image_numbers):
    """How many temperature increments while acquiring these images?"""
    if temp.hardware_triggered:
        from numpy import concatenate
        T = array([temperature(i) for i in image_numbers])
        dT = T[1:]-T[0:-1]
        dT = concatenate((dT,dT[-1:] if len(dT)>0 else [0]))
        ##assert all(dT == dTs(image_numbers))
        temp_inc = dT/temp.step
        # Make sure rounding error does not accumulate
        for i in range(0,len(temp_inc)-1):
            d = rint(temp_inc[i])-temp_inc[i]
            temp_inc[i] -= d
            temp_inc[i+1] += d
        temp_inc = abs(rint(temp_inc).astype(int))
        temp_inc = list(temp_inc)
    else: temp_inc = [nan]*len(image_numbers)
    return temp_inc

def temp_step(image_number):
    """How much to increment the temperature at each trigger?"""
    i = image_number
    T = temperature
    N = nimages()
    # Find the nexdt image where the temperature is changing.
    while i < N-1 and T(i+1) == T(i): i += 1
    if i > N-1 and i > 1: i -= 1
    dT = T(i+1)-T(i)
    step = (1 if dT >= 0 else -1)*temp.step
    return step

def temp_steps(image_numbers): return [temp_step(i) for i in image_numbers]
 
def temperature_controller_start_images(image_numbers):
    """Configure temperature controller
    image_numbers: list of 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    if collection_variable_enabled('temperature') \
        and variable_hardware_triggered('temperature') \
        and len(image_numbers) > 0:
        image_number = image_numbers[0]
        T = temperature(image_number)
        Tstep = temp_step(image_number)
        Tstop = 120 if temp_step(image_number) > 0 else -30
        temperature_controller.command_value = T
        temperature_controller.trigger_start = T
        temperature_controller.trigger_stepsize = Tstep
        temperature_controller.trigger_stop = Tstop
        temperature_controller.trigger_enabled = True

def temperature_controller_start_image(image_number):
    """Configure temperature controller
    image_number: 1-based integer"""
    if collection_variable_enabled('temperature') \
        and variable_hardware_triggered('temperature'):
        if dT(image_number) == 0:
            T = temperature(image_number)
            Tstep = temp_step(image_number)
            Tstop = 120 if temp_step(image_number) > 0 else -30
            if temperature_controller.command_value != T:
                temperature_controller.command_value = T
            if temperature_controller.trigger_start != T:
                temperature_controller.trigger_start = T
            if temperature_controller.trigger_stepsize != Tstep:
                temperature_controller.trigger_stepsize = Tstep
            if temperature_controller.trigger_stop != Tstop:
                temperature_controller.trigger_stop = Tstop

def temperature_controller_finish_images(image_numbers):
    """Configure temperature controller
    image_numbers: list of 1-based integers
    e.g. image_numbers = collection_pass(1)"""
    if collection_variable_enabled('temperature') \
        and variable_hardware_triggered('temperature'):
        temperature_controller.trigger_enabled = False


# Sample Translation

def prepare_sample_translation(passno=0,wait=True):
    """This is to bring the sample in the right starting position for continuous
    translation.
    The passno parameter refers to the pass number, because the each pass can have a different
    travel range (alternating direction, or incomplete pass at the end)"""
    # Go to the start of translation range.
    if "continuous" in translate.mode:
        (DiffX.speed,DiffY.speed,DiffZ.speed) = sample_translation_speed()
        (DiffX.value,DiffY.value,DiffZ.value) = sample_translation_start(passno)
        if wait: # Wait until the sample to stops moving
            while (DiffX.moving or DiffY.moving or DiffZ.moving) and not task.cancelled:
                sleep (0.025)

def initiate_sample_translation(passno=0):
    """Starts translating the sample
    The passno parameter refers to the pass number, because the each pass can have a different
    travel range (alternating direction, or incomplete pass at the end)
    passno is 0-based"""
    if "continuous" in translate.mode:
        (DiffX.speed,DiffY.speed,DiffZ.speed) = sample_translation_speed()
        (DiffX.value,DiffY.value,DiffZ.value) = sample_translation_end(passno)

def bursts_per_image(image_number):
    """How many groups of X-ray pulses are used to acquire one image?"""
    # Methods-based data collection
    bursts = toint(SAXS_WAXS_methods.passes_per_image.value)
    return bursts
 
def burst_length(image_number):
    """How many X-ray pulses are group together in a burst?"""
    # Methods-based data collection
    mode = SAXS_WAXS_methods.Ensemble_mode.value
    burst_length = Ensemble_SAXS.burst_length_of_mode(mode)
    return burst_length

def npasses(image_number):
    """If sample translation is enabled, several passes may be needed to
    acquire a n image.
    Depending of the speed of translation and the number of pulses, the
    sample translation needs to be broken up into a number of separate
    strokes.
    image_number: 1-based index"""
    # Methods-based data collection
    return toint(SAXS_WAXS_methods.passes_per_image.value)
    
def npulses_of_pass(image_number,passno):
    """Return the number of X-ray pulses in nth passno
    image_number: 1-based index
    passno: 0-based index"""
    # Methods-based data collection
    mode = SAXS_WAXS_methods.Ensemble_mode.value
    burst_length = Ensemble_SAXS.burst_length_of_mode(mode)
    return burst_length

def sample_translation_starting_point():
    """The starting position for DiffX,DiffY,DiffZ.
    Return value: (x,y,z)"""
    z = min(sample.zs)
    if align.enabled: x,y = 0,align_offset(Phi.value,z)
    else: x,y = nan,nan # nan = Do not move. Keep current position.
    return (x,y,z)

def sample_translation_ending_point():
    """The starting position for DiffX,DiffY,DiffZ.
    Return value: (x,y,z)"""
    z = max(sample.zs)
    if align.enabled: x,y = 0,align_offset(Phi.value,z)
    else: x,y = nan,nan # nan = Do not move. Keep current position.
    return (x,y,z)

def sample_translation_start(passno):
    """The starting position for DiffX,DiffY,DiffZ for the nth passno.
    passno is 0-based.
    Return value: (x,y,z)"""
    if passno % 2 == 0: return sample_translation_starting_point()
    else: return sample_translation_ending_point()
    
def sample_translation_end(passno):
    """return the ending position for DiffX,DiffY,DiffZ for the nth passno
    passno is 0-based"""
    x,y,z = zip(sample_translation_starting_point(),sample_translation_ending_point())
    dt = abs(z[1] - z[0])/DiffZ.speed
    pps = int(dt/timing_system.waitt.value) # pulses_per_stroke
    fraction = float(npulses_of_pass(task.image_number,passno))/pps
    fraction = min(max(0.0,fraction),1.0)
    i = passno % 2 ; j = 1-i
    x = x[i]*(1-fraction) + x[j]*fraction
    y = y[i]*(1-fraction) + y[j]*fraction
    z = z[i]*(1-fraction) + z[j]*fraction
    return (x,y,z)

def sample_translation_speed():
    """This is to continuously translate the sample during the acqusition of
    an image.
    Returns the required translation speeds for DiffX,DiffY,DiffZ in mm/s"""
    if "continuous" in translate.mode: return (DiffX.speed,DiffY.speed,DiffZ.speed)
    x,y,z = zip(sample_translation_starting_point(),sample_translation_ending_point())
    dx = abs(x[1] - x[0])
    dy = abs(y[1] - y[0])
    dz = abs(z[1] - z[0])
    vx = DiffX.speed
    vy = DiffY.speed
    vz = DiffZ.speed
    dt = dz/DiffZ.speed
    if dt>0 and dx>0: vx = dx/dt
    if dt>0 and dy>0: vy = dy/dt
    return (vx,vy,vz)

def normal_speed():
    """Returns the standard translation speeds for DiffX,DiffY,DiffZ in mm/s"""
    # Set speed to always go at a slow rate. RH
    return (0.2,0.2,DiffZ.speed)
    #return (0.00313991, 0.00128627,DiffZ.speed)

def sample_translation_summary():
    """short description for log file"""
    s = ""
    if "during image" in translate.mode:
        dz = max(sample.zs)-min(sample.zs)
        s += "during image step: %.3f mm, " % sample.z_step
        s += "%s spots, " % translation_during_image_unique_nspots()
        if translate.interleave_factor > 1:
            s += "in %d interleaved passes, " % translate.interleave_factor
        if translate.single: s += "single shot per pass, "
        s += "Z speed %.3f mm/s, " % DiffZ.speed
    if "after image" in translate.mode:
        s += "after image step: %.5f mm, " % translation_after_image_zstep()
        s += "every %d images, " % translate.after_images
        s += "return every %d series, " % translate.return_after_series
        if translate.after_image_interleave_factor > 1:
            s += "in %d interleaved passes, " % \
                 translate.after_image_interleave_factor
    if "continous" in translate.mode:
        dz = max(sample.zs)-min(sample.zs)
        s += "continous: DZ=%.3f mm, " % dz
        s += ", Z speed %.3f mm/s" % DiffZ.speed
    if "linear stage" in translate.mode:
        s += "linear stage"
    s = s.rstrip(", ")
    if s == "": s = "off"
    return s

def logfile_start_images(image_numbers):
    logfile_update() # Generate header if needed
    # In case the image is recollected, make sure to leave no duplicate
    # entries in the logfile.
    logfile_delete_image_numbers(image_numbers)
    current_image_number_start_updating()
    logfile_start_updating(image_numbers)

def logfile_finish_images(image_numbers):
    logfile_finish_updating()
    ##exec_delayed(1,'logfile_finish_updating()')

logfile_keep_updating = False

def logfile_start_updating(image_numbers):
    """Begin collecting per-image statistics for diagnostics PVs."""
    global logfile_keep_updating
    logfile_keep_updating = True
    from thread import start_new_thread
    start_new_thread(logfile_update_task,(image_numbers,))

def logfile_finish_updating():
    """End collecting per-image statistics for diagnostics PVs."""
    global logfile_keep_updating
    logfile_keep_updating = False

def logfile_update_task(image_numbers):
    """Keep updating the logfile as new images are acquired"""
    debug("lauecollect: logging started")
    from time import time
    if logfile_keep_updating: last_active = time()
    ending = False
    while logfile_keep_updating or time()-last_active < 2.0:
        Nfinished = 0
        for i in image_numbers:
            if not image_logged(i) and image_finished(i):
                image_info[i]["logged"] = time()
                logfile_update(i)
        if all([image_logged(i) for i in image_numbers]):
            debug("lauecollect: logging completed")
            break
        if logfile_keep_updating and not ending: last_active = time()
        elif not ending: ending = True; debug("lauecollect: logging ending")
    debug("lauecollect: logging stopped")

def initialize_logfile():
    """Create a log file with an inforational header and column labels"""
    if not exists(logfile()):
        debug("logfile header...")
        if not exists(dirname(logfile())): makedirs(dirname(logfile()))
        log = file(logfile(),"a")
        for line in logfile_info().split("\n"): log.write("# "+line+"\n")
        # Generate column headers.
        if "phi" in Spindle.name.lower(): angle = "angle"
        else: angle = Spindle.name.replace(" ","")
        header = "#date time\tfile\tdelay"+\
            "\twaiting-time[s]\tbunches-per-pulse\tnom.pulses"+\
            "\tnom.delay[s]\tact.delay[s]\tsdev(act.delay)[s]\tnum(act.delay)"+\
            "\tx-ray[Vs]\tsdev(x-ray[Vs])\tnum(x-ray)"+\
            "\txray-gate-start[s]\txray-gate-stop[s]\tx-ray-offset[V]"+\
            "\tlaser\tsdev(laser)\tnum(laser)"
        for name in collection_variables():
            header += "\t"+name
            unit = variable_unit(name)
            if unit: header += "["+unit+"]"
        for i in range(0,diagnostics_PVs()):
            header += "\t"+diagnostics_PV_comment(i)
            header += "\tsdev("+diagnostics_PV_comment(i)+")"
            header += "\tnum("+diagnostics_PV_comment(i)+")"
        header += "\t"+"comment"
        log.write(header+"\n")
        debug("logfile header done")

logfile_lock = allocate_lock()

def logfile_update(image_number=None):
    """Add image information to the end of the data collection log file"""
    with logfile_lock:
        if not exists(logfile()): initialize_logfile()

    if image_number is not None: 
        timestamp = image_timestamp(image_number)
        image_filename = basename(filename(image_number))

        import datetime
        date_time = datetime.datetime.fromtimestamp(timestamp).strftime("%d-%b-%y %H:%M:%S.%f")[:-3]
        if laser_on(image_number): delay_string = time_string(timepoint(image_number))
        else: delay_string = "-"

        waitting_time = tostr(wait_time(image_number))
        bunches_per_pulse = tostr(chopper_pulses())
        nom_pulses = tostr(npulses(image_number))

        if laser_on(image_number): nom_delay = tostr(delay(image_number))
        else: nom_delay = "nan"

        if diagnostics.enabled and diagnostics.delay:
            act_delay = tostr(timing_diagnostics_delay(image_number))
            sdev_delay = tostr(timing_diagnostics_sdev_delay(image_number))
            num_delay = tostr(timing_diagnostics_num_delay(image_number))
        else: act_delay = sdev_delay = "nan"; num_delay = "0"
        if diagnostics.enabled and diagnostics.xray:
            xray = tostr(xray_pulse.average)
            sdev_xray = tostr(xray_pulse.stdev)
            num_xray = tostr(xray_pulse.count)
            xray_gate_start = tostr(diagnostics.xray_gate_start)
            xray_gate_stop = tostr(diagnostics.xray_gate_stop)
            xray_offset = tostr(diagnostics.xray_offset_level)
        else:
            xray = sdev_xray = "nan"; num_xray = "0"
            xray_gate_start = xray_gate_stop = xray_offset = "nan"
        if diagnostics.enabled and diagnostics.laser:
            ref = diagnostics.laser_reference
            offset = diagnostics.laser_offset
            laser = tostr((laser_pulse.average - offset) / (ref - offset))
            sdev_laser = tostr(laser_pulse.stdev / (ref - offset))
            num_laser = tostr(laser_pulse.count)
        else: laser = sdev_laser = "nan"; num_laser = "0"

        record = date_time+"\t"+image_filename+"\t"+delay_string+\
            "\t"+waitting_time+"\t"+bunches_per_pulse+"\t"+nom_pulses+\
            "\t"+nom_delay+\
            "\t"+act_delay+"\t"+sdev_delay+"\t"+num_delay+\
            "\t"+xray+"\t"+sdev_xray+"\t"+num_xray+\
            "\t"+xray_gate_start+"\t"+xray_gate_stop+"\t"+xray_offset+\
            "\t"+laser+"\t"+sdev_laser+"\t"+num_laser

        for name in collection_variables():
            record += "\t"+tostr(collection_variable_value(name,image_number))

        for i in range(0,diagnostics_PVs()):
            record += "\t"+tostr(diagnostics_PV_image_avg(i,image_number))
            record += "\t"+tostr(diagnostics_PV_image_sdev(i,image_number))
            record += "\t"+tostr(diagnostics_PV_image_count(i,image_number))

        global logfile_comment
        record += "\t"+logfile_comment
        logfile_comment = ""

        with logfile_lock:    
            # In case the image is recollected, make sure to leave no duplicate
            # entries in the logfile.
            ##logfile_delete_filename(image_filename) # time consuming
            file(logfile(),"a").write(record+"\n")

def log_comment(comment):
    """This will be logged as comment to the next image when the image is saved."""
    global logfile_comment
    if logfile_comment: logfile_comment += "; "
    logfile_comment += comment

logfile_comment = ""

def logfile_has_entries(image_filenames):
    """Is there an entry for this image in the log file?
    image_filenames: filenames of images (with or without directory)
    """
    from os.path import basename
    entries = logfile_entries()
    return array([basename(f) in entries for f in image_filenames])

def logfile_has_entry(image_filename):
    """Is there an entry for this image in the log file?
    image_filename: filename of image (with or without directory)
    """
    return logfile_has_entries([image_filename])[0]

def logfile_entries():
    """Is there an entry for this image in the log file?
    image_filename: basename of image filename (without directory)
    """
    try: log = file(logfile())
    except: return []
    lines = log.read().split("\n")
    # 'split' makes the last line an empty line.
    if lines and lines[-1] == "": lines.pop(-1)
    filenames = []
    for line in lines:
        if line.startswith("#"): continue # Ignore comment lines.
        fields = line.split("\t")
        if len(fields)>1: filenames += [fields[1]]
    return filenames

def logfile_delete_image_numbers(image_numbers):
    """Make sure that there are no duplicate entries in the
    data collection logfile, in the case an image is recollected.
    image_filename: basename of image filename (without directory)
    """
    image_filenames = [basename(filename(i)) for i in image_numbers]
    logfile_delete_filenames(image_filenames)

def logfile_delete_filenames(image_filenames):
    """Make sure that there are no duplicate entries in the
    data collection logfile, in the case an image is recollected.
    image_filename: basename of image filename (without directory)
    """
    try: log = file(logfile())
    except: return
    lines = log.read().split("\n")
    # 'split' makes the last line an empty line.
    if lines and lines[-1] == "": lines.pop(-1)
    output_lines = list(lines)
    # Remove matching lines.
    for line in lines:
        if line.startswith("#"): continue # Ignore comment lines.
        fields = line.split("\t")
        if len(fields)>1 and fields[1] in image_filenames:
            output_lines.remove(line)
    # Update the log file if needed.
    if output_lines != lines:
        log = file(logfile(),"w")
        for line in output_lines: log.write(line+"\n")

def logfile_delete_filename(image_filename):
    """Make sure that there are not duplicate entries in the
    data collection logfile, in the case an image is recollected.
    image_filename: basename of image filename (without directory)
    """
    logfile_delete_filenames([image_filename])

current_logfile = string_table()

def logfile_set_values(column_names,image_numbers,values_list):
    """Modify multiple columns
    column_names: list of strings
    image_numberes: list of 1-based integers        
    values_list: list of lists of strings"""
    current_logfile.reread(logfile())
    if current_logfile.comments == "": current_logfile.comments = logfile_info()
    current_logfile.set_values(column_names,array(image_numbers)-1,values_list)
    current_logfile.save()


def logfile_info():
    """Comment lines for headre of logfile as
    Multiline string"""
    comments = ""
    comments += ("Data collection log file generated by Lauecollect "+
        __version__+"\n")
    comments += ("Description: "+param.description+"\n")
    try:
        comments += ("source: U23 at %.2f mm, U27 at %.2f mm\n" %
            (U23.value,U27.value))
    except: pass
    w = Slit1H.value
    h = Slit1V.value
    comments += ("white beam slits (at 28 m): %.3f mmh x %.3f mmv\n" % (w,h))
    m1 = mir1Th.value
    m2 = mir2Th.value
    comments += ("mirrors incidence angles: %.3f mrad, %.3f mrad\n" %(m1,m2))
    comments += ("high-speed chopper phase: %s\n" % time_string(timing_system.hsc.delay.value))
    comments += ("sample slits: %.3f mmh x %.3f mmv" %
        (shg.value,svg.value))
    if sho.value != 0: comments += (", offset %+.3f mmh" % sho.value)
    if svo.value != 0: comments += (", offset %+.3f mmv" % svo.value)
    comments += ("\n")
    comments += ("detector distance: %.1f mm\n" % DetZ.value)
    comments += ("pulses per image (on,off): %d,%d\n" % (options.npulses,options.npulses_off))
    s = "%.3f" % options.min_waitts[0]
    for t in options.min_waitts[1:]: s += ",%.3f" % t
    s += "/%.3f" % options.min_waitt_off
    comments += ("min. time between pulses (on/off): %s\n" % s)
    comments += ("max. time between pulses (off): %.3f s\n" %
        options.max_waitt_off)
    if align.enabled:
        comments += ("auto align: probe depth %.3f mm\n" % align.beamsize)
    else: comments += ("auto align: off\n")
    comments += ("sample translation: "+sample_translation_summary()+"\n")
    comments += ("syringe pump: "+pump_summary()+"\n")
    if collection_variable_enabled("chopper_mode"):
        comments += ("chopper: variable")
        for i in range (0,len(chopper.y)):
            comments += (", Y=%g mm: %g pulses, %s, min delay %s" %
                (chopper.y[i],chopper.pulses[i],time_string(chopper.time[i]),
                time_string(chopper.min_dt[i])))
        comments += ("\n")
    else: comments += ("chopper: fixed, Y=%g mm\n" % ChopY.value)
    comments += ("diagnostics: %s\n" % diagnostics_summary())
    comments += ("process variables: %s\n" % diagnostics_PV_summary())
    comments += ("beam check: %s\n" % xray_beam_check_summary())
    return comments
    
def tostr(x):
    """Converts a number to a string.
    This is needed to handle "not a number" and infinity properly.
    Under Windows, 'str()','repr()' and '%' format 'nan' as '-1.#IND' and 'inf'
    as '1.#INF', which is inconsistent with Linux ('inf' and 'nan').
    """
    if isinstance(x,basestring): return x
    try:
        if isnan(x): return "nan"
        if isinf(x) and x>0: return "inf"
        if isinf(x) and x<0: return "-inf"
        return "%g" % x
    except: return str(x)

def str_to_float_list(s):
    """Convert comma-separated text to Python list of floating point numbers."""
    from numpy import arange
    try: l = eval(s)
    except: l = 0
    if not hasattr(l,"__len__"): l = [l]
    if type(l) != list: l = list(l)
    for i in range(0,len(l)):
        try: l[i] = float(l[i])
        except: l[i] = 0.0
    return l

def filename(image_number):
    """Absolute pathname of the nth image of the current dataset.
    Image numbers start with 1."""
    # For speedup, cache the filename for 10 s.
    global filename_cache
    if not "filename_cache" in globals(): filename_cache = {}
    if image_number in filename_cache:
        f,timestamp = filename_cache[image_number]
        if time()-timestamp < 10: return f
    f = __filename__(image_number)
    filename_cache[image_number] = (f,time())
    return f
    
def __filename__(image_number):
    """Absolute pathname of the nth image of the current dataset.
    Image numbers start with 1."""
    ##if image_number > nimages(): return ""
    if image_number == 0: return single_image_filename()

    filename = param.path+"/xray_images/"+param.file_basename
    
    for name in collection_variables()[::-1]:
        if variable_include_in_filename(name):
            value = collection_variable_value(name,image_number)
            text = variable_formatted_value(name,value)
            if text: filename += "_"+text
            count = collection_variable_repeat_count(name,image_number)
            if count>1: filename += "-"+str(count)
            
    ext = param.extension.strip(".")
    filename += "."+ext
    return filename

def image_filenames(image_numbers):
    """List of image file names with directory
    image_numbers: list or array of 1-based indices
    """
    return [filename(i) for i in image_numbers]

def all_image_filenames():
    """List of all image file names of the current data set with directory
    """
    return image_filenames(range(1,nimages()+1))

def waveform_filenames(image_numbers,name="xray"):
    """Where to store the X-ray diagnostics oscilloscope data
    image_numbers: list of 1-based indices"""
    filenames = []
    img_filenames = image_filenames(image_numbers)
    # Assuming bursts_per_image is the same for all images...
    Nfiles = bursts_per_image(image_numbers[0]) if len(image_numbers) > 0 else 0
    if Nfiles <= 1:
        for f in img_filenames:
            filename = f.replace("."+param.extension,"_"+name+".trc")
            filename = filename.replace("/xray_images/","/"+name+"_traces/")
            filenames.append(filename)
    else:
        for f in img_filenames:
            for j in range(0,Nfiles):
                filename = f.replace("."+param.extension,"_%02d_" % (j+1) + name+".trc")
                filename = filename.replace("/xray_images/","/"+name+"_traces/")
                filenames.append(filename)
    return filenames

def basenames(nmax=1000):
    """List the filenames of the dataset"""
    nmax = min(nmax,nimages())
    return "\n".join("%4d %s"%(i,basename(filename(i))) for i in range(1,nmax+1))

def extension():
    """Ending of filename, including dot(.)"""
    return "."+param.extension.strip(".")

def single_image_filename():
    """Used by "single image"
    Return value: absolute pathname"""
    ext = param.extension.strip(".")
    i = 0
    filename = "%s/xray_images/%s_%03d.%s" % \
        (param.path,param.file_basename,i+1,ext)
    while exists(filename):
        i += 1
        filename = "%s/xray_images/%s_%03d.%s" % \
            (param.path,param.file_basename,i+1,ext)
    return filename

def logfile():
    return param.path+"/"+param.logfile_filename
    
def first_image_number():
    """The number of the first image that has not been collected already.
    If all image are collected, return Nimages+1.
    return value: 1-based index"""
    filenames = all_image_filenames()
    exist = exist_files(filenames) & logfile_has_entries(filenames)
    if not all(exist): first_image_number = where(~exist)[0][0]+1
    else: first_image_number = nimages()+1
    return first_image_number

# Because of NFS attribute caching 'exists' sometimes reports files created
# by the MAR CCD server non-existing. Lising the directory contents re-
# freshes the NFS cache.

def exists2(filename):
    """Tell whether, on the local fie system, there exists a file or directory
    with a given name."""
    import os.path
    if os.path.exists(filename): return True
    try: listdir(dirname(filename)) # trigger update of NFS attribute cache
    except: pass
    return os.path.exists(filename)

# Replacement for Python's built-in "mkdirs" from the os.path module

def makedirs(path):
    """Replacement for Python's built-in "mkdirs" from the os module
    This version of makedirs makes sure that all directories created are
    world-writable. This is necessary because the MAR CC Dserver writes
    from a different computer with a different user id (marccd=500) than
    then user caccount on the beamline control computer (useridb=615).
    """
    from os import makedirs
    if not exists(path): makedirs(path)
    try: chmod (path,0777)
    except OSError: pass

# Data collection strategy

def variables():
    """Data collection parameter names.
    List of strings."""
    return ["delay","angle","laser_on","repeat","repeat2","level","translation",
            "translation_mode","chopper_mode","temperature","xray_on"]

def collection_variable_order():
    """List of variable names, starting with the fastest variable to the slowest
    variable"""
    return options.collection_order

def collection_variable_set_order(order):
    # Perform sanity check
    for i in range(0,len(order)):
        for name in order[i]:
            if name not in variables(): order[i].remove(name)
    while [] in order: order.remove([])

    old_order = options.collection_order
    options.collection_order = order
    # Keep filename in sync
    old_names = flatten(old_order)
    new_names = flatten(order)
    added   = [name for name in new_names if not name in old_names] 
    removed = [name for name in old_names if not name in new_names]
    for name in removed:
        if name in options.variable_include_in_filename:
            options.variable_include_in_filename.remove(name)
    for name in added:
        if name not in options.variable_include_in_filename:
            options.variable_include_in_filename.append(name)        
    
def collection_variables():
    """Which variabled change during the data collection?
    Return value: list of strings
    Order: Fast, medium, slow"""
    variable_names = flatten(collection_variable_order())
    ##variable_names =  [name for name in variable_names if variable_nchoices(name) > 1]
    return variable_names

def collection_variable_enabled(name):
    """Is this variable used during data collection?"""
    return name in collection_variables()

def collection_variable_set_enabled(name,value):
    """Turn off on on the usage of this variable used during data collection.
    value: False or True"""
    if value: collection_variable_enable(name)
    else: collection_variable_disable(name)

def collection_variable_enable(name):
    """Use this variable during data collection.
    By default, this will be the slowest changing variable."""
    if name in variables():
        if not collection_variable_enabled(name):
            order = collection_variable_order()+[[name]]
            collection_variable_set_order(order)

def collection_variable_disable(name):
    """Do not use this variable during data collection."""
    groups = collection_variable_order()
    for i in range(0,len(groups)):
        if name in groups[i]: groups[i].remove(name)
    while [] in groups: groups.remove([])
    collection_variable_set_order(groups)

def flatten(l):
    """Make a simple list out of list of lists"""
    try: return [item for sublist in l for item in sublist]
    except: return l

def variable_nchoices(name):
    """Number of choices for a data collection parameter
    name: data collection parameter:
    "delay","angle","laser_on","repeat","level","translation"
    """
    if name == "angle": nchoices = nangles()
    elif name == "delay": nchoices = len(variable_choices(name))
    elif name == "laser_on": nchoices = len(variable_choices(name))
    elif name == "repeat": nchoices = options.npasses
    elif name == "repeat2": nchoices = options.npasses2
    elif name == "level": nchoices = len(variable_choices(name))
    elif name == "translation": nchoices = translation_after_image_nspots()
    elif name == "translation_mode": nchoices = ntimepoints()
    elif name == "chopper_mode":
        nchoices = ntimepoints() if len(chopper.modes) == 0 else len(chopper.modes)
    elif name == "temperature": nchoices = len(variable_choices(name))
    elif name == "xray_on": nchoices = len(options.xray_on)
    else: len(variable_choices(name))
    nchoices = max(nchoices,1)
    return nchoices

def variable_choice(name,i):
    """ith of the possible n values for a data collection parameter
    name: data collection parameter:
    "delay","angle","laser_on","repeat","level","translation"
    i: 0-based integer
    Return value: real number
    """
    if name == "angle": choice = angle_of_orientation(i)
    elif name == "delay": choice = variable_choices(name)[i]
    elif name == "laser_on": choice = variable_choices(name)[i]
    elif name == "repeat": choice = i
    elif name == "repeat2": choice = i
    elif name == "level": choice = variable_choices(name)[i]
    elif name == "translation":
        nspots = translation_after_image_nspots()
        m = translate.after_image_interleave_factor
        i = interleaved_order(i,m,nspots)
        z = min(sample.zs) + i*translation_after_image_zstep()
        choice = z
    elif name == "translation_mode":
        # Avoid mode changes for reference images.
        while i<ntimepoints()-1 and timepoints()[i] == param.ref_timepoint: i+=1
        choice = Ensemble_SAXS.mode_of_delay(timepoints()[i])
    elif name == "chopper_mode":
        if len(chopper.modes) == 0:
            choice = chopper_mode_of_timepoint_number(i)
        else:
            if not i < len(chopper.modes): i = len(chopper.modes)-1
            return chopper.modes[i]
    elif name == "temperature": choice = variable_choices(name)[i]
    elif name == "xray_on":
        choice = options.xray_on[i] if i<len(options.xray_on) else True
    else: choice = variable_choices(name)[i]
    return choice

def variable_choices(name):
    """All possible values for a data collection parameter
    name: data collection parameter:
    "delay","angle","laser_on","repeat","level","translation"
    Return value: list of real number"""
    if name == "angle": choices = angle_choices()
    elif name == "delay":
        choices = options.variable_choices[name] if name in options.variable_choices else []
    elif name == "laser_on":
        choices = options.variable_choices[name] if name in options.variable_choices else []
    elif name == "repeat": choices = range(0,options.npasses)
    elif name == "repeat2": choices = range(0,options.npasses2)
    elif name == "level":
        choices = options.variable_choices[name] if name in options.variable_choices else []
    elif name == "temperature":
        choices = options.variable_choices[name] if name in options.variable_choices else []
    elif name == "translation_mode":
        choices = [Ensemble_SAXS.mode_of_delay(t) for t in timepoints()]
    elif name == "chopper_mode":
        if len(chopper.modes) == 0:
            choices = [chopper_mode_of_timepoint_number(i) \
                for i in range(0,ntimepoints())]
        else: choices = chopper.modes
    elif name == "xray_on": choices = options.xray_on
    else:
        choices = options.variable_choices[name] if name in options.variable_choices else []
    if len(choices) == 0: choices = [variable_value(name)]
    return choices

def variable_set_choices(name,values):
    """Set all possible values for a data collection parameter
    values: list of values"""
    options.variable_choices[name] = values

def variable_choice_repeat_count(name):
    """If there are duplicate values in the choices,
    a unique integer count for each"""
    # For speedup, cache the filename for 10 s.
    global cache
    if not "cache" in globals(): cache = {}
    if ("variable_choice_repeat_count",name) in cache:
        x,timestamp = cache["variable_choice_repeat_count",name]
        if time()-timestamp < 10: return x
    x = __variable_choice_repeat_count__(name)
    cache["variable_choice_repeat_count",name] = (x,time())
    return x
 
def __variable_choice_repeat_count__(name):
    """If there are duplicate values in the choices,
    a unique integer count for each"""
    values = variable_choices(name)
    return [values[0:i+1].count(values[i]) for i in range(0,len(values))]

def variable_value(name):
    """Data collection parameter as currently read 
    name: data collection parameter:
    "delay","angle","laser_on","repeat","level","translation"
    """
    if name == "angle": return Spindle.command_value
    if name == "delay":
        if "linear stage" in translate.mode: return Ensemble_SAXS.delay
        else: return timing_sequencer.delay
    if name == "laser_on":
        if "linear stage" in translate.mode: return Ensemble_SAXS.laser_on
        else: return timing_sequencer.laser_on
    if name == "repeat": return 1
    if name == "repeat2": return 1
    if name == "level": return trans.value
    if name == "translation": return diffractometer.zc
    if name == "translation_mode": return Ensemble_SAXS.mode
    if name == "chopper_mode": return chopper_mode_current()
    if name == "temperature":
        try: return temperature_controller.value
        except AttributeError: return nan
    if name == "xray_on":
        if "linear stage" in translate.mode: return Ensemble_SAXS.ms_on
        else: return timing_sequencer.ms_on
    return nan

def variable_set_value(name,value):
    """Change the data collection parameter (in hardware)
    name: data collection parameter:
    "delay","angle","laser_on","repeat","level","translation"
    value: real number"""
    if name == "angle": Spindle.command_value = value
    if name == "delay":
        if "linear stage" in translate.mode: Ensemble_SAXS.delay = value
        else: timing_sequencer.delay = value
    if name == "laser_on":
        if "linear stage" in translate.mode: Ensemble_SAXS.laser_on = value
        else: timing_sequencer.laser_on = value
    if name == "repeat": pass
    if name == "repeat2": pass
    if name == "level": trans.value = value
    if name == "translation": diffractometer.z = value
    if name == "translation_mode":
        if value != Ensemble_SAXS.mode: Ensemble_SAXS.mode = value
    if name == "chopper_mode":
        if value != chopper_mode_current(): set_chopper_mode(value,wait=False)
    if name == "temperature":
        # Only update set point if needed.
        if value != temperature_controller.command_value:
            progress("temperature: set point %.3fC -> %.3fC"
                % (temperature_controller.command_value,value))
            temperature_controller.command_value = value
            global temperature_controller_last_update
            temperature_controller_last_update = time()
    if name == "xray_on":
        if "linear stage" in translate.mode: Ensemble_SAXS.ms_on = value
        else: timing_sequencer.ms_on = value

temperature_controller_last_update = 0
temperature_controller_last_instable = 0

def variable_changing(name):
    """Is a motors currenly moving?
    name: data collection parameter:
    "delay","angle","laser_on","repeat","level","translation"
    value: real number
    """
    if name == "angle": return diffractometer.Phi.moving
    if name == "delay": return False
    if name == "laser_on": return False
    if name == "repeat": return False
    if name == "repeat2": return False
    if name == "level": return trans.moving
    if name == "translation": return diffractometer.Z.moving
    if name == "translation_mode": return False
    if name == "chopper_mode": return chopper.wait and chopper_moving()
    if name == "temperature":
        # Work-around for slow "stable" PV update issue.
        if time() - temperature_controller_last_update < 2.0: return True
        instable = temperature_controller.moving
        global temperature_controller_last_instable
        if instable: temperature_controller_last_instable = time()
        settling = time()-temperature_controller_last_instable < temp.settling_time
        return settling
    if name == "xray_on": return False
    return False

def variable_wait(name):
    """Suspend data collection when changing this variable?"""
    ##if variable_hardware_triggered(name): return False
    wait = options.variable_wait[name] if name in options.variable_wait else True
    return wait

def variable_set_wait(name,value):
    """Suspend data collection when changing this variable?
    value: True of False"""
    options.variable_wait[name] = bool(value)

def variable_hardware_triggered(name):
    """Can this variable be changed in hardware-triggred mode?"""
    if name == "angle": return False
    if name == "delay": return True
    if name == "laser_on": return True
    if name == "repeat": return True
    if name == "repeat2": return True
    if name == "level": return False
    if name == "translation": return translate.hardware_triggered
    if name == "translation_mode": return True
    if name == "chopper_mode": return not chopper.wait
    if name == "temperature": return temp.hardware_triggered
    if name == "xray_on": return True
    return False

def variable_formatted_value(name,value):
    """Data collection variable as formatted string"""
    if name == "angle": return "%.3f%s" % (value,Spindle.unit)
    if name == "delay": return time_string(value)
    if name == "laser_on": return "on" if value else "off"
    if name == "repeat": return "%d" % (value+1)
    if name == "repeat2": return "%d" % (value+1)
    if name == "translation": return "%.3fmm" % value
    if name == "translation_mode": return value
    if name == "chopper_mode": return "%gpulses" % chopper_pulses_of_mode(value)
    if name == "level": return "%.4f" % value
    if name == "temperature": return ("%.3f" % value).rstrip("0").rstrip(".")+"C"
    if name == "xray_on": return "xray" if value else "bkg"
    return str(value)

def variable_unit(name):
    """Unit symbol for a collection variable"""
    if name == "angle": return "deg"
    if name == "delay": return "s"
    if name == "laser_on": return ""
    if name == "repeat": return ""
    if name == "repeat2": return ""
    if name == "translation": return "mm"
    if name == "level": return ""
    if name == "temperature": return "C"
    if name == "xray_on": return ""
    return ""

def variable_include_in_filename(name):
    return name in options.variable_include_in_filename;
    
def set_collection_variables(image_number,wait=False):
    """Set all collection variables
    image_number: 1-based index
    wait=True: only return after motor move has completed"""
    names = collection_variables()
    names = [name for name in names
        if not (variable_hardware_triggered(name) and not variable_wait(name))]
    if not wait: names = [name for name in names if not variable_wait(name)]
    for name in names:
        variable_set_value(name,collection_variable_value(name,image_number))
    if wait:
        names = [name for name in names if variable_wait(name)]
        variables_wait(names)

def set_collection_variable(name,image_number,wait=False):
    """name: one of 'collection_variables()'
    image_number: 1-based index
    wait=True: only return after motor move has completed"""
    variable_set_value(name,collection_variable_value(name,image_number))
    if wait:
        while variable_changing(name) and not task.cancelled:
            value = variable_value(name)
            progress(name+": "+variable_formatted_value(name,value))
            sleep(0.1)
        
def variables_wait(names=None):
    """Wait for all motors to complete moving"""
    if names is None: names = collection_variables()
    changing = [variable_changing(name) for name  in names]
    while any(changing) and not task.cancelled:
        t = []
        for i in range(0,len(names)):
            if changing[i]:
                value = variable_value(names[i])
                t += [names[i]+": "+variable_formatted_value(names[i],value)]
        t = ",".join(t)
        progress(t)
        sleep(0.1)
        changing = [variable_changing(name) for name  in names]

def collection_variables_changing():
    """Is any motor currently moving"""
    for name in collection_variables():
        if variable_changing(name): return True
    return False

collection_starting_values = {}

def collection_variables_start_dataset():
    """Set all collection variables"""
    global collection_starting_values
    names = [n for n in collection_variables() if variable_return(n)]
    collection_starting_values = dict([(n,variable_value(n)) for n in names])
    ##motors = [variable_motor(n) for n in names]
    ##generate_autorecovery_restore_point("Data Collection",motor)
    image_number = first_image_number()
    for name in names: set_collection_variable(name,image_number,wait=False)
    variables_wait(names)

def variable_return(name):
    """Restore this motor to its oroingal position afte data collection
    finishes?"""
    if name in options.variable_return: value = options.variable_return[name]
    else: value = False
    return value

def variable_set_return(name,value):
    """Restore this motor to its oroingal position afte data collection
    finishes?
    value: True or False"""
    options.variable_return[name] = value
    
def collection_variables_finish_dataset():
    """Set all collection variables"""
    names = [name for name in collection_variables() if variable_return(name)]
    for name in names:
        value = collection_variable_return_value(name)
        if not isnan(value): variable_set_value(name,value)
    ##variables_wait(names)

def collection_variable_return_value(name):
    if name in options.variable_return_value:
        value = options.variable_return_value[name]
    elif name in collection_starting_values:
        value = collection_starting_values[name]
    else: value = variable_value(name)
    return value

def collection_variable_set_return_value(name,value):
    if not isnan(value): options.variable_return_value[name] = value
    else: del options.variable_return_value[name]

def collection_variable_return_to_starting_value(name):
    return name not in options.variable_return_value

def collection_variable_set_return_to_starting_value(name,value):
    if value:
        if name in options.variable_return_value:
            del options.variable_return_value[name]
    else: options.variable_return_value[name] = variable_value(name)

def nimages():
    """Total number of image in the data set"""
    counts = variable_counts()
    max_counts = [max(x) for x in counts]
    from numpy import product
    ntotal = product(max_counts)
    return ntotal

def nimages_to_collect():
    """At which number of images to end data collection if "Finish Time Series"
    is requested"""
    if not task.finish_series: return nimages()
    period = collection_variable_period(options.finish_series_variable)
    n = int(round_up(task.image_number,period))
    return n

def variable_values(image_number):
    """image_number: 1-based integer
    Return value: nested list of real numbers"""
    indices = variable_indices(image_number)
    values = []
    for name_list,index_list in zip(collection_variable_order(),indices):
        values += [[]]
        for name,index in zip(name_list,index_list):
            values[-1] += [variable_choice(name,index)]
    return values

def collection_variable_value(name,image_number):
    """What is the value of a data collection parameter for a given image.
    image_number: 1-based integer
    name: data collection parameter:
    "delay","angle","laser_on","repeat","level","translation"
    Return value: real numbers"""
    i = collection_variable_index(name,image_number)
    return variable_choice(name,i)

def collection_variable_repeat_count(name,image_number):
    """What is the value of a data collection parameter for a given image.
    image_number: 1-based integer
    name: data collection parameter:
    "delay","angle","laser_on","repeat","level","translation"
    Return value: real numbers"""
    if name == "repeat": return 1
    i = collection_variable_index(name,image_number)
    counts = variable_choice_repeat_count(name)
    count = counts[i] if i < len(counts) else 1
    return count

def collection_variable_values(name):
    """List of the values for a data collection parameter for
    the entrire dataset
    name: data collection parameter"""
    return [collection_variable_value(name,i) for i in range(1,nimages()+1)]

def variable_constant_range(name,starting_image_number):
    """Number of images that will be collected without changing the
    parameter given be 'name', starting from the image given by
    'starting_image_number'
    name: data collection parameter
    starting_image_number: 1-based integer"""
    value = collection_variable_value(name,starting_image_number)
    for i in range(starting_image_number,nimages()+1):
        if collection_variable_value(name,i) != value: return i-starting_image_number
    return nimages()+1 - starting_image_number

def collection_passes(starting_image_number=1,npasses=inf):
    """Break up the datea dataset into passes that can be collected using
    hardware trigger
    starting_image_number: 1-based index
    return value: list of lists of image numbers"""
    # Not hardware-triggerd collection parameters.
    wait_vars = [var for var in collection_variables()
        if variable_wait(var)]
    passes = []
    i = starting_image_number
    while i <= nimages_to_collect() and len(passes) < npasses:
        # Group the images into block that can be collected in one pass using
        # hardware trigger.
        if len(wait_vars) > 0:
            n = min([variable_constant_range(var,i) for var in wait_vars])
        else: n = nimages()-(i-1)
        # Create a break to perform an X-Ray beam check.
        n = min(n,xray_beam_check_after(i)-(i-1))
        image_numbers = array(range(i,i+n))
        ##filenames = [filename(j) for j in image_numbers]
        filenames = image_filenames(image_numbers)
        progress("looking for existing images files...")
        exist = exist_files(filenames) & logfile_has_entries(filenames)
        progress("looking for existing images files done.")
        image_numbers = image_numbers[~exist]
        if len(image_numbers) > 0: passes += [image_numbers]
        i += n
        if n == 0: break
    return passes

def collection_pass(starting_image_number):
    """The series of images that can be collected using hardware trigger,
    starting_image_number: 1-based index"""
    passes = collection_passes(starting_image_number,npasses=1)
    if len(passes) == 0: return []
    return passes[0]

def variable_counts():
    """The number of values for each variable.
    Return value: nested list if integers"""
    counts = []
    for name_list in collection_variable_order():
        counts += [[]]
        for name in name_list: counts[-1] += [variable_nchoices(name)]
    return counts

def variable_indices(image_number):
    """image_number: 1-based integer
    Return value: nested list of integers"""
    image_number -= 1# convert to 0-baed integer
    counts = []
    for name_list in collection_variable_order():
        counts += [[]]
        for name in name_list: counts[-1] += [variable_nchoices(name)]
    max_counts = [max(x) for x in counts]
    max_indices = []
    for n in max_counts:
        max_indices += [image_number % n]
        image_number /= n
    indices = []
    for max_index,count_list in zip(max_indices,counts):
        indices += [[]]
        for count in count_list: indices[-1] += [max_index % count]
    return indices

def collection_variable_period(name):
    """Every how many images t ohte values of this variable repeat?
    name: data collection parameter, e.g. "delay" """
    n = 1
    for name_list in collection_variable_order():
        n *= max([variable_nchoices(n) for n in name_list])
        if name in name_list: break
    return n

def collection_variable_index(name,image_number):
    """For a given image, the value of the data collection is the nth
    of the choices for the values of this parameter.
    image_number: 1-based integer
    name: data collection parameter:
    "delay","angle","laser_on","repeat","level","translation"
    Return value: 0-based integer"""
    indices = variable_indices(image_number)
    values = []
    for name_list,index_list in zip(collection_variable_order(),indices):
        values += [[]]
        for n,i in zip(name_list,index_list):
            if name == n: return i
    return 0

def linear_ranges(values):
    """Break of list of values into lists where the value changes linearly"""
    ranges = []
    def close(x,y): return abs(y-x) < 1e-6
    for i in range(0,len(values)):
        is_linear_before = i >= 2 and \
            close(values[i]-values[i-1],values[i-1]-values[i-2])
        is_linear_after = 1 <= i <= len(values)-2 and \
            close(values[i]-values[i-1],values[i+1]-values[i])
        if is_linear_before or \
            (len(ranges) > 0 and len(ranges[-1]) == 1 and is_linear_after):
            ranges[-1] += [values[i]]
        else: ranges += [[values[i]]]
    return ranges

def list_to_string(values):
    """Format a list of values, using shortcuts.
    [20,21,22,23,24,25] -> '20 to 25 in steps of 1'"""
    ranges = linear_ranges(values)
    parts = []
    for r in ranges:
        if len(r) == 1: part = "%g" % r[0]
        else:
            begin,end,step = r[0],r[-1],r[1]-r[0]
            if step != 0: part = "%g,%g..%g" % (begin,begin+step,end)
            else: part = "%g(x%d)" % (r[0],len(r))
        parts += [part]
    text = ",".join(parts)
    return text

def string_to_list(text):
    """Convert a string to a list of numbers, interpresting shortcuts
    '20 to 25 in steps of 1' -> [20,21,22,23,24,25]"""
    from parse import parse
    from numpy import arange,sign
    text = text.replace("\n","")
    parts = text.split(",")
    values = []
    for part in parts:
        part = part.replace(" ","")
        if ".." in part and "step" in part:
            if parse("{:g}..{:g}step{:g}",part):
                begin,end,step = parse("{:g}..{:g}step{:g}",part)
                dir = sign(end-begin)
                step = dir*abs(step)
                if step != 0: values += list(arange(begin,end+step/2,step))
                else: values += [begin]
        if ".." in part:
            if parse("{:g}..{:g}",part):
                begin,end = parse("{:g}..{:g}",part)
                if len(values) > 0: step = begin-values[-1]
                else: step = 1
                dir = sign(end-begin)
                step = dir*abs(step)
                if step != 0: values += list(arange(begin,end+step/2,step))
                else: values += [begin]
        elif "(x" in part:
            if parse("{:g}(x{:d})",part):
                value,n = parse("{:g}(x{:d})",part)
                values += [value]*n
        else:
            try: values += [float(eval(part))]
            except Exception,msg: warn("%r: %r" % (part,msg))
    return values

def nimages_per_timeseries():
    """Number of images before the timepoints repeat"""
    return nimages_per_timepoint()*ntimepoints()

def nimages_per_orientation():
    """Number of images before the sample is rotated"""
    # TO DO
    if nangles() == 1: return nimages() 
    return nimages_per_orientation_()

def nimages_per_orientation_():
    """Number of images before the sample is rotated"""
    # TO DO
    return nimages_per_timeseries()*nlevels_used()

def nimages_per_pass():
    """Number of images per if the number of passes (repeats) is set to 1"""
    return nimages_per_orientation_()*nangles()

def passno(image_number):
    """To which pass belongs the image number?
    image_number: 1-based index
    Return value: 1-based index"""
    n = nimages_per_pass()
    return (image_number-1)/n + 1

def angle(image_number):
   """Goniometer spindle setting; image_number is 1-based"""
   return collection_variable_value("angle",image_number)

def orientation_number(image_number):
    """Sequence number for spindle angles, same as series number.
    image_number: 1-based index
    Return value: 1-based index"""
    return collection_variable_index("angle",image_number)+1

def nangles():
    """Number of spindle orientation in the entire data set"""
    if param.amode == "User-defined list": return max(len(param.alist),1)
    if param.amax == param.amin: return 1
    if param.astep == 0: return 1 
    na = abs(param.amax-param.amin)/param.astep
    return int(round(na))+1

def angle_choices():
    """All goniometer angles to use during the data collection"""
    return [angle_of_orientation(i) for i in range(0,nangles())]

def angle_of_orientation(j):
    """Goniometer spindle setting; orientation_number j is 0-based"""
    # If no rotation range is 0, do not rotate at all.
    n = nangles()
    da = abs(param.astep)*sign(param.amax-param.amin)
    if param.amode == "Single pass":
        if param.amin == param.amax: return Spindle.value
        return param.amin + j*da
    elif param.amode == "Two interlaced passes":
        if param.amin == param.amax: return Spindle.value
        j = j*2
        if j>n: j=n-(j-n)
        return param.amin + j*da
    elif param.amode == "Filling gaps":
        if param.amin == param.amax: return Spindle.value
        # Use gap-filling scheme based on the 'golden ratio'.
        # At any given time duiring the data collection the ratio between the
        # largest and smallest gap is 1:0.6180.
        phi = (sqrt(5)-1)/2
        return param.amin + (j*phi % 1)*(param.amax-param.amin)
    elif param.amode == "User-defined list":
        if len(param.alist) == 0: return Spindle.value
        return param.alist[j % len(param.alist)]
    else: return Spindle.value

def timepoints():
    """List of time points"""
    if not laser_enabled(): return [nan]
    return variable_choices("delay")

def ntimepoints():
    """Number of time points"""
    if not laser_enabled(): return 1 
    return variable_nchoices("delay")

def next_delay(t):
    """Next possible pump-probe delay to the given value"""
    if "linear stage" in translate.mode: t = Ensemble_SAXS.next_delay(t)
    return t

def next_delays(t):
    """Next possible pump-probe delay to the given value
    t: list of time delays in seconds"""
    tn = [next_delay(ti) for ti in t]
    T = tn[0:1]
    for i in range(1,len(t)):
        if t[i] == t[i-1] or tn[i] != tn[i-1]: T += [tn[i]]
    return T

def nimages_per_timepoint():
    """Number of images acquired for each timpoint
    on = 1, off/on = 2, off/on/off = 3"""
    return variable_nchoices("laser_on")

def laser_on_nchoices():
    """How many laser modes (on/off) to use?"""
    return len(variable_choices("laser_on"))

def laser_on_choices():
    """List of booleans"""
    return variable_choices("laser_on")

def laser_mode_on(image_number):
    """Is the laser to be fired for this image?
    When using laser mode 'off/on', or 'off/on/off'
    image_number: 1-based index
    return value: true or false"""
    return collection_variable_value("laser_on",image_number)

def laser_on(image_number):
    """Is the laser to be fired for this image?
    image_number: is 1-based integer 
    Return value: True or False"""
    if not laser_mode_on(image_number): return False
    if isnan(timepoint(image_number)): return False
    if collection_variable_value("level",image_number) == 0: return False
    return True

def laser_enabled():
    """Use the laser during data acqisition?
    True or False"""
    if len(variable_choices("laser_on")) == 0: use = False
    elif len(variable_choices("laser_on")) == 1 and variable_choices("laser_on")[0] == False: use = False
    else: use = True
    return use

def timepoint(image_number):
    """Laser to X-ray pump-probe delay.
    image_number: is 1-based integer
    Returns time in seconds, None for laser off image"""
    return collection_variable_value("delay",image_number)

def delay(image_number):
    """Laser to X-ray pump-proble delay for a given image number.
    Image number start with 1. delay = 0 for a laser off image."""
    # If the image does not require the laser firing, set time timing
    # for the followong image
    i = image_number
    i0 = i
    while timepoint(i) is None and i<i0+4 and i<nimages(): i += 1
    t =  timepoint(i)
    if t is None: t= nan
    return t
    
def timepoint_number(image_number):
    """Which pump-probe delay to use for this image number? 
    image_number: 1-based index
    Return value: 0-based index"""
    return collection_variable_index("delay",image_number)

def orientation_image_number(image_number=0):
    """How many images into a time series is this image number? 
    image_number: 1-based index
    Return value: 0-based index"""
    # TO DO
    return (image_number-1) % nimages_per_orientation_()
    
def nlevels_used():
    """In case a variable attenuator is used, number of laser energy levels"""
    if not collection_variable_enabled("level"): return 1
    return variable_nchoices("level")

def wait_time(image_number):
    """Waiting time between pulses for a given image number"""
    t = timepoint(image_number)

    # If the image is an "off" image and the waiting time for the off images
    # is specified to be different from the on images, always use this
    # value.
    if isnan(t) and options.min_waitt_off != options.min_waitts[0]:
        return options.min_waitt_off

    # For "off" images, it is possible to specify a maximum waiting time.
    if isnan(t): maxwt = options.max_waitt_off
    else: maxwt = inf

    # If the image is an "off" image, use the waitting time for the next
    # timepoint. If the are two off images following each other
    # the first is for the preceeding time point, the second for the
    # following time point.
    if isnan(t): t = timepoint(image_number+1)
    if isnan(t): t = timepoint(image_number-1)
    wt =  wait_time_for_delay(t)
    wt = min(wt,maxwt)
    return wt

def wait_time_for_delay(t):
    """Waiting time between pulses as function of pump-probe delay
    t: pump-probe delay in seconds"""
    if isnan(t): return options.min_waitt_off
    # Leave an 15-ms margin after the probe pulse for sample translation.
    ##dt = translate.move_time if "linear stage" in translate.mode else 0
    dt = 0
    wt = round_up(t+dt,timing_system.waitt.stepsize)
    # Find the smallest specified waitting time that is large than the current.
    options.min_waitts.sort()
    for t in options.min_waitts:
        if t >= wt: wt = t ; break
    return wt

def timepoint_repeat_number(image_number):
    """How many times has the time point of the image been repeated in the
    current time series?
    image_number: 1-based index"""
    t = collection_variable_value("delay",image_number)
    it = collection_variable_index("delay",image_number)
    ts = variable_choices("delay")[0:it]
    return ts.count(t)
    
def timepoint_repeat_per_series(image_number):
    """Tell how many times does a timepoint occur per time series
    image_number: 1-based index"""
    t = collection_variable_value("delay",image_number)
    ts = variable_choices("delay")
    return ts.count(t)

def npulses(image_number,passno=0):
    """How many X-ray bursts to send to the sample as function of image
    number. image_number is 1-based, passno is 0-based.
    """
    # When using sample translation the exposure may be boken up
    # into several passes.
    if passno != None: npulses = npulses_of_pass(image_number,passno)
    else:
        # Methods-based data collection
        mode = SAXS_WAXS_methods.Ensemble_mode.value
        burst_length = Ensemble_SAXS.burst_length_of_mode(mode)
        passes = SAXS_WAXS_methods.passes_per_image.value
        npulses = burst_length*passes
    return npulses

def ms_shutter_opening_time(image_number,passno=None):
    """Tell the ms shutter opening time is seconds"""
    wt = wait_time(image_number)
    # If running slower than 82 Hz, operate the shutter in pulsed mode.
    # (minimum opening time).
    if wt > timing_system.hlct: return 0
    # If operating at 82 Hz, the opening time is determined by the number
    # of pulses per image or per pass.
    np = npulses(image_number,passno)
    t = np*wt
    return t

def ms_shutter_mode(image_number):
    """ "pulsed" or "timed".
    At maximum reption rate the shutter no longer isolates single pulses
    but gates the X-ray exposure time."""
    wt = wait_time(image_number)
    # If running slower than 82 Hz, operate the shutter in pulsed mode.
    # (minimum opening time).
    if wt > timing_system.hlct: return "pulsed"
    else: return "timed"


def set_chopper(image_number=None):
    """ This sets the chopper operating offset aproprialy for the bunch mode
    of the given image number."""
    if not collection_variable_enabled("chopper_mode"): return
    if image_number == None: image_number = task.image_number
    set_chopper_mode(collection_variable_value("chopper_mode",image_number))

def set_chopper_mode(chopper_mode,wait=True):
    """chopper_mode: 0-base index, row of table of chopper settings"""
    x = chopper.x[int(chopper_mode)]
    y = chopper.y[int(chopper_mode)]
    phase = chopper.phase[int(chopper_mode)]
    if wait: set_chopper_parameters(x,y,phase)
    else: set_chopper_parameters_nowait(x,y,phase)

def set_chopper_parameters(x,y,phase):
    """phase: in units of seconds"""
    old_y = ChopY.value
    old_phase = timing_system.hsc.delay.value
    phase_change_time = time()
    ChopX.value = x
    ChopY.value = y
    timing_system.hsc.delay.value = phase
    while (ChopX.moving or ChopY.moving) and not task.cancelled: sleep(0.1)
    # When moving the chopper vertically, it can excite an oscillation in
    # the magnetic bearing. Wait for 5 s for the oscillation to subside.
    settling_time = 5.0
    if abs(ChopY.value - y) > 0.001:
        t = time()
        while time()-t < settling_time and not task.cancelled: sleep(0.1)
    # When changing the high-speed chopper phase, there is a slew rate and
    # a settling time.
    slew_rate = 100e-9 # 100 ns per second
    settling_time = 10.0
    waiting_time = abs(timing_system.hsc.delay.value-old_phase)/slew_rate + settling_time
    if abs(timing_system.hsc.delay.value - old_phase) > 1e-9:
        while time()-phase_change_time < waiting_time and not task.cancelled:
            sleep(0.1)
        
    if task.cancelled: ChopX.stop(); ChopY.stop()

chopper_old_y,chopper_old_phase = nan,nan
chopper_change_time = 0

def set_chopper_parameters_nowait(x,y,phase):
    """phase: in units of seconds"""
    global chopper_old_y,chopper_old_phase,chopper_change_time
    chopper_old_y,chopper_old_phase = ChopY.value,timing_system.hsc.delay.value
    chopper_change_time = time()
    ChopX.value = x
    ChopY.value = y
    timing_system.hsc.delay.value = phase

def chopper_moving():
    """Hase th echoppre not yet settled?"""
    while (ChopX.moving or ChopY.moving): return True
    # When moving the chopper vertically, it can excite an oscillation in
    # the magnetic bearing. Wait for 5 s for the oscillation to subside.
    settling_time = 5.0
    if abs(chopper_old_y - ChopY.value) > 0.001:
        if time()-chopper_change_time < settling_time: return True
    # When changing the high-speed chopper phase, there is a slew rate and
    # a settling time.
    slew_rate = 100e-9 # 100 ns per second
    settling_time = 10.0
    waiting_time = abs(timing_system.hsc.delay.value-chopper_old_phase)/slew_rate + settling_time
    if abs(timing_system.hsc.delay.value - chopper_old_phase) > 1e-9:
        if time()-chopper_change_time < waiting_time: return True
    return False

def set_chopper_y(chopy):
    """This sets the chopper operating offset."""
    if abs(ChopY.value - chopy) < 0.001: return
    ChopY.value = chopy
    while ChopY.moving and not task.cancelled: sleep(0.1)
    # After the chopper reached the final position, wiat for 5 s for the
    # magnetic bearing to settle.
    t = time()
    while time()-t < 5.0 and not task.cancelled: sleep(0.1)
    if task.cancelled: ChopY.stop()

def chopper_mode(image_number):
    """0-based index to look up chopper.x, chopper.y, chopper.phase
    image_number: 1-based integer"""
    return collection_variable_value("chopper_mode",image_number)

def chopper_pulses(image_number=None):
    """How many single pulses the chopper transmits per opening,
    or in hybrid mode, how many single bunches the tranmitted intensity
    corresponds to, for a given image number.
    If the image number is omitted, return the current value.
    image_number: 1-based integer"""
    if image_number == None: return chopper_pulses_current()
    if not collection_variable_enabled("chopper_mode"): return chopper_pulses_current()
    mode_number = collection_variable_value("chopper_mode",image_number)
    n = chopper.pulses[int(mode_number)] if not isnan(mode_number) else nan
    return n

def chopper_pulses_of_mode(i):
    """How many single pulses the chopper transmits per opening,
    or in hybrid mode, how many single bunches the tranmitted intensity
    corresponds to, based on the current settings of the chopper.
    i: 0-based integer"""
    if isnan(i) or i<0 or i>=len(chopper.pulses): return nan
    return chopper.pulses[int(i)]

def chopper_pulses_current():
    """How many single pulses the chopper transmits per opening,
    or in hybrid mode, how many single bunches the tranmitted intensity
    corresponds to, based on the current settings of the chopper."""
    i = chopper_mode_current()
    if isnan(i) or i<0 or i>=len(chopper.pulses): return nan
    return chopper.pulses[int(i)]
    
def chopper_mode_of_timepoint_number(i):
    """0-based index to look up chopper.x, chopper.y, chopper.phase
    for the given laser to X-ray time delay in seconds.
    The criteria for selection the operation mode are the following:
    1. The opening with the highest possible transmission should be used
    2. The chopper opening time should not exceed 1/2.5 of the pump probe time
    delay.
    i: 0-based timepoint index (range: 0 to ntimepoints()-1)
    """
    # Avoid mode changes for reference images.
    while i<ntimepoints()-1 and timepoints()[i] == param.ref_timepoint: i+=1
    mode = chopper_mode_of_timepoint(timepoints()[i])
    return mode

def chopper_mode_of_timepoint(t):
    """0-based index to look up chopper.x, chopper.y, chopper.phase
    for the given laser to X-ray time delay in seconds.
    The criteria for selection the operation mode are the following:
    1. The opening with the highest possible transmission should be used
    2. The chopper opening time should not exceed 1/2.5 of the pump probe time
    delay.
    """
    from numpy import array,where,nanmax,nanargmax
    if isnan(t) or isnan(t): return chopper_mode_max()
    usable = (array(chopper.min_dt) <= t) & (array(chopper.use) == 1)
    npulses = nanmax(array(chopper.pulses)[usable])
    i = where((array(chopper.pulses) == npulses) & (array(chopper.use) == 1))[0]
    i = i[0]
    return i

def chopper_mode_current():
    """0-based index to look up chopper.x, chopper.y, chopper.phase.
    Based on current x and y position.
    Return nan if too far from any known position.
    """
    from numpy import nanmin,nanargmin,array,sqrt,nan
    n = min(len(chopper.x),len(chopper.y))
    dx = array(chopper.x[0:n])-ChopX.value
    dy = array(chopper.y[0:n])-ChopY.value
    dt = array(chopper.phase[0:n])-timing_system.hsc.delay.value
    rmsd = sqrt(((dx/0.1)**2+(dy/0.1)**2+(dt/10e-9)**2)/3)
    if not nanmin(rmsd) <= 1: return nan
    return nanargmin(rmsd)

def chopper_mode_max():
    "0-based index. In which chopper mode do you get the maximum intensity?"
    from numpy import array,nanargmax
    return nanargmax(array(chopper.pulses)*array(chopper.use))

def time_remaining():
    "Estimates the time in seconds to complete the current dataset"
    t = 0.0
    for i in range (task.image_number,nimages()): t += acquisition_time(i)
    return t

def time_info():
    "Informational message about collection time"
    t = time_remaining()
    if t: return time_string(t)
    else: return ""

def acquisition_time(image_number):
    i = image_number

    readout_time = 2.5 # X-ray detector readout time
    overhead = 2.0 # writing log file etc.

    t = alignment_time(i) + integration_time(i)
    # CCD readout can be concurrent with everything except integration.
    t += max(rotation_time(i)+overhead,readout_time)

    return t

def rotation_time(image_number):
    i = image_number
    da = abs(angle(i) - angle(i-1))
    rotation_speed = 30.0 # deg/s
    return da/rotation_speed

def alignment_time(image_number):
    "Estimated time spend on sample alignment scans"
    i = image_number
    da = abs(angle(i) - angle(i-1))
    if align.enabled and da > 0:
        scan_points = round(abs((align.end-align.start)/align.step))+1
        # bin factor chgange: 2 x 1.9 s
        # 1.9 s readout time, 0.7 s for moving, 5 s processing time
        # Epirically found 2.6 s per scan point + 16 s overhead
        return scan_points * (1.9 + 0.7) + 16.0
    else: return 0

def integration_time(image_number):
    "Estimated time spend accumulating data in the X-ray detector"
    i = image_number
    t = timepoint(i)
    if isnan(t): t = 0
    wt = wait_time(i)
    integration_time = (0.5+npulses(i)-1)*wt+t
    # time lost due to top-ups: 50 top-ups per hour, 5 s pre top-up
    # + 1 s safty margin + 1 waiting time lost per top up
    usable_fraction = 1 - 50*(5.0+1.0+wt) / 3600
    integration_time *= 1/usable_fraction
    return integration_time

def sign(x):
    "1 for a positive number, -1 for a negative number, 0 for zero" 
    if x>0: return 1
    if x<0: return -1
    return 0

def update_bkg_image():
    """Update the backgound image if needed, for instance after the server has
    been restarted or after the bin factor has been changed.
    """
    if options.xray_detector_enabled:
        if ccd.bkg_valid(): return
        ##sleep(2.5) # needed for the clearing of the CCD chip
        ccd.read_bkg()

def xray_safety_shutters():
    """Tell the status of 'Remote Shutter' (in beamline frontend).
    Return 'open' or 'closed'"""
    state = caget("PA:14ID:STA_A_FES_OPEN_PL.VAL")
    if state == 1: return "open"
    elif state == 0: return "closed"
    else: return "state "+str(state)


def open_xray_safety_shutters():
    """Try to remote frontend shutter and waits until the shutter opens
    (If the X-ray hutches are not locked or the storage ring is down this may take
    forever.)"""
    t = time()
    xray_safety_shutters_open.value = True
    while not xray_safety_shutters_open.value == True and not task.cancelled:
        sleep(0.2)
        if time()-t > 30 and not options.wait_for_beam: break

def close_xray_safety_shutters():
    """Remote Frontend shutter"""
    xray_safety_shutters_open.value = False
    while not xray_safety_shutters_open.value == False and not task.cancelled:
        sleep(0.2)

def open_laser_safety_shutter():
    laser_safety_shutter_open.value = True
    t = time()
    while not laser_safety_shutter_open.value == True and not task.cancelled:
        sleep(0.2)
        if time()-t > 4 and not options.open_laser_safety_shutter and \
            True in variable_choices("laser_on"): break

def wait_for(condition,timeout=nan):
    """Halt execution until the condition passed as string evaluates to 
    True.
    timeout: in unit of seconds. If specified unconditionally return after
    the number of seconds has passed."""
    start = time()
    while not eval(condition) and not task.cancelled:
        if time() - start > timeout: break
        sleep(0.05)

def timing_diagnostics_start_dataset():
    global timing_diagnostics_delays
    timing_diagnostics_delays = {}

timing_diagnostics_delays = {}

def timing_diagnostics_start_images(image_numbers=None):
    """Measure the Laser to X-ray delay using the timing oscilloscope
    and save the results to a log file."""
    global timing_diagnostics_keep_monitoring
    timing_diagnostics_keep_monitoring = True
    from thread import start_new_thread
    start_new_thread(timing_diagnostics_monitor,())

timing_diagnostics_keep_monitoring = False

def timing_diagnostics_finish_images(image_numbers=None):
    """Turn off the timing oscilloscope time scale updates and logging of
    time delays."""
    global timing_diagnostics_keep_monitoring
    timing_diagnostics_keep_monitoring = False

def timing_diagnostics_monitor():
    """Measure the Laser to X-ray delay using the timing oscilloscope
    and save the results to a log file."""
    global timing_diagnostics_last_delay, timing_diagnostics_last_image_number
    while timing_diagnostics_keep_monitoring:
        if diagnostics.enabled and diagnostics.delay:
            adjust_timing_scope_range()

            image_number1 = timing_system.image_number.count
            delay = actual_delay.value - diagnostics.timing_offset
            image_number = timing_system.image_number.count

            if not image_number in diagnostics_image_times:
                diagnostics_image_times[image_number] = [time()]
            else: diagnostics_image_times[image_number] += [time()]
                
            if not isnan(delay) and image_number == image_number1 and \
                delay != timing_diagnostics_last_delay:
                if not image_number in timing_diagnostics_delays:
                    timing_diagnostics_delays[image_number] = [delay]
                else: timing_diagnostics_delays[image_number] += [delay]
            if image_number != timing_diagnostics_last_image_number and \
                not isnan(timing_diagnostics_last_image_number):
                timing_diagnostics_log(timing_diagnostics_last_image_number)
            timing_diagnostics_last_delay = delay
            timing_diagnostics_last_image_number = image_number

timing_diagnostics_last_delay = nan
timing_diagnostics_last_image_number = nan

diagnostics_image_times = {}

def diagnostics_image_start_time(image_number):
    if not image_number in diagnostics_image_times: t = time()
    else: t = min(diagnostics_image_times[image_number])
    return t

def diagnostics_image_end_time(image_number):
    if not image_number in diagnostics_image_times: t = time()
    else: t = max(diagnostics_image_times[image_number])
    return t

def timing_diagnostics_delay(image_number):
    from numpy import average
    if not image_number in timing_diagnostics_delays: delay = nan
    else: delay = average(timing_diagnostics_delays[image_number])
    return delay

def timing_diagnostics_sdev_delay(image_number):
    from numpy import std
    if not image_number in timing_diagnostics_delays: sdev_delay = nan
    else: sdev_delay = std(timing_diagnostics_delays[image_number])
    return sdev_delay

def timing_diagnostics_num_delay(image_number):
    from numpy import std
    if not image_number in timing_diagnostics_delays: num_delay = 0
    else: num_delay = len(timing_diagnostics_delays[image_number])
    return num_delay

def timing_diagnostics_log(image_number):
    """Write timing diagnostics infomration into a separate log file"""
    logfile = timing_diagnostics_logfile()
    if not exists(logfile):
        if not exists(dirname(logfile)): makedirs(dirname(logfile))
        header = "#date time\tfilename\tact.delay[s]\tsdev(act.delay)[s]\tnum(act.delay)\n"
        file(logfile,"w").write(header)
    line = "%s\t%s\t%s\t%s\t%s\n" % (
        timestamp(diagnostics_image_end_time(image_number)),
        basename(filename(image_number)),
        timing_diagnostics_delay(image_number),
        timing_diagnostics_sdev_delay(image_number),
        timing_diagnostics_num_delay(image_number),
    )
    file(logfile,"a").write(line)

def timing_diagnostics_logfile():
    """Write timing diagnostics information into a separate log file"""
    base,ext = splitext(logfile())
    filename = base+"_timing.txt"
    return filename

def timing_scope_range(t):
    """Time scale of the oscilloscope such that both laser
    and X-ray pulses are within the recorded time window.
    The X-ray pulse is at the trigger point T=0 in the middle of the
    window the laser pulse preceeds is by the nominal time delay
    specified by t.
    t: laser to X-tay time sedleay in seconds"""
    return max(abs(t)*2*1.25,diagnostics.min_window)

def adjust_timing_scope_range(image_number=None):
    """Adjust the time scale of the oscilloscope such that both laser
    and X-ray pulses are within the recorded time window.
    The X-ray pulse is at the trigger point T=0 in the middle of the
    window the laser pulse preceeds is by the nominal time delay."""
    if image_number is None: image_number = timing_system.image_number.count
    nom_delay = collection_variable_value("delay",image_number)
    actual_delay.time_range = timing_scope_range(nom_delay)

def image_info_reset():
    global current_image_number_keep_updating
    current_image_number_keep_updating = False
    global image_info_acquiring
    image_info_acquiring = False
    global image_info_image_number
    image_info_image_number = 0
    global image_info
    image_info = {}

image_info_reset()

def current_image_number_start_updating():
    """Begin collecting per-image statistics for diagnostics PVs."""
    global image_info_acquiring
    image_info_acquiring = False
    global current_image_number_keep_updating
    current_image_number_keep_updating = True
    from thread import start_new_thread
    start_new_thread(current_image_number_update_task,())

def current_image_number_finish_updating():
    """End collecting per-image statistics for diagnostics PVs."""
    global current_image_number_keep_updating
    current_image_number_keep_updating = False

def current_image_number_update_task():
    """Keep the variable 'image_info_image_number' up to date"""
    while current_image_number_keep_updating:
        current_image_number_update()
        sleep(0.02)

def current_image_number_update():
    """Update the variable 'image_info_image_number' once"""
    image_number = timing_system.image_number.count
    global image_info_image_number
    last_image_number = image_info_image_number
    
    if image_number != last_image_number:
        if not last_image_number in image_info: image_info[last_image_number] = {}
        image_info[last_image_number]["finished"] = time()
        if not image_number in image_info: image_info[image_number] = {}
        image_info[image_number]["started"] = time()

    image_info_image_number = image_number

    acquiring = timing_sequencer.queue_active
    global image_info_acquiring
    last_acquiring = image_info_acquiring

    if acquiring != last_acquiring:
        if acquiring:
            if not image_number in image_info: image_info[image_number] = {}
            image_info[image_number]["started"] = time()
        if not acquiring:
            if not image_number in image_info: image_info[image_number] = {}
            image_info[image_number]["finished"] = time()

    image_info_acquiring = acquiring

def current_image_number():
    return image_info_image_number

def image_timestamp(image_number):
    if image_number in image_info and "started" in image_info[image_number]:
        t = image_info[image_number]["started"]
    else: t = 0
    return t

def image_finished(image_number):
    # Make sure image_info get s updated.
    if not current_image_number_keep_updating: current_image_number_update()
    i = image_number 
    if i in image_info and\
        "started" in image_info[i] and "finished" in image_info[i] and\
        image_info[i]["finished"] > image_info[i]["started"]:
        finished = True
    else: finished = False
    return finished

def image_logged(image_number):
    i = image_number 
    logged = i in image_info and "logged" in image_info[i]
    return logged


def diagnostics_start_dataset():
    """To be called beffore the start of data collection"""
    image_info_reset()
    diagnostics_reset()
    timing_diagnostics_start_dataset()

def diagnostics_finish_dataset():
    """To be called after the end of data collection"""
    if diagnostics.enabled and diagnostics.xray_record_waveform:
        exec_delayed(2,"xray_trace.waveform_autosave = False")
    if diagnostics.enabled and diagnostics.laser_record_waveform:
        exec_delayed(2,"laser_trace.waveform_autosave = False")

def diagnostics_start_images(image_numbers):
    """To be called before starting the dataset"""
    if diagnostics.enabled:
        if diagnostics.delay:
            xray_pulse.enabled = diagnostics.xray
        if diagnostics.delay:
            laser_pulse.enabled = diagnostics.laser

        if diagnostics.xray_record_waveform:
            progress("uploading x-ray waveform file list...")
            filenames = waveform_filenames(image_numbers,"xray")
            # Split up waveforms into multiple files if there are mutiple bursts.
            n = burst_length(image_numbers[0])
            xray_trace.acquire_sequence(n)
            xray_trace.sequence_timeout_enabled = False
            xray_trace.noise_filter = "None"
            xray_trace.sampling_rate = diagnostics.xray_sampling_rate
            xray_trace.time_range    = diagnostics.xray_time_range
            xray_trace.trigger_delay = diagnostics.xray_time_offset
            xray_trace.acquire_waveforms(filenames) 
            xray_trace.scope.trigger_mode = "Normal" # Needed?
            progress("uploading x-ray waveform file list done.")
            progress("")
            # Turn off measurments slowing down the scope, if not needed.
            if not diagnostics.xray: xray_trace.scope.measurement_enabled = False
        if diagnostics.laser_record_waveform and laser_enabled():
            progress("uploading laser waveform file list...")
            filenames = waveform_filenames(image_numbers,"laser")
            # Split up waveforms into multiple files if there are mutiple bursts.
            n = burst_length(image_numbers[0])
            laser_trace.acquire_sequence(n)
            laser_trace.sequence_timeout_enabled = False
            laser_trace.noise_filter = "None"
            laser_trace.sampling_rate = diagnostics.laser_sampling_rate
            laser_trace.time_range    = diagnostics.laser_time_range
            laser_trace.trigger_delay = diagnostics.laser_time_offset
            laser_trace.acquire_waveforms(filenames)
            laser_trace.scope.trigger_mode = "Normal" # Needed?
            progress("uploading laser waveform file list done.")
            progress("")
            # Turn off measurments slowing down the scope, if not needed.
            if not diagnostics.laser: laser_trace.scope.measurement_enabled = False
        if diagnostics.delay:
            timing_diagnostics_start_images(image_numbers)
        diagnostics_start_montitoring()

def diagnostics_finish_images(image_numbers):
    if diagnostics.enabled and diagnostics.delay:
        timing_diagnostics_finish_images(image_numbers)
    diagnostics_finish_montitoring()
    current_image_number_finish_updating()

def diagnostics_start_image(image_number):
    """To called before an image is acquired.
    image_number: 1-based index"""
    if diagnostics.enabled:
        if diagnostics.xray:
            n = npulses(task.image_number)
            if not diagnostics.xray_record_waveform or n==1: xray_pulse.start()
        if diagnostics.laser: laser_pulse.start()
    
def diagnostics_finish_image(image_number):
    """Called after an image was acquired.
    image_filename: used as a basename for additional diagnositcs files to be
    writtten
    image_number: 1-based index"""
    if not diagnostics.enabled: return

diagnostics_keep_monitoring = False

def diagnostics_start_montitoring():
    """Begin collecting per-image statistics for diagnostics PVs."""
    global diagnostics_keep_monitoring
    diagnostics_keep_monitoring = True
    from thread import start_new_thread
    for i in range(0,diagnostics_PVs()):
        start_new_thread(diagnostics_monitor_PV,(diagnostics_PV_name(i),))

def diagnostics_finish_montitoring():
    """End collecting per-image statistics for diagnostics PVs."""
    global diagnostics_keep_monitoring
    diagnostics_keep_monitoring = False

def diagnostics_reset():
    global diagnostics_data
    diagnostics_data = {}

diagnostics_reset()

def diagnostics_monitor_PV(name):
    """Collect per image statistics for diagnostics PVs."""
    while diagnostics_keep_monitoring:
        if diagnostics.enabled:
            if not name in diagnostics_data: diagnostics_data[name] = {}
            i = current_image_number()
            if not i in diagnostics_data[name]: diagnostics_data[name][i] = \
               {"sum":0.0,"sum2":0.0,"count":0,"last":0.0}
            s = diagnostics_data[name][i]
            val = diagnostics_value(name)
            if current_image_number() == i:
                if not isnan(val) and val != s["last"]:
                    s["sum"] += val
                    s["sum2"] += val**2
                    s["count"] += 1
                    s["last"] = val
            sleep(0.02)

def diagnostics_PV_image_avg(i_PV,image_number,):
    """Average value of a process variable that is monitored during an
    image acquisition
    i_PV: 0-based index
    image_number: 1-based index
    """
    i = image_number
    name = diagnostics_PV_name(i_PV)
    if name in diagnostics_data:
        if i in diagnostics_data[name]:
            s = diagnostics_data[name][i]
            sum,n = s["sum"],s["count"]
            if n > 0: value = sum/n
            else: value = nan
        else: value = nan
    else: value = nan
    return value

def diagnostics_PV_image_sdev(i_PV,image_number):
    """Standard deviation of the individual sampled value
    that is monitored during an image acquisition
    i_PV: 0-based index
    image_number: 1-based index
    """
    i = image_number
    name = diagnostics_PV_name(i_PV)
    if name in diagnostics_data:
        if i in diagnostics_data[name]:
            s = diagnostics_data[name][i]
            sum,sum2,n = s["sum"],s["sum2"],s["count"]
            if n > 0: value = sqrt(sum2/n - (sum/n)**2)
            else: value = nan
        else: value = nan
    else: value = nan
    return value

def diagnostics_PV_image_count(i_PV,image_number):
    """How many times has a process variable been measured during
    an image acquisition?
    i_PV: 0-based index
    image_number: 1-based index
    """
    i = image_number
    name = diagnostics_PV_name(i_PV)
    if name in diagnostics_data:
        if i in diagnostics_data[name]:
            s = diagnostics_data[name][i]
            value = s["count"]
        else: value = 0
    else: value = 0
    return value

def diagnostics_value(name):
    """The value of a process variable, if name is a process variable.
    Otherwise, name is assumed to be the name of a Python object and
    its 'value' property is used."""
    try: x = eval(name)
    except: return tofloat(caget(name))
    return tofloat(getattr(x,"value",x))

def diagnostics_xray_offset():
    """Integral area over width of gate in units of Vs"""
    gate_width = diagnostics.xray_gate_stop - diagnostics.xray_gate_start
    return diagnostics.xray_offset_level*gate_width

def diagnostics_set_xray_offset(offset):
    "offset: integral area over width of gate"
    gate_width = diagnostics.xray_gate_stop - diagnostics.xray_gate_start
    diagnostics.xray_offset_level = offset/gate_width

def diagnostics_PVs():
    """Number of active diagnostics PVs"""
    n = 0
    for i in range(0,min(len(diagnostics.PVs),len(diagnostics.PVuse))):
        if diagnostics.PVuse[i]: n += 1
    return n

def diagnostics_PV_name(i):
    """Name of ith active process variable"""
    n = -1
    for j in range(0,min(len(diagnostics.PVuse),len(diagnostics.PVs))):
        if diagnostics.PVuse[j]: n += 1
        if n == i: return diagnostics.PVs[j]
    return ""

def diagnostics_PV_comment(i):
    """Descriptive comment for ith active process variable"""
    n = -1
    for j in range(0,min(len(diagnostics.PVuse),len(diagnostics.PVnames))):
        if diagnostics.PVuse[j]: n += 1
        if n == i: return diagnostics.PVnames[j]
    return "PV"

def diagnostics_PV_summary():
    "Listing of process variable definitions in text form (for log file header)."
    s = ""
    for i in range(0,diagnostics_PVs()):
        s += diagnostics_PV_comment(i)+": "
        s += diagnostics_PV_name(i)+"; "
    s = s.rstrip("; ")
    return s

def diagnostics_summary():
    "Short listing of calibration constants in text form (for log file header)."
    s = ""
    if diagnostics.delay:
        s += "delay: offset %g s; " % diagnostics.timing_offset
    if diagnostics.xray:
        ref = diagnostics.xray_reference
        offset = diagnostics_xray_offset()
        s += "x-ray: reference %g, offset %g; " % (ref,offset)
    if diagnostics.laser:
        ref = diagnostics.laser_reference
        offset = diagnostics.laser_offset
        s += "laser: reference %g, offset %g; " % (ref,offset)
    s = s.rstrip("; ")
    return s

def tofloat(x):
    """Like builtin 'float', but do not raise an exception, return 'nan'
    instead."""
    try: return float(x)
    except: return nan

# Sample Alignment:

def collectinion_zs():
    """At which z positions to collect data"""
    n = translation_after_image_nspots()
    zs = []
    for i in range(0,n):
       zs += [min(sample.zs) + i*translation_after_image_zstep()]
    return zs

def zs(image_number):
    "Number of DiffZ position for an given image"
    return translation_during_image_unique_zs(image_number)

def alignment_all_support_points():
    """"Phi values and Z values for all alignment scan done so far as numpy
    array"""
    PHI,Z = array(align_table())[0:2]
    return array([PHI,Z])

def sample_aligned_at(phi,z):
    """Whas an alignment scan performed at (phi,z)?"""
    PHI,Z = alignment_all_support_points()
    for (phis,zs) in zip(PHI,Z):
        if abs(phi-phis)<1e-3 and abs(z-zs)<1e-3: return True
    return False

## image_number=90; phi = angle(image_number); z = zs(image_number)[0]

def within_interpolation_range(phi,z):
    """Is the position (phi,z) close enough to an already measured support points
    such that interpolation can be used?"""
    PHI,Z = alignment_closest_support_points(phi,z)
    dphi,dz = alignment_interpolation_dphi(),alignment_interpolation_dz()
    eps = 1e-3
    def amax(a): return max(a) if len(a)>0 else nan
    def amin(a): return min(a) if len(a)>0 else nan
    phi1,phi2 = amax(PHI[PHI<=phi+eps]),amin(PHI[phi-eps<=PHI])
    phi_within_range = phi2-phi1 <= dphi+eps
    Zs = Z[(PHI==phi1) | (PHI==phi2)]
    # z need to be in between the zs
    z_within_range = amin(Zs) <= z+eps and z-eps <= amax(Zs)
    within_range = phi_within_range and z_within_range
    return within_range

def alignment_closest_support_points(phi,z):
    """Phi values and z values of the four closest (phi,z) pairs
    for which alignemnt scans have been performed.
    If (phi,z) is inside the support point network, four points are returned.
    If outside, less than four.
    Return value: two numpy arrays: PHI,Z"""
    from numpy import concatenate,argmin,nan,isnan,array,any
    phi = phi % 360
    PHI,Z = alignment_all_support_points()
    PHI = concatenate((PHI-360,PHI,PHI+360))

    PHI1,PHI2 = PHI[PHI<=phi],PHI[PHI>=phi]
    PHI1,PHI2 = PHI[PHI<=phi],PHI[PHI>=phi]
    phi1 = PHI1[argmin(abs(PHI1-phi))] if len(PHI1)>0 else nan
    phi2 = PHI2[argmin(abs(PHI2-phi))] if len(PHI2)>0 else nan
    phi1 = phi1 % 360
    phi2 = phi2 % 360
    if phi1 == phi2: phi2 = nan
    Z1,Z2 = Z[Z<=z],Z[Z>=z]
    z1 = Z1[argmin(abs(Z1-z))] if len(Z1)>0 else nan
    z2 = Z2[argmin(abs(Z2-z))] if len(Z2)>0 else nan
    if z1 == z2: z2 = nan
    points = array([[phi1,z1],[phi1,z2],[phi2,z1],[phi2,z2]])
    points = points[~any(isnan(points),axis=1)]
    PHI,Z = points.T
    # Check if the points are support points.
    PHIs,Zs = alignment_all_support_points()
    OK = array([any((phi==PHIs) & (z == Zs)) for (phi,z) in zip(PHI,Z)],bool) 
    PHI,Z = PHI[OK],Z[OK]
    return PHI,Z
    
def alignment_interpolation_dphi():
    """How close have measured support points to on both sides to to calculate
    the crsyal edge rather than measure it."""
    if align.align_at_collection_phis: return align.intepolation_dphi
    else: return inf

def alignment_interpolation_dz():
    """How close have measured support points to on both sides to to calculate
    the crsyal edge rather than measure it."""
    if align.align_at_collection_zs: return align.intepolation_dz
    else: return inf

def alignment_support_points(phi,z):
    """The closest values of Phi and DiffZ for which an aligment was
    already done.
    returns (phi1,phi2,z1,z2)
    If no support point is avaiable any of phi1,phi2,z1,z2 can by nan."""
    from numpy import array,argmin,nan
    PHI,Z = array(align_table())[0:2]
    PHI1,PHI2 = PHI[PHI<=phi],PHI[PHI>=phi]
    phi1 = PHI1[argmin(abs(PHI1-phi))] if len(PHI1)>0 else nan
    phi2 = PHI2[argmin(abs(PHI2-phi))] if len(PHI2)>0 else nan 
    Z1,Z2 = Z[Z<=z],Z[Z>=z]
    z1 = Z1[argmin(abs(Z1-z))] if len(Z1)>0 else nan
    z2 = Z2[argmin(abs(Z2-z))] if len(Z2)>0 else nan
    return phi1,phi2,z1,z1

def alignment_closest_phi_z(phi=None,z=None):
    """The closest values of Phi and DiffZ for which an aligment was
    already done."""
    if phi == None: phi = Phi.command_value
    if z == None: z = diffractometer.zc

    table = align_table()
    PHI = table[0]
    Z = table[1]
    n = len(table[0])
    if n == 0: return nan,nan
    dphi = inf
    for i in range(0,n): dphi=min(dphi,abs(phi-PHI[i]))
    j = 0; dz = inf
    for i in range(0,n):
        if abs(phi-PHI[i]) <= dphi:
            if abs(z-Z[i]) < dz: dz = abs(z-Z[i]); j = i
    return PHI[j],Z[j]

def alignment_center(gonz=None):
    """Return the (gonx,gony) reference for aligning the crystal top edge
    to the X-ray beam.
    With automatic sample translation the alignment center is dynamically
    changing as the sample is translated in goniometer z direction. The
    (gonx,gony) center as function of DiffZ is calculated by linear inter-
    polation between the tranlation endpoints."""
    x,y,z = sample.center
    return x,y

def set_sample_center(x=None,y=None,z=None):
    "Define the center of the sample"
    if x == None: x = DiffX.command_value
    if y == None: y = DiffY.command_value
    if z == None: z = DiffZ.command_value
    center = x,y,z
    if sample_center() != center: align.center_time = time()
    sample.center = center
    align.center_sample = param.file_basename
    save_settings()

def sample_center():
    """DiffX,DiffY,DiffZ motor positions at the time 'Define Center'
    button was pressed."""
    return sample.center

def alignment_needed_for(image_number):
    """Run at least one alignment scan for the given image number?"""
    phi = angle(image_number)
    for z in zs(image_number):
        if within_interpolation_range(phi,z): continue
        PHI,Z = sample.closest_support_points(phi,z)
        if align.align_at_collection_zs:
            if len(zs(image_number)) <= 1: Z = [z]
        if align.align_at_collection_phis:
            PHI = [phi]*len(Z)
        for (phi_s,z_s) in zip(PHI,Z):
            if not sample_aligned_at(phi_s,z_s): return True
    return False

def align_sample_if_needed_for(image_number):
    """Run the neccessary alignment scans for the given image number
    restore: Return X,Y,Z,Phi to their original values?"""
    phi = angle(image_number)
    align_sample_if_needed_for_phi(phi)
    
def align_sample_if_needed_for_phi(phi):
    """Run the neccessary alignemt scans for the given orientation
    restore: Return X,Y,Z,Phi to their original values?"""
    if not align.enabled: return

    PHIs,Zs = scans_at_phi_z_needed_for_phi(phi)
    align_sample_at(PHIs)

def scans_at_phi_z_needed_for_phi(phi):
    """At which values of phi and z alignment scans need to be done
    to collect at phi?
    Return value: list of phi values,list of z vales as tuple"""
    if align.align_at_collection_phis and not align.align_at_collection_zs:
        Zs = [z for z in sample.spot_zs if not within_interpolation_range(phi,z)]
        PHIs = [phi]*len(Zs)
    else:
        PHIs,Zs = [],[]
        for z in sample.spot_zs:
            if not within_interpolation_range(phi,z):
                PHI,Z = sample.closest_support_points(phi,z)
                if align.align_at_collection_zs:
                    if len(collectinion_zs()) <= 1: Z = [z]
                if align.align_at_collection_phis:
                    from numpy import unique
                    Z = unique(Z)
                    PHI = [phi]*len(Z)
                PHIs += PHI
                Zs += list(Z)
    return PHIs,Zs

def alignment_scan_dir(phi=None,z=None):
    """Scratch directory where to store the images acquired during an alignment
    scan."""
    if phi == None: phi = diffractometer.phic
    if z == None: z = diffractometer.zc
    return param.path+"/alignment/scan_phi=%.3f_z=%.3f" % (phi,z)
    
def align_sample_at(PHIs):
    """Acquire a series of image with different vertical offsets 
    in order to to find the edge of the crystal
    PHIs: list of phi angles
    Zs: list of z support points in z direction"""
    # Group alignment scans by phi.
    from numpy import unique
    for phi in unique(PHIs):
        diffractometer.phi = phi
        while diffractometer.moving and not task.cancelled: sleep (0.01)
        align_sample()

def align_sample():
    """Acquire a series of alignment scans at different horizontal
    positions given by Zs, in order to to find the edge of the crystal at the
    current phi orienation.
    Zs: lists of horizontal positions at which to perform alignment scans"""
    action = task.action; task.action = "Align Sample"
    PHIs = [diffractometer.phic]
    Zs = sample.spot_zs
    progress("Performing alignment scans at phi=%r,z=%r"%(list(PHIs),list(Zs)))

    alignment_scan_start()

    image_numbers = alignment_pass(1)
    while len(image_numbers) > 0 and not task.cancelled:
        alignment_scan_start_images(image_numbers)
        alignment_scan_wait(image_numbers)
        image_numbers = alignment_pass(image_numbers[-1]+1)

    alignment_scan_finish(image_numbers)
    task.action = action

def alignment_pass(starting_image_number=1):
    """starting_image_number: 1-based
    return value: lsit of 1-based image numbers"""
    # Break up the dataset into passes limited by the number of positions
    # the motion controller can store.
    X,Y,Z,PHI,OFFSET,filenames = alignment_scan_parameters()
    i = starting_image_number-1
    nmax = triggered_motion.max_steps(3)
    Nimages = min(len(filenames)-i,nmax)
    image_numbers = range(i+1,i+Nimages+1)
    return image_numbers
      
def alignment_scan_start():
    # Generate a logfiles to be used later by "diffraction_profile".
    X,Y,Z,PHI,OFFSET,filenames = alignment_scan_parameters()
    from os.path import relpath
    data = {}
    for i in range(0,len(filenames)):
        x,y,z,phi,offset,filename = X[i],Y[i],Z[i],PHI[i],OFFSET[i],filenames[i]
        logfilename = param.path+"/alignment/scan_phi=%.3f_z=%.3f.log" % (phi,z)
        if "reference" in filename: continue
        if not logfilename in data: data[logfilename]= []
        f = relpath(filename,param.path+"/alignment")
        data[logfilename] += [(phi,offset,f)]
    for logfilename in data:
        tab = data[logfilename]
        s = "#phi\toffset\tfilename\n"
        for record in tab: s += "%g\t%g\t%s\n" % record
        if not exists(dirname(logfilename)): makedirs(dirname(logfilename))
        file(logfilename,"wb").write(s)
    # Make sure that the image files do not exists already.
    for filename in filenames:
        if exists(filename): remove(filename)


def alignment_scan_start_images(image_numbers):
    """Configure hardware
    image_numbers: list of 1-based integers,
    e.g. image_numbers = alignment_pass(1)"""
    alignment_scan_motion_controller_start_images(image_numbers)
    alignment_scan_xray_detector_start_images(image_numbers)
    alignment_scan_timing_system_start_images(image_numbers)

def alignment_scan_motion_controller_start_images(image_numbers):
    """Configure motion controller
    image_numbers: list of 1-based integers
    e.g. image_numbers = alignment_pass(1)"""
    X,Y,Z,PHI,OFFSET,filenames = alignment_scan_parameters()
    XYZ = array([X,Y,Z]).T        
    triggered_motion.xyz = XYZ
    triggered_motion.waitt = timing_system.waitt.next(align.waitt)
    triggered_motion.armed = True

def alignment_scan_timing_system_start_images(image_numbers):
    """Configure timing system
    image_numbers: list of 1-based integers
    e.g. image_numbers = alignment_pass(1)"""
    nimages = len(image_numbers)
    # The detector trigger pulse at the beginning of the first image is to
    # dump zingers that may have accumuated on the CCD. This image is discarded.
    # An extra detector trigger is required after the last image,
    waitt   =       [align.waitt]*nimages+[align.waitt]
    burst_waitt =   [0.012]*nimages+[0.012]
    burst_delay =   [0]*nimages+[0]
    npulses =       [align.npulses]*nimages+[align.npulses]
    laser_on =      [0]*nimages+[0]
    ms_on =         [1]*nimages+[0]
    xatt_on =       [align.attenuate_xray]*nimages+[align.attenuate_xray]
    trans_on =      [1]*nimages+[0]
    xdet_on =       [1]*nimages+[1]
    xosct_on =      [1]*nimages+[0]
    image_numbers = image_numbers+[image_numbers[-1]+1]
    ##timing_sequencer.inton_sync = 0
    timing_system.image_number.count = 0
    timing_system.pulses.count = 0
    ##timing_sequencer.running = False
    timing_sequencer.acquire(
        waitt=waitt,
        burst_waitt=burst_waitt,
        burst_delay=burst_delay,
        npulses=npulses,
        laser_on=laser_on,
        ms_on=ms_on,
        xatt_on=xatt_on,
        trans_on=trans_on,
        xdet_on=xdet_on,
        xosct_on=xosct_on,
        image_numbers=image_numbers,
    )
    
def alignment_scan_xray_detector_start_images(image_numbers):
    """Configure X-ray area detector
    image_numbers: list of 1-based integers
    e.g. image_numbers = alignment_pass(1)"""
    if options.xray_detector_enabled:
        X,Y,Z,PHI,OFFSET,filenames = alignment_scan_parameters()
        filenames = [filenames[i-1] for i in image_numbers]
        # The first image needs to be discarded, because there is one more
        # detector trigger pulse than there are images.
        filenames = ["/tmp/jumk.rx"]+[filenames]
        ccd.bin_factor = align.ccd_bin_factor # Speeds up the acquisition time
        ccd.acquire_images(image_numbers,filenames) 
        show_images(filenames)


def alignment_scan_wait(image_numbers):
    """Wait for scan to complete
    image_numbers: list of 1-based integers, e.g. image_numbers = alignment_pass(1)"""
    while alignment_scan_running(image_numbers) and not task.cancelled:
        sleep(0.01)

def alignment_scan_running(image_numbers):
    """Is scan complete?
    image_numbers: list of 1-based integers, e.g. image_numbers = alignment_pass(1)"""
    if alignment_scan_timing_system_running(image_numbers): return True
    elif alignment_scan_xray_detector_running(image_numbers): return True
    else: return False

def alignment_scan_timing_system_running(image_numbers):
    """Is scan complete?
    image_numbers: list of 1-based integers, e.g. image_numbers = alignment_pass(1)"""
    i = timing_system.image_number.count
    p = timing_system.pulses.count
    progress("acquiring image %3d, %d pulses" % (i,p))
    running = (i < image_numbers[-1]) if len(image_numbers)>0 else False
    return running

def alignment_scan_xray_detector_running(image_numbers):
    """Is scan complete?
    image_numbers: list of 1-based integers, e.g. image_numbers = alignment_pass(1)"""
    if options.xray_detector_enabled:
        state = ccd.state()
        progress("X-ray detector: %s" % state)
        running = (state == "acquiring series")
    else: running = False
    return running


def alignment_scan_finish(image_numbers):
    """image_numbers: list of 1-based integers, e.g. image_numbers = alignment_pass(1)"""
    alignment_scan_timing_system_finish(image_numbers)
    if options.xray_detector_enabled: alignment_scan_xray_detector_finish(image_numbers)

def alignment_scan_timing_system_finish(image_numbers):
    """image_numbers: list of 1-based integers, e.g. image_numbers = alignment_pass(1)"""
    # Make sure shutters are closed
    timing_sequencer.psg_state = 0
    timing_sequencer.ms_state = 0
    timing_sequencer.s3_state = 0

def alignment_scan_xray_detector_finish(image_numbers):
    """image_numbers: list of 1-based integers, e.g. image_numbers = alignment_pass(1)"""
    PHIs = [diffractometer.phic]
    Zs = sample.spot_zs
    update_diffraction_profiles(PHIs,Zs)
    for phi in PHIs:
        for z in Zs: process_alignment_scan(phi,z)


def alignment_scan_parameters(PHIs=None,Zs=None):
    """Return value: X,Y,Z,PHI,OFFSET,filename
    (X,Y,Z for SampleX,SampleY,SampleZ)"""
    if PHIs is None: PHIs = [diffractometer.phic]
    X,Y,Z,PHI,OFFSET,filenames = [],[],[],[],[],[]
    for phi in PHIs:
        for s in sample.samples:
            cx1,cy1,cz1 = diffractometer.xyz_of_sample(s["start"],phi)
            cx2,cy2,cz2 = diffractometer.xyz_of_sample(s["end"],phi)
            # Start with a reference image through the center of the crystal that
            # is valid for all scans done at the same orientation
            cx,cy,cz = (cx1+cx2)/2,(cy1+cy2)/2,(cz1+cz2)/2
            X += [cx]; Y += [cy]; Z += [cz]; PHI += [phi]; OFFSET += [0]
            filenames += [param.path+"/alignment/reference_phi=%.3f.mccd" % phi]
            if align.align_at_collection_zs: align_zs = collectinion_zs()
            else: align_zs = [cz1,cz2] if Zs is None else Zs
            for z in align_zs:
                cx = interpolate([[cz1,cx1],[cz2,cx2]],z)
                cy = interpolate([[cz1,cy1],[cz2,cy2]],z)
                npoints = int(ceil(sample.sample_r/align.step))+1
                # Start outside the crystal, scan till the center is reached.
                offsets = [-align.step*i for i in range(0,npoints)][::-1]
                X += [cx]*npoints
                Y += [cy+offset for offset in offsets]
                Z += [z]*npoints
                PHI += [phi]*npoints
                OFFSET += offsets
                scan_dir = param.path+"/alignment/scan_phi=%.3f_z=%.3f" % (phi,z)
                filenames += [scan_dir+"/offset=%.3f.mccd" % y for y in offsets]

    return X,Y,Z,PHI,OFFSET,filenames

def alignment_status():
    "Short status report about progress of current alignement scan"
    status = ""
    if task.action == "Align Sample": status += "Aligning: "
    else: status += "Current settings: "
    status += "%s=%g %s, " % (Spindle.name,Spindle.value,Spindle.unit)
    status += "Z=%.3f mm, " % DiffZ.value
    status += "offset %.3f mm, " % diffractometer.y
    if task.action == "Align Sample":
        ccd_state = ccd.state()
        if ccd_state != "idle" and ccd_state != "": status += ccd_state+", "
        if timing_system.pulses.count > 0: status += "%d pulses, " % timing_system.pulses.count
        if options.wait_for_topup and time_to_next_refill.value < 1.0:
           t = time_to_next_refill.value
           if t > 0: status += "%g s until next top-up, " % t
           if t == 0: status += "top-up in progress, "
    if task.comment: status += task.comment+", "
    status = status.strip(", ")
    return status
    
def alignment_summary():
    "Short report about last alignment scan"
    s = ""
    if any(isnan(sample_center())): s += "Sample not yet centered."
    else:
        x,y,z = sample_center()
        s += "Sample '%s' centered at " % align.center_sample
        s += "X=%.3f, Y=%.3f, Z=%.3f" % (x,y,z)
        if align.center_time:
            if time()- align.center_time < 24*60*60: format = "at %H:%M"
            else: format = "on %d %b %y %H:%M"
            s += " "+strftime(format,localtime(align.center_time))+"."
    s += "\n"
    if not align.enabled:
        s += "No alignment scans. No vertical adjustment."
        return s
    if alignment_needed_for(task.image_number):
        phi = angle(task.image_number)
        align_phi,align_z = alignment_closest_phi_z(phi)
        offset = align_offset(align_phi,align_z)
        s += "Alignment needed at Phi=%g %s. " % (phi,Phi.unit)
        if not isnan(offset):
            s += ("Last measured offset %.3f mm " % offset)
            s += ("at Phi=%g, Z=%.3f mm." % (align_phi,align_z))
        else:
            s += "No previous information available."
    else:
        align_phi,align_z = alignment_closest_phi_z()
        offset = align_offset(align_phi,align_z)
        s += ("Using offset %.3f mm, recorded at %s=%.3f deg, Z=%.3f" %
            (offset,Spindle.name,align_phi,align_z))
    return s

def set_offset(offset):
    """Translates the sample vertically relative to the position it was
    centered."""
    while diffractometer.moving and not task.cancelled: sleep(0.05)
    diffractometer.xy = 0,offset
    while diffractometer.moving and not task.cancelled: sleep(0.05)
    diffractometer.stop()

def align_offset(phi=None,z=None):
    """Tell the position of DiffX and DiffY where the sample is aligned as
    function of Phi and DiffZ, based on ealier diffraction scans.
    Interpolate as function of phi and z."""
    from numpy import array,argsort
    
    if phi == None: phi = diffractometer.phic
    if z == None: z = diffractometer.zc
    # Load lookup table of already measured offsets.
    PHI,Z,X,Y,OFFSET = array(align_table())[0:5]
    # Interpolate
    offset = interpolate_2D(PHI,Z,OFFSET,phi,z)
    return offset

def interpolate_2D(PHI,Z,OFFSET,phi,z):
    """Perform two-dimensional interpolation of data define on a rectangular
    grid.
    PHI,Z: arrays, define grid of support points.
    OFFSET: array, defines value at support points.
    phi,z: where to interpolate
    Return value: OFFSET at (phi,z)"""
    from numpy import concatenate,mean,nan,unique,sort
    if len(OFFSET) == 0: return nan
    
    # Take into account that angles are periodic.    
    phi %= 360
    PHI %= 360
    PHI = concatenate((PHI-360,PHI,PHI+360))
    Z = concatenate((Z,Z,Z))
    OFFSET = concatenate((OFFSET,OFFSET,OFFSET))

    # Find the next smaller and larger phi.
    # If interpolation is not possible, extrapolate.
    phis = unique(PHI)
    if phi < min(phis):   phi1,phi2 = phis[0:2][0],phis[0:2][-1]
    elif phi > max(phis): phi1,phi2 = phis[-2:][0],phis[-2:][-1]
    else: phi1,phi2 = max(phis[phis<=phi]),min(phis[phis>=phi])

    # Find the next smaller and larger z for both phis.
    # If interpolation is not possible, extrapolate.
    zs1 = unique(Z[PHI==phi1])
    zs2 = unique(Z[PHI==phi2])
    if z < min(zs1):   z11,z12 = zs1[0:2][0],zs1[0:2][-1]
    elif z > max(zs1): z11,z12 = zs1[-2:][0],zs1[-2:][-1]
    else: z11,z12 = max(zs1[zs1<=z]),min(zs1[zs1>=z])

    if z < min(zs2):   z21,z22 = zs2[0:2][0],zs2[0:2][-1]
    elif z > max(zs2): z21,z22 = zs2[-2:][0],zs2[-2:][-1]
    else: z21,z22 = max(zs2[zs2<=z]),min(zs2[zs2>=z])

    # Look up the offset at the four support points.
    offset11 = mean(OFFSET[(PHI==phi1) & (Z==z11)])
    offset12 = mean(OFFSET[(PHI==phi1) & (Z==z12)])
    offset21 = mean(OFFSET[(PHI==phi2) & (Z==z21)])
    offset22 = mean(OFFSET[(PHI==phi2) & (Z==z22)])

    # Interpolate in z.
    if z12 == z11: offset1 = offset11
    else: offset1 = offset11*(z12-z)/(z12-z11) + offset12*(z-z11)/(z12-z11)
    if z22 == z21: offset2 = offset21
    else: offset2 = offset21*(z22-z)/(z22-z21) + offset22*(z-z21)/(z22-z21)
    # Interpolate in phi.
    if phi1 == phi2: offset = offset1
    else: offset = offset1*(phi2-phi)/(phi2-phi1) + offset2*(phi-phi1)/(phi2-phi1)
    return offset

def update_diffraction_profiles(PHIs=None,Zs=None):
    """Calculate the figure of merit for each image and save it to a file.
    This procedure is intented to be run a a sparate thread while the scan image are
    still being collected"""
    from numpy import sum
    if PHIs is None: PHIs = [diffractometer.phic]
    if Zs is None: Zs = sample.spot_zs

    phi = PHIs[0]
    ref_filename = param.path+"/alignment/reference_phi=%.3f.mccd" % phi
    PHI,Z,OFFSET,filenames = [],[],[],[]
    for z in Zs:
        scan_logfile = alignment_scan_dir(phi,z)+".log"
        if exists(scan_logfile):
            offset_list,filename_list = read(scan_logfile,labels="offset,filename")
            PHI += [phi]*len(filename_list)
            Z += [z]*len(filename_list)
            OFFSET += offset_list
            filenames += [param.path+"/alignment/"+f for f in filename_list]

    FOM = [nan]*len(filenames)
    processed = [False]*len(filenames)
    Nprocessed = 0
    result_files = []
    for i in range(0,len(filenames)):
        result_file = param.path+"/alignment/profile_phi=%.3f_z=%.3f.txt" % (PHI[i],Z[i])
        if not result_file in result_files: result_files += [result_file]

    image_size = ccd.filesize(align.ccd_bin_factor)

    if not (exists_file(ref_filename) and getsize(ref_filename) == image_size):
        progress("waiting for %r..." % basename(ref_filename))
    while not (exists_file(ref_filename) and getsize(ref_filename) == image_size) \
        and not task.cancelled: sleep(0.1)
    progress("%s: peak integration mask..." % basename(ref_filename))
    integration_mask = peak_integration_mask(numimage(ref_filename))
    progress("%s: peak integration mask done" % basename(ref_filename))

    while sum(processed)<len(filenames) and not task.cancelled:
        for i in range(0,len(filenames)):
            if task.cancelled: break
            if exists_file(filenames[i]) and getsize(filenames[i]) == image_size \
                and not processed[i]:
                progress("processing %3d/%d %r" % (i+2,len(filenames)+1,basename(filenames[i],1)))
                FOM[i] = sum(integration_mask*numimage(filenames[i]))
                processed[i] = True

        if sum(processed) > Nprocessed and not task.cancelled:
            progress("saving results")
            results = {}
            for i in range(0,len(FOM)):
                if not processed[i]: continue
                result_file = param.path+"/alignment/profile_phi=%.3f_z=%.3f.txt" % (PHI[i],Z[i])
                if not result_file in results: results[result_file] = "#offset\tFOM\n"
                results[result_file] += "%.3f\t%.0f\n" % (OFFSET[i],FOM[i])
            for result_file in results: file(result_file,"wb").write(results[result_file])

        Nprocessed = sum(processed)
        if sum(processed) < len(filenames):
            progress("%r/%r images found" % (sum(processed),len(filenames)))
            # Give up on the missing image files if no change for 60 s.
            processed_time = max([getmtime(f) for f in result_files if exists_file(f)])
            last_image_time = max([getmtime(f) for f in filenames if exists_file(f)])
            if time() - last_image_time > 15: break
            else: sleep(1)

    if sum(processed) < len(filenames):
        missing_files = ", ".join([basename(filenames[i],1)
            for i in range(0,len(filenames)) if not processed[i]])
        if len(missing_files)>60: msg = missing_files[0:60]+"..."
        warn("missing: "+missing_files)

def basename(pathname,level=0):
    """Ending part of a pathanme.
    level: how mane directories levels to include"""
    from os.path import basename,dirname
    s = basename(pathname)
    for i in range(0,level):
        pathname = dirname(pathname)
        s = basename(pathname)+"/"+s
    return s

def getsize(filename):
    """The length of a file in bytes or 0 if te file does not exists"""
    from os.path import getsize
    try: return getsize(filename)
    except OSError: return 0

def exists_file(pathname):
    """Like "exists" but deals with a problem related NFS attribute caching, which makes
    "exits" sometimes erronously report a file as nonexsitent, that was newly created
    from a remote machine"""
    from os.path import basename,dirname; from os import listdir
    filename = basename(pathname)
    dir = dirname(pathname)
    if dir == "": dir = "."
    try: filenames = listdir(dir)
    except OSError: return False
    return filename in filenames
        
def process_alignment_scan(phi=None,z=None):
    """Analyze series of diffraction images recorded at different sample offsets"""
    if phi == None: phi = diffractometer.phic
    if z == None: z = diffractometer.zc
    progress("processing alignment scan for phi=%.3f,z=%.3f" % (phi,z))

    align.profile = diffraction_profile(phi,z)
    if len(align.profile) == 0: return
    edge = find_edge(align.profile)
    offset = edge + align.beamsize
   
    # Save the lookup table.
    PHI,Z,X,Y,OFFSET = align_table()
    # Eliminate dupliate entries
    if len(PHI) > 0:
        PHI,Z,X,Y,OFFSET = zip(*[row for row in zip(PHI,Z,X,Y,OFFSET)
            if not allclose(row[0:2],(phi,z))])
    PHI,Z,X,Y,OFFSET = list(PHI),list(Z),list(X),list(Y),list(OFFSET)
    PHI += [phi]; Z += [z]; X += [0]; Y += [0]; OFFSET += [offset]
    set_align_table((PHI,Z,X,Y,OFFSET))
    try: merge_alignment_scans()
    except: warn("'merge_alignment_scans' failed")

    progress("processed alignment scan for phi=%.3f,z=%.3f" % (phi,z))

def align_table():
    """Lookup table for past alignemnt scans.
    Columns: Phi,DiffZ,DiffX,DiffY,offset"""
    filename = param.path+"/alignment/phi,z,x,y,offset.txt"
    try: table = read(filename)
    except: table = [[],[],[],[],[]]
    if len(table) != 5: table = [[],[],[],[],[]]
    return table

def set_align_table(table):
    """Update lookup table for past alignemnt scans,
    Columns: Phi,DiffZ,DiffX,DiffY,offset"""
    filename = param.path+"/alignment/phi,z,x,y,offset.txt"
    save(table,filename,labels="phi,z,x,y,offset")

def align_time():
    """Last ime an alignemt scan was done successfully"""
    from os import stat
    filename = param.path+"/alignment/phi,z,x,y,offset.txt"
    try: return stat(filename)[8]
    except OSError: return 0 
    
def merge_alignment_scans():
    """Generate a file containing all the alignment scans"""
    scan_dir = param.path+"/alignment"
    PHI,Z = read(scan_dir+"/phi,z,x,y,offset.txt",labels="phi,z")
    N = len(PHI)
    if N == 0: return
    z = [[]]*N
    I = [[]]*N
    n = [nan]*N
    for i in range(0,N):
        z[i],I[i] = read(scan_dir+"/profile_phi=%.3f_z=%.3f.txt" % (PHI[i],Z[i]))
    # Extra reference intensities
    Iref = [[]]*N
    for i in range(0,N): Iref[i] = I[i][0]
    # Skip first data point (reference)
    for i in range(0,N): z[i],I[i] = z[i][1:],I[i][1:]
    # Round offset to 1 um precision.
    dz = 0.001
    for i in range(0,N): z[i] = list(rint(array(z[i])/dz)*dz)
    # Sort all scans
    from numpy import argsort
    for i in range(0,N):
        order = argsort(z[i])
        z[i] = list(array(z[i])[order])
        I[i] = list(array(I[i])[order])
    # Make all scans have the same range be prepending an appending NaNs.
    zmin = inf
    for i in range(0,N): zmin = min(zmin,min(z[i]))
    for i in range(0,N):
        n = int(round((z[i][0]-zmin)/align.step))
        z[i] = [nan]*n + z[i]
        I[i] = [nan]*n + I[i]
    length = 0
    for i in range(0,N): length = max(length,len(z[i]))
    for i in range(0,N):
        z[i] = z[i] + [nan]*(length-len(z[i]))
        I[i] = I[i] + [nan]*(length-len(I[i]))
    from numpy import average,where
    z = array(z)
    za = [average(z[:,i][where(~isnan(z[:,i]))]) for i in range(length)]
    filename = scan_dir+"/profiles.txt"
    header = "Iref"
    for i in range(0,N): header += "\t%g" % Iref[i]
    save([za]+I,filename,labels=["Phi"]+PHI,header=header)
    merge_derivatives()

def merge_derivatives():
    "Generate a file containing the derivatives of all the alignment scans"
    scan_dir = param.path+"/alignment"
    PHI,Z = read(scan_dir+"/phi,z,x,y,offset.txt",labels="phi,z")
    N = len(PHI)
    if N == 0: return
    z = [[]]*N
    I = [[]]*N
    n = [nan]*N
    for i in range(0,N):
        z[i],I[i] = read(scan_dir+"/profile_phi=%.3f_z=%.3f.txt" % (PHI[i],Z[i]))
    # Calculcate derivatives.
    for i in range(0,N): 
        derivative_xy = derivative(zip(z[i],I[i]),npoints=align.npoints)
        z[i],I[i] = xvals(derivative_xy),yvals(derivative_xy)
    # Skip first data point (reference)
    for i in range(0,N): z[i],I[i] = z[i][1:],I[i][1:]
    # Round offset to 1 um precision.
    dz = 0.001
    for i in range(0,N): z[i] = list(rint(array(z[i])/dz)*dz)
    # Sort all scans
    from numpy import argsort
    for i in range(0,N):
        order = argsort(z[i])
        z[i] = list(array(z[i])[order])
        I[i] = list(array(I[i])[order])
    # Make all scans have the same range be prepending an appending NaNs.
    zmin = inf
    for i in range(0,N): zmin = min(zmin,min(z[i]))
    for i in range(0,N):
        n = int(round((z[i][0]-zmin)/align.step))
        z[i] = [nan]*n + z[i]
        I[i] = [nan]*n + I[i]
    length = 0
    for i in range(0,N): length = max(length,len(z[i]))
    for i in range(0,N):
        z[i] = z[i] + [nan]*(length-len(z[i]))
        I[i] = I[i] + [nan]*(length-len(I[i]))
    from numpy import average,where
    z = array(z)
    za = [average(z[:,i][where(~isnan(z[:,i]))]) for i in range(length)]
    filename = scan_dir+"/derivatives.txt"
    save([za]+I,filename,labels=["z"]+PHI)

# Needed by update_diffraction_profile
integration_mask = [] # used for peak integration
integration_mask_filename = "" # file from which integration_mask was generated

def update_diffraction_profile(phi=None,z=None):
    """Reduce a set of images into a one-dimensional diffraction strength profile.
    The result is saved in a file named 'alignment/profile_phi=N.NNN_z=N.NNN.txt'"""
    from numpy import sum
    if phi == None: phi = diffractometer.phic
    if z == None: z = diffractometer.zc

    profile_file = param.path+"/alignment/profile_phi=%.3f_z=%.3f.txt" % (phi,z)

    scan_logfile = alignment_scan_dir(phi,z)+".log"
    if not exists_file(scan_logfile):
        warn("%s not updated: %s not found" % \
            (basename(profile_file),basename(scan_logfile)))
        return
    try: offset = array(read(scan_logfile,labels="offset"))
    except:
        warn("%s not updated: %s corrupted" % \
            (basename(profile_file),basename(scan_logfile)))
        return
    image_files = array(read(scan_logfile,labels="filename"))
    if len(image_files) == 0:
        warn("%s not updated: %s contains no image files" % \
            (basename(profile_file),basename(scan_logfile)))
        return
    image_files = [param.path+"/alignment/"+image_files[i]
        for i in range(0,len(offset))]

    # Use image recorded through the center of the crystal as reference image
    # for all scans at the same orientation.
    ref_image_file = param.path+"/alignment/reference_phi=%.3f.mccd" % phi
    if not exists_file(ref_image_file):
        warn("%s not updated: reference image %s not found" % \
            (basename(profile_file),ref_image_file))
        return

    # Reuse data from existing diffraction profile.
    filenames = [ref_image_file]+image_files

    last_modified = max([getmtime(f) for f in filenames if exists_file(f)])
    if exists(profile_file) and getmtime(profile_file) > last_modified:
        info("%r is up to date" % basename(profile_file))
        return
    
    global integration_mask,integration_mask_filename
    if ref_image_file != integration_mask_filename:
        # Use the reference image for the spot positions.
        Iref = numimage(ref_image_file)
        progress("Peak integration mask")
        integration_mask = peak_integration_mask(Iref)
        integration_mask_filename = ref_image_file

    progress("Figure of merit")
    FOM = array([nan]*len(offset))
    for i in range(0,len(offset)):
        image_file = image_files[i]
        if not exists(image_file):
            FOM[i] = nan
        else:
            I = numimage(image_file)
            FOM[i] = sum(integration_mask*I)

    # Eliminate bad data points.
    bad = isnan(FOM)
    offset,FOM = offset[~bad],FOM[~bad]

    # Save the profile.
    progress("Saving")
    save([offset,FOM],profile_file,labels="offset,FOM")
    
def diffraction_profile(phi=None,z=None):
    """One-dimensional diffraction strength profile.
    Returns list of (x,y)-tuples."""    
    if phi == None: phi = diffractometer.phic
    if z == None: z = diffractometer.zc
    update_diffraction_profile(phi,z)

    profile_file = \
        param.path+"/alignment/profile_phi=%.3f_z=%.3f.txt" % (phi,z)
    offset,FOM = array([]),array([])
    if exists(profile_file):
        try: offset,FOM = array(read(profile_file))
        except: warn("ignoring corrupted file '%s'" % basename(profile_file))

    # Skip first data point (reference image)
    offset,FOM = offset[1:],FOM[1:]

    # Generate list of x,y pairs.
    from numpy import argsort
    order = argsort(offset)
    return zip(offset[order],FOM[order])

def diffraction_Iref(phi=None,z=None):
    """Reference intensity of diffraction strength profile."""    
    if phi == None: phi = diffractometer.phic
    if z == None: z = diffractometer.zc
    update_diffraction_profile(phi,z)

    profile_file = \
        param.path+"/alignment/profile_phi=%.3f_z=%.3f.txt" % (phi,z)
    offset,FOM = array([]),array([])
    if exists(profile_file):
        try: offset,FOM = array(read(profile_file))
        except: warn("ignoring corrupted file '%s'" % basename(profile_file))

    # The reference intensity is the first scan point in the file.
    if len(FOM) == 0: return nan
    return FOM[0]

def alignment_scan_has_edge(phi=None,z=None):
    """Determines wether a diffraction scan contains sufficient information to determine
    the edge of the crystal reliably."""    
    if phi == None: phi = diffractometer.phic
    if z == None: z = diffractometer.zc
    profile = diffraction_profile(phi,z)
    Iref = diffraction_Iref()
    return has_edge(profile,Iref)
            
def has_edge(profile,Iref):
    """Determine wether a diffraction scan contains sufficient information to determine
    the edge of the crystal reliably.
    profile: list of (x,y)-tuples
    Iref: reference_intensity"""
    if len(profile) < 2: return False
    slope_profile = derivative(profile,npoints=align.npoints)
    if len(slope_profile) < 2: return False
    I = yvals(profile)
    slope = yvals(slope_profile)
    return slope[-1] < slope[-2] and I[-2] > 0.1*Iref    

def test_edge_finder():
    """test the 'has_edge' function
    Prints table to stdout"""
    zs = sample.spot_zs
    phis = range(0,360,30)
    for phi in phis:
        for z in zs:
            print("%g %.3f %r" % (phi,z,alignment_scan_has_edge(phi,z)))
            

def find_edge(profile):
    """Find the point of maximum slope, with the slope averaged over
    align.npoints, and extrapolate down to the baseline.
    profile = list of (x,y)-tuples"""
    if len(profile) == 0: return nan
    slope = derivative(profile,npoints=align.npoints)
    ##x = x_at_ymax(slope)
    x = x_at_first_max_of_derivative(profile)
    dydx = yval(slope,x)
    y = yval(profile,x)
    y0 = min(yvals(profile))
    if dydx == 0: return nan
    x0 = x - (y-y0)/dydx
    # Sanity check: The edge must be inside the scan range.
    xmin,xmax = min(xvals(profile)),max(xvals(profile))
    x0 = clip(x0,xmin,xmax)
    return x0

def x_at_first_max_of_derivative(profile):
    """The first maximum of the derivative of "profile" where the intensity is
    higher that 5% of the maximum intensity.
    profile: list of (offset,I) pairs"""
    slope_xy = derivative(profile,npoints=align.npoints)

    x,I = xvals(profile),yvals(profile)
    slope_x,slope = xvals(slope_xy),yvals(slope_xy)
    # "profile" and "slope_xy" have different x scale
    i = 0
    while i<len(x) and len(slope_x)>0 and x[i]<slope_x[0]: i+= 1
    x,I = x[i:],I[i:]
    Iref = max(array(I)) if len(I)>0 else nan
    for i in range(3,min(len(I),len(slope))):
        if slope[i] < slope[i-1] and I[i-1] > 0.05*Iref: break
    x_at_max = x[i] if i<len(x) else nan
    return x_at_max

def estimate_scan_range(phi=None):
    """This is to speed to the edge finder by using prior information from
    previous edge scans, to minimize the scan range.
    Return (start,end) in units of mm.
    """
    if phi == None: phi = diffractometer.phic
    scan_dir = join(param.path,"alignment")
    phis = xvals(read_xy(join(scan_dir,"phi,offset.txt")))
    if len(phis) < align.last_scans_use:
        return align.start,align.end
    phis = phis[-align.last_scans_use:]
    phis.sort()
    phi_offset = []
    for angle in phis:
        profile = read_xy(join(scan_dir,"profile_%g.txt" % angle))  
        offset = x_at_max_slope(profile)
        phi_offset += [(angle,offset)]
    # Extend the phi range beyond [0,360].
    if len(phi_offset) > 0:
        first = (phi_offset[-1][0]-360,phi_offset[-1][1])
        last =   (phi_offset[0][0]+360,phi_offset[0][1])
        phi_offset = [first] + phi_offset + [last]
    offset = interpolate(phi_offset,phi)
    start = offset + 0.5*(align.min_scanpoints-1) * align.step
    # Do not go outside the full range.
    if start > align.start: start = align.start
    # Round start to the next multiple of step.
    start = align.start + round((start-align.start)/align.step)*align.step 
    end = start - (align.min_scanpoints-1) * align.step
    return start,end

def x_at_max_slope(xy_data):
    """Find the point of maximum slope, with the slope averaged over
    align.npoints."""
    if len(xy_data) == 0: return nan
    slope = derivative(xy_data,npoints=align.npoints)
    return x_at_ymax(slope)

def interpolate(xy_data,xval):
    "Linear interpolation"
    x = xvals(xy_data); y = yvals(xy_data); n = len(xy_data)
    if n == 0: return nan
    if n == 1: return y[0]
    
    for i in range (1,n):
        if x[i]>xval: break
    if x[i-1]==x[i]: return (y[i-1]+y[i])/2. 
    yval = y[i-1]+(y[i]-y[i-1])*(xval-x[i-1])/(x[i]-x[i-1])
    return yval
    
def x_at_ymax(xy_data):
    if len(xy_data) < 1: return nan
    x_at_ymax = xy_data[0][0]; ymax = xy_data[0][1] 
    for i in range (0,len(xy_data)):
        if xy_data[i][1] > ymax: x_at_ymax = xy_data[i][0]; ymax = xy_data[i][1]
    return x_at_ymax

def invert(xy_data):
    "takes the negative of y of yx_data"
    xy_inverted = []
    for i in range (0,len(xy_data)): xy_inverted.append((xy_data[i][0],-xy_data[i][1]))
    return xy_inverted 

def yval (xy_data,x0):
    """xy_data = list of (x,y)-tuples.
    Pairs (x,y[x]) are taken as support points for a function which is evaluated at 'x'. Linear 
    Interpolation is used.
    """
    N = len(xy_data); x = xvals(xy_data); y = yvals(xy_data)
    if N<1: return nan
    if N==1: return y[0]
    i=0
    if x[0] <= x[N-1]:
        while i+1<N-1 and x0>x[i+1]: i=i+1
    else:
        while i+1<N-1 and x0<=x[i+1]: i=i+1
    l = (x0-x[i])/(x[i+1]-x[i])
    return (1-l)*y[i]+l*y[i+1]

def xvals(xy_data):
    "xy_data = list of (x,y)-tuples. Teturns list of x values only."
    xvals = []
    for i in range (0,len(xy_data)): xvals.append(xy_data[i][0])
    return xvals  

def yvals(xy_data):
    "xy_data = list of (x,y)-tuples. Returns list of y values only."
    yvals = []
    for i in range (0,len(xy_data)): yvals.append(xy_data[i][1])
    return yvals  

def derivative(xy_data,npoints):
    """calculates the slope of xy data averaged of a number of points given by npoints
    xy_data = list of (x,y)-tuples
    """
    derivative=[]
    
    for j in range (0,len(xy_data)-npoints):
        sumx=0; sumy=0
        for i in range(j,j+npoints): sumx+=xy_data[i][0]; sumy+=xy_data[i][1]
        xmean = sumx/npoints; ymean = sumy/npoints
        sumxy=0; sumx2=0
        for i in range(j,j+npoints):
            sumxy+=(xy_data[i][0]-xmean)*(xy_data[i][1]-ymean)
            sumx2+=pow(xy_data[i][0]-xmean,2)
        if sumx2 != 0: dydx = sumxy/sumx2
        else: dydx = 0
        derivative.append((xmean,dydx))

    return derivative

    # (Warning: The following code might crash occasionally, because there is no bounds
    # checking on the index "i" of the array "slope". F .Schotte, Oct 26, 2014)

    # Zero out derivative beyond its first maximum.
    I = yvals(xy_data)
    Iref = array(I).max()
    slope = yvals(derivative)
    for i in range(3,len(I)):
        if slope[i] < slope[i-1] and I[i-1] > 0.05*Iref:
            break

    test = []
    for j in range(0,len(I)-npoints):
        if j <=  i:
            test.append(derivative[j])
        else: test.append((derivative[j][0],0))

    return test

def print_xy(xy_data):
    """(x,y) tuples as two columns.
    Prints table to stdout."""
    for i in range(0,len(xy_data)): 
         print("%g\t%g" % (xy_data[i][0],xy_data[i][1]))

def save_xy(xy_data,filename):
    """Write (x,y) tuples as two-column tab separated ASCII file."""
    if not exists (dirname(filename)): makedirs (dirname(filename))
    output = file(filename,"w")
    for i in range(0,len(xy_data)):
        output.write("%g\t%g\n" % (xy_data[i][0],xy_data[i][1]))

def read_xy(filename):
    """Reads two two-column ASCII file and returns as list of floating point
    [x,y] pairs"""
    try: infile = file(filename)
    except: return []
    data = []
    line = infile.readline()
    while line != '':
        try:
            cols = line.split()
            x = float(cols[0]); y = float(cols[1])
            data.append([x,y])
        except ValueError: pass
        line = infile.readline()
    return data

# Sample Translation

def translation_hardware_triggered():
    """Translate the sample during data collection"""
    return translate.mode != "off" and translate.hardware_triggered

def translate_sample():
    """Position the sample for the beginning of an image acquisition"""
    if translate.mode in ("off","linear stage"): return
    x,y,z = translation_after_image_xyz(task.image_number)
    DiffX.value,DiffY.value,DiffZ.value = x,y,z
    while (DiffX.moving or DiffY.moving or DiffZ.moving) and not task.cancelled:
        sleep (0.05)

def translation_after_image_xyz(image_number):
    """for "after image" translation mode. Return value: (x,y,z)"""
    if "grid scan" in translate.mode:
        x,y,z = grid_position(image_number)
    else:
        z = translation_after_image_z(image_number)
        x,y = translation_xy(z,angle(image_number))
    return (x,y,z)

def grid_position(image_number):
    """For photocrystallography chip"""
    i = image_number
    i = i-1 # convert from 1-based to 0-based index
    i = int(floor(i/translate.after_images))
    x,y,z = grid.point(i) # SampleX,SampleY,SampleZ
    dx,dy,dz = diffractometer_xyz((x,y,z))
    return dx,dy,dz

def diffractometer_xyz((x,y,z)):
    """Transform from hardwre to diffractometer coordinates
    (x,y,z): hardware coordinates (SampleX,SampleY,SampleZ)
    return value: (x,y,z) tuple"""
    dx,dy = diffractometer.diffractometer_xy(x,y,SamplePhi.value)
    dz = diffractometer.diffractometer_z(z)
    return dx,dy,dz

def translation_after_image_z(image_number):
    """Starting point defined by "after image" translation
    image_number: 1-based index"""
    if not ("after image" in translate.mode or
            "during image" in translate.mode or
            "continuous" in translate.mode):
        z = nan # Do not move. Keep current position.
    elif not "after image" in translate.mode: z = min(sample.zs)
    else:
        i = image_number
        i = i-1 # convert from 1-based to 0-based index
        # Return to starting position after how many series?
        nrepeat = translate.return_after_series * nimages_per_orientation()
        i = i % nrepeat
        # After how many images to translate?
        i = int(floor(i/translate.after_images))
        nspots = translation_after_image_nspots()
        i = i % nspots
        m = translate.after_image_interleave_factor
        i = interleaved_order(i,m,nspots)
        z = min(sample.zs) + i*translation_after_image_zstep()
    return z

def translation_after_image_plot():
    n = nimages_per_timeseries()
    N = range(1,n+1)
    Z = [translation_after_image_z(i+1) for i in range(0,n)]
    from Plot import Plot
    Plot(zip(N,Z),title="Sample Translation",xaxis="image #",yaxis="DiffZ[mm]")

def translation_after_image_nspots():
    """Number of unique spots for 'after image' sampel translation
    defined by marked range in microscope camera"""
    n = translate.after_image_nspots
    n = max(int(n),1)
    return n

def set_translation_after_image_nspots(n):
    """Number of unique spots for 'after image' sampel translation
    defined by marked range in microscope camera"""
    n = max(int(n),1)
    translate.after_image_nspots = n

def translation_after_image_zstep():
    """How much to translation the sampel after each image?"""
    if len(sample.zs) == 0: return nan
    full_range = max(sample.zs) - min(sample.zs)
    if translate.after_image_nspots > 1:
        zstep = full_range/(translate.after_image_nspots-1)
    else: zstep = 0
    return zstep

def set_translation_after_image_zstep(zstep):
    """How much to translation the sampel after each image?"""
    full_range = max(sample.zs) - min(sample.zs)
    if zstep > 0:
        translate.after_image_nspots = int(rint(full_range/zstep))+1
    else: translate.after_image_nspots = 1

def translation_xy(z,phi):
    """Matching DiffX,DiffY positionion for a given DiffZ position"""
    if not ("after image" in translate.mode or
            "during image" in translate.mode or
            "continuous" in translate.mode):
        x,y = nan,nan # nan = Do not move. Keep current position.
    else:
        s = sample.samples[0]
        cx1,cy1,cz1 = diffractometer.xyz_of_sample(s["start"],phi)
        cx2,cy2,cz2 = diffractometer.xyz_of_sample(s["end"],phi)
        x = interpolate([[cz1,cx1],[cz2,cx2]],z)
        y = interpolate([[cz1,cy1],[cz2,cy2]],z)
        if align.enabled:
            offset = align_offset(phi,z)
            if not isnan(offset): y += offset    
    return (x,y)

def translation_during_image_stroke():
    """Sample translation during te aquisition of an image in mm"""
    if "during image" in translate.mode:
        n = translation_during_image_unique_nspots()
        return max(n-1,0) * sample.z_step
    elif "continuous" in translate.mode: return 0 # Update this!
    else: return 0

def translation_during_image_unique_zs(image_number):
    """for 'during image' translation"""
    z0 = translation_after_image_z(image_number)
    if "during image" in translate.mode:
        dz = sample.z_step
        n = translation_during_image_unique_nspots()
        return [z0 + dz*i for i in range(0,n)]
    else: return [z0]

def translation_during_image_unique_nspots():
    """How many spots are visited in 'during image' translation
    couinting each position only once."""
    if not "during image" in translate.mode: return 1
    if not "after image" in translate.mode: return len(sample.zs)
    return translate.during_image_nspots

def translation_during_image_set_unique_nspots(n):
    """How many spots are visited in 'during image' translation
    couinting each position only once."""
    translate.during_image_nspots = n

def translation_during_image_nspots(image_number):
    """How many spots are visited when collecting an image
    in "during image" translation mode?"""
    if translate.single: return npulses(image_number)
    nunique = translation_during_image_unique_nspots()
    n = int(ceil(float(npulses(image_number))/nunique))
    return int(ceil(float(npulses(image_number))/n))

def translation_during_image_pulses_per_spot(image_number,spot_number):
    """How many X-ray pulses send to each spot
    when using "during image" translation mode?"""
    if translate.single: n = 1
    else:
        nunique = translation_during_image_unique_nspots()
        n = int(ceil(float(npulses(image_number))/nunique))
    return max(0,min(npulses(image_number) - n * spot_number,n))

def translation_during_image_xyz(image_number,spot_number):
    """Where does the sample need to be translated as function of pulse number
    when using "during image" translation mode?
    image_number: 1-based index
    spot_number: 0-based index
    Return value: DiffX,DiffY,DiffZ position in mm.
    """
    z = translation_during_image_z(image_number,spot_number)
    x,y = translation_xy(z,angle(image_number))
    return x,y,z

def translation_during_image_z(image_number,spot_number):
    """Tell where the sample needs to translated as function of pulse number
    when using "during image" translation mode.
    Return DiffZ position in mm
    image_number: 1-based index
    spot_number: 0-based index"""
    if not "during image" in translate.mode: return diffractometer.zc
    i = spot_number
    zs = translation_during_image_unique_zs(image_number)
    i = i % len(zs)
    m = translate.interleave_factor
    i = interleaved_order(i,m,len(zs))
    return zs[i]

def translation_during_image_zs(image_number):
    """Tell where the sample needs to translated as function of pulse number
    when using "during image" translation mode.
    Return DiffX,DiffY,DiffZ position in mm
    image_number: 1-based index"""
    n = translation_during_image_nspots(image_number)
    return [translation_during_image_z(image_number,i) for i in range(0,n)]

def interleaved_order(i,m,n):
    """Permute the order 0...n, to m passes.
    i: 0-based index
    m: interleave factor
    n: total number"""
    return interleaved_sequence(m,n)[i]

def interleaved_sequence(m,n):
    """Permute the order 0...n into m passes.
    m: interleave factor
    n: total number"""
    from numpy import arange
    l = int(ceil(n/float(m)))
    order = arange(0,l*m).reshape(l,m).T.flatten()
    order = order[order<n]
    return order

def pump_setup():
    """Prepare for hardwre trigged pumping"""
    axis_number = 4 ##PumpA.axis_number
    if pump.enabled and pump.hardware_triggered:
        transon.value = 1 # Tell timing system to generate trigger pulses
        triggered_motion.PumpA.enabled = 1
        triggered_motion.PumpA.trigger_divisor = options.npulses*pump.frequency
        triggered_motion.PumpA.relative_move = 1
        triggered_motion.PumpA.positions = [pump.step]
        triggered_motion.enabled = True
        ##triggered_motion.step_count = 1
    else: 
        try: triggered_motion.axis_enabled[axis_number] = 0
        except: pass

def pump_sample_if_needed():
    """Execute a syringe pump command, if needed for the NEXT image."""
    if not pump.enabled or pump.hardware_triggered: return
    if not pump_needed_after_image(task.image_number): return
    progress("Pumping...")
    PumpA.command_value += pump.step
    while PumpA.moving and not task.cancelled: sleep(0.1)
    progress("Pumping... done")

def pump_needed_after_image(image_number):
    """Tell whether the syringe pump should be operated before the given
    image_number."""
    if not pump.enabled: return False
    # pump.frequency defines every how many image the pumping needs to be
    # performed.
    R = round(image_number % pump.frequency)
    return (R == 0)
    
def pump_summary():
    """This is what is written into the log file"""
    if not pump.enabled: return "disabled"
    return "step %g" % pump.step

def xray_beam_check_after(starting_image_number):
    """After which image number perform the next beam check?
    image_number: 1-based index"""
    if xraycheck.enabled:
        period = collection_variable_period(xraycheck.run_variable)        
        n = int(round_up(starting_image_number,period))
    else: n = inf
    return n

def xray_beam_check_before(image_number):
    """Perform an beam chech before this image?
    image_number: 1-based index"""
    if xraycheck.enabled:
        period = collection_variable_period(xraycheck.run_variable)        
        check = (image_number % period == 1) and image_number > 1
    else: check = False
    return check

def xray_beam_check_summary():
    """Summary for log file."""
    if not xraycheck.enabled: return "disabled"
    s = 'run after series of "%s"' % xraycheck.run_variable
    return s

def run_xray_beam_check(apply_correction=False):
    """Correct X-ray beam position drift"""
    if task.cancelled: return    
    action = task.action; task.action = "X-Ray Beam Check"
    generate_autorecovery_restore_point("Beamcheck",
        ("MirrorV","MirrorH","shg","svg"))

    if xraycheck.type == "beam position":
        from xray_beam_position_check import xray_beam_position_check
        xray_beam_position_check.acquire_image()
        if apply_correction: xray_beam_position_check.apply_correction()
    else: # "I0"
        from xray_beam_check import xray_beam_check
        xray_beam_check.perform_x_scan()
        if apply_correction: xray_beam_check.apply_x_correction()
        xray_beam_check.perform_y_scan()
        if apply_correction: xray_beam_check.apply_y_correction()

    xraycheck.comment = ""
    save_settings()
    clear_autorecovery_restore_point()
    task.action = action

def laser_beamcheck_needed():
    """Tell whether beam position drift should be corrected
    before the current image"""
    if not lasercheck.enabled: return False
    if not laser_enabled(): return False # Not needed when not using the laser.
    
    # Only optimize the beamline before the beginning of a time series.
    if lasercheck.at_start_of_time_series:
        if orientation_image_number(task.image_number) != 0: return False 

    if time() - lasercheck.last > lasercheck.interval: return True
    else: return False

def laser_beamcheck(apply_correction=True):
    """Correct laser beam position drift.
    This reads an image if thw laser beam profile from  CCD camera
    measures te centered position and applies corrective action by moving the
    LaserX and LaserZ motors.
    """
    from beam_profiler import acquire_image,xy_projections,FWHM,CFWHM,SNR,ROI
    from PIL import Image
    global lasercheck_image

    if task.cancelled: return    
    action = task.action; task.action = "Laser Beam Check"

    if options.open_laser_safety_shutter:
        lasercheck.comment = "Opening laser shutter..."
        open_laser_safety_shutter()

    # Record the current settings to restore them after the optimization is
    # completed.
    old_laserx = LaserX.value
    old_laserz = LaserZ.value
    old_tmode = tmode.value
    old_waitt = timing_system.waitt.value
    old_lxd = timing_system.lxd.value
    old_laseron = laseron.value
    old_mson = mson.value
    old_VNFilter = VNFilter.command_value
    old_illuminator_on = illuminator_on.value

    generate_autorecovery_restore_point("Laser Beamcheck",["LaserX","LaserZ",
        "tmode","waitt","lxd","laseron","mson","VNFilter"]+
        lasercheck.park_motors)

    # Make sure the sample illuminator is not obscuring the beam profile camera.
    if options.use_illuminator:
        illuminator_on.value = False
        lasercheck.comment = "Retracting illuminator..."
        wait_for("not illuminator_on.moving",timeout=1)
    
    if lasercheck.retract_sample:
        # In order to spare the sample, move it out of the X-ray beam and turn off
        # the laser firing.
        laser_beamcheck_remember_sample_pos()
        lasercheck.comment = "Retracting sample..."
        laser_beamcheck_goto_park_pos()
    
    # In order to get a well-defined beam profile the laser needs to be triggered
    # at sufficient repetition rate.
    lasercheck.comment = "Attenuating..."
    VNFilter.value = lasercheck.attenuator
    while VNFilter.moving and not task.cancelled: sleep (0.1)

    timing_system.lxd.value = 0 # to make sure it is compatible with rep rate

    timing_system.waitt.value = 1.0/lasercheck.reprate
    # When chainging the repetiton rate, the new rate does not take effect
    # immediately. The change is delayed by up to one cycle of the previous
    # waiting time. (Rob Henning, 21 Jun 2010)
    sleep(old_waitt)

    mson.value = 0 # turn off X-ray beam by disable ms shutter opening
    tmode.value = 0 # continuous mode
    laseron.value = 1 # fire laser

    lasercheck.comment = "Acquiring image..."
    image = acquire_image() # Get a beam profile image from the CCD camera. 
    lasercheck.comment = "Acquiring image...done"
    lasercheck.zprofile,lasercheck.xprofile = xy_projections(image)
    lasercheck_image = ROI(image)
    lasercheck.last = time()

    sum_x = 0.0; sum_z = 0.0; sum_SN = 0.0; n = 0
    # Make sure that the profile is meaured with sufficient signal-to-noise
    # ratio before attempting to run the optimization.
    signal_to_noise = min(SNR(lasercheck.zprofile),SNR(lasercheck.xprofile))
    if signal_to_noise > lasercheck.signal_to_noise:
        sum_z += CFWHM(lasercheck.zprofile)
        sum_x += CFWHM(lasercheck.xprofile)
        sum_SN += signal_to_noise
        n += 1

    if signal_to_noise > lasercheck.signal_to_noise:
        # Average the center positions
        N = lasercheck.naverage
        while n < N:
            if task.cancelled: break
            lasercheck.comment = "Averaging %d/%d images..." % (n+1,N)
            image = acquire_image()
            lasercheck.zprofile,lasercheck.xprofile = xy_projections(image)
            signal_to_noise = min(SNR(lasercheck.zprofile),SNR(lasercheck.xprofile))
            if signal_to_noise > lasercheck.signal_to_noise:
                sum_z += CFWHM(lasercheck.zprofile)
                sum_x += CFWHM(lasercheck.xprofile)
                sum_SN += signal_to_noise
                n += 1
            lasercheck_image = ROI(image)
            lasercheck.last = time()
        z = sum_z/n
        x = sum_x/n
        signal_to_noise = sum_SN/n
        new_laserz = LaserZ.value - z
        new_laserx = LaserX.value - x
        lasercheck.comment = "Average error %.3f, %.3f mm, " % (z,x)
        lasercheck.comment += "signal/noise: %.3g. " % (signal_to_noise)
        if apply_correction:
            LaserZ.value = new_laserz
            LaserX.value = new_laserx
            lasercheck.comment += "Change: "
            lasercheck.comment += \
                "LaserZ from %.3f to %.3f, " % (old_laserz,new_laserz)
            lasercheck.comment += \
                "LaserX from %.3f to %.3f mm " % (old_laserx,new_laserx)
            while (LaserZ.moving or LaserZ.moving) and not task.cancelled:
                sleep (0.1)
    else: 
        lasercheck.comment = "Insufficient signal/noise (%g<%g)" % \
            (signal_to_noise,lasercheck.signal_to_noise)

    lasercheck.last_image = param.path+"/beam profile.png"
    if not exists(dirname(lasercheck.last_image)):
        makedirs(dirname(lasercheck.last_image))
    lasercheck_image.save(lasercheck.last_image)

    logfile = param.path+"/laser_beamcheck.log"
    timestamp = strftime("%d %b %y %H:%M",localtime(lasercheck.last))
    file(logfile,"a").write(timestamp+" "+lasercheck.comment+"\n")    
    log_comment("Laser Beam check: "+lasercheck.comment)
    save_settings()

    # Restore the settings to their value before the optimization.
    lasercheck.comment += " - Restoring settings"
    tmode.value = old_tmode
    timing_system.waitt.value = old_waitt
    timing_system.lxd.value = old_lxd
    laseron.value = old_laseron
    mson.value = old_mson
    VNFilter.value = old_VNFilter
    if options.use_illuminator:
        illuminator_on.value = old_illuminator_on

    if lasercheck.retract_sample: laser_beamcheck_goto_sample_pos()

    while VNFilter.moving and not task.cancelled: sleep (0.1)
    lasercheck.comment = lasercheck.comment.replace(" - Restoring settings","")

    if not task.cancelled: clear_autorecovery_restore_point()
    else: trigger_autorecovery()

    task.action = action

def laser_beamcheck_remember_park_pos():
    """Make the current position the one to go in
    'laser_beamcheck_goto_park_pos'."""
    lasercheck.park_positions = []
    for motor_name in lasercheck.park_motors:
        motor = eval(motor_name)
        lasercheck.park_positions += [motor.command_value]
    
def laser_beamcheck_remember_sample_pos():
    """Make the current position the one to go in
    'laser_beamcheck_goto_sample_pos'."""
    lasercheck.sample_position = []
    for motor_name in lasercheck.park_motors:
        motor = eval(motor_name)
        lasercheck.sample_position += [motor.command_value]
    
def laser_beamcheck_goto_park_pos():
    """Move the sample out of the laser beam.
    Needed before running a laser beam check."""
    for i in range(0,len(lasercheck.park_motors)):
        motor = eval(lasercheck.park_motors[i])
        if i >= len(lasercheck.park_positions): break
        motor.value = lasercheck.park_positions[i]
        while motor.moving and not task.cancelled: sleep (0.1)
        if task.cancelled: motor.stop(); break

def laser_beamcheck_goto_sample_pos():
    """Return the sample to the position for data collection.
    Needed before running a laser beam check."""
    # The motors need to be moved in reverse order, compared to retracting
    # the sample.
    for i in range(len(lasercheck.park_motors)-1,-1,-1):
        motor = eval(lasercheck.park_motors[i])
        if i >= len(lasercheck.sample_position): break
        motor.value = lasercheck.sample_position[i]
        while motor.moving and not task.cancelled: sleep (0.1)
        if task.cancelled: motor.stop(); break            

def laser_beamcheck_park_summary():
    """Summarize the motors to move, before running a laser beam check."""
    s = ""
    N = min(len(lasercheck.park_motors),len(lasercheck.park_positions))
    for i in range(0,N):
        s += "%s: %g, " % (lasercheck.park_motors[i],lasercheck.park_positions[i])
    return s.rstrip(", ")

def timing_check_needed():
    """Tell whether beam position drift should be correected
    before the current image"""
    if not timingcheck.enabled: return False
    if not laser_enabled(): return False
    
    # Run only before the beginning of a time series.
    if timingcheck.at_start_of_time_series:
        if orientation_image_number(task.image_number) != 0: return False 

    if time() - timingcheck.last > timingcheck.interval: return True
    else: return False

def timing_check_summary():
    """Summary for log file."""
    if not timingcheck.enabled: return "disabled"
    s = "repeat every "+time_string(timingcheck.interval)
    if timingcheck.at_start_of_time_series:
        s += ", only at start of time series"
    if timingcheck.retract_sample:
        s += ", retracting sample by %g mm " % timingcheck.retract_sample
        s += "using motor %s" % timingcheck.sample_motor
    return s    

def run_timing_check(apply_correction=True):
    """This check and correct laser-to-X-ray timing drift"""
    # This calls an EPICS state notation code program called "BeamCheck"
    # written by Tim Graber, running on the server "everest".
    # This program used the Pulsed X-ray signal of the I0 PIN diode,
    # recorded by the Wavesurfer oscilloscope.
    if task.cancelled: return    
    action = task.action; task.action = "Timing Check"

    motors = "tmode","waitt","lxd","laseron","ChopX","ChopY","hscd","VNFilter"
    if timingcheck.sample_motor: motors += [timingcheck.sample_motor]
    generate_autorecovery_restore_point("Timing Check",motors)

    if options.wait_for_beam:
        timingcheck.comment = "Opening X-ray Shutter..."
        wait_for_beam()
    if options.open_laser_safety_shutter:
        timingcheck.comment = "Opening Laser Shutter..."
        open_laser_safety_shutter()

    # Record the current settings to restore them after the optimization is
    # completed.
    old_xoscton = xoscton.value
    old_xray_shutter_enabled = Ensemble_SAXS.xray_shutter_enabled
    old_tmode = tmode.value
    old_waitt = timing_system.waitt.value
    old_lxd = timing_system.lxd.value
    old_laseron = laseron.value
    old_chopx = ChopX.command_value
    old_chopy = ChopY.command_value
    old_chopper_phase = timing_system.hsc.delay.value
    if timingcheck.sample_motor:
        sample_motor = eval(timingcheck.sample_motor)
        old_sample_pos = sample_motor.command_value
    old_VNFilter = VNFilter.command_value
    
    # In order to spare the sample, move it out of the X-ray beam and
    # attenuate the laser beam to minimum power.
    if timingcheck.sample_motor and timingcheck.retract_sample:
        timingcheck.comment = "Retracting sample..."
        sample_motor.value += timingcheck.retract_sample
        while sample_motor.moving and not task.cancelled: sleep (0.1)
    timingcheck.comment = "Attenuating laser beam at sample..."
    VNFilter.value = timingcheck.attenuator_angle
    while VNFilter.moving and not task.cancelled: sleep (0.1)

    # If the chopper height is variable, use the maximum number of bunches per
    # pulse for the optimization (for example use 11 bunches rather than 1.)
    if collection_variable_enabled("chopper_mode"): set_chopper_mode(chopper_mode_of_timepoint(0))

    xoscton.value = 1
    Ensemble_SAXS.xray_shutter_enabled = True
    laseron.value = 1
    ##timing_system.waitt.value = 0.024
    timing_system.lxd.value = 0
    ##tmode.value = 0

    # Make sure that there is an X-ray signal before attempting to run
    # the optimization.
    # The X-ray intensity should be at least 20% of the value recorded as
    # reference.
    # Average for 1 s (10 samples at 10 Hz)
    xray_pulse.start()
    start = time()
    while time()-start < 1 and not task.cancelled: sleep (0.1) 
    offset = diagnostics_xray_offset()
    xray1 = (xray_pulse.average-offset) / (diagnostics.xray_reference-offset)

    if not task.cancelled:
        if xray1 > timingcheck.min_intensity:
            # Adjust the time scale of the oscilloscope such that both laser
            # and X-ray pulses are within the recorded time window.
            # The X-ray pulse is at the trigger point T=0 in the middle of the
            # window the laser pulse preceeds is by the nominal time delay
            # specified by timing_system.lxd.value.
            actual_delay.time_range = diagnostics.min_window

            # Measure for 10 seconds.
            actual_delay.start()
            start = time()
            while time()-start < 10 and not task.cancelled:
                sleep (0.1)
                t  = actual_delay.average
                sdev = actual_delay.stdev
                N = actual_delay.count
                err = sdev/sqrt(N-1)
                timingcheck.comment = \
                    "Timing error %s, sdev %s, %s samples, sampling error %s" % \
                    (time_string(t),time_string(sdev),N,time_string(err))
            # Sanity check.
            max_sdev = 70e-12
            OK = (not task.cancelled and not isnan(t) and sdev < max_sdev)
            if isnan(t): timingcheck.comment = "Measurement failed"
            if sdev > 70e-12:
                timingcheck.comment = "Jitter of measurement too high (%s < %s)" % \
                    (time_string(sdev),time_string(max_sdev))
            # Apply correction
            if OK and apply_correction and abs(t) > 10e-12 and abs(t) > 2*err:
                offset0 = timing_system.lxd.offset
                timing_system.lxd.define_value(t)
                # Resolution oftiming_system.lxd. is 10 ps. Define the closes possible value to 0
                # as 0.
                timing_system.timing_system.lxd.value = 0
                timing_system.lxd.define_value(0)
                correction = timing_system.lxd.offset - offset0
                timingcheck.comment += " - Correction: %s" % time_string(correction)
        else: 
            timingcheck.comment = "X-ray intensity too low (%.3g < %g)" % \
                (xray1,timingcheck.min_intensity)

    if task.cancelled: timingcheck.comment = "Cancelled"
    
    # Restore the settings to their value before the optimization.
    comment = timingcheck.comment
    timingcheck.comment += " - Restoring settings..."

    xoscton.value = old_xoscton
    Ensemble_SAXS.xray_shutter_enabled = old_xray_shutter_enabled
    tmode.value = old_tmode
    timing_system.waitt.value = old_waitt
    timing_system.lxd.value = old_lxd
    laseron.value = old_laseron
    if timingcheck.sample_motor: sample_motor.value = old_sample_pos
    VNFilter.value = old_VNFilter
    ChopX.value = old_chopx
    ChopY.value = old_chopy
    timing_system.hsc.delay.value = old_chopper_phase

    if timingcheck.sample_motor:
        while sample_motor.moving and not task.cancelled: sleep (0.1)
    while VNFilter.moving and not task.cancelled: sleep (0.1)

    if collection_variable_enabled("chopper_mode"):
        set_chopper_parameters(old_chopx,old_chopy,old_chopper_phase)

    timingcheck.comment = comment

    # Record the last time the optimization was done.
    timingcheck.last = time()
    save_settings()
    log_comment("Timing check: "+timingcheck.comment)

    clear_autorecovery_restore_point()
    task.action = action

def sample_photo_needed(image_number=None):
    """Acquire a sample photo?"""
    if image_number is None: image_number = task.image_number
    if not sample_photo.enabled: return False
    # Acquire a sample photo at the beginning of every series.
    at_start_of_series = orientation_number(image_number) != orientation_number(image_number-1)
    return at_start_of_series
    
def sample_photo_acquire(test=False):
    """Take a snapshot of the sample"""
    if task.cancelled: return
    action = task.action; task.action = "Sample Photo"
    generate_autorecovery_restore_point("Sample Photo",("laser_safety_shutter_open",
        "illuminator_on","DiffX","DiffY","DiffZ","Phi"))

    # Remember settings:
    laser_shutter_was_open = laser_safety_shutter_open.value
    illuminator_was_inserted = illuminator_on.value
    phi = Phi.value
    x,y,z = DiffX.value,DiffY.value,DiffZ.value
    
    # When the laser shutter is open, a liquid crystal shutter protects
    # the camera.
    if options.open_laser_safety_shutter: laser_safety_shutter_open.value = False
    # Illuminate the sample.
    if options.use_illuminator: illuminator_on.value = True
    # View the sample at phi = 0.
    if len(sample_photo.phis) > 0: Phi.value = sample_photo.phis[0]
    # Return the sample to the click-center position.
    if align.enabled: DiffX.value,DiffY.value,DiffZ.value = sample.center
    while (illuminator_on.moving or Phi.moving or
        DiffX.moving or DiffY.moving or DiffZ.moving) and not task.cancelled:
        sleep(0.2)

    from WideFieldCamera_image import acquire_image
    # If the liquid crystal shutter was closed, discard the first few images,
    # because the auto-exposure feature of the camera needs time to
    # Adjust to the new higher light level.
    ##if laser_shutter_was_open or not illuminator_was_inserted:
    ##    for i in range(0,3): sample_photo_set_current_image(acquire_image())

    for phi in sample_photo.phis:
        Phi.value = phi
        while Phi.moving and not task.cancelled: sleep(0.1)
        if task.cancelled: break
        image = acquire_image()
        if not test: save_image(image,sample_photo_filename())
        sample_photo_set_current_image(image)

    # Restore settings.
    Phi.value = phi
    if align.enabled: DiffX.value,DiffY.value,DiffZ.value = x,y,z
    if options.use_illuminator: illuminator_on.value = illuminator_was_inserted
    if options.open_laser_safety_shutter: laser_safety_shutter_open.value = laser_shutter_was_open 
    while (illuminator_on.moving or Phi.moving or
        DiffX.moving or DiffY.moving or DiffZ.moving) and not task.cancelled:
        sleep(0.2)

    clear_autorecovery_restore_point()
    task.action = action

def save_image(image,filename):
    """Write a PIL image to a file."""
    from os.path import dirname,exists; from os import makedirs
    dir = dirname(filename)
    if dir!= "" and not exists(dir): makedirs(dir)
    image.save(filename)
    image.filename = filename
    
def sample_photo_filename(image_number=None,phi=None):
    """Where to save the current sample photo"""
    if image_number is None: image_number = task.image_number
    if phi is None: phi = Phi.command_value
    from os.path import splitext
    basename = splitext(filename(image_number))[0]
    pathname = basename+"_%g_deg_photo.jpg" % phi
    return pathname

def sample_photo_last_filename():
    for i in range(task.image_number,0,-1):
        for phi in sample_photo.phis:
            if exists(sample_photo_filename(i,phi)):
                return sample_photo_filename(i,phi)
    return ""

def sample_photo_current_image():
    global sample_photo_current_image_
    if not "sample_photo_current_image_" in globals():
        from PIL import Image
        if sample_photo_last_filename():
            image = Image.open(sample_photo_last_filename())
        else: image = Image.new('RGB',(1360,1024))
        sample_photo_current_image_ = image
    return sample_photo_current_image_

def sample_photo_set_current_image(image):
    global sample_photo_current_image_
    sample_photo_current_image_ = image


def generate_autorecovery_restore_point(name,motor_names):
    """Generate an auto-recovery file, in case 'lauecollect' crashes during a
    beam check.
    motor_names: list of Python variable names"""
    s = "operation = %r\n" % name
    for motor_name in motor_names:
        motor = eval(motor_name)
        if hasattr(motor,"command_value"): value = motor.command_value
        else: value = motor.value
        s += "%s.value = %r\n" % (motor_name,value)
    if not exists(settingsdir()): makedirs(settingsdir())
    file(settingsdir()+"/lauecollect_autorecovery.py","w").write(s)

def clear_autorecovery_restore_point():
    "Undo 'generate_autorecovery_restore_point'"
    filename = settingsdir()+"/lauecollect_autorecovery.py"
    if exists(filename): remove(filename)

def trigger_autorecovery():
    """Something left in a messy state (cancelled? creashed?)"""
    task.autorecovery_needed = True


def sign(x):
    if x>0: return 1
    if x<0: return -1
    return 0

def functions(module):
    "Generates a list of all callable function that are members of a module"
    function = type(functions)
    fnames = []
    for name in dir(module):
        if type(module.__dict__[name]) == function:
            fname = name
            args = module.__dict__[name].func_code.co_varnames
            fname += "("
            for arg in args: fname += (arg+",")
            fname = fname.strip(",")
            fname += ")"
            fnames.append(fname)
    return fnames


def check_beamline_status():
    """Test a series of conditions that needs to be met before data collection
    can start:
    Undulators closed, front end shutter open, ... 
    """
    U23gap = U23.value; U27gap = U27.value
    bad = (U23gap > 29 and U27gap > 29)
    if bad:
        message = "U23 at %.3f, U27 at %.3f mm\n" % (U23gap,U27gap)
        message += "Change to U23 at %.3f, U27 at %.3f mm?" % \
            (checklist.U23,checklist.U27)
        dlg = wx.MessageDialog(None,message,"Undulators",wx.OK|wx.CANCEL|
            wx.ICON_WARNING)
        dlg.CenterOnParent()
        OK = (dlg.ShowModal() == wx.ID_OK) 
        dlg.Destroy()
        if OK:
            U23.value = checklist.U23
            U27.value = checklist.U27
            while (U23.moving or U27.moving) and not task.cancelled:
                sleep(0.1)
            U23.stop() ; U27.stop()
            
    state = xray_safety_shutters_open.value
    if state != "open":
        permit = xray_safety_shutters_enabled.value
        if not permit: state += ", no permit"
    OK = (state == "open")

def debug_logfile():
    """File name error messages."""
    from tempfile import gettempdir
    return gettempdir()+"/lauecollect_debug.log"

def timestamp(seconds=None):
    """Current date and time as formatted ASCII text, precise to 1 ms
    seconds: time elapsed since 1 Jan 1970 00:00:00 UST"""
    if seconds is None: seconds = time()
    from datetime import datetime
    timestamp = str(datetime.fromtimestamp(seconds))
    return timestamp[:-3] # omit microsconds

def progress(message):
    """Report progress to be display by the GUI"""
    task.comment = message
    if message:
        info(message)

def debug(message):
    """Print debug mesage"""
    global debug_last_message
    if message == debug_last_message: return
    debug_last_message = message
    from logging import debug
    debug(message)

debug_last_message = ""

def round_next(x,step):
    """Rounds x up or down to the next multiple of step."""
    if step == 0: return x
    return round(x/step)*step

def round_up(x,step):
    """Rounds x up to the next multiple of step."""
    from math import ceil
    if step == 0: return x
    return ceil(float(x)/float(step))*step

def toint(x):
    """Try to convert x to an integer number without rasing an exception."""
    try: return int(x)
    except: return x

def round_down(x,step):
    """Rounds x down to the next multiple of step."""
    from math import floor
    if step == 0: return x
    return floor(float(x)/float(step))*step

def module_dir():
    "directory of the current module"
    from os.path import dirname
    module_dir = dirname(module_path())
    if module_dir == "": module_dir = "."
    return module_dir

def module_path():
    "full pathname of the current module"
    from sys import path
    from os import getcwd
    from os.path import basename,exists
    from inspect import getmodulename,getfile
    # 'getfile' retreives the source file name name compiled into the .pyc file.
    pathname = getfile(lambda x: None)
    if exists(pathname): return pathname
    # The module might have been compiled on a different machine or in a
    # different directory.
    pathname = pathname.replace("\\","/")
    filename = basename(pathname)
    dirs = [dir for dir in [getcwd()]+path if exists(dir+"/"+filename)]
    if len(dirs) == 0: warn("pathname of file %r not found" % filename)
    dir = dirs[0] if len(dirs) > 0 else "."
    pathname = dir+"/"+filename
    return pathname

def UNIX_pathname(pathname):
  """This converts the pathname of a file on a network file server from
  the local format to the format used on a UNIX compter.
  e.g. "//id14bxf/data" in Windows maps to "/net/id14bxf/data" on Unix"""
  if not pathname: return pathname
  # Try to expand a Windows drive letter to a UNC name. 
  try:
    import win32wnet
    # Convert "J:/anfinrud_0811/Data" to "J:\anfinrud_0811\Data".
    pathname = pathname.replace("/","\\")
    pathname = win32wnet.WNetGetUniversalName(pathname)
  except: pass
  # Convert separators from DOS style to UNIX style.
  pathname = pathname.replace("\\","/")

  if pathname.find("//") == 0: # //server/share/directory/file
    parts = pathname.split("/")
    if len(parts) >= 4:
      server = parts[2] ; share = parts[3]
      path = ""
      for part in parts[4:]: path += part+"/"
      path = path.rstrip("/")
      if not exists("//"+server+"/"+share) and exists("/net/"+server+"/"+share):
          pathname = "/net/"+server+"/"+share+"/"+path
  return pathname


# Get the last save parameters.
reload_settings()
# Go to the first image
##task.image_number = first_image_number() # slow!

def alignment_survey():
    for phi in range(30,360,30):
        Phi.value = phi; Phi.wait()
        align_sample()

def load_variable_sequence(filename):
    """Load data colelction parameters from a spreadsheet table"""
    global sequence 
    from table import table
    sequence = table(filename,separator="\t")
    for name in sequence.columns:
        set_variable_sequence(name,sequence[name])
    save_settings()

def set_variable_sequence(name,values):
    """Load data collection parameters from a spreadsheet table"""
    if name == "delay":
        variable_set_choices(name,list(seconds(list(values))))
    elif name == "laser_on":
        variable_set_choices("laser_on",list(values))
    elif name == "xray_on":
        options.xray_on = list(values)
    elif name == "translation_mode":
        translate.modes = list(values)
    elif name == "chopper_mode":
        chopper.modes = list(values)
    elif name == "pump_on":
        pump.on = list(values)

"""This is to run the modules as a stand-alone program.
This code is only executed when the file is passed a run-time argument to
the Python interpreter."""
if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s",
        ##filename=debug_logfile()
    )
    image_numbers = collection_pass(1) # for debugging
    from thread import start_new_thread
    ##print('start_new_thread(collect_dataset,())')
    ##print('collect_dataset()')
    print('image_numbers = collection_pass(1)')
    print('timing_system_start_images(image_numbers)')
    
