"""
Raster scan of a sample holder containing multiple crystals.
The sample holder is a flattened Mylar tubing of about 2 mm width, mounted
horizontally, facing the X-ray beam, with a 30-degree tilt with respect the
vertical.
The scan identifies the location of the crystals based on their X-ray
diffraction properties.

Author: Friedrich Schotte
Date created: Feb 13, 2017
Date last modified: Oct 27, 2017
"""
from instrumentation import *
__version__ = "2.4" # lauecollect 
from rayonix_detector_continuous_1 import ccd # use old version
from Ensemble import ensemble
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
    dt = persistent_property("dt",0.0244388571428)
    start_dt = persistent_property("start_dt",0.0244388571428*2)
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

    repeat_number = persistent_property("repeat_number",1)

    def get_center(self): return self.cx,self.cy,self.cz
    def set_center(self,value): self.cx,self.cy,self.cz = value
    center = property(get_center,set_center)

    def get_position(self): return SampleX.value,SampleY.value,SampleZ.value
    def set_position(self,value):
        SampleX.value,SampleY.value,SampleZ.value = value
    position = property(get_position,set_position)

    @property
    def moving(self): return any([m.moving for m in SampleX,SampleY,SampleZ])

    def get_stepsize(self): return self.dx
    def set_stepsize(self,value): self.dx = self.dy = value
    stepsize = property(get_stepsize,set_stepsize)

    def get_lauecollect_directory(self):
        """location to store files"""
        import lauecollect; lauecollect.reload_settings()
        directory = lauecollect.param.path
        return directory
    def set_lauecollect_directory(self,value):
        import lauecollect
        lauecollect.param.path = value
        lauecollect.save_settings()        
    lauecollect_directory = property(get_lauecollect_directory,set_lauecollect_directory)    

    collection_directory = persistent_property("collection_directory",
        "/net/mx340hs/data/anfinrud_1711/Data/Laue/Test/Test1")

    def get_directory(self):
        """location to store files"""
        directory = self.collection_directory+"/alignment"
        return directory
    def set_directory(self,value):
        self.collection_directory = value.replace("/alignment","")
    directory = property(get_directory,set_directory)

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
        """How many scan points are there per repeat?"""
        return self.NX*self.NY

    @property 
    def scan_Ntot(self):
        """How many scan points are there in all repeats?"""
        return self.scan_N*self.repeat_number

    def get_NX(self):
        """How many scan points are there in the horizontal direction?"""
        from numpy import rint
        eps = 1e-6
        NX = int(rint((self.width+eps)/self.dx)) + 1
        return NX
    def set_NX(self,NX): self.width = (NX-1)*self.dx
    NX = property(get_NX,set_NX)

    def get_NY(self):
        """How many scan points are there in the vertical direction?"""
        from numpy import rint
        eps = 1e-6
        NY = int(rint((self.height+eps)/self.dy)) + 1
        return NY
    def set_NY(self,NY): self.height = (NY-1)*self.dy
    NY = property(get_NY,set_NY)

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
        """Perform a single image scan"""
        self.cancelled = False
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
        from time import sleep
        if self.motion_controller_enabled:
            self.jog_xray_shutter()
            self.goto_center()
            info("Setting up motion controller...")
            self.start_program()

    def goto_center(self):
        from time import sleep
        while self.moving: sleep(0.05)
        if self.position != self.center:
            info("returning to center: %r to %r..." % (self.position,self.center))
            self.position = self.center
            while self.moving: sleep(0.05)
        
    def jog_xray_shutter(self):
        # Because of settling of particles in the ferrofluiidic feed-through
        # of te X-ray ms shutter, the first operation might have execessive
        # positino error, not compensated by the servo feedback loop
        # (ca 3 degreees), leading to only partial transmission of the X-ray
        # beam.
        # By "jogging" the shutter before first use, the ferro fluid is
        # "loosened up" again.
        from time import sleep,time
        if time() - self.last_jog_xray_shutter > 600:
            info("Jogging X-ray shutter")
            from ms_shutter import ms_shutter
            pos = msShut.value
            if pos > ms_shutter.open_pos: step = +10
            else: step = -10
            msShut.value = pos + step
            ##while msShut.moving: sleep(0.01)
            msShut.value = pos
            while msShut.moving: sleep(0.01)
            self.last_jog_xray_shutter = time()

    last_jog_xray_shutter = persistent_property("last_jog_xray_shutter",0)

    def timing_system_start(self):
        """Configure timing system for scan"""
        info("Setting up timing system...")
        # Timing calibration is different from Lauecollect
        timing_sequencer.ms.offset = 0.0105 # 0.0095,0.010,0.0105,0.011,0.0115,[0.012]
        # Sample translation trigger needs to be "start_dt" before the first
        # X-ray pulse.
        timing_sequencer.trans.offset = self.start_dt # 0.005
        ##timing_sequencer.cache_size = 0 # clear cache
        Ntot = self.scan_Ntot
        N = self.scan_N
        Nr = self.repeat_number
        image_numbers = range(1,Ntot+1)

        timing_sequencer.queue_active = False # hold off exection till setup complete
        timing_system.image_number.count = 0
        timing_system.pass_number.count = 0
        timing_system.pulses.count = 0

        # Restart time for program
        Nw = 4 # in dt cycles
        
        # The detector trigger pulse at the beginning of the first image is to
        # dump zingers that may have accumuated on the CCD. This image is discarded.
        # An extra detector trigger is required after the last image,
        # to save the last image.
        
        waitt   =       ([self.dt]*N+[self.dt]*Nw)*Nr+[self.dt]
        burst_waitt =   ([self.dt]*N+[self.dt]*Nw)*Nr+[self.dt]
        burst_delay =   ([0]*N+[0]*Nw)*Nr+[0]
        npulses =       ([1]*N+[1]*Nw)*Nr+[1]
        laser_on =      ([0]*N+[0]*Nw)*Nr+[0]
        ms_on =         ([1]*N+[0]*Nw)*Nr+[0]
        trans_on =      ([1]+[0]*(N-1+Nw))*Nr+[0]
        xdet_on =   [1]+([1]*N+[0]*Nw)*Nr
        xosct_on =      ([1]*N+[0]*Nw)*Nr+[0]
        image_numbers = flatten([range(i+1,i+N+1)+[i+N]*Nw for i in range(0,Ntot,N)])+[Ntot]
        
        timing_sequencer.acquire(
            waitt=waitt,
            burst_waitt=burst_waitt,
            burst_delay=burst_delay,
            npulses=npulses,
            laser_on=laser_on,
            ms_on=ms_on,
            trans_on=trans_on,
            xdet_on=xdet_on,
            xosct_on=xosct_on,
            image_numbers=image_numbers,
        )

    def xray_detector_start(self):
        """Configure X-ray area detector
        image_numbers: list of 1-based integers
        e.g. image_numbers = alignment_pass(1)"""
        if self.xray_detector_enabled:
            info("Setting up X-ray detector...")
            import lauecollect; lauecollect.load_settings()
            from ImageViewer import show_images
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
        xray_trace.acquire_sequence(self.scan_N)
        xray_trace.acquire_waveforms(self.xray_trace_filenames)

    @property
    def xray_trace_filenames(self):
        """List of waveform files"""
        filenames = [self.directory+"/%02d_xray_trace.trc" % (repeat+1)
            for repeat in range(0,self.repeat_number)]
        return filenames

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
        running = i < self.scan_Ntot
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
        from os.path import basename
        if self.motion_controller_enabled:
            running = False
            ##running = (self.position != self.center)
            ##running = self.program_running == basename(self.program_filename)
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
            pass
            ##self.goto_center()
            ##ensemble.program_filename = "ms-shutter.ab"
        
    def xray_detector_finish(self):
        pass
        
    def timing_system_finish(self):
        timing_sequencer.queue_active = False
        timing_sequencer.queue_length = 0
        # Timing calibration is different from Lauecollect
        timing_sequencer.ms.offset = 0.013
        timing_sequencer.trans.offset = 0.005
        timing_sequencer.buffer_size = 0

    def get_ms_shutter_enabled(self):
        return self.program_running == "ms-shutter.ab"
    def set_ms_shutter_enabled(self,value):
        if value:
            # Timing calibration is different from Lauecollect
            timing_sequencer.ms.offset = 0.013
            timing_sequencer.trans.offset = 0.005
            ##timing_sequencer.cache_size = 0 # clear cache
            self.program_running = "ms-shutter.ab"
        else:
            self.program_running = ""
    ms_shutter_enabled = property(get_ms_shutter_enabled,set_ms_shutter_enabled)

    def diagnostics_finish(self):
        """diagnostics"""
        info("Restoring X-ray oscilloscope...")
        xray_trace.sampling_mode = "RealTime"
        xray_trace.trigger_mode = "Normal"

    def start_program(self):
        from os.path import basename
        from time import sleep
        if not self.parameter_file_up_to_date:
            self.program_running = ""
            while self.program_running: sleep(0.1)
            self.update_parameter_file()
        if not self.program_running == basename(self.program_filename):
            self.program_running = self.program_filename
            # Wait for compilation and loading to complete
            while not self.program_running == basename(self.program_filename):
                sleep(0.1) 

    def get_program_running(self):
        program = ensemble.UserString0 if ensemble.program_running else ""
        return program
    def set_program_running(self,filename):
        from os.path import basename
        ensemble.program_filename = basename(filename)
    program_running = property(get_program_running,set_program_running)

    @property
    def program_filename(self):
        """AeroBasic program"""
        from normpath import normpath
        filename = normpath(ensemble.program_directory)+"/RasterScan.ab"
        return filename

    @property
    def parameter_file_up_to_date(self):
        """Update Aerobasic header file to be included in main program at
        compilation time"""
        from os.path import basename
        parameter_code = dos_text(self.parameter_code)
        old_parameter_code = file(self.parameter_filename).read()
        up_to_date = parameter_code == old_parameter_code
        return up_to_date

    def update_parameter_file(self):
        """Update Aerobasic header file to be included in main program at
        compilation time"""
        from os.path import basename
        info("Updating file %r..." % basename(self.parameter_filename))
        file(self.parameter_filename,"wb").write(dos_text(self.parameter_code))        

    @property
    def parameter_filename(self):
        """AeroBasic program"""
        from normpath import normpath
        filename = normpath(ensemble.program_directory)+"/RasterScan_parameters.abi"
        return filename

    @property
    def parameter_code(self):
        """Aerobasic header file to be included in main program at complation"""
        s = ""
        s += "'Automatically generated by image_scan.py %s\n" % __version__
        s += "DECLARATIONS\n"
        s += "GLOBAL NR AS INTEGER = %s\n" % self.NY
        s += "GLOBAL NC AS INTEGER = %s\n" % self.NX
        s += "GLOBAL DZ AS DOUBLE = %s\n" % self.stepsize
        s += "GLOBAL NT AS INTEGER = %s\n" % self.NT
        s += "GLOBAL NP AS INTEGER = %s\n" % self.NP
        s += "END DECLARATIONS\n"
        return s

    def get_NT(self):
        """Startup delay in multiples of 12 ms"""
        from numpy import rint
        NT = int(rint(self.start_dt/timing_system.hlct))
        return NT
    def set_NT(self,NT): self.start_dt = NT*timing_system.hlct 
    NT = property(get_NT,set_NT)

    def get_NP(self):
        """Scan period in multiples of 12 ms"""
        from numpy import rint
        NP = int(rint(self.dt/timing_system.hlct))
        return NP
    def set_NP(self,NP): self.dt = NP*timing_system.hlct 
    NP = property(get_NP,set_NP)

    @property
    def image_filenames(self):
        I,J = self.scan_IJ
        X,Y,Z = self.scan_XYZ
        dir = self.directory
        image_filenames = [[
                dir+"/%02d,%02d_%+.3f,%+.3f,%+.3f_%02d.mccd" %
                (j,i,x,y,z,repeat+1) for i,j,x,y,z in zip(I,J,X,Y,Z)]
            for repeat in range(0,self.repeat_number)]
        image_filenames = flatten(image_filenames)
        return image_filenames

    @property
    def logfile(self):
        from table import table
        from os.path import basename,exists
        from time_string import date_time
        from numpy import concatenate
        if exists(self.log_filename): logfile = table(self.log_filename)
        else:
            logfile = table()
            logfile["date time"] = [date_time(t) for t in self.start_time+self.scan_T]
            logfile["filename"] = [basename(f) for f in self.image_filenames]
            DX,DY = concatenate([self.scan_DXDY.T]*self.repeat_number).T
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
        from numpy import fromfunction,average,zeros,where
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
        return I,J

    def analyze(self):
        from image_analysis import crystal_IJ
        self.crystal_IJ = crystal_IJ(self.directory)
        self.saved_crystal_positions = self.crystal_XYZ

    def get_crystal_IJ(self):
        """coordinates of crystal centers
        I: 0-based horizontal pixel coordinates, from left
        J: 0-based vertical pixel coordinates, from top
        """
        from table import table
        from numpy import array
        if self.has_crystal_IJ:
            data = table(self.crystal_IJ_filename,separator="\t")
            IJ = data["I","J"].asarray
        else: IJ = array([[],[]],dtype=int)
        return IJ
    def set_crystal_IJ(self,IJ):
        """X,Y,Z coordinates of crystal centers"""
        from table import table
        data = table(columns=["I","J"],data=IJ)
        data.save(self.crystal_IJ_filename) ##,separator="\t")
    crystal_IJ = property(get_crystal_IJ,set_crystal_IJ)

    @property
    def has_crystal_IJ(self):
        from os.path import exists
        return exists(self.crystal_IJ_filename)
    
    @property
    def crystal_IJ_filename(self):
        return self.directory+"/crystal_IJ.txt"

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
        self.saved_crystal_positions = XYZ
        return XYZ

    def get_saved_crystal_positions(self):
        """X,Y,Z coordinates of crystal centers"""
        from table import table
        data = table(self.saved_crystal_positions_filename,separator="\t")
        XYZ = data["X","Y","Z"]
        return XYZ
    def set_saved_crystal_positions(self,XYZ):
        """X,Y,Z coordinates of crystal centers"""
        from table import table
        data = table(columns=["X","Y","Z"],data=XYZ)
        data.save(self.saved_crystal_positions_filename) ##,separator="\t")
    saved_crystal_positions = property(get_saved_crystal_positions,set_saved_crystal_positions)

    @property
    def has_saved_crystal_positions(self):
        from os.path import exists
        return exists(self.saved_crystal_positions_filename)
    
    @property
    def saved_crystal_positions_filename(self):
        return self.directory+"/crystal_positions.txt"

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
        PDF_file.savefig(fig)
        PDF_file.close()
        close("all")

    def goto_crystal(self,i):
        SampleX.value,SampleY.value,SampleZ.value = self.crystal_XYZ[:,i]

    def goto_IJ(self,I,J):
        SampleX.value,SampleY.value,SampleZ.value = self.XYZ([self.DX(I),self.DY(J)])

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

    def collect(self):
        """Instruct Lauecollect to collect data"""
        from time import sleep
        from os.path import basename
        import lauecollect
        positions = self.crystal_XYZ.T
        for i in range(0,len(positions)):
            self.ms_shutter_enabled = True
            self.position = positions[i]
            while self.moving: sleep(0.1)
            lauecollect.param.path = self.collection_directory
            file_basename = "%s-%d" % (basename(self.collection_directory),i+1)
            lauecollect.param.file_basename = file_basename
            lauecollect.collect_dataset()      

