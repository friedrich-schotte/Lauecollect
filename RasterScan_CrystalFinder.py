#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  3 12:12:27 2017

@author: philipa
"""

import os
from numpy import *
from pylab import *
from PIL import Image
from scipy import interpolate
from time import time
from matplotlib.backends.backend_pdf import PdfPages
import sys; sys.path += ["//Mirror/Femto/C/All\ Projects/Software/TWAX/Friedrich/",\
                         "//Mirror/Femto/C/All\ Projects/Software/TReX/Python/"]
from scipy.ndimage.filters import gaussian_gradient_magnitude, gaussian_filter
from find import find
from os.path import getsize

def image_load_ROI(name,ROI):
    """Load image and truncate dimensions according to ROI;
        ROI: [x0,y0,w] with w odd so the beam center is in the center pixel;
        Returns I"""
    x0,y0,w = ROI
    xmin,xmax = x0-(w-1)/2,x0+(w-1)/2+1
    ymin,ymax = y0-(w-1)/2,y0+(w-1)/2+1
    I = array(Image.open(name).convert("I"),float32)[xmin:xmax,ymin:ymax]
    return I

def RS_indices(name):
    """Extract raster-scan indices (row,column) from name; returns (r,c)."""
    indices = name.split("/")[-1].split("_")[0].split(",")
    R = int(indices[0])
    C = int(indices[1])
    return R,C

def image_SAXS_intensity(I_array,radius = 15):
    """Given I_array, calculate integrated SAXS intensity near beamstop
    Returns [I_SAXS]"""
    from numpy import indices
    N_images,w,h = shape(I_array)
    xmin,xmax = (w-1)/2-radius,(w-1)/2+radius+1
    ymin,ymax = (h-1)/2-radius,(h-1)/2+radius+1
    x_indices,y_indices = indices((2*radius+1,2*radius+1))
    SAXS_mask = sqrt((y_indices-radius)**2+(x_indices-radius)**2) < radius
    SAXS_mask[radius-1:radius+2,radius-1:radius+2] = 0
    SAXS_mask = array(SAXS_mask)
    N_SAXS = sum(SAXS_mask)
    BKG_mask = ~SAXS_mask
    BKG_mask[radius-1:radius+2,radius-1:radius+2] = 0
    N_BKG = sum(BKG_mask)
    I_BKG = (I_array[:,xmin:xmax,ymin:ymax]*BKG_mask).sum(axis=2).sum(axis=1)
    I_sum = (I_array[:,xmin:xmax,ymin:ymax]*SAXS_mask).sum(axis=2).sum(axis=1)
    I_SAXS = I_sum - I_BKG*N_SAXS/float(N_BKG)
    return I_SAXS   

def image_beamstop_intensity(I_array,scale=0.6385):
    """Given I_array, calculate transmitted intensity through the beamstop;
       scale, determined experimentally, corrects background subtraction error;
       Returns I_BS"""
    N_images,w,h = shape(I_array)
    x0,y0 = (w-1)/2,(h-1)/2
    I_sum3x3 = I_array[:,x0-1:x0+2,y0-1:y0+2].sum(axis=2).sum(axis=1)
    I_sum5x5 = I_array[:,x0-2:x0+3,y0-2:y0+3].sum(axis=2).sum(axis=1)
    I_BS = I_sum3x3 - scale*(9./16)*(I_sum5x5-I_sum3x3)
    print "I_BS Standard deviation: ", I_BS.std()
    return I_BS  

def spotfinder(I,SNR = 10):
    """Finds spots whose Signal-to-Noise Ratio exceeds SNR (default = 10);
    returns S_mask"""
    from scipy.ndimage.filters import correlate, maximum_filter, minimum_filter
 
    w,h = shape(I)
    
    footprint0 = [[1,1,1],
                  [1,1,1],
                  [1,1,1]]
    footprint0 = array(footprint0)
    N0 = sum(footprint0) #9
    
    footprint1 = [[1,1,1],
                  [1,0,1],
                  [1,1,1]]
    footprint1 = array(footprint1)

    I_max = maximum_filter(I,footprint=footprint0)
    I_min = minimum_filter(I,footprint=footprint1)
    test1 = I == I_max
    test2 = ((I_max-I_min)/sqrt(I_max + I_min) > SNR)
    S_mask = test1 & test2                
    #S_mask = array(S_mask,int16)
    
    return S_mask

def crystal_COM(C_image):
    """Determine Center-Of-Mass coordinates for each diffraction spot;
    return coordinates."""
    N_spots = len(C_image)
    r0 = [[-1,-1,-1],[0,0,0],[1,1,1]]
    c0 = [[-1,0,1],[-1,0,1],[-1,0,1]]  
    
    COM = []
    for i in range(N_spots):
        row,col = where(C_image[i] == C_image[i].max())
        r_indices = row + r0 
        c_indices = col + c0
        try:
            C_sub = C_image[i,r_indices,c_indices]
            COM.append([(C_sub*c_indices).sum()/C_sub.sum(),(C_sub*r_indices).sum()/C_sub.sum()])
        except:
            COM.append([nan,nan])  
    
    return array(COM)


close("all") # Close all open charts.
    
# Detector parameters.
x0,y0,w = 1988/4,int(1965/4),481 # beam center and Region of Interest dimension (odd)
ROI = [x0,y0,w] # Region Of Interest
wavelength = 1.0358 # in Angstroms.
distance = 185.8 #  mm.
pixelsize = 0.08854 # in mm.
    
# Find Raster-Scan images according to name.
analysis_root = "/Volumes/data-3/anfinrud_1711-1/Data/Laue/Lyz/Lyz-1/alignment/"
RS_images = array(find(analysis_root,name="*.mccd",exclude=[]))
sort_indices = argsort(RS_images)
RS_images = RS_images[sort_indices]

t0 = time()
row = []
col = []
I_array = [] # Image array
for name in RS_images: # Process Images one at a time.
    Ri,Ci = RS_indices(name)
    row.append(Ri)
    col.append(Ci)
    I_array.append(image_load_ROI(name,ROI))
I_array = array(I_array)
N_Ri = max(row)+1
N_Ci = max(col)+1
N_images = len(I_array)

t1 = time()
print "Time to load",N_images,"images (s):", t1-t0

I_BS = image_beamstop_intensity(I_array)
I_BS_image = I_BS.reshape((N_Ri,N_Ci))
t2 = time()
print "Time to calculate I_BS (s): ", t2-t1

I_SAXS = image_SAXS_intensity(I_array)
I_SAXS_image = I_SAXS.reshape((N_Ri,N_Ci))
t3 = time()
print "Time to calculate I_SAXS (s): ", t3-t2

offset = ((I_array[0] > 0)*10).sum()    # 10 count offset
background = gaussian_filter(I_array,5)  # approximate background by smoothing image
signal = (I_array - background) # diffracted photons
S_mask = signal/sqrt(I_array + 5) > 5 # S/N criterion; readout variance ~5
signal = signal*S_mask

D_pixels = S_mask.sum(axis=1).sum(axis=1) # number of pixels with diffraction
D_pixels_image = D_pixels.reshape((N_Ri,N_Ci))

D_photons = signal.sum(axis=1).sum(axis=1) - I_SAXS# sum of diffracted photons in each image
D_photons_image = D_photons.reshape((N_Ri,N_Ci))

S_photons = background.sum(axis=1).sum(axis=1) - offset - D_photons
S_photons_image = S_photons.reshape((N_Ri,N_Ci))

Xtal_mask = spotfinder(D_photons_image,100)
Y0,X0 = where(Xtal_mask)

t4 = time()
print "Time to process",N_images,"images (s):", t4-t3

ion()

chart = figure(figsize=(8,8))
title('I_BS_image')
imshow(I_BS_image, cmap=cm.jet, origin = 'upper', interpolation = 'nearest')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)

chart = figure(figsize=(8,8))
title('I_SAXS_image')
imshow(I_SAXS_image, cmap=cm.jet, origin = 'upper', interpolation = 'nearest')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)

chart = figure(figsize=(8,8))
title('S_photons_image')
imshow(S_photons_image, cmap=cm.jet, origin = 'upper', interpolation = 'nearest')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)

chart = figure(figsize=(8,8))
title('D_pixels_image')
imshow(D_pixels_image, cmap=cm.jet, origin = 'upper', interpolation = 'nearest')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)

chart = figure(figsize=(8,8))
title('D_photons_image')
imshow(D_photons_image, cmap=cm.jet, origin = 'upper', interpolation = 'nearest')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)
scatter(X0,Y0,s=4,color = 'black')
ticks = arange(0,N_Ri,2)
yticks(ticks)

D_max = where(D_photons == D_photons.max())[0][0]

D_max = 255
if True:
    chart = figure(figsize=(8,8))
    title('background['+str(D_max)+']')
    imshow(background[D_max], cmap=cm.jet, origin = 'upper', interpolation = 'nearest')
    colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)
    
    chart = figure(figsize=(8,8))
    title('signal['+str(D_max)+']')
    imshow(log10(signal[D_max]+1), cmap=cm.jet, origin = 'upper', interpolation = 'nearest')
    colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)

show()