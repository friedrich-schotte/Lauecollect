"""
Optimize the X-ray beam position on the X-ray area detector.

Friedrich Schotte, Nov 1, 2016 - Nov 2, 2016
"""
from instrumentation import MirrorH,MirrorV,shg,svg,ccd,timing_system
from profile import xy_projections,FWHM,CFWHM,xvals,yvals,overloaded_pixels,SNR
from Ensemble_SAXS_pp import Ensemble_SAXS
from CA import caget,caput,PV
from persistent_property import persistent_property
from numpy import average,asarray,where
from thread import start_new_thread
from time import sleep,time
from ImageViewer import show_images
from logfile import LogFile
from os.path import exists
from normpath import normpath
from logging import debug,info,warn,error

__version__ = "1.0"

class Xray_Beam_Position_Check(object):
    name = "xray_beam_position_check"

    class Settings(object):
        name = "settings"
        # X-Ray beam steering controls.
        # Horizontal deflection mirror jacks
        def get_x1_motor(self): return MirrorH.m1.prefix
        def set_x1_motor(self,value): MirrorH.m1.prefix = value
        x1_motor = property(get_x1_motor,set_x1_motor)
        def get_x2_motor(self): return MirrorH.m2.prefix
        def set_x2_motor(self,value): MirrorH.m2.prefix = value
        x2_motor = property(get_x2_motor,set_x2_motor)

        def get_y_motor(self): return MirrorV.prefix
        def set_y_motor(self,value): MirrorV.prefix = value
        y_motor = property(get_y_motor,set_y_motor)
        
        # To narrow down aperture upstream of the detector for higher senitivity 
        def get_x_aperture_motor(self): return shg.prefix
        def set_x_aperture_motor(self,value): shg.prefix = value
        x_aperture_motor = property(get_x_aperture_motor,set_x_aperture_motor)
        def get_y_aperture_motor(self): return svg.prefix
        def set_y_aperture_motor(self,value): svg.prefix = value
        y_aperture_motor = property(get_y_aperture_motor,set_y_aperture_motor)

        x_aperture_norm = persistent_property("x_aperture_norm",0.150)
        y_aperture_norm = persistent_property("y_aperture_norm",0.050)
        x_aperture_scan = persistent_property("x_aperture_scan",0.050)
        y_aperture_scan = persistent_property("y_aperture_scan",0.020)

        def get_x_aperture(self): return shg.command_value
        def set_x_aperture(self,value): shg.command_value = value
        x_aperture = property(get_x_aperture,set_x_aperture)

        def get_y_aperture(self): return svg.command_value
        def set_y_aperture(self,value): svg.command_value = value
        y_aperture = property(get_y_aperture,set_y_aperture)

        def get_timing_system_ip_address(self): return timing_system.ip_address
        def set_timing_system_ip_address(self,value): timing_system.ip_address = value
        timing_system_ip_address = property(get_timing_system_ip_address,set_timing_system_ip_address)

        acquire_image_timeout = 30 # seconds        

        x_gain = persistent_property("x_gain",0.143) # mrad/mm
        y_gain = persistent_property("y_gain",2.7) # V/mm was: 1/3.3e-3
        x_nominal = persistent_property("x_nominal",175.927) # mm from left, 2016-03-05
        y_nominal = persistent_property("y_nominal",174.121) # mm from top,  2016-03-05
        history_length = persistent_property("history_length",50) 
        average_samples = persistent_property("average_samples",1)
        x_enabled = persistent_property("x_enabled",False)
        y_enabled = persistent_property("y_enabled",False)
        ROI_width = persistent_property("ROI_width",1.0) # mm
        x_ROI_center = persistent_property("x_ROI_center",175.9) # mm from left
        y_ROI_center = persistent_property("y_ROI_center",174.1) # mm from top    
        min_SNR = persistent_property("min_SNR",5.0) # signal-to-noise ratio    

        image_filename = persistent_property("image_filename",
            "//mx340hs/data/rayonix_scratch/xray_beam_position.rx")

    settings = Settings()

    log = LogFile(name+".log",["date time","x","y","x_control","y_control","image_timestamp"])
    if log.filename == "":
        log.filename = "//mx340hs/data/anfinrud_1611/Logfiles/xray_beam_position_check.log"

    def update(self):
        t = self.image_timestamp
        if t != 0 and abs(t - self.last_image_timestamp) >= 0.1:
            x,y = self.beam_position
            xc,yc = self.x_control,self.y_control
            self.log.log(x,y,xc,yc,t)

    @property
    def x_average(self): return average(self.x_samples)

    @property
    def y_average(self): return average(self.y_samples)

    @property
    def x_history(self): return self.log.history("x",count=self.settings.history_length)

    @property
    def y_history(self): return self.log.history("y",count=self.settings.history_length)

    @property
    def t_history(self): return self.log.history("date time",count=self.settings.history_length)

    @property
    def x_samples(self): return self.log.history("x",count=self.settings.average_samples)

    @property
    def y_samples(self): return self.log.history("y",count=self.settings.average_samples)

    @property
    def last_image_timestamp(self):
        t = self.log.history("image_timestamp",count=1)
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
        return self.log.history("x_control",count=self.settings.average_samples)
    
    @property
    def y_control_samples(self):
        return self.log.history("y_control",count=self.settings.average_samples)

    @property
    def x_control_history(self):
        return self.log.history("x_control",count=self.settings.history_length)

    @property
    def y_control_history(self):
        return self.log.history("y_control",count=self.settings.history_length)


    @property
    def x_control_corrected(self):
        """Value for the y control in order to bring the x position back to
        its nominal value"""
        x_control = self.x_control_average - \
            (self.x_average - self.x_nominal)*self.settings.x_gain
        return x_control

    @property
    def y_control_corrected(self):
        """Value for the y control in order to bring the y position back to
        its nominal value"""
        y_control = self.y_control_average - \
            (self.y_average - self.y_nominal)*self.settings.y_gain
        return y_control

    def apply_correction(self):
        self.apply_x_correction()
        self.apply_y_correction()        

    def apply_x_correction(self):
        self.x_control = self.x_control_corrected

    def apply_y_correction(self):
        self.y_control = self.y_control_corrected

    cancelled = persistent_property("cancelled",False)
    acquire_image_started = persistent_property("acquire_image_started",0.0)

    def get_x_control(self): return MirrorH.command_value
    def set_x_control(self,value): MirrorH.command_value = value
    x_control = property(get_x_control,set_x_control)

    def x_next(self,x):
        """The next value that is an intergal motor step"""
        offset = MirrorH.offset
        dx = self.settings.x_resolution
        return round_next(x-offset,dx)+offset

    def y_next(self,y):
        """The next value that is an intergal motor step"""
        offset = 0 ##MirrorV.offset
        dy = self.settings.y_resolution
        return round_next(y-offset,dy)+offset

    def get_y_control(self): return MirrorV.command_value
    def set_y_control(self,value): MirrorV.command_value = value
    y_control = property(get_y_control,set_y_control)

    def acquire_image_setup(self):
        self.settings.x_aperture = self.settings.x_aperture_scan
        self.settings.y_aperture = self.settings.y_aperture_scan

    def acquire_image_unsetup(self):
        self.settings.x_aperture = self.settings.x_aperture_norm
        self.settings.y_aperture = self.settings.y_aperture_norm

    def get_acquire_image_running(self):
        return self.acquire_image_started > time()-self.settings.acquire_image_timeout
    def set_acquire_image_running(self,value):
        if value:
            if not self.acquire_image_running: self.start_acquire_image()
        else: self.cancelled = True
    acquire_image_running = property(get_acquire_image_running,set_acquire_image_running)

    def start_acquire_image(self):
        self.cancelled = False
        start_new_thread(self.acquire_image,())

    def acquire_image(self):
        self.acquire_image_started = time()
        self.acquire_image_setup()

        ccd.ignore_first_trigger = False
        ccd.acquire_images_triggered([normpath(self.settings.image_filename)])
        show_images(normpath(self.settings.image_filename))
        Ensemble_SAXS.acquire(delays=[0],laser_on=[False])
        tmax = time()+self.settings.acquire_image_timeout
        while ccd.state() != "idle" and not self.cancelled and time()<tmax: sleep(0.05)
        ccd.abort()

        self.acquire_image_unsetup()
        self.acquire_image_started = 0
        self.update()

    @property
    def x_beam(self): return self.beam_position[0]

    @property
    def y_beam(self): return self.beam_position[1]

    @property
    def beam_position(self):
        xprofile,yprofile = xy_projections(self.image,self.ROI_center,
            self.ROI_width)
        x,y = CFWHM(xprofile),CFWHM(yprofile)
        return x,y

    @property
    def x_error(self): return self.x_beam - self.x_nominal

    @property
    def y_error(self): return self.y_beam - self.y_nominal

    @property
    def image_OK(self):
        return not self.image_overloaded and self.SNR > self.settings.min_SNR

    @property
    def image_overloaded(self):
        return overloaded_pixels(self.image,self.ROI_center,self.ROI_width)

    @property
    def SNR(self):
        xprofile,yprofile = xy_projections(self.image,self.ROI_center,
            self.ROI_width)
        return (SNR(xprofile)+SNR(yprofile))/2

    @property
    def image(self):
        from numimage import numimage
        filename = normpath(self.settings.image_filename)
        if exists(filename): image = numimage(filename)
        else: image = self.default_image
        # Needed for "BeamProfile" to detect image updates.
        # If a memory-mapped image would be chached by "BeamProfile", the
        # comparison with the new image would show no difference, since the
        # cached image dynamically updates.
        image = image.copy() 
        return image

    @property
    def x_ROI_center(self): return self.settings.x_ROI_center

    @property
    def y_ROI_center(self): return self.settings.y_ROI_center

    @property
    def ROI_center(self): return self.x_ROI_center,self.y_ROI_center

    @property
    def ROI_width(self): return self.settings.ROI_width

    @property
    def x_nominal(self): return self.settings.x_nominal

    @property
    def y_nominal(self): return self.settings.y_nominal

    @property
    def default_image(self):
        from numimage import numimage
        from numpy import uint16
        image = numimage((3840,3840),pixelsize=0.0886,dtype=uint16)+10
        return image

    @property
    def image_timestamp(self):
        """Full pathname of the last recorded image"""
        from os.path import getmtime,dirname
        from os import listdir
        filename = normpath(self.settings.image_filename)
        if exists(filename): listdir(dirname(filename)) # for NFS attibute caching
        t = getmtime(filename) if exists(filename) else 0
        return t

