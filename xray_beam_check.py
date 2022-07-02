"""
Optimize the X-ray pulse intensity at the sample
The X-ray beam is steered through an aperture upstream the I0 PIN detector
while recorded the transmitted pulse energy through with the X-ray oscillope
by gated integration of the X-ray pulse.
A three-point scan is performed and the optimum determined by parabolic fit.

Author: Friedrich Schotte
Date created: 2016-06-25
Date last modified: 2022-03-28
Revision comment: Cleanup: timing_system_composer
"""
__version__ = "1.2.5"

from instrumentation import xray_pulse
from CA import caget,caput,PV
from persistent_property import persistent_property
from numpy import nan,sqrt,arange
from time import sleep,time
from instrumentation import MirrorH,MirrorV,s1hg,shg,svg
from logfile import LogFile

class Xray_Beam_Check(object):
    name = "xray_beam_check"

    class Settings(object):
        name = "xray_beam_check.settings"
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

        dx_scan = persistent_property("dx_scan",6*0.000416*2/1.045) # stepsize: 0.000416*2/1.045 = 0.000796 mrad
        dy_scan = persistent_property("dy_scan",0.150) # in V
        x_resolution = persistent_property("x_resolution",0.000416*2/1.045) # stepsize: 0.000416*2/1.045 = 0.000796 mrad
        y_resolution = persistent_property("y_resolution",0.001) # in V

        beamline_mode = persistent_property("beamline_mode","SAXS/WAXS")
        beamline_modes = ["SAXS/WAXS","Laue"]

        @property
        def x_aperture_control(self):
            """Which motor to use to narrow down the horizontal arperture"""
            return s1hg if self.beamline_mode == "Laue" else shg
            
        @property
        def y_aperture_control(self):
            """Which motor to use to narrow down the horizontal arperture"""
            return svg

        # To narrow down aperture upstream of the detector for higher senitivity 
        def get_x_aperture_motor(self): return self.x_aperture_control.prefix
        def set_x_aperture_motor(self,value):
            self.x_aperture_control.prefix = value
        x_aperture_motor = property(get_x_aperture_motor,set_x_aperture_motor)
        def get_y_aperture_motor(self): return self.y_aperture_control.prefix
        def set_y_aperture_motor(self,value): self.y_aperture_control.prefix = value
        y_aperture_motor = property(get_y_aperture_motor,set_y_aperture_motor)

        x_aperture_norm = persistent_property("x_aperture_norm",0.150)
        y_aperture_norm = persistent_property("y_aperture_norm",0.050)
        x_aperture_scan = persistent_property("x_aperture_scan",0.050)
        y_aperture_scan = persistent_property("y_aperture_scan",0.020)

        def get_x_aperture(self): return self.x_aperture_control.command_value
        def set_x_aperture(self,value):
            self.x_aperture_control.command_value = value
        x_aperture = property(get_x_aperture,set_x_aperture)

        def get_y_aperture(self): return self.y_aperture_control.command_value
        def set_y_aperture(self,value):
            self.y_aperture_control.command_value = value
        y_aperture = property(get_y_aperture,set_y_aperture)

        @property
        def x_aperture_moving(self): return self.x_aperture_control.moving

        @property
        def y_aperture_moving(self): return self.y_aperture_control.moving

        def get_timing_system_ip_address(self): return self.timing_system.ip_address
        def set_timing_system_ip_address(self,value): self.timing_system.ip_address = value
        timing_system_ip_address = property(get_timing_system_ip_address,set_timing_system_ip_address)

        def get_scope_ip_address(self): return xray_pulse.scope.ip_address
        def set_scope_ip_address(self,value): xray_pulse.scope.ip_address = value
        scope_ip_address = property(get_scope_ip_address,set_scope_ip_address)

        ms_on_norm = persistent_property("ms_on_norm",True)
        xosct_on_norm = persistent_property("xosct_on_norm",True)

        scan_timeout = 30 # seconds        

        timing_mode = persistent_property("timining_mode","SAXS/WAXS")
        timing_modes = ["SAXS/WAXS","Laue"]

        @property
        def timing_system_composer(self):
            return self.timing_system.composer

        @property
        def timing_system(self):
            from timing_system import timing_system
            return timing_system(self.timing_system_name)
        
        timing_system_name = "BioCARS"

    settings = Settings()

    log = LogFile(name+".log",["date time","x_control","y_control"])
    from redirect import log_filename
    log.filename = log_filename("xray_beam_check")

    x_scan_x =    persistent_property("x_scan_x",   []) 
    x_scan_I =    persistent_property("x_scan_I",   []) 
    x_scan_sigI = persistent_property("x_scan_sigI",[]) 
    y_scan_y =    persistent_property("y_scan_y",   []) 
    y_scan_I =    persistent_property("y_scan_I",   []) 
    y_scan_sigI = persistent_property("y_scan_sigI",[])

    cancelled = persistent_property("cancelled",False)
    x_scan_started = persistent_property("x_scan_started",0.0)
    y_scan_started = persistent_property("y_scan_started",0.0)

    def get_x_control(self): return MirrorH.command_value
    def set_x_control(self,value): MirrorH.command_value = value
    x_control = property(get_x_control,set_x_control)

    def x_next(self,x):
        """The next value that is an intergal motor step"""
        offset = MirrorH.offset
        dx = self.settings.x_resolution
        return round_next(x-offset,dx)+offset

    def y_next(self,y):
        """The next value that is an integral motor step"""
        offset = 0 ##MirrorV.offset
        dy = self.settings.y_resolution
        return round_next(y-offset,dy)+offset

    def get_y_control(self): return MirrorV.command_value
    def set_y_control(self,value): MirrorV.command_value = value
    y_control = property(get_y_control,set_y_control)

    def x_pre_scan_setup(self):
        self.settings.x_aperture_norm = self.settings.x_aperture
        self.settings.x_aperture = self.settings.x_aperture_scan
        while self.settings.x_aperture_moving and not self.cancelled: sleep(0.1)
        ##xray_pulse.scope.sampling_mode = "RealTime" # Lauecollect uses "Sequence"
        xray_pulse.enabled = True

    def x_post_scan_setup(self):
        self.settings.x_aperture = self.settings.x_aperture_norm
        xray_pulse.enabled = False

    def y_pre_scan_setup(self):
        self.settings.y_aperture_norm = self.settings.y_aperture
        self.settings.y_aperture = self.settings.y_aperture_scan
        while self.settings.y_aperture_moving and not self.cancelled: sleep(0.1)
        ##xray_pulse.scope.sampling_mode = "RealTime" # Lauecollect uses "Sequence"
        xray_pulse.enabled = True

    def y_post_scan_setup(self):
        self.settings.y_aperture = self.settings.y_aperture_norm
        xray_pulse.enabled = False

    def timing_system_pre_scan_setup(self):
        # Save current settings
        self.settings.xosct_on_norm = self.settings.timing_system_composer.xosct_on
        self.settings.ms_on_norm = self.settings.timing_system_composer.ms_on

        if not self.settings.timing_system_composer.xosct_on:
            self.settings.timing_system_composer.xosct_on = True
        if not self.settings.timing_system_composer.ms_on:
            self.settings.timing_system_composer.ms_on = True
        while not (self.settings.timing_system_composer.xosct_on
            and self.settings.timing_system_composer.ms_on) and not self.cancelled:
            sleep(0.1)

    def timing_system_post_scan_setup(self):
        # Restore settings
        self.settings.timing_system_composer.xosct_on = self.settings.xosct_on_norm
        self.settings.timing_system_composer.ms_on = self.settings.ms_on_norm

    def get_x_scan_running(self):
        return self.x_scan_started > time()-self.settings.scan_timeout
    def set_x_scan_running(self,value):
        if value:
            if not self.x_scan_running: self.start_x_scan()
        else: self.cancelled = True
    x_scan_running = property(get_x_scan_running,set_x_scan_running)

    def get_y_scan_running(self):
        return self.y_scan_started > time()-self.settings.scan_timeout
    def set_y_scan_running(self,value):
        if value:
            if not self.y_scan_running: self.start_y_scan()
        else: self.cancelled = True
    y_scan_running = property(get_y_scan_running,set_y_scan_running)

    def start_x_scan(self):
        self.cancelled = False
        from threading import Thread
        thread = Thread(target=self.perform_x_scan)
        thread.daemon = True
        thread.start()

    def start_y_scan(self):
        self.cancelled = False
        from threading import Thread
        thread = Thread(target=self.perform_y_scan)
        thread.daemon = True
        thread.start()

    def perform_x_scan(self):
        self.x_scan_started = time()
        self.x_pre_scan_setup()
        self.timing_system_pre_scan_setup()
        self.x_scan_x = []; self.x_scan_I = []; self.x_scan_sigI = []
        x0 = self.x_control
        # Start scanning in positive direction.
        dx = self.settings.dx_scan
        x = x0
        self.x_control = x; I,sigI = self.I_sigI
        self.x_scan_x += [x]; self.x_scan_I += [I]; self.x_scan_sigI += [sigI]
        x += dx
        self.x_control = x; I,sigI = self.I_sigI
        self.x_scan_x += [x]; self.x_scan_I += [I]; self.x_scan_sigI += [sigI]
        # If the intensity goes down, reverse direction.
        if self.x_scan_I[1] < self.x_scan_I[0]:
            dx = -dx; x = x0
            self.x_scan_x    = self.x_scan_x[::-1]
            self.x_scan_I    = self.x_scan_I[::-1]
            self.x_scan_sigI = self.x_scan_sigI[::-1]
        x += dx
        self.x_control = x; I,sigI = self.I_sigI
        self.x_scan_x += [x]; self.x_scan_I += [I]; self.x_scan_sigI += [sigI]
        # Continue scanning until a maximum is reached.
        while self.x_scan_I[-1] > self.x_scan_I[-2] and not self.cancelled:
            x += dx
            self.x_control = x; I,sigI = self.I_sigI
            self.x_scan_x += [x]; self.x_scan_I += [I]; self.x_scan_sigI += [sigI]
        # Return to the starting point.
        self.x_control = x0
        self.x_post_scan_setup()
        self.timing_system_post_scan_setup()
        self.x_scan_started = 0

    def perform_y_scan(self):
        self.y_scan_started = time()
        self.y_pre_scan_setup()
        self.timing_system_pre_scan_setup()
        self.y_scan_y = []; self.y_scan_I = []; self.y_scan_sigI = []
        y0 = self.y_control
        # Start scanning in positive direction.
        dy = self.settings.dy_scan
        y = y0
        self.y_control = y; I,sigI = self.I_sigI
        self.y_scan_y += [y]; self.y_scan_I += [I]; self.y_scan_sigI += [sigI]
        y += dy
        self.y_control = y; I,sigI = self.I_sigI
        self.y_scan_y += [y]; self.y_scan_I += [I]; self.y_scan_sigI += [sigI]
        # If the intensity goes down, reverse direction.
        if self.y_scan_I[1] < self.y_scan_I[0]:
            dy = -dy; y = y0
            self.y_scan_y    = self.y_scan_y[::-1]
            self.y_scan_I    = self.y_scan_I[::-1]
            self.y_scan_sigI = self.y_scan_sigI[::-1]
        y += dy
        self.y_control = y; I,sigI = self.I_sigI
        self.y_scan_y += [y]; self.y_scan_I += [I]; self.y_scan_sigI += [sigI]
        # Continue scanning until a mayimum is reached.
        while self.y_scan_I[-1] > self.y_scan_I[-2] and not self.cancelled:
            y += dy
            self.y_control = y; I,sigI = self.I_sigI
            self.y_scan_y += [y]; self.y_scan_I += [I]; self.y_scan_sigI += [sigI]
        # Return to the starting point.
        self.y_control = y0
        self.y_post_scan_setup()
        self.timing_system_post_scan_setup()
        self.y_scan_started = 0

    @property
    def x_control_corrected(self):
        if len(self.x_scan_x) < 3 or len(self.x_scan_I) < 3: return nan
        x = parabola_vertex(self.x_scan_x[-3:],self.x_scan_I[-3:])[0]
        x = self.x_next(x)
        return x

    @property
    def y_control_corrected(self):
        if len(self.y_scan_y) < 3 or len(self.y_scan_I) < 3: return nan
        y = parabola_vertex(self.y_scan_y[-3:],self.y_scan_I[-3:])[0]
        ##y = self.y_next(y)
        return y

    @property
    def x_scan_x_fit(self): return parabolic_fit(self.x_scan_x,self.x_scan_I)[0]
    @property
    def x_scan_I_fit(self): return parabolic_fit(self.x_scan_x,self.x_scan_I)[1]

    @property
    def y_scan_y_fit(self): return parabolic_fit(self.y_scan_y,self.y_scan_I)[0]
    @property
    def y_scan_I_fit(self): return parabolic_fit(self.y_scan_y,self.y_scan_I)[1]

    def apply_x_correction(self):
        self.x_control = self.x_control_corrected
        self.update_log()

    def apply_y_correction(self):
        self.y_control = self.y_control_corrected
        self.update_log()

    def update_log(self):
        """Create a log file entry every time a correction is applied"""
        self.log.log(self.x_control,self.y_control)
        

    @property
    def I_sigI(self):
        """X-ray beam intensity"""
        xray_pulse.reset_average()
        sleep(4)
        I = xray_pulse.average
        sI = xray_pulse.stdev
        N = xray_pulse.count
        sigI = I/sqrt(N-1) if N>1 else nan
        return I,sigI

