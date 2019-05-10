#!/bin/env python
"""Take a snapshot of sample using the Wide-filed camera image
Friedrich Schotte, APS, 8 Jul 2010 - 25 Oct 2014"""
__version__ = "2.2"

from GigE_camera import GigE_camera
from logging import debug

name = "WideFieldCamera"

# Under Linux, The Prosilica library requires administrative privileges
# to use multicast. Unless the calling prgram is registered in sudoers
# data base, 'use_multicast' needs to be set to False.
# If multicast is set to False, the image acquisition will fail if a
# another application acquires images from the beam profilter camera at
# the same time.
use_multicast = False

def camera_acquire_image():
    """Acquire a single image from the camera and return as PIL image.
    This function is *NOT SAFE* to use for Python applications using network
    communication ("Interrupted system call"), because loads the Prosilica
    library."""
    from time import time
    from PIL import Image # Python Imaging Library
    
    camera = GigE_camera(parameter("camera.IP_addr"),use_multicast=use_multicast)
    camera.last_timestamp = 0

    camera.start()    
    t = time()
    while not camera.has_image or camera.timestamp == 0:
        if time()-t > 2.0 and not "started" in camera.state:
            log ("camera_acquire_image: image unreadable (%s)" % camera.state); break
        if time()-t > 5.0:
            log ("camera_acquire_image: image acquistion timed out (%s)" % camera.state); break
        sleep(0.1)

    camera.stop()

    debug("get_image: read image with %dx%d pixels, %d bytes" %
        (camera.width,camera.height,len(camera.rgb_data)))
    image = Image.new('RGB',(camera.width,camera.height))
    image.fromstring(camera.rgb_data)
    image = rotated_image(image)
    return image

def camera_save_image(filename):
    """Acquire a single image from the camera and save it as a file.
    filename: the exension determines the image format, may be '.jpg',
    '.png' or '.tif' or any other extension supported by the Python
    Image Library (PIL)
    This function is *NOT SAFE* to use for Python applications using network
    communication ("Interrupted system call"), because loads the Prosilica
    library."""
    image = camera_acquire_image()
    image.save(filename)

def camera_image_size():
    """Image width and height, without rotation applied.
    This function is *NOT SAFE* to use for Python applications using network
    communication ("Interrupted system call"), because loads the Prosilica
    library."""
    camera = GigE_camera(parameter("camera.IP_addr"))
    width,height = camera.width,camera.height
    orientation = parameter('Orientation',90) # in degrees counter-clockwise
    if orientation == None: orienation = 0
    orientation %= 360
    if orientation == 90 or orientation == 270: width,height = height,width
    return width,height

def subprocess(command):
    """Execute the given command in a subprocess.
    The standard ouput of the command is returned as a string with trailing
    newline.
    If you need the result of the command, the command should contain a 'print'
    statement. E.g. 'print get_center()'. Multiple commands can be
    concatenated, separated by semicolons.
    Functions that load the Prosilica library interfere with network
    communication ("Interrupted system call").
    Executing them in a subprocess makes it safe for applications that use
    network communications to call them."""
    from sys import executable as python
    from subprocess import Popen,PIPE
    from sys import stderr
    command = "from %s import *; %s" % (modulename(),command)
    for attempt in range(0,3):
        try:
            process = Popen([python,"-c",command],stdout=PIPE,stderr=PIPE,
                universal_newlines=True)
            break
        except OSError,msg: # [Errno 513] Unknown error 513
            log("subprocess: %s" % msg)
            sleep(1)
    output,error = process.communicate()
    if "Traceback" in error: raise RuntimeError(repr(command)+"\n"+error)
    if error: stderr.write(error)
    return output
    
def save_image(filename):
    """Acquire a single image from the camera and save it as a file.
    filename: the exension determines the image format, may be '.jpg',
    '.png' or '.tif' or any other extensino supported by the Python Image
    Library (PIL)
    The Prosilica library is loaded in a subprocess."""
    subprocess("camera_save_image(%r)" % filename)
    ##image = acquire_image()
    ##image.save(filename)

