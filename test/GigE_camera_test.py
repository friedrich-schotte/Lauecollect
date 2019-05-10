from GigE_camera import GigE_camera,sleep
from time import time
from numpy import average,sum

# id14b-prosilica1 - Microscope camera
# id14b-prosilica2 - Wide-field camera
# id14b-prosilica3 - Laser beam profile at sample
# id14b-prosilica4 - Laser beam profile in beam conditioning box

camera = GigE_camera("id14b-prosilica1.cars.aps.anl.gov",
    use_multicast=False)
camera.pixel_format = "Rgb24"
camera.start()
t = time()
while not camera.has_image:
    print camera.state
    if time()-t > 2.0 and not "started" in camera.state:
        print ("Prosilica image unreadable (%s)" % camera.state)
        break
    if time()-t > 5.0:
        print ("image acquistion timed out (%s)" % camera.state)
        break
    sleep(0.1)
print "acquisition time %.3fs" % (time()-t)
R,G,B = image = camera.rgb_array
camera.stop()
I = float(sum(image))/image.size
print "average: %g counts/pixel" % I
print "fraction of pixels >0: %g" % average(image != 0)

def rotate(image,angle):
    """A rotated version of the input image.
    'angle' is in units of deg, positive = counterclockwise.
    'angle' must be a multiple of 90 deg"""
    if angle % 360 == 0:   return image
    if angle % 360 == 90:  return image.transpose(0,2,1)[:,:,::-1]
    if angle % 360 == 180: return image[:,::-1,::-1]
    if angle % 360 == 270: return image.transpose(0,2,1)[:,::-1,:]
    return image

image2 = rotate(image,90)
    
# Display the image
from pylab import *
chart = figure(figsize=(8,8))
imshow(minimum(image2,255).T,cmap=cm.gray,origin='upper',interpolation='nearest')
show()
