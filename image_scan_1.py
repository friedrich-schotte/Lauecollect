"""
Raster scan of a sample holder containing multiple crystals.
The sample holder is a flattened Mylar tubing of about 2 mm width, mounted
horizontally, facing the X-ray beam, with a 30-degree tilt with respect the
vertical.
The scan identifies the location of the crystals based on their X-ray
diffraction properties.
Friedrich Schotte, Feb 13, 2017 - Oct 5, 2017
"""
from instrumentation import *
__version__ = "1.3.7" # stepsize
from rayonix_detector_continuous_1 import ccd # use old version
from Ensemble import ensemble
from ms_shutter import ms_shutter
from logging import debug,info,warn,error
import glogging as g

class Image_Scan(object):
    name = "image_scan"
    from persistent_property import persistent_property
    from numpy import sin,cos,radians
    cx = persistent_property("cx",0.0) # center [mm]
    cy = persistent_property("cy",0.0) # center [mm]
    cz = persistent_property("cz",0.0) # center [mm]
    dx = persistent_property("dx",0.03) # step size [mm] (0.03 -> 0.02)
    dy = persistent_property("dy",0.03) # step size [mm] (0.03 -> 0.02)
    width  = persistent_property("width", 0.3) # range [mm] (0.3 -> 0.12)
    height = persistent_property("height",0.9) # range [mm] (0.9 -> 0.6)
    # sample carrier tilt to X-ray beam in deg (0 = normal)
    phi = persistent_property("phi",-30)
    # acquisition rate: timing_system.hlct*2 for ca 40 Hz
    ##dt = persistent_property("dt",0.0244388571428)
    control_ms_shutter = persistent_property("control_ms_shutter",False)
    motion_controller_enabled = persistent_property("motion_controller_enabled",True)
    trigger_scope = persistent_property("trigger_scope",False) 

    # Analyze only the central part of the images? Which faction?
    ROI_fraction = persistent_property("ROI_fraction",0.333) 
    peak_detection_threshold = persistent_property("peak_detection_threshold",10.0) 
    subtract_background = persistent_property("subtract_background",False) 

    start_time = persistent_property("start_time",0) # last time scan was run
    cancelled = persistent_property("cancelled",False)
    Nanalyzed = 0 # how many images have been processed?

    def get_center(self): return self.cx,self.cy,self.cz
    def set_center(self,value): self.cx,self.cy,self.cz = value
    center = property(get_center,set_center)

    def get_position(self): return SampleX.value,SampleY.value,SampleZ.value
    def set_position(self,value):
        SampleX.value,SampleY.value,SampleZ.value = value
    position = property(get_position,set_position)

    def get_stepsize(self): return self.dx
    def set_stepsize(self,value): self.dx = self.dy = value
    stepsize = property(get_stepsize,set_stepsize)

    def get_directory(self):
        """location to store files"""
        import lauecollect; lauecollect.reload_settings()
        directory = lauecollect.param.path+"/alignment"
        return directory
    def set_directory(self,value):
        import lauecollect
        lauecollect.param.path = value.replace("/alignment","")
        lauecollect.save_settings()        
    directory = property(get_directory,set_directory)

    def get_dt(self):
        import lauecollect; lauecollect.reload_settings()
        return lauecollect.align.waitt
    def set_dt(self,value):
        import lauecollect
        lauecollect.align.waitt = value
        lauecollect.save_settings()
    dt = property(get_dt,set_dt)

    def get_xray_detector_enabled(self):
        import lauecollect; lauecollect.reload_settings()
        return lauecollect.options.xray_detector_enabled
    def set_xray_detector_enabled(self,value):
        import lauecollect
        lauecollect.options.xray_detector_enabled = value
        lauecollect.save_settings()
    xray_detector_enabled = property(get_xray_detector_enabled,
        set_xray_detector_enabled)

    @property
    def motors(self):
        """axis names"""
        motors = ["X","Y","Z"]
        if self.control_ms_shutter: motors += ["msShut_ext"]
        return motors

    def DX(self,I):
        """Horizontal offset relative to center in mm,
        negative = left, positive = right
        I: 0-based pixel coordinate, from left, may be an array"""
        DX = (I-0.5*(self.NX-1))*self.dx
        return DX

    def I(self,DX):
        """0-based horizontal pixel coordinate, from left
        DX: horizontal offset relative to center in mm,
        negative = left, positive = right
        may be an array
        """
        I = DX/self.dx + 0.5*(self.NX-1)
        return I

    def DY(self,J):
        """Vertical offset relative to center in mm,
        negative = down, positive = up
        J: 0-based pixel coordinate, from top, may be an array"""
        DY = -(J-0.5*(self.NY-1))*self.dy
        return DY

    def J(self,DY):
        """0-based vertical pixel coordinate, from top
        DY: vertical offset relative to center in mm,
        negative = down, positive = up
        may be an array
        """
        J = -DY/self.dy + 0.5*(self.NY-1)
        return J

    @property
    def scan_IJ(self):
        """list of arrays of integer coordinates for a scan
        I: 0-based horozontal pixel coordinate, from left
        J: 0-based vertical pixel coordinate, from top
        """
        from numpy import array,arange
        IP,JP = arange(0,self.NX),arange(0,self.NY)
        # In the horizontal direction, alternate direction from line to line.
        I = [(IP if j%2==0 else IP[::-1]) for j in range(0,self.NY)]
        J = [[j]*self.NX for j in JP]
        I,J = array(I).flatten(),array(J).flatten()
        IJ = array([I,J])
        return IJ

    @property
    def scan_DXDY(self):
        """list of arrays of DX and DY coordinates for a scan
        DY: horizontal direction, orthogonal to X-ray beam
        DY: vertical direction, orthogonal to X-ray beam
        """
        from numpy import array
        I,J = self.scan_IJ
        DXDY = array([self.DX(I),self.DY(J)])
        return DXDY 

    @property
    def grid_VXVY(self):
        """Scanning velocities at each grid point
        VY: horizontal direction, orthogonal to X-ray beam
        VY: vertical direction, orthogonal to X-ray beam
        """
        from numpy import array
        vx = self.dx/self.dt
        # In the horizontal direction, alternate direction from line to line.
        VX = [[vx if i%2==0 else -vx]*self.NX for i in range(0,self.NY)]
        VY = [[0]*self.NX for i in range(0,self.NY)]
        VX,VY = array(VX).flatten(),array(VY).flatten()
        VX[0] = VX[-1] = 0
        VXVY = array([VX,VY])
        return VXVY

    @property
    def scan_XYZ(self):
        """list of arrays of x,y and z coordinates"""
        XYZ = self.XYZ(self.scan_DXDY)
        return XYZ

    def XYZ(self,(DX,DY)):
        """Transform fro m2D to 3D coordinates
        DX: horizontal offset relative to center in mm,
        negative = left, positive = right; may be an array
        DY: vertical offset relative to center in mm,
        negative = down, positive = up; may be an array
        """
        from numpy import sin,cos,radians,array
        X = self.cx+DY*sin(radians(self.phi))
        Y = self.cy+DY*cos(radians(self.phi))
        Z = self.cz+DX
        XYZ = array([X,Y,Z])
        return XYZ

    @property
    def scan_VXVYVZ(self):
        """list of arrays of x,y and z coordinates"""
        from numpy import sin,cos,radians,array
        VXG,VYG = self.grid_VXVY
        VX = VYG*sin(radians(self.phi))
        VY = VYG*cos(radians(self.phi))
        VZ = VXG
        VXVYVZ = array([VX,VY,VZ])
        return VXVYVZ

    @property 
    def scan_N(self):
        """How many scan points are there?"""
        return self.NX*self.NY

    @property 
    def NX(self):
        """How many scan points are there in the horizontal direction?"""
        from numpy import rint
        eps = 1e-6
        NX = int(rint((self.width+eps)/self.dx)) + 1
        return NX

    @property 
    def NY(self):
        """How many scan points are there in the vertical direction?"""
        from numpy import rint
        eps = 1e-6
        NY = int(rint((self.height+eps)/self.dy)) + 1
        return NY

    @property
    def scan_T(self):
        """Time for each scan point"""
        from numpy import arange
        T = self.dt*arange(0,self.scan_N)
        return T

    @property
    def x_PVT(self):
        """Position, velocity and time"""
        P,V,T = self.scan_XYZ[0],self.scan_VXVYVZ[0],self.scan_T
        return P,V,T

    @property
    def y_PVT(self):
        """Position, velocity and time"""
        P,V,T = self.scan_XYZ[1],self.scan_VXVYVZ[1],self.scan_T
        return P,V,T

    @property
    def z_PVT(self):
        """Position, velocity and time"""
        P,V,T = self.scan_XYZ[2],self.scan_VXVYVZ[2],self.scan_T
        return P,V,T

    @property
    def PVT(self):
        PVTs = [self.x_PVT,self.y_PVT,self.z_PVT]
        if self.control_ms_shutter: PVTs += [ms_shutter.PVT(self.scan_T)]
        PVT = self.conbine_trajectories(PVTs)
        return PVT

    @staticmethod
    def conbine_trajectories(PVTs):
        from numpy import concatenate,sort,unique,array
        # common time points
        T = unique(sort(concatenate([PVT[2] for PVT in PVTs]))) 
        P,V = [],[]
        for PVT in PVTs:
            p,v = self.PV(PVT)
            P += [p(T)]
            V += [v(T)]
        P,V = array(P),array(V)
        return P,V,T

    @staticmethod
    def PV(PVT):
        """Position and velocity as continous functions of time
        PVT: tuple of 1-d vectors, positino, velocity, time
        return value: tuple of two interpolation functions
        """
        from scipy.interpolate import interp1d
        from numpy import nan,concatenate
        P,V,T = PVT
        dt = 1e-3
        P2 = interl(P,P+V*dt)
        T2 = interl(T,T+dt)
        T2 = concatenate(([-1e3],T2,[1e3]))
        P2 = concatenate(([P2[0]],P2,[P2[-1]]))
        p = interp1d(T2,P2,bounds_error=False,fill_value=nan)
        T = concatenate(([-1e3],T,[1e3]))
        V = concatenate(([V[0]],V,[V[-1]]))
        v = interp1d(T,V,kind="linear",bounds_error=False,fill_value=nan)
        return p,v

    def acquire(self):
        """Perform image scan"""
        self.clear()
        self.start()
        info("Scanning...")
        self.wait()
        info("Scan completed")
        self.finish()

    def scan(self):
        """Perform image scan and analyze result"""
        self.acquire()
        self.analyze()

    def start(self):
        """Initial setup for image scan"""
        from time import time
        self.start_time = time()
        self.prepare()
        self.acquisition_start()

    def clear(self):
        """Remove all iamge files"""
        from os.path import exists
        from shutil import rmtree
        if exists(self.directory):
            try: rmtree(self.directory)
            except Exception,msg: warn("rmtree: %s: %s" % (self.directory,msg))

    def prepare(self):
        """Initial setup for image scan"""
        self.motion_controller_start()
        self.xray_detector_start()
        self.diagnostics_start()
        self.timing_system_start()

    def timing_system_acquiring(self):
        """Has the timing system started acquiring data?"""
        return  timing_system.image_number.count > 0 \
            or timing_system.pass_number.count > 0 

    def motion_controller_start(self):
        """Configure motion controller for scan"""
        self.jog_xray_shutter()
        info("Setting up motion controller...")
        if self.motion_controller_enabled: self.start_program()

    def jog_xray_shutter(self):
        # Because of settling of particles in the ferrofluiidic feed-through
        # of te X-ray ms shutter, the first operation might have execessive
        # positino error, not compensated by the servo feedback loop
        # (ca 3 degreees), leading to only partial transmission of the X-ray
        # beam.
        # By "jogging" the shutter before first use, the ferro fluid is
        # "loosened up" again.
        from time import sleep
        info("Jogging X-ray shutter")
        from ms_shutter import ms_shutter
        pos = msShut.value
        if pos > ms_shutter.open_pos: step = +10
        else: step = -10
        msShut.value = pos + step
        ##while msShut.moving: sleep(0.01)
        msShut.value = pos
        while msShut.moving: sleep(0.01)

    def timing_system_start(self):
        """Configure timing system for scan"""
        info("Setting up timing system...")
        import lauecollect; lauecollect.reload_settings()
        # Timing calibration for X-ray shutter is different from Lauecollect
        timing_sequencer.ms.offset = 0.0105 # 0.0095,0.010,0.0105,0.011,0.0115,[0.012]
        timing_sequencer.trans.offset = 0.005 # 0.005
        timing_sequencer.cache_size = 0
        nimages = self.scan_N
        image_numbers = range(1,self.scan_N+1)

        timing_sequencer.queue_active = False # hold off exection till setup complete
        timing_system.image_number.count = 0
        timing_system.pass_number.count = 0
        timing_system.pulses.count = 0

        # The detector trigger pulse at the beginning of the first image is to
        # dump zingers that may have accumuated on the CCD. This image is discarded.
        # An extra detector trigger is required after the last image,
        # to save the last image.
        waitt   =       [self.dt]*nimages+[self.dt]
        burst_waitt =   [self.dt]*nimages+[self.dt]
        burst_delay =   [0]*nimages+[0]
        npulses =       [lauecollect.align.npulses]*nimages+[lauecollect.align.npulses]
        laser_on =      [0]*nimages+[0]
        ms_on =         [1]*nimages+[0]
        xatt_on =       [lauecollect.align.attenuate_xray]*nimages+[lauecollect.align.attenuate_xray]
        trans_on =      [1]*nimages+[0]
        xdet_on =       [1]*nimages+[1]
        xosct_on =      [1]*nimages+[0]
        image_numbers = image_numbers+[image_numbers[-1]]
        
        timing_sequencer.acquire(
            waitt=waitt,
            burst_waitt=burst_waitt,
            burst_delay=burst_delay,
            npulses=npulses,
            laser_on=laser_on,
            ms_on=ms_on,
            xatt_on=xatt_on,
            trans_on=trans_on,
            xdet_on=xdet_on,
            xosct_on=xosct_on,
            image_numbers=image_numbers,
        )

    def xray_detector_start(self):
        """Configure X-ray area detector
        image_numbers: list of 1-based integers
        e.g. image_numbers = alignment_pass(1)"""
        info("Setting up X-ray detector...")
        import lauecollect; lauecollect.load_settings()
        from ImageViewer import show_images
        if self.xray_detector_enabled:
            filenames = self.image_filenames
            show_images(filenames)
            ccd.bin_factor = lauecollect.align.ccd_bin_factor # Speeds up the acquisition time

    def acquisition_start(self):
        from time import sleep
        filenames = self.image_filenames

        xdet_on = timing_sequencer.xdet_on
        info("X-ray detector continuously triggered: %r" % xdet_on)
        
        # If the X-ray detector is not continuously triggered...
        if not xdet_on: xdet_count = timing_system.xdet_count.count+2 # discard first dummy image

        timing_sequencer.queue_active = True

        info("Timing system: Waiting for acquisition to start...")
        while not self.timing_system_acquiring(): sleep(0.01)
        info("Timing system: Acquisition started.")

        if xdet_on: xdet_count = timing_system.xdet_count.count+1

        info("First image: xdet_count=%r" % xdet_count)
        ccd.acquire_images_triggered(filenames,start=xdet_count)

    def diagnostics_start(self):
        """Configure diagnostics"""
        info("Setting up X-ray oscilloscope...")
        if self.scan_N > 1: xray_trace.acquire_sequence(self.scan_N)
        xray_trace.acquire_waveforms([self.directory+"/xray_trace.trc"])

    def wait(self):
        """Wait for scan to complete
        image_numbers: list of 1-based integers, e.g. image_numbers = alignment_pass(1)"""
        from time import sleep
        while self.running and not self.cancelled: sleep(0.01)

    @property
    def running(self):
        """Is scan complete?
        image_numbers: list of 1-based integers, e.g. image_numbers = alignment_pass(1)"""
        if self.timing_system_running: running = True
        elif self.xray_detector_running: running = True
        elif self.motion_controller_running: running = True
        else: running = False
        return running

    @property
    def timing_system_running(self):
        """Is scan complete?"""
        i = timing_system.image_number.count
        p = timing_system.pulses.count
        info("acquiring image %3d, %d pulses" % (i,p))
        running = i < self.scan_N and self.scan_N > 0
        return running

    @property
    def xray_detector_running(self):
        """Is scan complete?"""
        if self.xray_detector_enabled:
            nimages = ccd.nimages
            info("X-ray detector: %s images left to save" % nimages)
            running = (nimages > 0)
        else: running = False
        return running        

    @property
    def motion_controller_running(self):
        """Is scan complete?"""
        if self.motion_controller_enabled:
            running = ensemble.program_filename == self.program_filename
        else: running = False
        return running

    def finish(self):
        """End scan"""
        self.motion_controller_finish()
        self.xray_detector_finish()
        self.timing_system_finish()
        ##self.diagnostics_finish()

    def motion_controller_finish(self):
        # Return to the center
        if self.motion_controller_enabled:
            SampleX.value,SampleY.value,SampleZ.value = self.cx,self.cy,self.cz
            info("Restarting program 'ms-shutter.ab'")
            ensemble.program_filename = "ms-shutter.ab"
        
    def xray_detector_finish(self):
        pass
        
    def timing_system_finish(self):
        timing_sequencer.queue_active = False
        timing_sequencer.queue_length = 0
        # Timing calibration for X-ray shutter is different from Lauecollect
        timing_sequencer.ms.offset = 0.013
        timing_sequencer.trans.offset = 0.005
        timing_sequencer.buffer_size = 0

    def diagnostics_finish(self):
        """diagnostics"""
        info("Restoring X-ray oscilloscope...")
        xray_trace.sampling_mode = "RealTime"
        xray_trace.trigger_mode = "Normal"

    def start_program(self):
        from os.path import basename
        from time import sleep
        program = dos_text(self.program_code)
        old_program = file(self.program_filename).read()
        if program != old_program:
            info("Updating file %r..." % basename(self.program_filename))
            file(self.program_filename,"wb").write(program)
        ensemble.program_filename = "" # stop program if already running
        while ensemble.program_filename: sleep(0.1)
        ensemble.program_filename = basename(self.program_filename)
        while not ensemble.program_filename: sleep(0.1) # compilation and loading

    @property
    def program_filename(self):
        """AeroBasic program"""
        from normpath import normpath
        filename = normpath(ensemble.program_directory)+"/image_scan.ab"
        return filename

    @property
    def program_code(self):
        """AeroBasic program"""
        from numpy import maximum,arange
        from datetime import datetime
        P,V,T = self.PVT
        if min(T) < 0: T -= min(T) # negative TIME not allowed for PVT
        T = maximum(T,0.001) # TIME 0 not allowed for PVT
        t = str(datetime.now())
        DIN = "X,1,0" # sample tranlation digital input
        if self.control_ms_shutter: DIN = "msShut_ext,0,1" # ms shutter trigger
        s = ""
        s += "'Automatically generated by image_scan.py %s\n" % __version__
        s += "PROGRAM\n"
        s += "  PLANE 1\n"
        s += "  RECONCILE "+" ".join(self.motors)+"\n"
        s += "  RAMP MODE RATE\n"
        s += "  RAMP RATE 200\n"
        s += "  LINEAR "+" ".join(["%s %.3f" % (m,p) for (m,p) in zip(self.motors,P[:,0])])+"\n"
        s += "  WAIT MOVEDONE "+" ".join(self.motors)+"\n"
        s += "  ABS 'Positions specified in absolute coordinates\n"
        s += "  VELOCITY ON\n"
        s += "  WHILE DIN(%s)=0 'wait for next low-to-high transition.\n" % DIN
        s += "    DWELL 0.00025\n"
        s += "  WEND\n"
        if self.trigger_scope: s += "  SCOPETRIG ' for diagnostics\n"
        s += "  PVT INIT TIME ABS\n"
        for i in range(0,len(T)):
            s += "  PVT "
            s += " ".join(["%s %.8f,%g" % (m,p,v) for (m,p,v) in zip(self.motors,P[:,i],V[:,i])])
            s += " TIME %.6g\n" % T[i]
        s += "  WAIT MOVEDONE "+" ".join(self.motors)+"\n"
        s += "  PLANE 0\n"
        s += "  RECONCILE "+" ".join(self.motors)+"\n"
        s += "  'Return to starting point\n"
        motors = self.motors[0:3]; xyz = self.cx,self.cy,self.cz
        s += "  LINEAR "+" ".join(["%s %.3f" % (m,p) for (m,p) in zip(motors,xyz)])+"\n"
        s += "  WAIT MOVEDONE "+" ".join(motors)+"\n"
        s += "END PROGRAM"
        return s

    @property
    def image_filenames(self):
        I,J = self.scan_IJ
        X,Y,Z = self.scan_XYZ
        dir = self.directory
        image_filenames = [
            dir+"/%02d,%02d_%+.3f,%+.3f,%+.3f.mccd" % (i,j,x,y,z)
            for i,j,x,y,z in zip(I,J,X,Y,Z)]
        return image_filenames

    @property
    def logfile(self):
        from table import table
        from os.path import basename,exists
        from time_string import date_time
        if exists(self.log_filename): logfile = table(self.log_filename)
        else:
            logfile = table()
            logfile["date time"] = [date_time(t) for t in self.start_time+self.scan_T]
            logfile["filename"] = [basename(f) for f in self.image_filenames]
            DX,DY = self.scan_DXDY
            logfile["X[mm]"] = DX
            logfile["Y[mm]"] = DY
        logfile.filename = self.log_filename
        return logfile

    def generate_logfile(self):
        """Save scan log file"""
        self.logfile.save()

    @property
    def log_filename(self):
        filename = self.directory+"/image_scan.log"
        return filename

    def acquire_camera_image(self):
        filename = self.camera_image_filename.replace("/net/","//")
        self.camera.acquire_sequence(filenames=[filename])

    @property
    def camera(self):
        from GigE_camera_client import Camera
        camera = Camera("MicroscopeCamera")
        return camera

    @property
    def camera_image_filename(self):
        filename = self.directory+"/image.jpg"
        return filename     

    def analyze(self):
        """Process the acquired images"""
        self.calculate_FOM()
        self.generate_FOM_image()
        self.generate_plot()
        ##self.generate_spot_mask()

    def calculate_FOM(self):
        """Process the acquired images"""
        from numpy import zeros,sum
        from numimage import numimage
        from peak_integration import peak_integration_mask
        images = self.images
        FOM = zeros(self.scan_N)
        for self.Nanalyzed in range(0,self.scan_N):
            if self.Nanalyzed % 10 == 0:
                info("analysis %.f%%" % (float(self.Nanalyzed)/self.scan_N*100))
            image = images[self.Nanalyzed]
            FOM[self.Nanalyzed] = sum(peak_integration_mask(image)*image)
        logfile = self.logfile
        logfile["FOM"] = FOM
        logfile.save()

    def calculate_FOM_Fast(self):
        """Process the acquired images"""
        from numpy import zeros,sum,uint32
        from peak_integration import peak_integration_mask
        images = self.images
        sum_image = sum(images.astype(uint32),axis=0)
        info("Peak mask of summed image...")
        mask = peak_integration_mask(sum_image)
        info("FOM...")
        FOM = zeros(self.scan_N)
        for self.Nanalyzed in range(0,self.scan_N):
            FOM[self.Nanalyzed] = sum(mask*images[self.Nanalyzed])
        info("FOM done.")
        logfile = self.logfile
        logfile["FOM"] = FOM
        logfile.save()

    Nsvd = persistent_property("Nsvd",5)
    SVD_rotation = persistent_property("SVD_rotation",False)

    @property
    def SVD_bases(self):
        from numpy.linalg import svd
        from numpy import zeros,nan,diag,dot
        from SVD_rotation import SVD_rotation_max_V_2D_auto_correlation
        images = self.images_ordered
        NX,NY,w,h = images.shape
        image_data = images.reshape((NX*NY,w*h))
        info("SVD...")
        U,s,V = svd(image_data.T,full_matrices=False)
        # Discard insignificant vectors.
        s_all = s
        U,s,V = U[:,0:self.Nsvd],s[0:self.Nsvd],V[0:self.Nsvd]
        if self.SVD_rotation:
            info("SVD rotation...")
            US,V = SVD_rotation_max_V_2D_auto_correlation(U,s,V,(self.NX,self.NY),
                diagnostics=self.directory+"/SVD rotation scan auto-correlation")
        else: US = dot(U,diag(s))
        info("SVD done.")
        # Restore original shapes.
        base_images = US.T.reshape((self.Nsvd,w,h))
        base_maps = V.reshape((self.Nsvd,self.NX,self.NY))
        return base_maps,s_all,base_images

    @property
    def SVD_bases(self):
        from numpy.linalg import svd
        from numpy import zeros,nan,diag,dot
        from SVD_rotation import SVD_rotation_min_V_cross_correlation
        images = self.images_ordered
        NX,NY,w,h = images.shape
        image_data = images.reshape((NX*NY,w*h))
        info("SVD...")
        U,s,V = svd(image_data,full_matrices=False)
        # Discard insignificant vectors.
        s_all = s
        U,s,V = U[:,0:self.Nsvd],s[0:self.Nsvd],V[0:self.Nsvd]
        if self.SVD_rotation:
            info("SVD rotation...")
            U,SV = SVD_rotation_min_V_cross_correlation(U,s,V,
                diagnostics=self.directory+"/SVD rotation image cross-correlation")
        else: SV = dot(diag(s),V)
        info("SVD done.")
        # Restore original shapes.
        base_maps = U.T.reshape((self.Nsvd,self.NX,self.NY))
        base_images = SV.reshape((self.Nsvd,w,h))
        return base_maps,s_all,base_images

    def generate_SVD_plot(self):
        import matplotlib; matplotlib.use("PDF",warn=False) # Turn off Tcl/Tk GUI.
        from matplotlib.backends.backend_pdf import PdfPages
        from pylab import figure,imshow,plot,title,grid,xlabel,ylabel,xlim,ylim,\
            xticks,yticks,legend,gca,rc,cm,colorbar,annotate,subplot,close,\
            tight_layout,loglog
        from numpy import clip,amin,amax,average,sum
        from matplotlib.colors import ListedColormap
        maps,s,images = self.SVD_bases
        info("Plotting...")
        PDF_file = PdfPages(self.directory+"/SVD.pdf")
        
        fig = figure(figsize=(5,5))
        loglog(range(1,self.Nsvd+1),s[0:self.Nsvd],".",color="red")
        loglog(range(self.Nsvd+1,len(s)+1),s[self.Nsvd:],".",color="blue")
        grid()
        xlabel("base number")
        ylabel("singular value")
        tight_layout()
        PDF_file.savefig(fig)
        
        for (i,(map,image)) in enumerate(zip(maps,images)):
            # SVD components map have abitrary sign.
            if abs(amin(map)) > amax(map): map *= -1; image *= -1 
            fig = figure(figsize=(5,7))
            subplot(2,1,1)
            title("%d" % (i+1))
            imshow(map.T,cmap=cm.gray,interpolation='nearest')
            colorbar()
            xlim(-0.5,self.NX-0.5)
            ylim(-0.5,self.NY-0.5)
            subplot(2,1,2)
            Imin,Imax = 0.02*amin(image),0.02*amax(image)
            imshow(clip(image,Imin,Imax).T,cmap=cm.gray,interpolation='nearest')
            colorbar()
            PDF_file.savefig(fig)
        PDF_file.close()
        close("all")
        info("Plotting done.")

    def generate_FOM_image(self):
        """Save the ccan result in the form of an image"""
        self.FOM_image.save()

    @property
    def FOM_image(self):
        """Scan result presented as image"""
        from numimage import numimage
        from numpy import rint
        logfile = self.logfile
        X,Y,FOM = logfile.X,logfile.Y,logfile.FOM
        I = rint(self.I(X)).astype(int)
        J = rint(self.J(Y)).astype(int)
        image = numimage((self.NX,self.NY))
        image[I,J] = FOM
        image.pixelsize = self.dx
        image.filename = self.FOM_image_filename
        return image

    @property
    def FOM_image_filename(self):
        filename = self.directory+"/FOM_image.tiff"
        return filename

    @property
    def images_ordered(self):
        """Image data to use for analysis, reordered from scan order to X,Y
        order, as 4D numpy array, shape NX x NY x W x H"""
        from numpy import zeros,nan
        images = self.images
        info("Reordering images...")
        N,w,h = images.shape
        images_ordered = zeros((self.NX,self.NY,w,h))+nan
        I,J = self.scan_IJ
        for i in range(0,N): images_ordered[I[i],J[i]] = images[i]
        return images_ordered

    @property
    def images(self):
        """Image data to use for analysis in collection order
        All images as 3D numpy array, shape Nimages x W x H"""
        if self.subtract_background: images = self.background_subtracted_images
        else: images = self.image_ROIs
        return images

    @property
    def image_ROIs(self):
        """Image data to use for analysis
        All iamges as 3D numpy array, shape Nimage x W x H"""
        from numimage import numimage
        from numpy import array
        info("Mapping images...")
        images = [numimage(f) for f  in self.image_filenames]
        images = [self.ROI(image) for image in images]
        info("Loading images...")
        images = array(images)
        info("Loading images done.")
        return images

    def ROI(self,image):
        """Region of interest for analysis
        image: 2D numpy array"""
        from numpy import rint
        w,h = image.shape
        x = self.ROI_fraction # real number between 0 and 1.0, e.g. 0.333
        imin,imax = int(rint(w/2*(1-x))),int(rint(w/2*(1+x)))
        ROI = image[imin:imax,imin:imax]
        return ROI

    def generate_spot_mask(self):
        """Save spot mask from FOM calculation in the form of an image"""
        self.spot_mask.save()

    @property
    def spot_mask(self):
        from numpy import zeros,sum,uint32
        from peak_integration import spot_mask
        from numimage import numimage
        images = self.images
        sum_image = sum(images.astype(uint32),axis=0)
        info("Peak mask of summed image...")
        mask = spot_mask(sum_image)
        mask = numimage(mask)
        mask.filename = self.spot_mask_filename
        return mask

    @property
    def spot_mask_filename(self):
        filename = self.directory+"/spot_mask.tiff"
        return filename

    @property
    def crystal_mask(self):
        """bitmap showing location of crystals. 1 = crystal, 0 = no crystal"""
        from peak_integration import spot_mask
        FOM = self.FOM_image
        mask = spot_mask(FOM,self.peak_detection_threshold)
        return mask

    @property
    def crystal_IJ(self):
        """coordinates of crystal centers
        I: 0-based horizontal pixel coordinates, from left
        J: 0-based vertical pixel coordinates, from top
        """
        from scipy.ndimage.measurements import label
        from numpy import fromfunction,average,zeros,where,array
        mask = self.crystal_mask
        FOM = self.FOM_image
        # Find clusters
        labelled_mask,n = label(mask)
        Is = fromfunction(lambda i,j:i,mask.shape)
        Js = fromfunction(lambda i,j:j,mask.shape)
        I,J = zeros(n),zeros(n)
        for i in range(0,n):
            pixels = where(labelled_mask==i+1)
            I[i] = average(Is[pixels],weights=FOM[pixels])
            J[i] = average(Js[pixels],weights=FOM[pixels])
        return array([I,J])

    @property
    def crystal_DXDY(self):
        """Coordinates of crystal centers as DX,DY"""
        I,J = self.crystal_IJ
        DX,DY = self.DX(I),self.DY(J)
        return DX,DY
    
    @property
    def crystal_XYZ(self):
        """X,Y,Z coordinates of crystal centers"""
        DX,DY = self.crystal_DXDY
        XYZ = self.XYZ((DX,DY))
        return XYZ

    def generate_plot(self):
        import matplotlib; matplotlib.use("PDF",warn=False) # Turn off Tcl/Tk GUI.
        from matplotlib.backends.backend_pdf import PdfPages
        from pylab import figure,imshow,plot,title,grid,xlabel,ylabel,xlim,ylim,\
            xticks,yticks,legend,gca,rc,cm,colorbar,annotate,close
        from matplotlib.colors import ListedColormap
        image = self.FOM_image
        mask = self.crystal_mask
        I,J = self.crystal_IJ
        PDF_file = PdfPages(self.directory+"/plot.pdf")
        fig = figure(figsize=(5,5))
        imshow(image.T,cmap=cm.gray,interpolation='nearest')
        colorbar()
        cmap = ListedColormap([[0,0,0],[1,0,0]])
        imshow(mask.T,alpha=0.5,cmap=cmap,interpolation='nearest')
        plot(I,J,"ro")
        for n in range(0,len(I)): annotate(str(n),xy=(I[n],J[n]),color="yellow")
        xlim(-0.5,self.NX-0.5)
        ylim(-0.5,self.NY-0.5)
        xlabel("I")
        ylabel("J")
        PDF_file.savefig(fig)
        PDF_file.close()
        close("all")

    def goto_crystal(self,i):
        SampleX.value,SampleY.value,SampleZ.value = self.crystal_XYZ[:,i]

    def goto_ij(self,i,j):
        SampleX.value,SampleY.value,SampleZ.value = self.XYZ([self.DX(i),self.DY(j)])

    @property
    def background_subtracted_images(self):
        """Image data to use for analysis
        All iamges as 3D numpy array, shape Nimage x W x H"""
        from numimage import numimage
        from background_image import background_subtracted
        from os.path import exists
        from numpy import array,where
        info("Mapping images...")
        filenames = self.image_filenames
        images = []
        for i in range(0,len(filenames)):
            filename = filenames[i]
            background_subtracted_filename = filename.replace("/alignment/",
                "/alignment/background_subtracted/%r/" % self.ROI_fraction)
            if not exists(background_subtracted_filename):
                image = self.ROI(numimage(filename))
                image = background_subtracted(image)
                numimage(image+10).save(background_subtracted_filename)
            images += [numimage(background_subtracted_filename)]
        info("Loading images...")
        images = array(images)
        info("Loading images done.")
        # offset 10 = 0 counts
        images = where(images!=0,images-10.0,0.0)
        return images


