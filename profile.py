"""Beam Profile Analysis
Author: Friedrich Schotte, Mar 2 2016 - Mar 5, 2017
"""
__version__ = "1.0.1" # nan

def xy_projections(image,(cx,cy),d):
    """Calculate a horizonal and vertical projections of a region of interest
    of the image.
    image: 2D numpy array, must have "pixelsize" attribute
    cx,cy: center in mm
    d: diameter in mm"""
    from numpy import rint,array,sum,nansum,isnan

    # Clip to ROI (region of interest)
    pixelsize = image.pixelsize
    ROI = cx-d/2,cx+d/2,cy-d/2,cy+d/2
    ixmin,ixmax,iymin,iymax = rint(array(ROI)/pixelsize).astype(int)
    image = image[ixmin:ixmax,iymin:iymax]
    # Generate projection on the X and Y axis.
    xproj = nansum(image,axis=1)/sum(~isnan(image),axis=1)
    yproj = nansum(image,axis=0)/sum(~isnan(image),axis=0)
    # Scale projections in units of mm.
    xscale = [(ixmin+i+0.5)*pixelsize for i in range(0,len(xproj))]
    yscale = [(iymin+i+0.5)*pixelsize for i in range(0,len(yproj))]
    xprofile = zip(xscale,xproj)
    yprofile = zip(yscale,yproj)

    return xprofile,yprofile

def overloaded_pixels(image,(cx,cy),d):
    """Number pixels marked as overloaded (intensity 65535).
    image: 2D numpy array, must have "pixelsize" attribute
    cx,cy: center in mm
    d: diameter in mm"""
    from numpy import rint,array,sum,nansum,isnan
    # Clip to ROI (region of interest)
    pixelsize = image.pixelsize
    ROI = cx-d/2,cx+d/2,cy-d/2,cy+d/2
    ixmin,ixmax,iymin,iymax = rint(array(ROI)/pixelsize).astype(int)
    image = image[ixmin:ixmax,iymin:iymax]
    # Count overloaded pixels.
    n = int(sum(image == 65535))
    return n

def x_projection(image,(cx,cy),d):
    """Calculate a horizonal and vertical projections of a region of interest
    of the image.
    image: 2D numpy array, must have "pixelsize" attribute
    cx,cy: center in mm
    d: diameter in mm"""
    from numpy import rint,array,sum,nansum,isnan
    # Clip to ROI (region of interest)
    pixelsize = image.pixelsize
    ROI = cx-d/2,cx+d/2,cy-d/2,cy+d/2
    ixmin,ixmax,iymin,iymax = rint(array(ROI)/pixelsize).astype(int)
    image = image[ixmin:ixmax,iymin:iymax]
    # Generate projection on the X and Y axis.
    xproj = nansum(image,axis=1)/sum(~isnan(image),axis=1)
    # Scale projections in units of mm.
    xscale = [(ixmin+i+0.5)*pixelsize for i in range(0,len(xproj))]
    xprofile = zip(xscale,xproj)
    return xprofile

def y_projection(image,(cx,cy),d):
    """Calculate a horizonal and vertical projections of a region of interest
    of the image.
    image: 2D numpy array, must have "pixelsize" attribute
    cx,cy: center in mm
    d: diameter in mm"""
    from numpy import rint,array,sum,nansum,isnan
    # Clip to ROI (region of interest)
    pixelsize = image.pixelsize
    ROI = cx-d/2,cx+d/2,cy-d/2,cy+d/2
    ixmin,ixmax,iymin,iymax = rint(array(ROI)/pixelsize).astype(int)
    image = image[ixmin:ixmax,iymin:iymax]
    # Generate projection on the X and Y axis.
    yproj = nansum(image,axis=0)/sum(~isnan(image),axis=0)
    # Scale projections in units of mm.
    yscale = [(iymin+i+0.5)*pixelsize for i in range(0,len(yproj))]
    yprofile = zip(yscale,yproj)
    return yprofile

def FWHM(data):
    """Calculates full-width at half-maximum of a positive peak of a curve
    given as list of [x,y] values"""
    from numpy import nan
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
    from numpy import nan
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