xray_beam_position_check = Xray_Beam_Position_Check()
    
def round_next(x,step):
    """Rounds x up or down to the next multiple of step."""
    if step == 0: return x
    return round(x/step)*step

if __name__ == "__main__":
    from pdb import pm
    from CA import cainfo
    from instrumentation import mir2X1,mir2X2,mir2Th
    self = xray_beam_position_check # for debugging
    ##print('xray_beam_position_check.settings.timing_system_ip_address = %r' % xray_beam_position_check.settings.timing_system_ip_address)
    ##print('xray_beam_position_check.settings.x1_motor       = %r' % xray_beam_position_check.settings.x1_motor)
    ##print('xray_beam_position_check.settings.x2_motor       = %r' % xray_beam_position_check.settings.x2_motor)
    ##print('xray_beam_position_check.settings.y_motor        = %r' % xray_beam_position_check.settings.y_motor)
    ##print('xray_beam_position_check.settings.x_aperture_motor=%r' % xray_beam_position_check.settings.x_aperture_motor)
    ##print('xray_beam_position_check.settings.y_aperture_motor=%r' % xray_beam_position_check.settings.y_aperture_motor)
    ##print('xray_beam_position_check.x_control               = %.4f' % xray_beam_position_check.x_control)
    ##print('xray_beam_position_check.y_control               = %.4f' % xray_beam_position_check.y_control)
    print('xray_beam_position_check.acquire_image()')
    print('xray_beam_position_check.image')
    ##print('xray_beam_position_check.x_average')
    ##print('xray_beam_position_check.y_average')
    ##print('xray_beam_position_check.x_control_corrected')
    ##print('xray_beam_position_check.y_control_corrected')
