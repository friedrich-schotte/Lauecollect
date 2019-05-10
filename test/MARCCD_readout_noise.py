"""
Script to characterize the MAR CCD detector
Friedrich Schotte, 11 Feb 2009
"""

from id14 import * # Beamline instrumentation
from os import makedirs
from os.path import exists,dirname,basename
from numpy import array,where,isnan,amax,zeros,rint,isinf,nansum,nanmax,sum,average
from textfile import read,save

scan_dir = "/data/anfinrud_0902/Data/MARCCD/readout_noise_raw4"

npasses = 32

def acquire():
    "Acquires a series of images"
    # Make sure directory exists
    if not exists (scan_dir): makedirs (scan_dir)
    
    for i in range(0,npasses):
       ccd.start()
       ccd.readout()
       while ccd.state() != "idle": sleep(0.1)
       sleep(5)
       filename = "%s/%03d.mccd" % (scan_dir,i+1)
       ccd.save_image(filename)
       while ccd.state() != "idle": sleep(0.1)
       sleep(5)
       filename = "%s/%03d_raw.mccd" % (scan_dir,i+1)
       ccd.save_raw_image(filename)
       while ccd.state() != "idle": sleep(0.1)
       sleep(5)

def analyze():
    """Processes the dataset in directory 'scan_dir' """
    # for debugging
    global filenames,pos,I0,curr,sum_image,ave_image,peakI,x,y,r,image,I
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
    acquire()