image_scan = Image_Scan()


def dos_text(text):
    """Convert UNIX to DOS text"""
    return text.replace("\n","\r\n")

def interl(a,b):
    """Combine two arrays of the same length alternating their elements"""
    from numpy import column_stack,ravel
    return ravel(column_stack((a,b)))


if __name__ == "__main__":
    self = image_scan # for debugging
    import logging
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s")
    g.filename = self.directory+"/debug.pdf"
    print('self.center = %.3f,%.3f,%.3f' % self.center)
    print('self.center = self.position')
    print('self.width,self.height  = %.3f,%.3f # 0.500,0.700' % (self.width,self.height))
    ##print('self.dx,self.dy = %.3f,%.3f' % (self.dx,self.dy))
    print('self.stepsize = %.3f' % self.stepsize)
    print('self.scan_N = %r' % self.scan_N)
    print('self.dt = %r # timing_system.hlct*2' % self.dt)
    ##print('ms_shutter.dt = %r # 0.008' % ms_shutter.dt)
    ##print('self.trigger_scope = %r' % self.trigger_scope)
    print('ensemble.program_directory = %r' % ensemble.program_directory)
    print('self.directory = %r' % self.directory)
    print('')
    ##print('self.subtract_background = %r' % self.subtract_background)
    ##print('self.ROI_fraction = %r # 0.1667' % self.ROI_fraction)
    ##print('self.peak_detection_threshold = %r' % self.peak_detection_threshold)
    ##print('')
    ##print('self.acquire_camera_image()')
    print('self.acquire()')
    ##print('self.analyze()')
    ##print('self.scan()')
    ##print('self.crystal_XYZ')
    ##print('self.goto_crystal(0)')
    ##print('self.crystal_IJ')
    ##print('self.goto_ij(0,0)')
    ##print('self.goto_IJ(11,4)')
    ##print('self.Nsvd = %r' % self.Nsvd)
    ##print('self.SVD_rotation = %r' % self.SVD_rotation)
    ##print('self.generate_SVD_plot()')
    ##print('images = self.background_subtracted_images')
    ##print('images = self.images')
    from os.path import exists

    
