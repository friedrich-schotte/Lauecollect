# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 08:33:58 2017

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
from scipy.ndimage.filters import gaussian_gradient_magnitude
from find import find
from os.path import getsize

def image_SVD(I):
    """Performs SVD on array of images.
    Returns U,s,VT.
    """
    print "PERFORMING SINGULAR VAULE DECOMPOSITION OF IMAGES..."
    N_images,w,h = shape(I)
    I = reshape(I,(N_images,w*h))       # Reshape 3D array to 2D.
    U,s,VT = svd(I.T,full_matrices=0)
    U = reshape(U.T,(N_images,w,h))     # Reshape 2D array to 3D.
    for i in arange(N_images):
        if abs(U[i].max()) < abs(U[i].min()):
            U[i] *= -1
            VT[i] *= -1
    return U,s,VT

def image_load_ROI(name,ROI):
    """Load image and truncate dimensions according to ROI;
        ROI: [x0,y0,w] with w odd so the beam center is in the center pixel;
        Returns I"""
    x0,y0,w = ROI
    xmin,xmax = x0-(w-1)/2,x0+(w-1)/2+1
    ymin,ymax = y0-(w-1)/2,y0+(w-1)/2+1
    I = array(Image.open(name).convert("I"),float32).T[xmin:xmax,ymin:ymax]
    return I

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
 
def image_mask(CS_mask,radius = 15):
    """Masks 2 pixels along edges and central SAXS region, which is 
    specified by radius in pixels (default = 15)."""
    from numpy import indices
    w,h = shape(CS_mask)
    x_indices,y_indices = indices((w,h))
    SAXS_mask = sqrt((y_indices-(h-1)/2)**2+(x_indices-(w-1)/2)**2) < radius
    Border_mask = (y_indices<2) | (y_indices>(h-3)) | \
                  (x_indices<2) | (x_indices>(w-3))
    CS_mask *= ~(SAXS_mask | Border_mask)
    return CS_mask
    
def image_spotfinder(I,SNR = 10):
    """Finds spots whose Signal-to-Noise Ratio exceeds SNR (default = 10);
    returns S_mask"""
    from scipy.ndimage.filters import correlate, maximum_filter, median_filter
   
    RO_var = 2.3**2 # Readout variance for detector
    #SNR = 10 # Signal-to-noise ratio threshold to be identified as a spot
    
    w,h = shape(I)
    
    footprint0 = [[1,1,1],
                  [1,1,1],
                  [1,1,1]]
    footprint0 = array(footprint0)
    N0 = sum(footprint0) #9

    footprint1 = [[1,1,1,1,1],
                  [1,0,0,0,1],
                  [1,0,0,0,1],
                  [1,0,0,0,1],
                  [1,1,1,1,1]]
    footprint1 = array(footprint1) 
    N1 = sum(footprint1) #16

    seed([1])    
    I += 0.1*(random_sample((w,h))-0.5)
    I_max = maximum_filter(I,footprint=footprint0)
    I_median = median_filter(I,footprint=footprint1)
    I_int = correlate(I,footprint0)
    IC = (I_int-N0*I_median) # Integrated counts, Background-subtracted 
    S_mask = (I == I_max) & \
             (IC/sqrt(I_int+(N0**2/N1)*I_median+RO_var*N0*(1+N0/N1)) > SNR)                
    S_mask = array(S_mask,int16)
    
    return S_mask

def image_spotselect(CS_mask,N_min = 2):
    """Finds spots that are represented in N_min or more images,
    and 4 or more pixels from any other spot;
    returns S_mask."""
    S_mask = (CS_mask > 0) 
    
    N_spots = sum(S_mask)
    X0,Y0 = where(S_mask)
    close = zeros(N_spots)
    for i in range(N_spots):
        for j in range(N_spots):
            if (i <> j) & (close[i] == 0):
                close[i] = sqrt((X0[i]-X0[j])**2+(Y0[i]-Y0[j])**2) < 4
    S_mask[X0[where(close == 1)],Y0[where(close == 1)]] = 0
    
    S_mask &= (CS_mask >= N_min) # Select spots found in N_min+ images
    
    return S_mask
    
