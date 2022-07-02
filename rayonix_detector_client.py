"""
Author: Friedrich Schotte
Date created: 2021-04-30
Date last modified: 2022-06-23
Revision comment: Generating "basename" properties locally
"""
__version__ = "1.10"


from cached_function import cached_function

from PV_record import PV_record
from monitored_property import monitored_property
from os.path import basename


@cached_function()
def rayonix_detector(domain_name): return Rayonix_Detector(domain_name)


class Rayonix_Detector(PV_record):
    from PV_property import PV_property
    from PV_connected_property import PV_connected_property
    from numpy import nan

    domain_name = "BioCARS"

    detector_online = PV_property("detector_online", nan)
    acquiring = PV_property(default_value=False)
    acquiring_images = PV_property("acquiring_images", nan)
    ready = PV_property("ready", False)
    update_background = PV_property("update_background", nan)
    last_image_number = PV_property("last_image_number", nan)
    xdet_acq_count = PV_property("xdet_acq_count", nan)
    current_image_filename = PV_property("current_image_filename", "")
    last_saved_image_filename = PV_property("last_saved_image_filename", "")
    nimages = PV_property("nimages", nan)
    bin_factor = PV_property("bin_factor", nan)
    readout_mode_number = PV_property("readout_mode_number", nan)
    readout_mode = PV_property("readout_mode", "")
    last_filename = PV_property("last_filename", "")
    scratch_directory_requested = PV_property("scratch_directory_requested", "")
    scratch_directory = PV_property("scratch_directory", "")
    scratch_directory_choices = PV_property("scratch_directory_choices", [])
    temp_image_count = PV_property("temp_image_count", nan)
    nimages_to_keep = PV_property("nimages_to_keep", nan)
    limiting_files = PV_property("limiting_files", nan)
    limiting_files_requested = PV_property("limiting_files_requested", nan)
    ip_address = PV_property("ip_address", "")
    ip_address_choices = PV_property("ip_address_choices", [])

    # Diagnostics
    xdet_trig_count = PV_property("xdet_trig_count", nan)
    xdet_trig_count_offset = PV_property("xdet_trig_count_offset", nan)
    xdet_trig_count_offset_mean = PV_property("xdet_trig_count_offset_mean", nan)
    xdet_trig_count_offset_error = PV_property("xdet_trig_count_offset_error", nan)
    acquire_timestamp_offset = PV_property("acquire_timestamp_offset", nan)
    collecting_dataset = PV_property("collecting_dataset", nan)
    xdet_trig_count_offsets = PV_property("xdet_trig_count_offsets", [])

    IOC_online = PV_connected_property("online")

    @monitored_property
    def last_saved_image_basename(self, last_saved_image_filename):
        return basename(last_saved_image_filename)

    @monitored_property
    def current_image_basename(self, current_image_filename):
        return basename(current_image_filename)

    @monitored_property
    def last_basename(self, last_filename):
        return basename(last_filename)


if __name__ == "__main__":  # for debugging
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = rayonix_detector(domain_name)

    print("self.detector_online")
    print("self.acquiring")
    print("self.acquiring = True")
    print("self.acquiring_images")
    print("self.acquiring_images = True")
    print("self.current_image_basename")
    print("")
