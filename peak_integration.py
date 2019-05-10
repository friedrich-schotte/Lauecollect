"""Peak integration for Lauecollect edge alignment scans. 

Philip Anfinrud, 6 Nov, 2010
Friedrich Schotte, 6 Nov 2010 - 7 Oct 2017
"""

__version__ = "1.3.3" # cleanup: from numpy import *
# Turn off IEEE-754 warnings in numpy 1.6+ ("invalid value encountered in...")
import numpy; numpy.seterr(invalid="ignore")

def spot_mask(I,threshold=5):
    """Generate a "spot mask" for a diffraction image with Bragg spots. 
    I: 2D nummpy array of type uint16
    return value: 2D numpy array the float with the same dimensions as I.
    Pixels the are part of a spot have the value 1.
    All other pixle have the value 0.
    threshold: peak detection threshold as multiple of sigma
    """
    from numpy import cast,float32,shape,sum,sqrt,array
    from pylab import seed, random_sample
    from scipy.ndimage.filters import correlate, maximum_filter, median_filter
    
    # Subtract 10 count offset from active area of image.
    I = cast[float32](I)
    I -= 10*(I>0)

    # 13 July 2014; mask beam passing through beam attenuator.
    #I[490:502,490:502] = 0. # 13 July 2014
    I[489:501,485:497] = 0. # 25 Oct 2014 

    # Add random numbers to eliminate identical values.
    seed([1]) 
    I += (random_sample(shape(I))-0.5)/10

    # Generate kernels for image filters.
    footprint0 = [[0,1,1,1,0],\
                  [1,1,1,1,1],\
                  [1,1,1,1,1],\
                  [1,1,1,1,1],\
                  [0,1,1,1,0]]
    N0 = sum(footprint0)
    footprint0 = array(footprint0)
    weights0 = footprint0*1./N0

    footprint1 = [[1,1,1],\
                  [1,1,1],\
                  [1,1,1]]
    footprint1 = array(footprint1)
    N1 = sum(footprint1)
    weights1 = footprint1*1./N1

    footprint2 = [[0,1,1,1,0],\
                  [1,0,0,0,1],\
                  [1,0,0,0,1],\
                  [1,0,0,0,1],\
                  [0,1,1,1,0]]
    footprint2 = array(footprint2)
    N2 = sum(footprint2)
    weights2 = footprint2*1./N2

    footprint3 = [[0,0,1,1,1,0,0],\
                  [0,1,0,0,0,1,0],\
                  [1,0,0,0,0,0,1],\
                  [1,0,0,0,0,0,1],\
                  [1,0,0,0,0,0,1],\
                  [0,1,0,0,0,1,0],\
                  [0,0,1,1,1,0,0]]
    footprint3 = array(footprint3)
    N3 = sum(footprint3)
    weights3 = footprint3*1./N3

    # Find spots and generate S_mask.
    S1 = correlate(I, weights1)
    S3 = median_filter(I, footprint=footprint3)
    I_max = maximum_filter(I, footprint=footprint0)
    S_mask = (I >= I_max) & ((S1-S3)/sqrt(S1/N1+S3/N3) > threshold)
    N_spots = sum(S_mask)
    S_mask = correlate(S_mask,footprint0)

    # Zero left and rightmost columns to correct for edge effects.
    S_mask[0:3,:] = False    # vertical left
    S_mask[-3:,:] = False  # vertical right
    return S_mask

def peak_integration_mask(I):
    """Generate a "spot mask" for a diffraction image with Bragg spots. 
    I: 2D nummpy array of type uint16
    return value: 2D numpy array the float with the same dimensions as I.
    Pixels the are part of a spot have a positive value.
    Pixels belonging to the background region surrounding a spot
    are assinged a negative value.
    All other pixle have the value zero.
    The positive value (same for all spots) and the negative value
    (same for all background regions) are scaled such that
    the quantity sum(mask*I) generates the background-corrected integrated
    intensity of all spots in units of detector counts.
    """
    from grow_mask import grow_mask
    from numpy import sum
    S_mask = spot_mask(I)
    # Construct spot minus background mask: SB_mask.
    B_mask = grow_mask(S_mask,1)
    B_mask &= ~S_mask
    SB_mask = S_mask-(float(sum(S_mask))/sum(B_mask))*B_mask
    return SB_mask

if __name__ == "__main__": # for testing
    # Load a test image.
    from PIL import Image
    import numpy
    image_file = "backup/peak_integration-2.2/alignment_scan/001.mccd"
    I0 = Image.open(image_file)
    I = numpy.array(I0.convert("I"), dtype = 'uint16').T

    # Time the 'peak_integration_mask' function.
    from time import time
    t0 = time()
    SB_mask = peak_integration_mask(I)    
    t1 = time()
    print "Time to find Spots and generate S_mask (s):",t1-t0

    # Perform the spot integration.
    print "Integrated intensity: ",sum(I*SB_mask)
    
    # Display the image and the 'mask'.
    from pylab import *
    chart = figure(figsize=(8,8))
    title(image_file)
    imshow(minimum(I,1000).T,cmap=cm.jet,origin='upper',interpolation='nearest')

    chart = figure(figsize=(8,8))
    title('SB_mask')
    imshow(SB_mask.T,cmap=cm.jet,origin='upper',interpolation='nearest')

    show()
