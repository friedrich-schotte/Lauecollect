#!/bin/env python
"""X-ray beam stabilization
Friedrich Schotte, Nov 22, 2015 - Jun 27, 2017
"""
__version__ = "1.2" # rayonix_detector_continuous

from profile import xy_projections,FWHM,CFWHM,xvals,yvals,overloaded_pixels,SNR
from table import table
from CA import caget,caput,PV
from persistent_property import persistent_property
from EPICS_Channel_Archiver import PV_history
from time import time,sleep
from numpy import average,asarray,where
from thread import start_new_thread
from logging import debug,info,warn,error
from time_string import timestamp,date_time
from logfile import LogFile
from os.path import exists
from normpath import normpath

class Xray_Beam_Stabilization(object):
    name = "xray_beam_stabilization"

    log = LogFile(name+".log",["date time","filename","x","y","x_control","y_control","image_timestamp"])
    if log.filename == "":
        log.filename = "//mx340hs/data/anfinrud_1702/Logfiles/xray_beam_stabilization.log"
    auto_update = False
    x_PV = persistent_property("x_PV","14IDC:mir2Th.VAL") # Piezo control voltage in V
    x_read_PV = persistent_property("x_read_PV","14IDC:mir2Th.RBV") 
    y_PV = persistent_property("y_PV","14IDA:DAC1_4.VAL") # Theta in mrad
    y_read_PV = persistent_property("y_read_PV","14IDA:DAC1_4.VAL") 
    x_gain = persistent_property("x_gain",0.143) # mrad/mm
    y_gain = persistent_property("y_gain",2.7) # V/mm was: 1/3.3e-3
    x_nominal = persistent_property("x_nominal",175.927) # mm from left, 2016-03-05
    y_nominal = persistent_property("y_nominal",174.121) # mm from top,  2016-03-05
    history_length = persistent_property("history_length",5) 
    average_samples = persistent_property("average_samples",5)
    x_enabled = False
    y_enabled = False
    ROI_width = persistent_property("ROI_width",1.0) # mm
    x_ROI_center = persistent_property("x_ROI_center",175.9) # mm from left
    y_ROI_center = persistent_property("y_ROI_center",174.1) # mm from top    
    min_SNR = persistent_property("min_SNR",5.0) # signal-to-noise ratio
    # Use only images matching this pattern, e.g. "5pulses"
    history_filter = persistent_property("history_filter","")     
    analysis_filter = persistent_property("analysis_filter","")     

    def __init__(self):
        """"""
        start_new_thread(self.keep_updated,())
    
    def keep_updated(self):
        while True:
            try:
                if self.auto_update: self.update()
                if self.x_enabled: self.apply_x_correction()
                if self.y_enabled: self.apply_y_correction()
            except Exception,m: info("xray_beam_stabilization: %s" % m); break
            sleep(1)

    def update(self):
        t = self.image_timestamp
        if t != 0 and abs(t - self.last_image_timestamp) >= 0.1:
            f = self.image_basename
            x,y = self.beam_position
            xc,yc = self.x_control,self.y_control
            self.log.log(f,x,y,xc,yc,t)

    @property
    def x_average(self): return average(self.x_samples)

    @property
    def y_average(self): return average(self.y_samples)

    @property
    def x_history(self): return self.history("x",count=self.history_length)

    @property
    def y_history(self): return self.history("y",count=self.history_length)

    @property
    def t_history(self): return self.history("date time",count=self.history_length)

    @property
    def x_samples(self): return self.history("x",count=self.average_samples)

    @property
    def y_samples(self): return self.history("y",count=self.average_samples)

    @property
    def last_image_timestamp(self):
        t = self.history("image_timestamp",count=1)
        t = t[0] if len(t)>0 else 0 
        return t

    def get_x_control(self): return tofloat(caget(self.x_read_PV))
    def set_x_control(self,value): return caput(self.x_PV,value)
    x_control = property(get_x_control,set_x_control)

    def get_y_control(self): return tofloat(caget(self.y_read_PV))
    def set_y_control(self,value): return caput(self.y_PV,value)
    y_control = property(get_y_control,set_y_control)

    def get_x_control_average(self): return average(self.x_control_samples)
    def set_x_control_average(self,value): self.x_control = value
    x_control_average = property(get_x_control_average,set_x_control_average)

    def get_y_control_average(self): return average(self.y_control_samples)
    def set_y_control_average(self,value): self.y_control = value
    y_control_average = property(get_y_control_average,set_y_control_average)

    @property
    def x_control_samples(self):
        return self.history("x_control",count=self.average_samples)
    
    @property
    def y_control_samples(self):
        return self.history("y_control",count=self.average_samples)

    @property
    def x_control_history(self):
        return self.history("x_control",count=self.history_length)

    @property
    def y_control_history(self):
        return self.history("y_control",count=self.history_length)

    @property
    def x_control_corrected(self):
        """Value for the y control in roder to bring the y position back to
        its nominal value"""
        x_control = self.x_control_average - \
            (self.x_average - self.x_nominal)*self.x_gain
        return x_control

    @property
    def y_control_corrected(self):
        """Value for the y control in roder to bring the y position back to
        its nominal value"""
        y_control = self.y_control_average - \
            (self.y_average - self.y_nominal)*self.y_gain
        return y_control

    def apply_correction(self):
        self.apply_x_correction()
        self.apply_y_correction()        

    def apply_x_correction(self):
        if self.image_OK:
            self.x_control = self.x_control_corrected

    def apply_y_correction(self):
        if self.image_OK:
            self.y_control = self.y_control_corrected

    @property
    def x_beam(self): return self.beam_position[0]

    @property
    def y_beam(self): return self.beam_position[1]

    @property
    def beam_position_HyunSun(self):
        from transmissive_beamstop import beam_center
        x,y = beam_center(self.image)
        return x,y

    @property
    def beam_position(self):
        xprofile,yprofile = xy_projections(self.image,self.ROI_center,self.ROI_width)
        x,y = CFWHM(xprofile),CFWHM(yprofile)
        return x,y

    @property
    def ROI_center(self): return self.x_ROI_center,self.y_ROI_center

    @property
    def image_OK(self):
        if self.image_overloaded: OK = False
        elif self.SNR < self.min_SNR: OK = False
        elif self.analysis_filter not in self.image_basename: OK = False
        else: OK = True
        return OK

    @property
    def image_overloaded(self):
        return overloaded_pixels(self.image,self.ROI_center,self.ROI_width)

    @property
    def SNR(self):
        xprofile,yprofile = xy_projections(self.image,self.ROI_center,self.ROI_width)
        return (SNR(xprofile)+SNR(yprofile))/2

    @property
    def image(self):
        from numimage import numimage
        from numpy import uint16
        filename = self.image_filename
        if filename: image = numimage(filename)
        else: image = self.default_image
        return image

    @property
    def default_image(self):
        from numimage import numimage
        from numpy import uint16
        image = numimage((3840,3840),pixelsize=0.0886,dtype=uint16)+10
        return image

    @property
    def image_timestamp(self):
        """Full pathname of the last recorded image"""
        from os.path import getmtime
        from normpath import normpath
        filename = self.image_filename
        t = getmtime(normpath(filename)) if filename else 0
        return t

    @property
    def image_filename(self):
        """Full pathname of the last recorded image"""
        image_filenames = self.image_filenames
        if len(image_filenames)>0: image_filename = image_filenames[-1]
        else: image_filename = ""
        self.last_image_filename = image_filename
        return image_filename

    last_image_filename = ""

    @property
    def image_filenames(self):
        """Full pathnames of the last recorded images"""
        from rayonix_detector_continuous import ccd
        return ccd.image_filenames
        
    @property
    def image_basename(self):
        """Filename of the last recorded image, with out directory"""
        from os.path import basename
        return basename(self.image_filename)

    def history(self,name,count):
        """Log history filtered by image filename pattern"""
        from numpy import array,chararray
        filename = self.log.history("filename",count=count)
        values = self.log.history(name,count=count)
        filename = array(filename,str).view(chararray)
        match = filename.find(self.history_filter)>=0
        values = array(values)[match]
        return values

xray_beam_stabilization = Xray_Beam_Stabilization()

def tofloat(x):
    """Convert to floating point number without throwing exception"""
    from numpy import nan
    try: return float(x)
    except: return nan


if __name__ == "__main__":
    from pdb import pm
    self = xray_beam_stabilization # for debugging
    print('self.log.filename = %r' % self.log.filename)
    print('self.history_filter = %r' % self.history_filter)
    print('self.history("x",count=10)')
    print('self.x_history')
    print('self.update()')
