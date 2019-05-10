"""
Scripts to verify the linearity of the MAR CCD detector
scan: data aqusistion
analyze_scan: image processing
Friedrich Schotte, APS, 5 Feb 2009
"""

from id14 import * # Beamline instrumentation
from os import makedirs
from os.path import exists,dirname,basename
from numpy import array,where,isnan,amax,zeros,rint,isinf,nansum,nanmax,sum,average
from textfile import read,save

scan_dir = "/data/anfinrud_0902/Data/MARCCD_linearity/scan3"

npasses = 32

# Stacked aluminum foil attenuator, step size 0.5 mm
motor = DetY
start = 2.1-0.7 # [mm] no foil: 2.1, lead tape 2.1-0.7
step = 0.7 # [mm] relative vertical offset of foils
end = start + 10*0.7 # [mm] maximum number of foils

# Record X-ray beam intensity
# C1 = I0 PIN diode reverse-biased, 50 Ohm, C4 = trigger
xray_pulse = id14b_wavesurfer.measurement(1)

I0_offset = 4.97e-9 # [Vs] measured in auto trigger mode

boxsize = 5 # [pixels] box size around peak to integrate

def scan():
    """Acquires a series of image with different vertical offsets 
    in order to to find the edge of the crystal"""
    # Make sure directory exists
    if not exists (scan_dir): makedirs (scan_dir)
    # Clean up directory.
    for i in range(0,100):
       filename = "%s/%03d.mccd" % (scan_dir,i+1)
       if exists(filename): remove(filename)
    pson.value = 0 # Disable ps laser.
    lxd.value = 0 # Make sure the X-ray pulse is not delayed.
    
    npoints = int(round(abs((end-start)/step)))+1

    logfile = "%s/scan.log" % scan_dir
    if not exists(logfile):
        log = file(logfile,"a")
        log.write("# source: U23 at %.2f mm, U27 at %.2f mm\n" %
            (caget("ID14ds:Gap.VAL"),caget("ID14us:Gap.VAL")))
        log.write("#filename\t%s[%s]\tI0[Vs]\tbunchcurrent[mA]\n" %
            (motor.name.replace(" ",""),motor.unit))
    log = file(logfile,"a")

    for j in range(0,npasses):
        for i in range(0,npoints):
          filename = "%s/%03d_%03d.mccd" % (scan_dir,i+1,j+1)
          if not exists(filename):
              pos = (start + i*step)
              print "%s\t%g" % (basename(filename),pos)
              motor.value = pos
              while motor.moving: sleep (0.1)
              acquire_single_shot(filename)
              log.write("%s\t%g\t%g\t%g\n" %
                  (basename(filename),pos,xray_pulse.average,bunch_current()))
              log.flush()

    motor.value = start # return the sample to starting point

def acquire_single_shot(filename):
    "Acquires a single image of an alignment scan"
    waitt.value = 0.1 # no need for long waiting time
    # Postpone the acquisition of the image, if a top-up is scheduled.
    if time_to_next_refill() < 1.0: print "Waiting for refill..."
    while time_to_next_refill() < 1.0: sleep (0.1)
    xray_pulse.start() # for diangostics
    ccd.start()
    pulses.value = 1 # This riggers the ms shutter once.
    while pulses.value > 0: sleep (0.1)
    # After pulses drops to zero, the Xr-ay pulse is sent within 0.1 s
    sleep (0.1)
    ccd.readout(filename)

def time_to_next_refill():
    """This tells the number of seconds to the next top-up.
    This is needed to decide whether it is necessary to postpone the next image
    until after the next top-up, to avoid collecting data during a top-up. """
    return caget("Mt:TopUpTime2Inject")

def bunch_current():
    "Reads current of of bunch '#1' in mA from the machine info"
    try: return float(caget("BNCHI:BunchCurrentAI.VAL"))
    except: return nan

def analyze_scan():
    """ Processes the dataset in directory 'scan_dir'
    """
    global filenames,pos,I0,curr,sum_image,ave_image,peakI,x,y,r,image,I # for debugging
    logfile = "%s/scan.log" % scan_dir
    filenames,pos,I0,curr = read(logfile,labels=
        "filename,DetY[mm],I0[Vs],bunchcurrent[mA]")
    nimages = len(filenames)

    # Find the peak position. This first image might be an empty image.
    # Thus use an averaged image to determine the peak position.
    print "Finding peak",
    w,h = imagesize(scan_dir+"/"+filenames[0])
    sum_image = zeros((w,h))
    count = 0
    for i in range(0,nimages):
        image = numimage(scan_dir+"/"+filenames[i])
        if isinf(nanmax(image)): print "!",; continue # skip saturated images
        print ".",
        sum_image += image
        count += 1
        if count>=5: break
    ave_image = sum_image/count

    peakI = nanmax(ave_image)
    peakpos = where(ave_image == peakI)
    x,y = peakpos[0][0],peakpos[1][0]
    print x,y
    r = int(rint(boxsize/2))

    I = array([nan]*nimages)
    for i in range(0,nimages):
        image = numimage(scan_dir+"/"+filenames[i])
        I[i] = average(image[x-r:x+r+1,y-r:y+r+1])
        print "%g\t%g" % (pos[i],I[i])

    outfile = "%s/scan.txt" % scan_dir
    save([pos,I,I0,curr],outfile,labels=
         "DetY[mm],I[counts],I0[Vs],bunchcurrent[mA]")

def imagesize(filename):
    """Get width and height in pixels as (w,h) pair"""
    from PIL import Image
    image = Image.open(filename)
    return image.size

def numimage(filename):
    """Load an image as numpy array"""
    from PIL import Image
    from numpy import array,where,nan,inf
    image = Image.open(filename)
    image = array(image.convert("I"),float).T
    image[where(image == 0)] = nan
    image[where(image == 65535)] = inf
    image -= 10 # undo MAR CCD image software offset
    return image

if __name__ == "__main__":
    "for testing"
    analyze_scan()
