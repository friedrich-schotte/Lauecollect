"""
Bitmap manipulation
Friedrich Schotte, Hun Sun Cho, Dec 2008 - 5 Sep 2009
"""

version = "1.2"

def grow_bitmap(mask,count=1):
    """Extents the area where the pixels have to value 1 by one pixel in each
    direction, including diagnonal by the number of pixels given by the
    parameter 'count'.
    If count is 1 or ommited a single pixel grows to nine pixels.
    """
    from numpy import array,zeros

    if count < 1: return mask
    if count > 1: mask = grow_bitmap(mask,count-1)
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

def within(image,x,y):
    w,h = image.shape
    return (0 <= x < h and 0 <= y < w)

def flood_fill(image,border_color,x,y,value):
    "Flood fill on a region of non-border_color pixels."
    if not within(image,x,y) or image[x,y] == border_color: return
    edge = [(x,y)]
    image [x,y] = value
    while edge:
        newedge = []
        for (x,y) in edge:
            for (s,t) in ((x+1,y), (x-1,y), (x,y+1), (x,y-1)):
                if within(image,s,t) and \
                	image[s,t] not in (border_color,value):
                    image[s,t] = value
                    newedge.append((s,t))
        edge = newedge


if __name__ == "__main__": # for testing..
    from numpy import *
    from pylab import *
    from time import time
    mask = zeros((2048,2048),int8)
    mask[924:1124,924:2048] = 1 # to be filled
    mask[924:1124,524:724] = 1 # not to be filled

    t = time()
    flood_fill(mask,0,1024,1024,2)
    print time()-t
    
    imshow(mask.T,interpolation='nearest')
    show()