def image_spotintegrate(I_array,S_mask):
    """Integrate spot locations defined by S_mask in I_array;
    returns array of integrated counts [C], corresponding Variance [V],
    and spot indices X0,Y0.""" 
    
    N_images,w,h = shape(I_array)
    X0,Y0 = where(S_mask)
    N_spots = len(X0)
    
    x_center = (w-1)/2
    y_center = (h-1)/2 
    
    footprint0 = [[1,1,1],\
                  [1,1,1],\
                  [1,1,1]]
    footprint0 = array(footprint0)
    N0 = sum(footprint0) #9
    indices0 = where(footprint0)    

    footprint1 = [[1,1,1,1,1],\
                  [1,0,0,0,1],\
                  [1,0,0,0,1],\
                  [1,0,0,0,1],\
                  [1,1,1,1,1]]
    footprint1 = array(footprint1) 
    indices1 = where(footprint1)
    
    C = [] # Counts
    V = [] # Variance
    for i in range(N_spots):        
        x_indices0 = X0[i] + indices0[0]-1
        y_indices0 = Y0[i] + indices0[1]-1
        I_int = I_array[:,x_indices0,y_indices0].sum(axis=1)
        x_indices1 = X0[i] + indices1[0]-2
        y_indices1 = Y0[i] + indices1[1]-2
        I_bkg = median(I_array[:,x_indices1,y_indices1],axis=1)
        C.append(I_int-N0*I_bkg)
        V.append(I_int)
    C = array(C)
    V = array(V)
    C = C.reshape((N_spots,N_images))
    V = V.reshape((N_spots,N_images))
    C_sum = C.sum(axis=1)
    sort_indices = argsort(C_sum)[::-1]
    C = C[sort_indices,:]
    V = V[sort_indices,:]
    return C,V
            
def RS_indices(name):
    """Extract raster-scan indices (row,column) from name; returns (r,c)."""
    indices = name.split("/")[-1].split("_")[0].split(",")
    R = int(indices[0])
    C = int(indices[1])
    return R,C

def crystal_COM(C_image):
    """Determine Center-Of-Mass coordinates for each diffraction spot;
    return coordinates."""
    N_spots = len(C_image)
    #r0 = [[-1,-1,-1],[0,0,0],[1,1,1]]
    #c0 = [[-1,0,1],[-1,0,1],[-1,0,1]] 
    r0 = [[-2,-2,-2,-2,-2],[-1,-1,-1,-1,-1],[0,0,0,0,0],[1,1,1,1,1],[2,2,2,2,2]]
    c0 = [[-2,-1,0,1,2],[-2,-1,0,1,2],[-2,-1,0,1,2],[-2,-1,0,1,2],[-2,-1,0,1,2]]  
    
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
    COM = array(COM)
    
   # group = ones(N_spots)*-1 
    #k=0
    #group[0] = 0
    #for i in range(N_spots):
    #    for j in range(N_spots):
    #        if (j <> i) & (group[j] == -1):
    #            if sqrt((COM[i,0]-COM[j,0])**2+(COM[i,1]-COM[j,1])**2) < 0.5:
    #                group[j] = k
    #S_mask[X0[where(close == 1)],Y0[where(close == 1)]] = 0
    
    #S_mask &= (CS_mask >= N_min)    
    
    return array(COM)

    
close("all") # Close all open charts.
    
# Detector parameters.
x0,y0,w = 496,490,161 # beam center and Region of Interest dimension (odd)
ROI = [x0,y0,w] # Region Of Interest
wavelength = 1.0358 # in Angstroms.
distance = 185.8 #  mm.
pixelsize = 0.079 # in mm.
    
