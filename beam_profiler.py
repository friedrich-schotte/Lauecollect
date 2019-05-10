#!/bin/env python
"""
Measure the poistion of the laser beam at the sample, based on a camera image.

Friedrich Schotte, APS, 8 Jul 2010 - 1 Jul 2012
"""

__version__ = "2.0.2"

from GigE_camera import GigE_camera

from sys import stdout

#IP_address = "id14b-prosilica3.cars.aps.anl.gov"
IP_address = "id14b-prosilica3.biocarsvideo.net"

pixelsize = 0.00465 # 1:1 imaging, same as CCD pixelsize

# Under Linux, The Prosilica library requires administrative privileges
# to use multicast. Unless the calling prgram is registered in sudoers
# data base, 'use_multicast' needs to be set to False.
# If multicast is set to False, the image acquisition will fail if a
# another application acquires images from the beam profilter camera at
# the same time.
use_multicast = False

def get_image():
    """Acquire a single image from the camera and return as PIL image.
    This function is *NOT SAFE* to use for Python applications using network
    communication ("Interrupted system call"), because loads the Prosilica
    library."""
    from time import time
    import Image # Python Imaging Library
    
    camera = GigE_camera(IP_address)
    # Under Linux use_multicast requires administrative priviledges.
    # Program needs to be registered in sudoers data base.
    camera.use_multicast = use_multicast 
    camera.last_timestamp = 0

    camera.start()    
    t = time()
    while not camera.has_image or camera.timestamp == 0:
        if time()-t > 2.0 and not "started" in camera.state:
            log ("Prosilica image unreadable (%s)" % camera.state); break
        if time()-t > 5.0:
            log ("Prosilica image acquistion timed out (%s)" % camera.state); break
        sleep(0.1)

    camera.stop()

    log("Info: read image image with %dx%d pixels, %d bytes" %
        (camera.width,camera.height,len(camera.rgb_data)))
    image = Image.new('RGB',(camera.width,camera.height))
    image.fromstring(camera.rgb_data)

    return image

def get_center():
    """Beam center pixel occordinates, without rotation applied.
    This function is *NOT SAFE* to use for Python applications using network
    communication ("Interrupted system call"), because loads the Prosilica
    library."""
    camera = GigE_camera(IP_address)
    return camera.center 

def get_image_size():
    """Image width and height, without rotation applied.
    This function is *NOT SAFE* to use for Python applications using network
    communication ("Interrupted system call"), because loads the Prosilica
    library."""
    camera = GigE_camera(IP_address)
    return camera.width,camera.height

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
    process = Popen([python,"-c",command],stdout=PIPE,stderr=PIPE,
        universal_newlines=True)
    output,error = process.communicate()
    if "Traceback" in error: raise RuntimeError(repr(command)+"\n"+error)
    if error: stderr.write(error)
    return output
    
def acquire_image(rotate=True):
    """Acquire a single image from the camera and return it as PIL image.
    If rotate = True, apply the same rotation as in the 'Laser Beam Profile'
    ImageViewer application.
    This function is safe to use from any Python application, because it does
    not load the Prosilica library. The task is preformed in a subprocess
    instead."""
    import Image
    w,h = image_size()
    image = Image.new('RGB',(w,h))
    global image_data # for debugging
    image_data = eval(subprocess("print repr(get_image().tostring())"))
    ##image_data = subprocess("stdout.write(get_image().tostring())")
    log("Info: got %d bytes of image data from subprocess" % len(image_data))
    log("Expecting %d, got %d bytes of image data" % (w*h*3,len(image_data)))
    if (len(image_data) == w*h*3): image.fromstring(image_data)
    else: log("Image data corrupted, substituting blank image")
    return rotated_image(image) if rotate else image

def rotated_image(image):
    """Apply the same rotation as in the 'Laser Beam Profile' ImageViewer
    application."""
    orientation = parameter('Orientation',90) # in degrees counter-clockwise
    if orientation == None: orienation = 0
    return image.rotate(orientation)

def center():
    """Beam center pixel occordinates, without rotation applied.
    This function is safe to use from any Python application, because it does
    not load the Prosilica library. The task is preformed in a subprocess
    instead."""
    return eval(subprocess("print get_center()"))

def image_size():
    """Image width and height, without rotation applied
    This function is safe to use from any Python application, because it does
    not load the Prosilica library. The task is preformed in a subprocess
    instead."""
    return eval(subprocess("print get_image_size()"))

def modulename():
    """Name of this Python module, without directory and extension,
    as used for 'import'"""
    from inspect import getmodulename,getfile
    return getmodulename(getfile(center))

def crosshair():
    """Cross hair coordinates in pixels with respect to the top left
    corner of the rotated image"""
    return rotate(center())

