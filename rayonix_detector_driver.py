"""
Rayonix MX series CCD X-ray detector

- Record timestamps of timing system x-ray detector trigger counts
- Record timestamps of timing system x-ray detector acquisition counts
- Record file timestamps of image numbers
- Record when acquisition started and ended.

- Tentatively assign x-ray detector trigger counts to image numbers based on timestamps
- Calculate offset of x-ray detector trigger counts to image numbers
- Reassign x-ray detector trigger counts to image numbers based on offset

- Assign x-ray detector trigger counts to x-ray detector acquisition counts.
- Calculate offset of x-ray detector trigger counts to x-ray detector acquisition counts after acquisition started.
- If there are unassigned trigger counts, use the calculated offset to assign them x-ray detector acquisition counts.

- Assign filenames to image numbers.

Author: Friedrich Schotte
Date created: 2016-06-17
Date last modified: 2022-07-05
Revision comment: Added: running

"""
__version__ = "8.4"

import logging
from os.path import basename

import numpy

from attribute_property import attribute_property
from cached_function import cached_function
from handler_method import handler_method
from monitored_value_property import monitored_value_property
from rayonix_detector_base_driver import Rayonix_Detector
from alias_property import alias_property
from date_time import date_time
from thread_property_2 import thread_property, cancelled
from db_property import db_property
from monitored_property import monitored_property
from function_property import function_property
from directory import directory
from numpy import nan

numpy.warnings.filterwarnings('ignore', 'Mean of empty slice')  # for nanmedian
numpy.warnings.filterwarnings('ignore', 'Degrees of freedom <= 0 for slice.')  # for nanmedian
numpy.warnings.filterwarnings('ignore', 'All-NaN slice encountered')  # for nanmedian

# logging.getLogger("monitored_property").level = logging.ERROR


@cached_function()
def rayonix_detector_driver(domain_name):
    return Rayonix_Detector_Driver(domain_name)


rayonix_detector = rayonix_detector_driver  # for backward compatibility