# Find Raster-Scan images according to name.
analysis_root = "/Volumes/data-1/anfinrud_1711-1/Data/Laue/Lyz/Lyz-1/alignment"
RS_images = array(find(analysis_root,name="*.mccd",exclude=[]))

t0 = time()

CS_mask = zeros((w,w),dtype = "int16") # Combined Spot mask
row = []
col = []
I_array = [] # Image array
for name in RS_images: # Process Images one at a time.
    Ri,Ci = RS_indices(name)
    row.append(Ri)
    col.append(Ci)
    Ii = image_load_ROI(name,ROI)
    S_mask = image_spotfinder(Ii,30)
    CS_mask += S_mask
    I_array.append(Ii)
I_array = array(I_array)
N_Ri = max(row)+1
N_Ci = max(col)+1
CS_mask = image_mask(CS_mask)
t1 = time()
print "Time to find",sum(CS_mask >0),"spots (s):", t1-t0

S_mask = image_spotselect(CS_mask)
#X0,Y0 = where(S_mask)

t2 = time()
N_spots = sum(S_mask)
print "Time to select", N_spots,"spots (s):", t2-t1

C,V = image_spotintegrate(I_array,S_mask)


t3 = time()
print "Time to integrate images (s): ", t3-t2

C_image = reshape(C,(N_spots,N_Ri,N_Ci))
COM = crystal_COM(C_image)
#print COM



t3 = time()
I_BS = image_beamstop_intensity(I_array)
t4 = time()
print "Time to calculate I_BS (s): ", t4-t3
I_SAXS = image_SAXS_intensity(I_array)
t5 = time()
print "Time to calculate I_SAXS (s): ", t5-t4


for j in range(N_spots):
    chart = figure(figsize=(6,8))
    title('Spot['+str(j)+']')
    imshow(C_image[j], cmap=cm.jet, origin = 'lower', interpolation = 'nearest')
    colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)
    scatter(COM[j,0],COM[j,1],marker = 'o',s=175,facecolors='none', edgecolors='black') 
   
chart = figure(figsize=(6,8))
title('C.sum()')
imshow(C_image.sum(axis=0), cmap=cm.jet, origin = 'lower', interpolation = 'nearest')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)
scatter(COM[:,0],COM[:,1],marker = 'o',s=175,facecolors='none', edgecolors='black') 
 
chart = figure(figsize=(8,8))
title('I_BS')
plot(I_BS)
grid(True)

chart = figure(figsize=(8,8))
title('I_BS')
I_BS_image = I_BS.reshape((N_Ri,N_Ci))
imshow(I_BS_image, cmap=cm.jet, origin = 'lower', interpolation = 'nearest')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)
  
chart = figure(figsize=(8,8))
title('I_SAXS')
I_SAXS_image = I_SAXS.reshape((N_Ri,N_Ci))
imshow(I_SAXS_image, cmap=cm.jet, origin = 'lower', interpolation = 'nearest')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)

chart = figure(figsize=(8,8))
title('sqrt(I_sum)')
from numpy import indices
radius = 15
N_images,h,w = shape(I_array)
x_indices,y_indices = indices((w,h))
SAXS_mask = sqrt((y_indices-(h-1)/2)**2+(x_indices-(w-1)/2)**2) < radius
I_sum = array(I_array.sum(axis=0),float32)
I_sum[where(SAXS_mask)]=nan
imshow(sqrt(I_sum.T), cmap=cm.jet, origin = 'upper', interpolation = 'nearest')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 0.823)
X0,Y0 = where(CS_mask > 0)
scatter(X0,Y0,s=4,color = 'black')
X0,Y0 = where(S_mask)
scatter(X0,Y0,s=8,color = 'red')

chart = figure(figsize=(8,8))
title('sqrt(C)')
sqrtC = sqrt(C)
sqrtC[where(isnan(sqrtC))]=0
imshow(sqrtC, cmap=cm.jet, origin = 'lower', interpolation = 'nearest',aspect = 'auto')
colorbar(orientation = 'vertical', pad = 0.0, shrink = 1)

show()