def rotate((x,y)):
    """Apply the same rotation as in the 'Laser Beam Profile' ImageViewer
    application to the cross-hair"""
    orientation = parameter('Orientation',90) # in degrees counter-clockwise
    if orientation == None: orienation = 0
    w,h = image_size()
    if orientation == 0: return (x,y)
    if orientation == -90: return (h-y,x)
    if orientation == 90: return (y,w-x)
    if orientation == 180: return (w-x,h-y)
    return (x,y)

def parameter(name,default_value=None):
    """Retreive a parameter used by the 'Laser Beam Profile' CameraViewer
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
    return settings_dir()+"/BeamProfile_settings.py"

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
    "full pathname of the current module"
    from sys import path
    from os import getcwd
    from os.path import basename,exists
    from inspect import getmodulename,getfile
    # 'getfile' retreives the source file name name compiled into the .pyc file.
    pathname = getfile(lambda x: None)
    ##print "module_path: pathname: %r" % pathname
    if exists(pathname): return pathname
    # The module might have been compiled on a different machine or in a
    # different directory.
    pathname = pathname.replace("\\","/")
    filename = basename(pathname)
    ##print "module_path: filename: %r" % filename
    dirs = [dir for dir in [getcwd()]+path if exists(dir+"/"+filename)]
    if len(dirs) == 0: print "pathname of file %r not found" % filename
    dir = dirs[0] if len(dirs) > 0 else "."
    pathname = dir+"/"+filename
    ##print "module_path: pathname: %r" % pathname
    return pathname

def ROI(image):
    """Image clipped to the region of interest as defined by the 'Laser Beam
    Profile' ImageViewer application."""
    # Get the region of interest
    ROI = parameter('ImageWindow.ROI',[[-1.0,-1.0],[1.0,1.0]])
    ##print "using ROI [%+.3f,%+.3f], "%tuple(ROI[0])+"[%+.3f,%+.3f] mm"%tuple(ROI[1])
    cx,cy = crosshair()
    ##print "using center",(cx,cy)
    dx = dy = pixelsize
    xmin = int(round(ROI[0][0]/dx+cx)) ; xmax = int(round(ROI[1][0]/dx+cx))
    ymin = int(round(cy-ROI[1][1]/dy)) ; ymax = int(round(cy-ROI[0][1]/dy))
    if xmin > xmax: xmin,xmax = xmax,xmin
    if ymin > ymax: ymin,ymax = ymax,ymin
    ##print "ROI [%d:%d,%d:%d]" % (xmin,xmax,ymin,ymax)
    return image.crop((xmin,ymin,xmax,ymax))

def xy_projections(image):
    """Calculate a horizonal and vertical projections of a region of interest
    of the image. The region of interest is the one define by the 'Laser Beam
    Profile' CameraViewer application.
    A rotated image as displayed and saved by the 'Laser Beam Profile'
    ImageViewer application must be passed in PIL format.
    """
    from numpy import array,sum,nansum,isnan

    image = ROI(image)
    R,G,B = image.split()
    R,G,B = array(R,float).T,array(G,float).T,array(B,float).T
    RGB = array([R,G,B])

    # Select which channels to use.
    R,G,B = RGB
    use_channels = (1,1,1) # use all channels R,G,B
    r,g,b = use_channels
    I = r*R + b*B + g*G

    # Generate projection on the X and Y axis.
    xproj = nansum(I,axis=1)/sum(~isnan(I),axis=1)
    yproj = nansum(I,axis=0)/sum(~isnan(I),axis=0)
    # Scale projections in units of mm.
    roi = parameter('ImageWindow.ROI',[[-1.0,-1.0],[1.0,1.0]])
    cx,cy = crosshair()
    dx = dy = pixelsize
    xmin = int(round(roi[0][0]/dx+cx)) ; xmax = int(round(roi[1][0]/dx+cx))
    ymin = int(round(cy-roi[1][1]/dy)) ; ymax = int(round(cy-roi[0][1]/dy))
    if xmin > xmax: xmin,xmax = xmax,xmin
    if ymin > ymax: ymin,ymax = ymax,ymin
    xscale = [(xmin+i-cx)*dx for i in range(0,len(xproj))]
    yscale = [(cy-(ymin+i))*dy for i in range(0,len(yproj))]
    xprofile = zip(xscale,xproj)
    yprofile = zip(yscale,yproj)

    return xprofile,yprofile

def FWHM(data):
    """Calculates full-width at half-maximum of a positive peak of a curve
    given as list of [x,y] values"""
    x = xvals(data); y = yvals(data); n = len(data)
    if n == 0: return nan
    HM = (min(y)+max(y))/2
    for i in range (0,n):
        if y[i]>HM: break
    if i == 0: x1 = x[0]
    else: x1 = interpolate_x((x[i-1],y[i-1]),(x[i],y[i]),HM)
    r = range(0,n); r.reverse()
    for i in r:
        if y[i]>HM: break
    if i == n-1: x2 = x[n-1]
    else: x2 = interpolate_x((x[i+1],y[i+1]),(x[i],y[i]),HM)
    return abs(x2-x1)