class Rayonix_Detector_Driver(Rayonix_Detector):
    """Rayonix MX series X-ray Detector, using continuous acquisition mode"""
    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        Rayonix_Detector.__init__(self)
        self.trigger_events = []
        self.temp_images = {}
        self.xdet_acq_count_offset = nan

        # For pylint "Instance attribute ... defined outside __init__"
        self.saving_images = False
        self.monitoring_new_temp_filenames = False
        self.updating_file_timestamps = False
        self.updating_xdet_trig_count_offset = False
        self.limiting_files = False
        self.monitoring_xdet_trig_count = False
        self.monitoring_xdet_acq_count = False
        self.monitoring_timing_system_acquiring = False
        self.monitoring_xdet_acq = False
        self.starting_acquisition = False
        self.stopping_acquisition = False
        self.monitoring_temp_basenames = False

    def __repr__(self):
        return f"{self.class_name}({self.domain_name!r})"

    @property
    def running(self):
        return self.monitoring_temp_basenames

    @running.setter
    def running(self, running):
        if running != self.running:
            if running:
                logging.debug("Starting...")
                self.monitoring_temp_basenames = True
                self.limit_files_autostart()
                if self.acquiring:
                    self.acquiring_images = True
            else:
                self.monitoring_temp_basenames = False
                self.limiting_files = False

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def name(self):
        return f"{self.domain_name}.{self.class_name}"

    domain_name = "BioCARS"

    # Used by "db_property"
    @property
    def db_name(self):
        return f"{self.domain_name}/rayonix_detector_driver"

    scratch_directory_requested = db_property("scratch_directory", "//mx340hs/data/tmp")

    xdet_trig_count_offset = db_property("xdet_trig_count_offset", 0, local=True)

    @monitored_property
    def scratch_directory(self, scratch_directory_requested):
        from normpath import normpath
        return normpath(scratch_directory_requested)

    @scratch_directory.setter
    def scratch_directory(self, value):
        self.scratch_directory_requested = value

    scratch_directory_choices = monitored_value_property([
        "/net/mx340hs/data/tmp",
        "/net/femto-data2/C/Data/tmp",
        "//femto-data2/C/Data/tmp",
        "/Mirror/femto-data2/C/Data/tmp",
    ])

    nimages_to_keep = db_property("nimages_to_keep", 1000)

    last_saved_image_filename = db_property("last_saved_image_filename", "", local=True)

    @monitored_property
    def ready(self, acquiring_images):
        return acquiring_images

    @monitored_property
    def acquiring_images(self, acquiring, trigger_monitoring, updating_file_timestamps, monitoring_new_temp_filenames):
        acquiring_images = all([
            acquiring,
            trigger_monitoring,
            updating_file_timestamps,
            monitoring_new_temp_filenames,
            # saving_images,
        ])
        return acquiring_images

    @acquiring_images.setter
    def acquiring_images(self, value):
        if value != self.acquiring_images:
            if value:
                self.temp_images = {}
                self.acquiring = True
                self.trigger_monitoring = True
                self.updating_file_timestamps = True
                # self.saving_images = True
                self.monitoring_new_temp_filenames = True
                self.xdet_trig_count_history.recording = True
                self.xdet_acq_count_history.recording = True
                self.xdet_acq_history.recording = True
                self.timing_system_acquiring_history.recording = True
            else:
                self.trigger_monitoring = False
                # self.updating_file_timestamps = False

    @property
    def trigger_monitoring(self):
        return all([
            self.monitoring_xdet_trig_count,
            self.updating_xdet_trig_count_offset,
            self.monitoring_timing_system_acquiring,
            self.monitoring_xdet_acq,
            self.monitoring_xdet_acq_count,
        ])

    @trigger_monitoring.setter
    def trigger_monitoring(self, value):
        if value != self.trigger_monitoring:
            self.monitoring_xdet_trig_count = value
            self.updating_xdet_trig_count_offset = value
            self.monitoring_timing_system_acquiring = value
            self.monitoring_xdet_acq = value
            self.monitoring_xdet_acq_count = value

    @property
    def monitoring_timing_system_acquiring(self):
        return self.handle_acquiring in self.timing_system_acquiring_handlers

    @monitoring_timing_system_acquiring.setter
    def monitoring_timing_system_acquiring(self, monitoring):
        if monitoring:
            self.timing_system_acquiring_handlers.add(self.handle_acquiring)
        else:
            self.timing_system_acquiring_handlers.remove(self.handle_acquiring)

    @property
    def monitoring_xdet_trig_count(self):
        return self.handle_xdet_trig_count in self.xdet_trig_count_handlers

    @monitoring_xdet_trig_count.setter
    def monitoring_xdet_trig_count(self, monitoring):
        if monitoring:
            self.xdet_trig_count_handlers.add(self.handle_xdet_trig_count)
        else:
            self.xdet_trig_count_handlers.remove(self.handle_xdet_trig_count)

    @property
    def monitoring_xdet_acq(self):
        return self.handle_xdet_acq in self.xdet_acq_handlers

    @monitoring_xdet_acq.setter
    def monitoring_xdet_acq(self, monitoring):
        if monitoring:
            self.xdet_acq_handlers.add(self.handle_xdet_acq)
        else:
            self.xdet_acq_handlers.remove(self.handle_xdet_acq)

    @property
    def monitoring_xdet_acq_count(self):
        return self.handle_xdet_acq_count in self.xdet_acq_count_handlers

    @monitoring_xdet_acq_count.setter
    def monitoring_xdet_acq_count(self, monitoring):
        if monitoring:
            self.xdet_acq_count_handlers.add(self.handle_xdet_acq_count)
        else:
            self.xdet_acq_count_handlers.remove(self.handle_xdet_acq_count)

    @handler_method
    def handle_acquiring(self, event):
        logging.debug(f"{date_time(event.time)}: acquiring = {event.value}")

    @handler_method
    def handle_xdet_trig_count(self, event):
        xdet_trig_count = event.value
        time = event.time
        # logging.debug(f"{date_time(time)}: xdet_trig_count={xdet_trig_count}")
        trigger_event = self.Trigger_Event(time=time, value=xdet_trig_count)
        self.trigger_events.append(trigger_event)
        self.trigger_events = self.trigger_events[-(self.nimages_to_keep + 10):]

    @handler_method
    def handle_xdet_acq(self, event):
        logging.debug(f"{date_time(event.time)}: xdet_acq = {event.value}")

    def save_filename(self, temp_filename):
        time = self.acquire_timestamp(temp_filename)
        if self.is_acquiring(time):
            xdet_trig_count = self.xdet_trig_count_of_image(temp_filename)
            xdet_acq_count = xdet_trig_count - self.get_xdet_acq_count_offset(time)
            save_filename = self.xray_image_filename(xdet_acq_count - 1)
            logging.debug(f"{basename(temp_filename)}: {date_time(time)}, xdet_trig_count={xdet_trig_count}, xdet_acq_count={xdet_acq_count}, {basename(save_filename)}")
        else:
            save_filename = ""
        return save_filename

    def acquire_timestamp(self, temp_filename):
        from rayonix_image import rayonix_image
        from numpy import isnan

        if not isnan(self.acquire_timestamp_offset):
            acquire_timestamp = rayonix_image(temp_filename).acquire_timestamp
            if isnan(acquire_timestamp):
                logging.error(f"failed to read acquire_timestamp of {temp_filename}")
            acquire_timestamp -= self.acquire_timestamp_offset
        else:
            logging.warning(f"acquire_timestamp_offset unknown")
            acquire_timestamp = nan

        if not isnan(acquire_timestamp):
            timing_system_timestamp = self.xdet_trig_count_history.closest_event_time(acquire_timestamp)
            if not isnan(timing_system_timestamp):
                acquire_timestamp = timing_system_timestamp
            else:
                logging.warning(f"No timing system timestamp for {temp_filename!r}")
            dt = timing_system_timestamp - acquire_timestamp
            if abs(dt) > 0.1:
                logging.warning(f"{temp_filename}: timing system timestamp {dt} s relative to acquire_timestamp")
        else:
            logging.warning(f"Failed to determine acquire_timestamp for {temp_filename!r}")

        return acquire_timestamp

    def xdet_trig_count_of_image(self, temp_filename):
        image_number = self.file_image_number(temp_filename)
        xdet_trig_count = image_number + self.xdet_trig_count_offset
        return xdet_trig_count

    def is_acquiring(self, acquire_timestamp):
        return self.timing_system_acquiring_history.value(acquire_timestamp)

    def get_xdet_acq_count_offset(self, time):
        from numpy import nan, isnan
        offset = nan
        t = time
        t_xdet_acq_count = self.xdet_acq_count_history.last_event_time_before_or_at(t)
        t_xdet_trig_count = self.xdet_trig_count_history.last_event_time_before_or_at(t)
        while not t_xdet_acq_count == t_xdet_trig_count:
            t = min(t_xdet_acq_count, t_xdet_trig_count)
            if isnan(t):
                break
            t_xdet_acq_count = self.xdet_acq_count_history.last_event_time_before_or_at(t)
            t_xdet_trig_count = self.xdet_trig_count_history.last_event_time_before_or_at(t)
        if t_xdet_acq_count == t_xdet_trig_count:
            t = t_xdet_acq_count
            xdet_acq_count = self.xdet_acq_count_history.value_before_or_at(t)
            xdet_trig_count = self.xdet_trig_count_history.value_before_or_at(t)
            if xdet_acq_count and xdet_trig_count:
                offset = xdet_trig_count - xdet_acq_count
                if t != time:
                    logging.info(f"Found offset for {date_time(t)} instead of {date_time(t)} (dt: {t-time:.9f} s)")

        if isnan(offset):
            logging.warning(f"Failed to determine xdet_acq_count_offset for {date_time(time)}")
        if not isnan(offset) and offset != self.xdet_acq_count_offset:
            logging.info(f"{date_time(time)}: offset {offset} (was: {self.xdet_acq_count_offset})")
            self.xdet_acq_count_offset = offset

        return offset

    @handler_method
    def handle_xdet_acq_count(self, event):
        xdet_acq_count = event.value
        time = event.time
        logging.debug(f"{date_time(time)}: xdet_acq_count = {xdet_acq_count}")

    @property
    def timing_system_acquiring_handlers(self):
        return self.timing_system_acquiring_reference.monitors

    @property
    def xdet_trig_count_history(self):
        from event_history_2 import event_history
        return event_history(self.xdet_trig_count_reference)

    @property
    def xdet_trig_count_handlers(self):
        return self.xdet_trig_count_reference.monitors

    @property
    def xdet_trig_count_reference(self):
        from reference import reference
        return reference(self.timing_system.channels.xdet.trig_count, "count")

    @property
    def xdet_acq_history(self):
        from event_history_2 import event_history
        return event_history(self.xdet_acq_reference)

    @property
    def xdet_acq_handlers(self):
        return self.xdet_acq_reference.monitors

    @property
    def xdet_acq_reference(self):
        from reference import reference
        return reference(self.timing_system.channels.xdet.acq, "count")

    @property
    def xdet_acq_count_history(self):
        from event_history_2 import event_history
        return event_history(self.xdet_acq_count_reference)

    @property
    def xdet_acq_count_handlers(self):
        return self.xdet_acq_count_reference.monitors

    @property
    def xdet_acq_count_reference(self):
        from reference import reference
        return reference(self.timing_system.channels.xdet.acq_count, "count")

    @property
    def timing_system_acquiring_history(self):
        from event_history_2 import event_history
        return event_history(self.timing_system_acquiring_reference)

    @property
    def timing_system_acquiring_reference(self):
        from reference import reference
        return reference(self.timing_system.registers.acquiring, "count")

    @thread_property
    def updating_file_timestamps(self):
        from numpy import isnan
        while not cancelled():
            temp_images = dict(self.temp_images)
            filenames = self.temp_filenames
            for filename in filenames:
                if cancelled():
                    break
                if filename not in temp_images:
                    temp_images[filename] = self.Image_Info(filename)
                image = temp_images[filename]

                if isnan(image.file_timestamp):
                    from os.path import getmtime
                    try:
                        image.file_timestamp = getmtime(filename)
                    except OSError:
                        pass
                if isnan(image.acquire_timestamp):
                    from rayonix_image import rayonix_image
                    try:
                        image.acquire_timestamp = rayonix_image(filename).acquire_timestamp
                    except (OSError, ValueError):
                        pass

            for image in list(temp_images.values()):
                if image.filename not in filenames:
                    try:
                        del temp_images[image.filename]
                    except KeyError:
                        pass
            self.temp_images = temp_images
            from time import sleep
            sleep(1.0)

    @thread_property
    def saving_images(self):
        from time import sleep
        while not cancelled():
            self.save_images()
            sleep(0.2)

    def save_images(self):
        """Check whether the last acquired image needs to be saved and save it."""
        for temp_filename in self.temp_filenames:
            self.save_temp_file(temp_filename)

    def save_temp_file(self, temp_filename):
        from os.path import exists
        save_filename = self.save_filename(temp_filename)
        if save_filename:
            # from os.path import exists
            # if not exists(save_filename):
            self.save(temp_filename, save_filename)
            if exists(save_filename):
                self.last_saved_image_filename = save_filename

    @staticmethod
    def save(temp_filename, filename):
        logging.debug(f"Saving {temp_filename} as {filename}")
        from os.path import exists, basename
        if not filename:
            logging.debug("Discarding %r" % basename(temp_filename))
        elif exists(temp_filename) and mtime(temp_filename) != mtime(filename):
            from os import makedirs, remove
            from shutil import copy2
            from os.path import exists, dirname
            if not exists(dirname(filename)):
                try:
                    makedirs(dirname(filename))
                except Exception as msg:
                    logging.warning("makedirs: %r: %s" % (dirname(filename), msg))
            try:
                remove(filename)
            except OSError:
                pass
            try:
                from os import link
                link(temp_filename, filename)
                logging.debug("Linked %r to %r" % (basename(temp_filename),
                                                   basename(filename)))
            except OSError:
                pass
            if exists(temp_filename) and not exists(filename):
                try:
                    copy2(temp_filename, filename)
                    logging.debug("Copied %r to %r" % (basename(temp_filename),
                                                       basename(filename)))
                except Exception as msg:
                    logging.error("Cannot copy %r to %r: %s" %
                                  (temp_filename, filename, msg))

    def temp_filename(self, xdet_acq_timestamp):
        """Full pathname of image file"""
        from numpy import inf
        filename = ""
        min_dt = inf
        images = list(self.temp_images.values())
        for image in images:
            timestamp = image.acquire_timestamp - self.acquire_timestamp_offset
            dt = timestamp - xdet_acq_timestamp
            if 0 <= dt < min_dt:
                min_dt = dt
                filename = image.filename
        return filename

    @thread_property
    def updating_xdet_trig_count_offset(self):
        from time import sleep

        while not cancelled():
            self.update_xdet_trig_count_offset()
            sleep(1.0)

    def update_xdet_trig_count_offset(self):
        from numpy import isnan
        if all([
            not self.collecting_dataset,
            not isnan(self.xdet_trig_count_offset_mean),
            self.xdet_trig_count_offset_error < 0.25,
            self.xdet_trig_count_offset != self.xdet_trig_count_offset_mean,
        ]):
            from numpy import rint
            self.xdet_trig_count_offset = rint(self.xdet_trig_count_offset_mean)
            logging.debug(f"xdet_trig_count_offset = {self.xdet_trig_count_offset}")

    @property
    def xdet_trig_count_offset_mean(self):
        from numpy import nanmedian
        return nanmedian(self.xdet_trig_count_offsets)

    @property
    def xdet_trig_count_offset_error(self):
        from numpy import nanstd
        return nanstd(self.xdet_trig_count_offsets)

    @property
    def xdet_trig_count_offsets(self):
        from numpy import array, nanargmin, abs, nan

        offsets = []
        images = list(self.temp_images.values())
        trigger_events = list(self.trigger_events)
        trigger_times = array([event.time for event in trigger_events])
        for image in images:
            t = image.acquire_timestamp - self.acquire_timestamp_offset
            dt = abs(t - trigger_times)
            try:
                i = nanargmin(dt)
            except ValueError:
                offset = nan
            else:
                event = trigger_events[i]
                xdet_trig_count = event.value
                n = self.file_image_number(image.filename)
                offset = xdet_trig_count - n
                # offset = (xdet_trig_count - 1) - n
            offsets.append(offset)
        return offsets

    @property
    def acquire_timestamp_offset(self):
        from numpy import nanmedian, nan
        offsets = self.acquire_timestamp_offsets
        offset = nanmedian(offsets) if offsets else nan
        return offset

    @property
    def acquire_timestamp_offsets(self):
        images = list(self.temp_images.values())
        offsets = [image.acquire_timestamp_offset for image in images]
        return offsets

    def timing_system_value(self, name):
        PV_name = getattr(self.timing_system, name).PV_name
        from CA import caget
        value = caget(PV_name)
        from numpy import nan
        if value is None:
            value = nan
        return value

    def set_timing_system_value(self, name, value):
        PV_name = getattr(self.timing_system, name).PV_name
        from CA import caput
        caput(PV_name, value)

    def xray_image_filename(self, xdet_acq_count, warning=True):
        """Where to archive the nth image of the current dataset?
        xdet_acq_count:image number (0 = first image of dataset)
        Return value: Absolute pathname"""
        from numpy import isnan
        file_basenames = self.file_basenames
        if not isnan(xdet_acq_count) and xdet_acq_count in range(0, len(file_basenames)):
            ext = "." + self.xray_image_extension.strip(".")
            filename = self.directory + "/xray_images/" + file_basenames[xdet_acq_count] + ext
        else:
            if warning:
                logging.warning(f"Dataset has no filename for xdet_acq_count={xdet_acq_count}")
            filename = ""
        return filename

    @property
    def acquiring(self):
        value = self.state() == 'acquiring series'
        return value

    @acquiring.setter
    def acquiring(self, value):
        if self.acquiring != value:
            if value:
                self.starting_acquisition = True
            else:
                self.stopping_acquisition = True

    n_digits = 7

    @thread_property
    def starting_acquisition(self):
        """Start continuous acquisition"""
        self.empty_scratch_directory()

        self.ignore_first_trigger = False
        n_frames = 10 ** self.n_digits - 1
        self.start_series_triggered(n_frames=n_frames,
                                    filename_base=self.scratch_directory + "/",
                                    filename_suffix=".rx", number_field_width=self.n_digits)

        self.limit_files_autostart()

    @thread_property
    def stopping_acquisition(self):
        """Stop continuous acquisition"""
        self.read_bkg()
        # self.abort()

    @thread_property
    def update_background(self):
        acquiring = self.acquiring
        self.read_bkg()
        self.acquiring = acquiring

    def empty_scratch_directory(self):
        """Limit the number of files in the scratch directory"""
        from os import remove
        for f in self.temp_filenames:
            try:
                remove(f)
            except Exception as msg:
                logging.warning("Cannot remove %r: %s" % (f, msg))
        from os.path import exists
        from os import makedirs
        directory = self.scratch_directory
        if not exists(directory):
            makedirs(directory)

    def limit_files_autostart(self):
        if self.limiting_files_requested:
            self.limiting_files = True

    limiting_files_requested = db_property("limiting_files_requested", True)

    @thread_property
    def limiting_files(self):
        logging.debug("Limiting files started")
        self.limiting_files_requested = True
        while not cancelled():
            self.limit_files()
            from time import sleep
            sleep(0.2)
        self.limiting_files_requested = False
        logging.debug("Limiting files stopped")

    def limit_files(self):
        """Limit the number of files in the scratch directory"""
        from os import remove
        files_to_delete = self.temp_filenames[0:-self.nimages_to_keep]
        for f in files_to_delete:
            try:
                remove(f)
            except OSError:
                pass

    def get_temp_image_count(self):
        return len(self.temp_filenames)

    def set_temp_image_count(self, count):
        from os import remove
        files_to_delete = self.temp_filenames[0:-count]
        for f in files_to_delete:
            try:
                remove(f)
            except OSError:
                pass

    temp_image_count = property(get_temp_image_count, set_temp_image_count)

    @property
    def current_image_filename(self):
        """Current image filename"""
        filename = self.xray_image_filename(self.xdet_acq_count, warning=False)
        return filename

    @property
    def nimages(self):
        """How many images left to save?"""
        nimages = self.acquisition.n - self.xdet_acq_count
        nimages = max(nimages, 0)
        return nimages

    @property
    def last_image_number(self):
        """Last acquired image"""
        last_image_number = self.file_image_number(self.last_filename)
        return last_image_number

    @property
    def last_filename(self):
        """File name of last acquired image"""
        filenames = self.temp_filenames
        filename = filenames[-1] if len(filenames) > 0 else ""
        return filename

    @staticmethod
    def file_image_number(filename):
        """Extract serial number from image pathname"""
        from os.path import basename
        try:
            image_number = int(basename(filename).replace(".rx", ""))
        except ValueError:
            image_number = 0
        return image_number

    def temp_filename_(self, image_number):
        return f"{self.scratch_directory}/{image_number:0{self.n_digits}d}.rx"

    temp_directory = function_property(directory, "scratch_directory")
    _temp_basenames = attribute_property("temp_directory", "files")

    @thread_property
    def monitoring_temp_basenames(self):
        from time import sleep
        while not cancelled():
            self.temp_basenames = self._temp_basenames
            sleep(0.5)

    temp_basenames = monitored_value_property([])

    @monitored_property
    def temp_filenames(self, scratch_directory, temp_basenames: list) -> list:
        basenames = temp_basenames
        basenames = [basename for basename in basenames if not basename.startswith(".")]
        filenames = [scratch_directory + "/" + f for f in basenames]
        filenames = sorted(filenames)
        return filenames

    @monitored_property
    def new_temp_filenames(self, temp_filenames):
        filenames = sorted(set(temp_filenames) - set(self.old_temp_filenames))
        self.old_temp_filenames = list(temp_filenames)
        return filenames

    old_temp_filenames = []

    @property
    def monitoring_new_temp_filenames(self):
        return self.handle_new_temp_filenames in self.new_temp_filenames_handlers

    @monitoring_new_temp_filenames.setter
    def monitoring_new_temp_filenames(self, monitoring):
        if monitoring:
            self.new_temp_filenames_handlers.add(self.handle_new_temp_filenames)
        else:
            self.new_temp_filenames_handlers.remove(self.handle_new_temp_filenames)

    @property
    def new_temp_filenames_handlers(self):
        from reference import reference
        return reference(self, "new_temp_filenames").monitors

    @handler_method
    def handle_new_temp_filenames(self, event):
        new_temp_filenames = event.value
        for temp_filename in new_temp_filenames:
            self.save_temp_file(temp_filename)

    @property
    def current_temp_filename(self):
        """Pathnames of last temporarily stored image"""
        filenames = self.temp_filenames
        if len(filenames) > 1:
            filename = filenames[-1]
        else:
            filename = ""
        return filename

    def set_bin_factor(self, value):
        """Image size reduction at readout time"""
        if value != Rayonix_Detector.get_bin_factor(self):
            acquiring = self.acquiring
            Rayonix_Detector.set_bin_factor(self, value)
            self.acquiring = acquiring

    bin_factor = property(Rayonix_Detector.get_bin_factor, set_bin_factor)

    # For backward compatibility

    @thread_property
    def live_image(self):
        """Display a live image"""
        from time import sleep
        while not cancelled():
            self.update_live_image()
            sleep(0.2)

    live_image_filename = ""

    def update_live_image(self):
        """Display a live image"""
        from ImageViewer import show_image
        filename = self.current_temp_filename
        if filename and filename != self.live_image_filename:
            show_image(filename)
            self.live_image_filename = filename

    def get_timing_mode(self):
        return "SAXS/WAXS"

    def set_timing_mode(self, value):
        pass

    timing_mode = property(get_timing_mode, set_timing_mode)
    timing_modes = ["SAXS/WAXS", "Laue"]

    xdet_trig_count = alias_property("timing_system.channels.xdet.trig_count.count")
    xdet_acq_count = alias_property("timing_system.channels.xdet.acq_count.count")
    timing_system_sequencer_acquiring = alias_property("timing_system_sequencer.acquiring")
    collecting_dataset = alias_property("acquisition.collecting_dataset")
    file_basenames = alias_property("acquisition.file_basenames")
    xray_image_extension = alias_property("acquisition.xray_image_extension")
    directory = alias_property("acquisition.directory")

    timing_system_sequencer = alias_property("timing_system.sequencer")
    timing_system = alias_property("domain.timing_system_client")
    acquisition = alias_property("domain.acquisition_client")

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    class Trigger_Event:
        def __init__(self, time, value):
            self.time = time
            self.value = value

        def __repr__(self):
            return f"{type(self).__name__}(time={date_time(self.time)}, value={self.value})"

        def __eq__(self, other):
            return all([
                type(self) == type(other),
                self.time == getattr(other, "time", None),
                self.value == getattr(other, "value", None),
            ])

    class Image_Info:
        from numpy import nan
        filename = ""
        file_timestamp = nan
        acquire_timestamp = nan

        def __init__(self, filename):
            self.filename = filename

        def __repr__(self):
            return f"{type(self).__name__}({self.filename!r}, file_timestamp={date_time(self.file_timestamp)})"

        def __eq__(self, other):
            return all([
                type(self) == type(other),
                self.filename == getattr(other, "filename", None),
            ])

        @property
        def acquire_timestamp_offset(self):
            # offset = acquire_timestamp - file_timestamp
            # acquire_timestamp = file_timestamp + offset
            # file_timestamp = acquire_timestamp - offset
            return self.acquire_timestamp - self.file_timestamp

    @handler_method
    def report(self, event): logging.info(f"{self}: {event}")


def mtime(filename):
    """When was the file modified the last time?
    Return value: seconds since 1970-01-01 00:00:00 UTC as floating point number
    0 if the file does not exist"""
    from os.path import getmtime
    try:
        return getmtime(filename)
    except OSError:
        return 0


if __name__ == "__main__":  # for debugging
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler

    domain_name = "BioCARS"
    from IOC import ioc as _ioc
    ioc = _ioc(f'{domain_name}.rayonix_detector')
    self = ioc.object
    # self = rayonix_detector_driver(domain_name)

    print("ioc.start()")
    print('self.start()')
    # print('self.monitoring_temp_basenames = True')


    @handler
    def report(event): logging.info(f"{event}")

    # from reference import reference as _reference
    # _reference(self, "temp_basenames").monitors.add(report)
    # _reference(self, "new_temp_filenames").monitors.add(report)

    # print(f"self.limiting_files = {self.limiting_files}")
    # print(f"self.limiting_files_requested = {self.limiting_files_requested}")
    # print(f"self.acquiring = {self.acquiring}")
    # print(f"self.acquiring_images = {self.acquiring_images}")
