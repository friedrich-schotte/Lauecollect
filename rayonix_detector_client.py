"""
Rayonix CCD X-ray detector
Friedrich Schotte
Date created: 2019-05-31
Date last modified: 2019-06-02
"""
__version__ = "2.0.2" # current_temp_filename, ip_address_choices

from logging import debug,info,warn,error

from tcp_client import tcp_client_object

class Rayonix_Detector(tcp_client_object):
    """Rayonix MX series X-ray Detector"""
    name = "rayonix_detector_client"

    from tcp_client import tcp_property
    online = tcp_property("online",False)
    acquiring = tcp_property("acquiring",False)
    last_image_number = tcp_property("last_image_number",0)
    current_image_basename = tcp_property("current_image_basename","")
    nimages = tcp_property("nimages",0)
    last_filename = tcp_property("last_filename","")
    bin_factor = tcp_property("bin_factor",0)
    scratch_directory = tcp_property("scratch_directory","")
    nimages_to_keep = tcp_property("nimages_to_keep",0)
    detector_ip_address = tcp_property("ip_address","")
    timing_mode = tcp_property("timing_mode","")
    timing_modes = tcp_property("timing_modes","")
    ADXV_live_image = tcp_property("ADXV_live_image",False)
    live_image = tcp_property("live_image",False)
    limit_files_enabled = tcp_property("limit_files_enabled",True)
    auto_start = tcp_property("auto_start",False)

    image_numbers = tcp_property("image_numbers",[])
    filenames = tcp_property("filenames",[])    
    xdet_trig_counts = tcp_property("xdet_trig_counts",{})    
    acquiring = tcp_property("acquiring",False)    
    trigger_monitoring = tcp_property("trigger_monitoring",False)    
    saving_images = tcp_property("saving_images",False)    

    current_temp_filename = tcp_property("current_temp_filename","")
    current_image_filename = tcp_property("current_image_filename","")

    ip_address_choices = [
        "localhost:2223",
        "id14b4.cars.aps.anl.gov:2223",
        "pico5.cars.aps.anl.gov:2223",
        "pico5.niddk.nih.gov:2223",
        "pico8.niddk.nih.gov:2223",
        "pico20.niddk.nih.gov:2223",
    ]
    detector_ip_address_choices = [
        "mx340hs.cars.aps.anl.gov:2222",
        "pico5.cars.aps.anl.gov:2222",
        "localhost:2222",
        "pico5.niddk.nih.gov:2222",
        "pico8.niddk.nih.gov:2222",
        "pico20.niddk.nih.gov:2222",
    ]

    def acquire_images(self,image_numbers,filenames):
        """Save a series of images
        image_numbers: 0-based, matching timing system's 'image_number''"""
        image_numbers = list(image_numbers)
        filenames = list(filenames)
        debug("image_numbers = %.200r" % image_numbers)
        self.image_numbers = image_numbers
        debug("filenames = %.200r" % filenames)
        self.filenames = filenames

        self.xdet_trig_counts = {}
        self.acquiring = True
        self.trigger_monitoring = True
        self.saving_images = True

    def cancel_acquisition(self):
        """Undo 'acquire_images', stop saving images"""
        self.image_numbers = []
        self.filenames = []
        self.trigger_monitoring = False

rayonix_detector = Rayonix_Detector()

if __name__ == "__main__": # for debugging
    from pdb import pm
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format=
            "%(asctime)s "
            "%(levelname)s "
            "%(funcName)s"
            ", line %(lineno)d"
            ": %(message)s"
    )
    self = rayonix_detector
    print("self.ip_address = %r" % self.ip_address)
    print("")
    print("self.online")
    print("self.acquiring")
    print("self.last_image_number")
    print("self.current_image_basename")
    print("self.nimages")
    print("self.last_filename")
    print("self.bin_factor")
    print("self.scratch_directory")
    print("self.nimages_to_keep = 999")
    print("self.detector_ip_address")
    print("self.timing_mode")
    print("self.ADXV_live_image")
    print("self.live_image")
    print("self.limit_files_enabled")
    print("self.auto_start")
    print("")
    print("self.image_numbers")
    print("self.filenames[0:5]")
    print("self.xdet_trig_counts")
    print("self.trigger_monitoring")
    print("self.saving_images")
    
