"""
Rayonix CCD X-ray detector
Friedrich Schotte
Date created: 2016-06-17
Date last modified: 2019-05-31
"""
__version__ = "2.0" # server

from logging import debug,info,warn,error
from rayonix_detector import Rayonix_Detector
from timing_sequencer import timing_sequencer
from Ensemble_SAXS_pp import Ensemble_SAXS
from timing_sequencer import timing_sequencer
from timing_system import timing_system 

class Rayonix_Detector_Continous(Rayonix_Detector):
    """Rayonix MX series X-ray Detector, using continuous acquistion mode"""
    name = "rayonix_detector_server"
    from persistent_property import persistent_property
    scratch_directory = persistent_property("scratch_directory",
        "/net/mx340hs/data/tmp")
    nimages_to_keep = persistent_property("nimages_to_keep",1000)
    filenames = persistent_property("filenames",[])
    image_numbers = persistent_property("image_numbers",[])
    timing_mode = persistent_property("timing_mode","SAXS/WAXS") # SAXS or Laue
    timing_modes = ["SAXS/WAXS","Laue"]
    auto_start = persistent_property("auto_start",True)

    def __init__(self):
        Rayonix_Detector.__init__(self)

    def acquire_images(self,image_numbers,filenames):
        """Save a series of images
        image_numbers: 0-based, matching timing system's 'image_number''"""
        self.image_numbers,self.filenames = list(image_numbers),list(filenames)
        debug("image_numbers = %.200r" % self.image_numbers)
        debug("filenames = %.200r" % self.filenames)

        self.xdet_trig_counts = {}
        self.acquiring = True
        self.trigger_monitoring = True
        self.saving_images = True
    acquire_images_triggered = acquire_images

    def cancel_acquisition(self):
        """Undo 'acquire_images', stop saving images"""
        self.image_numbers,self.filenames = [],[]
        self.trigger_monitoring = False

    __saving_images__ = False

    def get_saving_images(self):
        return self.__saving_images__
    def set_saving_images(self,value):
        if bool(value) == True and not self.saving_images: 
            from thread import start_new_thread
            self.__saving_images__ = True
            start_new_thread(self.save_images_task,())
        if bool(value) == False:
            self.saving_images_cancelled = True
            self.save_images_cancelled = True
    saving_images = property(get_saving_images,set_saving_images)

    def save_images_task(self):
        from time import sleep
        self.saving_images_cancelled = False
        while not self.saving_images_cancelled:
            self.save_images()
            sleep(0.2)
        self.__saving_images__ = False

    saving_images_cancelled = False

    def save_images(self):
        """Check whether the last acquired image needs to be saved and save it.
        """
        self.save_images_cancelled = False
        from os.path import exists,basename
        image_numbers,filenames = self.image_numbers,self.filenames
        for (image_number,filename) in zip(image_numbers,filenames):
            if self.save_images_cancelled: break
            temp_filename = self.temp_filename(image_number=image_number)
            if exists(temp_filename):
                ##debug("rayonix: saving image %r" % image_number)
                self.save(temp_filename,filename)
                image_numbers.remove(image_number)
                filenames.remove(filename)
        self.image_numbers,self.filenames = image_numbers,filenames

    save_images_cancelled = False

    def save(self,temp_filename,filename):
        from os.path import exists,basename
        if not filename:
            debug("rayonix: Discarding %r" % basename(temp_filename))
        elif exists(temp_filename) and mtime(temp_filename) != mtime(filename):
            from os import makedirs,remove
            from shutil import copy2
            from os.path import exists,dirname
            if not exists(dirname(filename)):
                try: makedirs(dirname(filename))
                except Exception,msg:
                    warn("rayonix: makedirs: %r: %s" % (dirname(filename),msg))
            try: remove(filename)
            except: pass
            try:
                from os import link
                link(temp_filename,filename)
                debug("rayonix: Linked %r to %r" % (basename(temp_filename),
                    basename(filename)))
            except Exception,msg: pass
            if exists(temp_filename) and not exists(filename):
                try:
                    copy2(temp_filename,filename)
                    debug("rayonix: Copied %r to %r" % (basename(temp_filename),
                        basename(filename)))
                except Exception,msg:
                    error("rayonix: Cannot copy %r to %r: %s" %
                        (temp_filename,filename,msg))

    def temp_filename(self,image_number=None,xdet_trig_count=None):
        """Full pathname of image file"""
        if image_number is not None:
            if image_number in self.xdet_trig_counts:
                filename = self.temp_filename(xdet_trig_count=
                    self.xdet_trig_counts[image_number])
            else: filename = ""
        if xdet_trig_count is not None:
            filename = "%s/%06d.rx" % (self.scratch_directory,xdet_trig_count)
        return filename

    def get_trigger_monitoring(self):
        from timing_system import timing_system
        return self.xdet_acq_handle in timing_system.xdet.acq.monitors
    def set_trigger_monitoring(self,value):
        from timing_system import timing_system
        if value != self.trigger_monitoring:
            if bool(value) == True:
                timing_system.xdet.acq.monitor(self.xdet_acq_handle,
                    new_thread=False)
            if bool(value) == False:
                timing_system.xdet.acq.monitor_clear(self.xdet_acq_handle)
    trigger_monitoring = property(get_trigger_monitoring,set_trigger_monitoring)

    def xdet_acq_handle(self):
        # Called when X-ray detector trigger level has changed.
        from timing_system import timing_system
        from numpy import nan
        from os.path import basename
        xdet_acq = self.xdet_acq
        acquiring = self.timing_system_acquiring
        xdet_trig_count = self.xdet_trig_count
        xdet_acq_count = self.xdet_acq_count
        debug("Got update: xdet_acq = %r (acquiring = %r, "\
            "xdet_trig_count = %r, xdet_acq_count %r)"\
            % (xdet_acq,acquiring,xdet_trig_count,xdet_acq_count))

        if acquiring and xdet_acq == 0: # falling edge
            debug("xdet_acq_count %s = xdet_trig_count %s = file %r" % (
                xdet_acq_count,
                xdet_trig_count,
                basename(self.filename(xdet_acq_count))
            ))
            self.xdet_trig_counts[xdet_acq_count] = xdet_trig_count

    def timing_system_property(name,default_value=0):
        def get(self):
            from timing_system import timing_system
            from CA import caget
            PV_name = eval("timing_system.%s.PV_name" % name)
            # Use "caget" to circumvent caching in the "timing_system" module
            value = caget(PV_name)
            try: value = type(default_value)(value)
            except: value = default_value
            return value
        return property(get)

    xdet_acq = timing_system_property("xdet_acq")
    timing_system_acquiring = timing_system_property("acquiring")
    xdet_acq_count = timing_system_property("xdet_acq_count")
    xdet_trig_count = timing_system_property("xdet_trig_count")
    
    xdet_trig_counts = {}
    
    def filename(self,xdet_acq_count):
        if xdet_acq_count in self.image_numbers:
            i = self.image_numbers.index(xdet_acq_count)
            filename = self.filenames[i]
        else: filename = ""
        return filename

    def get_acquiring(self):
        value = self.state() == 'acquiring series'
        return value
    def set_acquiring(self,value):
        if self.acquiring != value:
            if value: self.start()
            else: self.stop()
    acquiring = property(get_acquiring,set_acquiring)
    
    def start(self):
        """Start continuous acquistion"""
        from time import sleep

        if self.trigger_enabled:
            self.trigger_enabled = False
            while self.trigger_enabled: sleep(0.1)
            sleep(0.1)
        
        self.empty_scratch_directory()

        self.ignore_first_trigger = False
        self.start_series_triggered(n_frames=999999,
            filename_base=self.scratch_directory+"/",
            filename_suffix=".rx",number_field_width=6)

        timing_system.xdet_trig_count.value = 0
        timing_system.xdet_trig_count.count = 0
        self.trigger_enabled = self.auto_start
        
        self.filenames = {}
        self.limit_files_enabled = True

    def stop(self):
        """Stop continuous acquistion"""
        self.abort()
        self.trigger_enabled = False
        self.limit_files_enabled = False

    def get_trigger_enabled(self):
        """Timing system triggering detector?"""
        return self.timing_sequencer.xdet_on
    def set_trigger_enabled(self,value):
        self.timing_sequencer.xdet_on = value
    trigger_enabled = property(get_trigger_enabled,set_trigger_enabled)

    @property
    def timing_sequencer(self):
        return timing_sequencer if self.timing_mode == "Laue" \
            else Ensemble_SAXS

    def empty_scratch_directory(self):
        """Limit the number of files in the scratch directory"""
        from os import remove
        for f in self.image_filenames:
            try: remove(f)
            except Exception,msg: warn("Cannot remove %r: %s" % (f,msg))
        from os.path import exists
        from os import makedirs
        dir = self.scratch_directory
        if not exists(dir): makedirs(dir)

    def get_limit_files_enabled(self):
        return self.limit_files_task_running
    def set_limit_files_enabled(self,value):
        if value:
            if not self.limit_files_task_running:
                from thread import start_new_thread
                start_new_thread(self.limit_files_task,())
        else: self.limit_files_task_running = False
    limit_files_enabled = property(get_limit_files_enabled,set_limit_files_enabled)

    limit_files_task_running = False
    
    def limit_files_task(self):
        from time import sleep
        self.limit_files_task_running = True
        while self.limit_files_task_running:
            self.limit_files()
            sleep(0.2)

    def limit_files(self):
        """Limit the number of files in the scratch directory"""
        from os import remove
        files_to_delete = self.image_filenames[0:-self.nimages_to_keep]
        for f in files_to_delete:
            try: remove(f)
            except: pass

    @property
    def current_image_basename(self):
        """Current image filename without directory"""
        from os.path import basename
        return basename(self.current_image_filename)

    @property
    def current_image_filename(self):
        """Current image filename"""
        self.monitoring = True
        i = self.xdet_acq_count
        if i in self.image_numbers:
            j = self.image_numbers.index(i)
            if 0 <= j < len(self.filenames): filename = self.filenames[j]
            else: filename = ""
        else: filename = ""
        return filename

    @property
    def nimages(self):
        """How many images left to save?"""
        self.monitoring = True
        return self.__nimages__

    @property
    def __nimages__(self):
        """How many images left to save?"""
        from numpy import array,sum
        nimages = sum(array(self.image_numbers) > self.xdet_acq_count)
        return nimages

    @property
    def last_image_number(self):
        """Last acquired image"""
        last_image_number = self.file_image_number(self.last_filename)
        return last_image_number

    @property
    def last_filename(self):
        """File name of last acquired image"""
        filenames = self.image_filenames
        filename = filenames[-1] if len(filenames) > 0 else ""
        return filename

    def file_image_number(self,filename):
        """Extract serial number from image pathname"""
        from os.path import basename
        try: image_number = int(basename(filename).replace(".rx",""))
        except: image_number = 0
        return image_number        

    @property
    def image_filenames(self):
        """Pathnames of temporarily stored images, sorted by timestamp
        as list of strings"""
        from os import listdir
        from os.path import exists
        dir = self.scratch_directory
        try: files = listdir(dir)
        except: files = [] 
        files = [dir+"/"+f for f in files]
        files.sort()
        return files

    @property
    def current_temp_filename(self):
        """Pathnames of last temporarily stored image"""
        filenames = self.image_filenames
        if len(filenames) > 1: filename = filenames[-1]
        else: filename = ""
        return filename

    def set_bin_factor(self,value):
        """Image size reduction at readout time"""
        if value != Rayonix_Detector.get_bin_factor(self):
            acquiring = self.acquiring
            Rayonix_Detector.set_bin_factor(self,value)
            self.acquiring = acquiring
    bin_factor = property(Rayonix_Detector.get_bin_factor,set_bin_factor)

    def get_live_image(self):
        return self.live_image_task_running
    def set_live_image(self,value):
        if value:
            if not self.live_image_task_running:
                from thread import start_new_thread
                start_new_thread(self.live_image_task,())
        else: self.live_image_task_running = False
    live_image = property(get_live_image,set_live_image)

    live_image_task_running = False
    
    def live_image_task(self):
        """Display a live image"""
        from time import sleep
        self.live_image_task_running = True
        while self.live_image_task_running:
            if self.live_image: self.update_live_image()
            sleep(0.2)

    live_image_filename = ""

    def update_live_image(self):
        """Display a live image"""
        from ImageViewer import show_image
        filename = self.current_temp_filename
        if filename and filename != self.live_image_filename:
            show_image(filename)
            self.live_image_filename = filename

    def get_ADXV_live_image(self):
        return self.ADXV_live_image_task_running
    def set_ADXV_live_image(self,value):
        if value:
            if not self.ADXV_live_image_task_running:
                from thread import start_new_thread
                start_new_thread(self.ADXV_live_image_task,())
        else: self.ADXV_live_image_task_running = False
    ADXV_live_image = property(get_ADXV_live_image,set_ADXV_live_image)

    ADXV_live_image_task_running = False
    
    def ADXV_live_image_task(self):
        """Display a live image"""
        from time import sleep
        self.ADXV_live_image_task_running = True
        while self.ADXV_live_image_task_running:
            if self.ADXV_live_image: self.update_ADXV_live_image()
            sleep(0.2)

    ADXV_live_image_filename = ""

    def update_ADXV_live_image(self):
        """Display a live image"""
        from ADXV_live_image import show_image
        filename = self.current_temp_filename
        if filename and filename != self.ADXV_live_image_filename:
            show_image(filename)
            self.ADXV_live_image_filename = filename

rayonix_detector = Rayonix_Detector_Continous()
ccd = rayonix_detector 
self = rayonix_detector

def mtime(filename):
    """When was the file modified the last time?
    Return value: seconds since 1970-01-01 00:00:00 UTC as floating point number
    0 if the file does not exists"""
    from os.path import getmtime
    try: return getmtime(filename)
    except: return 0


from tcp_server import tcp_server
server = tcp_server("rayonix_detector_server",globals=globals(),locals=locals())

def run(): server.run()

if __name__ == "__main__": # for debugging
    from pdb import pm
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format=
            "%(asctime)s "
            "%(levelname)s "
            "%(funcName)s"
            ", line %(lineno)d"
            ": %(message)s"
    )
    print("server.port = %r" % server.port)
    print("server.running = True")
    print("run()")
