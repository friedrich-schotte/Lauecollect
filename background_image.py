"""Friedrich Schotte, 29 Apr 2014 - 15 Mar 2017"""
__version__ = "1.9"
from logging import debug,info,warn,error

def background_subtracted(image):
    image = image - background_image(image)
    return image

def background_image(image):
    """An image containing the part of the intensity of each pixel of the
    imput image that cannot be accouned for by Bragg reflections.
    Where the background cannot be determined the pixel value is nan.
    """
    from numimage import numimage
    from scipy.ndimage.filters import gaussian_filter
    from numpy import log,sqrt,sum,nan,average,zeros
    from time import clock

    # Parameters
    filter_width = 4.5 # FWHM in pixels, e.g. 18
    spot_threshold = 2.0 # for spot detection, multiples of sigma

    filter_sigma = filter_width/(2*sqrt(2*log(2)))

    image = image.astype(float)
    noise_image = noise(image)
    unusable_pixel_mask = beamstop_mask(image)|inactive_area(image)
    mask = zeros(image.shape,bool)

    info("Background image...")

    for i in range(0,10):
        filtered_image = gaussian_filter(image*(1-mask),sigma=filter_sigma,
            mode='constant')
        weights = gaussian_filter(1.0-mask,sigma=filter_sigma,mode='constant')
        background_image = filtered_image/weights
        Nmasked0 = sum(mask & ~unusable_pixel_mask)
        mask = (image - background_image > spot_threshold*noise_image) | \
            unusable_pixel_mask
        Nmasked = sum(mask & ~unusable_pixel_mask)
        ##info("masked %.3g%%" % (average(mask & ~unusable_pixel_mask)*100))
        if float(Nmasked-Nmasked0)/Nmasked < 0.001: break
    info("Background image done.")

    background_image[unusable_pixel_mask] = nan
    return numimage(background_image)

def noise(image):
    """Estimate of the RMS error of every pixel of the image, in ADC counts.
    image: pixel intensties as 2D numpy array, image file offset
    substracted, in ADC counts."""
    from numpy import sqrt,nan,where,seterr
    seterr(invalid="ignore") 
    # The "gain factor" is defined as number of ADC counts per photon
    # at the photon energy of CuKa (8.048 keV, 1.54 A)
    count_per_photon = 0.8*1.54/1.04
    readout_noise = 1.92 # ADC counts
    counts = image
    noise = sqrt(counts*count_per_photon+readout_noise**2)
    noise = where(active_area(image),noise,nan)
    return noise

def active_area(image):
    """Generate a bitmap of pixels that contain valid data.
    (1 = active, 0 = inactive)."""
    return ~inactive_area(image)

def inactive_area(image):
    """Generate a bitmap of pixels that do not contain valid data.
    (0 = active, 1 = inactive).
    MAR CCD image are circular, an stored as a quadratic bitmap image.
    The pixel intensity in the corners is set to zero to indicate that
    this area does not contain valid intensity, where as intensity zero
    is reperented by a numeric value of 10.
    We found that the pixels at the border of the active area have
    systematically too low intensities. These are marked as inactive, too.
    """
    from grow_bitmap import grow_bitmap
    mask = (image == 0)
    # Mask the border of the image.
    ##mask[0,:] = mask[-1,:] = True
    ##mask[:,0] = mask[:,-1] = True
    mask = grow_bitmap(mask)
    return mask

def beamstop_mask(image):
    from numpy import fromfunction
    # Parameters
    cx,cy = 6.5,-3.5 # offset from geometric center in mm
    R = 5.5 # mm
    w,h = image.shape
    dx = image.pixelsize
    cpx,cpy = w/2+cx/dx,h/2-cy/dx
    r = R/dx
    def masked(x,y): return (x-cpx)**2+(y-cpy)**2 < r**2
    mask = fromfunction(masked,(w,h))
    return mask
    