image_scan = Image_Scan()


def dos_text(text):
    """Convert UNIX to DOS text"""
    return text.replace("\n","\r\n")

def interl(a,b):
    """Combine two arrays of the same length alternating their elements"""
    from numpy import column_stack,ravel
    return ravel(column_stack((a,b)))

def flatten(l):
    """Converta nested to a flat list"""
    return [item for sublist in l for item in sublist]


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
    print('self.start_dt = %r # timing_system.hlct*2' % self.start_dt)
    print('self.NX = %r' % self.NX)
    print('self.NY = %r' % self.NY)
    print('self.NT = %r' % self.NT)
    print('self.NP = %r' % self.NP)
    print('self.scan_Ntot = %r' % self.scan_Ntot)
    ##print('self.trigger_scope = %r' % self.trigger_scope)
    ##print('ensemble.program_directory = %r' % ensemble.program_directory)
    ##print('self.directory = %r' % self.directory)
    print('self.collection_directory = %r' % self.collection_directory)
    print('self.lauecollect_directory = %r' % self.lauecollect_directory)
    print('self.collection_directory = self.lauecollect_directory')
    print('self.repeat_number = %r' % self.repeat_number)
    print('')
    print('self.ms_shutter_enabled = %r' % self.ms_shutter_enabled)
    ##print('')
    ##print('self.subtract_background = %r' % self.subtract_background)
    ##print('self.ROI_fraction = %r # 0.1667' % self.ROI_fraction)
    ##print('self.peak_detection_threshold = %r' % self.peak_detection_threshold)
    print('')
    ##print('self.scan()')
    print('self.acquire()')
    print('self.analyze()')
    print('self.crystal_IJ')
    print('self.crystal_XYZ')
    print('self.goto_crystal(0)')
    print('self.collect()')
    ##print('self.goto_IJ(11,4)')
    ##print('self.Nsvd = %r' % self.Nsvd)
    ##print('self.SVD_rotation = %r' % self.SVD_rotation)
    ##print('self.generate_SVD_plot()')
    ##print('images = self.background_subtracted_images')
    ##print('images = self.images')

    