def CFWHM(data):
    """Calculates the center of the full width half of the positive peak of
    a curve given as list of [x,y] values"""
    x = xvals(data); y = yvals(data); n = len(data)
    if n == 0: return nan
    HM = (min(y)+max(y))/2
    for i in range (0,n):
        if y[i]>HM: break
    if i == 0: x1 = x[0]
    else: x1 = interpolate_x((x[i-1],y[i-1]),(x[i],y[i]),HM)
    r = range(0,n); r.reverse()
    for i in r:
        if y[i]>HM: break
    if i == n-1: x2 = x[n-1]
    else: x2 = interpolate_x((x[i+1],y[i+1]),(x[i],y[i]),HM)
    return (x2+x1)/2.

def SNR(data):
    """Calculate the signal-to-noise ratio of a beam profile.
    It is defined as the ratio the peak height relative to the baseline and the
    RMS of the base line.
    The base line is the outer 20% of the profile on either end."""
    from numpy import rint,std,mean,mean,nan
    y = yvals(data); n = len(data)
    # Assume that the base line is the outer 20% of the data.
    n1 = int(rint(n*0.2)) ; n2 = int(rint(n*0.8))
    baseline = y[0:n1]+y[n2:-1]
    signal = max(y)-mean(baseline)
    noise = std(baseline)
    if noise != 0: return signal/noise
    else: return nan

def interpolate_x((x1,y1),(x2,y2),y):
    "Linear inteposition between two points"
    # In case the result is undefined, midpoint is as good as any value.
    if y1==y2: return (x1+x2)/2. 
    x = x1+(x2-x1)*(y-y1)/float(y2-y1)
    #print "interpolate_x [%g,%g,%g][%g,%g,%g]" % (x1,x,x2,y1,y,y2)
    return x

def xvals(xy_data):
    "xy_data = list of (x,y)-tuples. Returns list of x values only."
    xvals = []
    for i in range (0,len(xy_data)): xvals.append(xy_data[i][0])
    return xvals

def yvals(xy_data):
    "xy_data = list of (x,y)-tuples. Returns list of y values only."
    yvals = []
    for i in range (0,len(xy_data)): yvals.append(xy_data[i][1])
    return yvals

def log(message):
    "Append a message to the log file (/tmp/beam_profiler.log)"
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


def test():
    global image,xprofile,yprofile
    
    image = acquire_image()
    ##image = Image.open("/net/id14bxf/data/anfinrud_0907/Photos/2009.07.08 20.40 Laser profile.png")
    print "image size",image.size

    print "using center",crosshair()
    print "using ROI",parameter('ImageWindow.ROI',[[-1.0,-1.0],[1.0,1.0]])

    xprofile,yprofile = xy_projections(image)

    print "FWHM:   %.3f x %.3f mm" % ( FWHM(xprofile), FWHM(yprofile))
    print "center: %+.3f mm, %+.3f mm" % (CFWHM(xprofile),CFWHM(yprofile))
    print "S/N:    %.3g:1, %.3g:1" % (SNR(xprofile),SNR(yprofile)),
    OK = min(SNR(xprofile),SNR(yprofile)) > 15
    if OK: print "(OK)"
    else: print "(insufficient)"

    from Plot import Plot
    Plot(xprofile,title="xprofile")
    Plot(yprofile,title="yprofile")
    import wx
    wx.GetApp().MainLoop()

def test_direct():
    print "Running test ..."
    camera = GigE_camera("id14b-prosilica3.cars.aps.anl.gov",use_multicast=False)
    camera.start()
    print "Camera started..."
    sleep(2) 
    print camera.state
    print "has_image",camera.has_image
    print "pixel_format",camera.pixel_format
    print "width*height",camera.width*camera.height
    image = camera.rgb_array
    from numpy import average,sum
    I = float(sum(image))/image.size
    print "average intensity",I

def test_average():
    global image_data,image
    image_data = subprocess("stdout.write(get_image().tostring())")
    from numpy import frombuffer,uint8,average
    image = frombuffer(image_data,uint8).reshape(1360,1024,3)
    I = float(image.sum())/image.size
    print "average: %g counts/pixel" % I
    print "fraction of pixels >0: %g" % average(image != 0)

def test_single_image():
    from time import time
    from numpy import average,sum

    global camera,image,I
    
    camera = GigE_camera("id14b-prosilica4.cars.aps.anl.gov",
        use_multicast=False)
    camera.start()
    t = time()
    while not camera.has_image:
        if time()-t > 2.0 and not "started" in camera.state:
            print ("Prosilica image unreadable (%s)" % camera.state)
            break
        if time()-t > 5.0:
            print ("image acquistion timed out (%s)" % camera.state)
            break
        sleep(0.1)
    print "acquisition time %.3fs" % (time()-t)
    image = camera.rgb_array
    I = float(sum(image))/image.size
    print "average: %g counts/pixel" % I
    print "fraction of pixels >0: %g" % average(image != 0)

if __name__ == "__main__":
    "for testing"
    test()

