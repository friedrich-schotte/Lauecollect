"""
Bitmap manipulation
Friedrich Schotte, Hun Sun Cho, Dec 2008
"""

version = "1.1"

def grow_mask(mask,count=1):
    """Extents the area where the pixels have to value 1 by one pixel in each
    direction, including diagnonal by the number of pixels given by the
    parameter 'count'.
    If count is 1 or ommited a single pixel grows to nine pixels.
    """
    from numpy import array,zeros

    if count < 1: return mask
    if count > 1: mask = grow_mask(mask,count-1)
    w,h = mask.shape
    mask2 = zeros((w,h),mask.dtype)
    mask2 |= mask
    mask2[0:w,0:h-1] |= mask[0:w,1:h] # move up by 1 pixel
    mask2[0:w,1:h] |= mask[0:w,0:h-1] # move down by 1 pixel
    mask2[0:w-1,0:h] |= mask[1:w,0:h] # move to the left by 1 pixel
    mask2[1:w,0:h] |= mask[0:w-1,0:h] # move to the right by 1 pixel
    
    mask2[0:w-1,0:h-1] |= mask[1:w,1:h] # move left and up by 1 pixel
    mask2[0:w-1,1:h] |= mask[1:w,0:h-1] # move left and down by 1 pixel
    mask2[1:w,0:h-1] |= mask[0:w-1,1:h] # move up and up by 1 pixel
    mask2[1:w,1:h] |= mask[0:w-1,0:h-1] # move up and down by 1 pixel

    return mask2

if __name__ == "__main__": # for testing..
    from numpy import *
    # Create a test bitmask of size 5x5 with one pixel set to 1.
    mask = zeros((5,5),uint8)
    mask[2,2] = 1
    # Grow the area maked by one ones by one pixel.
    mask2 = grow_mask(mask,1)