def acquire_image():
    """Acquire a single image from the camera and return it as PIL image.
    If rotate = True, apply the same rotation as in the ImageViewer
    application.
    This function is safe to use from any Python application, because it does
    not load the Prosilica library. The task is preformed in a subprocess
    instead.
    The Prosilica library is loaded in a subprocess."""
    import Image
    w,h = image_size()
    image = Image.new('RGB',(w,h))
    global image_data # for debugging
    image_data = eval(subprocess("print repr(camera_acquire_image().tostring())"))
    log("acquire_image: got %d bytes of image data from subprocess" % len(image_data))
    if len(image_data) != w*h*3:
        log("acquire_image: expecting %d, got %d bytes of image data" %
            (w*h*3,len(image_data)))
    if len(image_data) == w*h*3: image.fromstring(image_data)
    else: log("acquire_image: image data corrupted, substituting blank image")
    return image

def rotated_image(image):
    """Apply the same rotation as in the  ImageViewer application."""
    orientation = parameter('Orientation',90) # in degrees counter-clockwise
    if orientation == None: orienation = 0
    return image.rotate(orientation)

def image_size():
    """Image width and height, without rotation applied
    This function is safe to use from any Python application, because it does
    not load the Prosilica library. The task is performed in a subprocess
    instead."""
    return eval(subprocess("print camera_image_size()"))

def modulename():
    """Name of this Python module, without directory and extension,
    as used for 'import'"""
    from inspect import getmodulename,getfile
    return getmodulename(getfile(lambda x:x))

def rotate((x,y)):
    """Apply the same rotation as in the ImageViewer application to the
    cross-hair"""
    orientation = parameter('Orientation',90) # in degrees counter-clockwise
    if orientation == None: orienation = 0
    w,h = image_size()
    if orientation == 0: return (x,y)
    if orientation == -90: return (h-y,x)
    if orientation == 90: return (y,w-x)
    if orientation == 180: return (w-x,h-y)
    return (x,y)

def parameter(name,default_value=None):
    """Retreive a parameter used by the CameraViewer
    application."""
    settings = file(settings_file()).read()
    for line in settings.split("\n"):
        line = line.strip(" \n\r")
        if len(line.split("=")) != 2: continue
        keyword,value = line.split(" = ")
        keyword = keyword.strip(" ")
        if keyword == name: return eval(value)
    return default_value

def settings_file():
    "pathname of the file used to store persistent parameters"
    return settings_dir()+"/"+name+"_settings.py"

def settings_dir():
    "pathname of the file used to store persistent parameters"
    path = module_dir()+"/settings"
    return path

def module_dir():
    "directory of the current module"
    from os.path import dirname
    module_dir = dirname(module_path())
    if module_dir == "": module_dir = "."
    return module_dir

def module_path():
    """Full pathname of the current module"""
    from sys import path
    from os import getcwd
    from os.path import basename,exists
    from inspect import getmodulename,getfile
    from logging import warn
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

def log(message):
    """Append a message to the log file (/tmp/beam_profiler.log)"""
    from tempfile import gettempdir
    from time import strftime
    from sys import stderr
    timestamp = strftime("%d-%b-%y %H:%M:%S")
    if len(message) == 0 or message[-1] != "\n": message += "\n"
    stderr.write("%s: %s" % (timestamp,message))
    logfile = gettempdir()+"/beam_profiler.log"
    file(logfile,"a").write(timestamp+" "+message)

def sleep(seconds):
    """Return after for the specified number of seconds"""
    # After load and initializing the PvAPI Python's built-in 'sleep' function
    # stops working (returns too early). The is a replacement.
    from time import sleep,time
    t = t0 = time()
    while t < t0+seconds: sleep(t0+seconds - t); t = time()


if __name__ == "__main__":
    """for testing"""
    print 'save_image("test/test.png")'

