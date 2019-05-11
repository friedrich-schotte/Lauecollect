#!/usr/bin/env python
"""Find the position of the direct X-ray beam in the X-ray detector,
attenuated by a transmissive beam stop.
Author: Hyun Sun Cho, Aug 26 2014 - Feb 23 2016
Friedrich Schotte, Feb 29, 2016 = Mar 1, 2016
"""
from numimage import numimage
from xray_beam_stabilization import xray_beam_stabilization
from numpy import *
from scipy.ndimage.filters import gaussian_filter,gaussian_gradient_magnitude

__version__ = "1.0.1" # speedup 4 s -> 1 ms, caching mask

mask_filename = "//mx340hs/data/anfinrud_1602/Logfiles/beamstop-1.png"
offset  = 10.0

# x-ray beam center
# estimated x and y pixel of x-ray beamcenter
xinit, yinit = 1985.249, 1964.92
window0 = 2*10+1 #7 #15 # full width, H and V are same

# beamstop center
xbsc, ybsc = 1986, 1964 #1983.,1968. #2*992.0, 2*981.0 # beamstop center
w,h = 3840, 3840 # 2x2 binning 
pxl_size = 0.1772/2 # 2x2 binning [mm] 

# roi window indices around beam center
x_i = round(xinit-window0/2)
x_f = round(x_i+window0)
y_i = round(yinit-window0/2)
y_f = round(y_i+window0)

def setup():
    """Calculate beamstop mask"""
    global bc_roi,Beamstopid_roi,mask

    mask_image = numimage(mask_filename)
    mask = mask_image[x_i:x_f,y_i:y_f]
    mask = mask_image[x_i+1.:x_f+1.,y_i:y_f]

    # beamstop - maximum ring , circle or ellipse?
    x_indices,y_indices = indices((w,h))
    # beamstop assuming ellipse - beamstop roi
    ellip_x, ellip_y = 2*4.0, 2*4.0 # pixels 

    # beamstopid - flat-area inside beamstop, assuming ellipse
    ellip_xid, ellip_yid = ellip_x*0.75, ellip_y*0.75
    distid_criteria = sqrt(ellip_yid**2*(x_indices-xbsc)**2+ellip_xid**2*(y_indices-ybsc)**2)
    Beamstopid = distid_criteria<(ellip_xid*ellip_yid)
    Beamstopid_roi = Beamstopid[x_i:x_f,y_i:y_f]

    # beamcenter roi  
    # tweak beam center roi to avoid spurious scattering
    beam_rx, beam_ry = 4.0, 4.0 # 5.0, 5.0 # pixels
    # just a little shift by 0.5 pixel to avoid beam spillage
    #Beamcenter_criteria =\
    #     sqrt(beam_ry**2*(x_indices-(xinit+0.5))**2+beam_rx**2*(y_indices-(yinit-1.0))**2) 
    Beamcenter_criteria =\
         sqrt(beam_ry**2*(x_indices-(xinit))**2+beam_rx**2*(y_indices-(yinit))**2)
    Beamcenter = Beamcenter_criteria < (beam_rx*beam_ry)
    bc_roi = Beamcenter[x_i:x_f,y_i:y_f]

def beam_center(image):
    """x,y in mm from top left corner"""
    if not "bc_roi" in globals(): setup()
    
    pixelsize = image.pixelsize

    Iroi_raw = image[x_i:x_f,y_i:y_f]
    mask_sat = (Iroi_raw == 65535)
    Iroi = image[x_i:x_f,y_i:y_f]-offset

    BSmin = Iroi[Beamstopid_roi].min()

    # generating "gaussian-filtered beamstop" set proper sigma 
    sigma_ = 0.6 #0.7 #0.6   # ~100/89./2.355 - 100um psf, 89um pixel by rayonix detector  
    sigma_2_scale = 9. #5.0 #10.  
    gfx_factor = 0.345 #0.1 #0.3 
    Ig_gf0 = gaussian_filter(Iroi*~mask+BSmin*mask,sigma=sigma_,order=0)
    Ig_gfx = gaussian_filter(Iroi*~mask+BSmin*mask,sigma=sigma_2_scale*sigma_,order=0) 
    try: Ig_gf = Ig_gf0 + gfx_factor*(Ig_gfx-Ig_gfx[mask & (Ig_gfx>0)].min())*mask
    except ValueError: Ig_gf = Ig_gf0 

    Ig_gf += (Iroi[mask].min()-Ig_gf[mask].min())*mask
    I_xray = Iroi-Ig_gf

    bc_roi_mod = bc_roi & ~mask_sat 
    xc = sum(sum(I_xray*bc_roi_mod,axis=1)*range(window0))/sum(I_xray*bc_roi_mod)
    yc = sum(sum(I_xray*bc_roi_mod,axis=0)*range(window0))/sum(I_xray*bc_roi_mod)      
    Iroi_int = sum(I_xray*bc_roi) # saturation pixels ?
    center_x = (xc+x_i)*pixelsize #[mm]
    center_y = (yc+y_i)*pixelsize #[mm]
    center_x,center_y = float(center_x),float(center_y)
    return center_x,center_y

if __name__ == "__main__":
    from pdb import pm
    from time import time
    print('image = xray_beam_stabilization.image')
    print('beam_center(image)')