xray_beam_check = Xray_Beam_Check()


def parabola_vertex(X,Y):
    """Vertex of a parabola given three points
    X: list of three value
    Y: list 3 values
    """
    x1,x2,x3 = X
    y1,y2,y3 = Y
    # http://stackoverflow.com/questions/717762/how-to-calculate-the-vertex-of-a-parabola-given-three-points
    # y = A * x**2 + B * x + C
    try:
        denom = (x1 - x2) * (x1 - x3) * (x2 - x3)
        A = (x3 * (y2 - y1) + x2 * (y1 - y3) + x1 * (y3 - y2)) / denom
        B = (x3**2 * (y1 - y2) + x2**2 * (y3 - y1) + x1**2 * (y2 - y3)) / denom
        C = (x2 * x3 * (x2 - x3) * y1 + x3 * x1 * (x3 - x1) * y2 + x1 * x2 * (x1 - x2) * y3) / denom
        xv = -B / (2*A)
        yv = C - B*B / (4*A)
    except ZeroDivisionError: xv,yv = nan,nan
    return xv,yv

def parabolic_fit(X,Y):
    """
    X: list of three value
    Y: list 3 values
    """
    x1,x2,x3 = X
    y1,y2,y3 = Y
    # http://stackoverflow.com/questions/717762/how-to-calculate-the-vertex-of-a-parabola-given-three-points
    # y = A * x^2 + B * x + C
    try:
        denom = (x1 - x2) * (x1 - x3) * (x2 - x3)
        A = (x3 * (y2 - y1) + x2 * (y1 - y3) + x1 * (y3 - y2)) / denom
        B = (x3**2 * (y1 - y2) + x2**2 * (y3 - y1) + x1**2 * (y2 - y3)) / denom
        C = (x2 * x3 * (x2 - x3) * y1 + x3 * x1 * (x3 - x1) * y2 + x1 * x2 * (x1 - x2) * y3) / denom
    except ZeroDivisionError: A,B,C = nan,nan,nan

    def f(x): return A * x**2 + B * x + C
    xa,xb = min(x1,x2,x3),max(x1,x2,x3)
    eps = 1e-10
    x = arange(xa,xb+eps,(xb-xa)/10)
    return x,f(x)
    
def tofloat(x):
    """Convert to floating point number without throwing exception"""
    from numpy import nan
    try: return float(x)
    except: return nan

def round_next(x,step):
    """Rounds x up or down to the next multiple of step."""
    if step == 0: return x
    return round(x/step)*step

if __name__ == "__main__":
    from pdb import pm
    import logging
    format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=format)
    from instrumentation import mir2X1,mir2X2,mir2Th
    self = xray_beam_check # for debugging
    ##print('xray_beam_check.settings.timing_system_ip_address = %r' % xray_beam_check.settings.timing_system_ip_address)
    ##print('xray_beam_check.settings.scope_ip_address = %r' % xray_beam_check.settings.scope_ip_address)
    ##print('xray_beam_check.settings.timing_mode = %r' % xray_beam_check.settings.timing_mode)
    ##print('xray_beam_check.settings.beamline_mode = %r' % xray_beam_check.settings.beamline_mode)
    ##print('')
    print('xray_beam_check.perform_x_scan()')
    print('xray_beam_check.perform_y_scan()')
