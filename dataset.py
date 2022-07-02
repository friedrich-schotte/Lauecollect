"""
Author: Friedrich Schotte
Date created: 2021-10-20
Date last modified: 2021-10-21
Revision comment:
"""
__version__ = "1.0"

import numpy

numpy.warnings.filterwarnings('ignore', r'Mean of empty slice')  # for nanmedian


class Dataset:
    xray_image_acquire_timestamp_clock_drift_rate = 1.95070e-05
    from attribute_property import attribute_property
    from directory import directory as directory_object
    from file import file
    from function_property import function_property
    from monitored_property import monitored_property
    from monitored_value_property import monitored_value_property

    def __init__(self, directory_name, timezone_offset=None):
        self.directory_name = directory_name
        if timezone_offset is not None:
            self.timezone_offset = timezone_offset

    def __repr__(self):
        return f"{type(self).__name__}({self.directory_name!r})"

    logfile = function_property(file, "logfile_name")
    logfile_content = attribute_property("logfile", "content")
    xray_image_directory = function_property(directory_object, "xray_image_directory_name")
    xray_image_basenames = attribute_property("xray_image_directory", "files")
    n = function_property(len, "logfile_lines")
    timezone_offset = monitored_value_property(-3600)
    directory_name = monitored_value_property("")

    @monitored_property
    def start_times(self, logfile_lines):
        from time_string import timestamp
        timestamps = [line.split("\t")[1] for line in logfile_lines]
        timestamps = [timestamp(t) for t in timestamps]
        return timestamps

    @monitored_property
    def end_times(self, logfile_lines):
        from time_string import timestamp
        timestamps = [line.split("\t")[2] for line in logfile_lines]
        timestamps = [timestamp(t) for t in timestamps]
        return timestamps

    @monitored_property
    def logfile_filenames(self, logfile_lines):
        filenames = [line.split("\t")[3] for line in logfile_lines]
        return filenames

    @monitored_property
    def xray_images(self, xray_image_filenames):
        from rayonix_image import rayonix_image
        images = [rayonix_image(f) for f in xray_image_filenames]
        return images

    @monitored_property
    def logfile_xray_images(self, logfile_xray_image_filenames):
        from rayonix_image import rayonix_image
        images = [rayonix_image(f) for f in logfile_xray_image_filenames]
        return images

    @monitored_property
    def logfile_xray_image_filenames(self, logfile_filenames):
        filenames = [self.xray_image_directory_name + "/" + f for f in logfile_filenames]
        return filenames

    @monitored_property
    def xray_image_filenames(self, xray_image_directory_name, xray_image_basenames):
        from os.path import isfile
        basenames = xray_image_basenames
        basenames = [basename for basename in basenames if not basename.startswith(".")]
        filenames = [xray_image_directory_name + "/" + f for f in basenames]
        filenames = [filename for filename in filenames if filename.endswith(".mccd")]
        filenames = [filename for filename in filenames if isfile(filename)]
        filenames = sorted(filenames)
        return filenames

    @monitored_property
    def xray_image_directory_name(self, directory_name):
        return directory_name + "/" + "xray_images"

    @monitored_property
    def logfile_lines(self, logfile_content):
        lines = logfile_content.splitlines()
        lines = [line for line in lines if not line.startswith("#")]
        return lines

    @monitored_property
    def logfile_name(self, directory_name, basename):
        return directory_name + "/" + basename + ".log"

    @monitored_property
    def basename(self, directory_name):
        from os.path import basename
        return basename(directory_name)

    @basename.setter
    def basename(self, basename):
        from os.path import dirname
        self.directory_name = dirname(self.directory_name) + "/" + basename

    @monitored_property
    def xray_image_timing_errors(self, xray_image_timestamps, end_times):
        from numpy import asarray
        n = min(len(xray_image_timestamps), len(end_times))
        dt = asarray(xray_image_timestamps[0:n]) - asarray(end_times[0:n])
        return dt

    @monitored_property
    def xray_image_timestamps(self, xray_image_acquire_timestamps, xray_image_acquire_timestamp_end_time_offset0,
                              xray_image_acquire_timestamp_clock_drift):
        from numpy import asarray
        timestamps = asarray(xray_image_acquire_timestamps) - xray_image_acquire_timestamp_clock_drift - \
            xray_image_acquire_timestamp_end_time_offset0

        return timestamps

    @monitored_property
    def xray_image_acquire_timestamp_end_time_offset0(self, xray_image_acquire_timestamp_end_time_offsets_adjusted):
        from numpy import nanmedian
        dt = nanmedian(xray_image_acquire_timestamp_end_time_offsets_adjusted)
        return dt

    @monitored_property
    def xray_image_acquire_timestamp_end_time_offsets_adjusted(self, xray_image_acquire_timestamp_end_time_offsets,
                                                               xray_image_acquire_timestamp_clock_drift):
        from numpy import asarray
        n = min(len(xray_image_acquire_timestamp_end_time_offsets), len(xray_image_acquire_timestamp_clock_drift))
        dt = asarray(xray_image_acquire_timestamp_end_time_offsets[0:n]) - \
            asarray(xray_image_acquire_timestamp_clock_drift[0:n])
        return dt

    @monitored_property
    def xray_image_acquire_timestamp_end_time_offsets(self, xray_image_acquire_timestamps, end_times):
        from numpy import asarray
        n = min(len(xray_image_acquire_timestamps), len(end_times))
        dt = asarray(xray_image_acquire_timestamps[0:n]) - asarray(end_times[0:n])
        return dt

    @monitored_property
    def xray_image_acquire_timestamp_clock_drift(self, end_times):
        from numpy import nan, asarray
        if len(end_times):
            t0 = end_times[0]
        else:
            t0 = nan
        t = asarray(end_times)
        dt = (t - t0) * self.xray_image_acquire_timestamp_clock_drift_rate
        return dt

    @monitored_property
    def xray_image_acquire_timestamps(self, logfile_xray_images):
        timestamps = [image.acquire_timestamp for image in logfile_xray_images]
        timestamps = [t - self.timezone_offset for t in timestamps]
        return timestamps


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # directory_name = "/net/femto-data2/C/Data/2021.10/WAXS/Ca-CaM/Ca-CaM_PumpProbe_PC1-1"
    directory_name = "/net/femto-data2/C/Data/2021.10/WAXS/Water/Water-static-3_W"
    self = Dataset(directory_name)

    print("from numpy import *")
    print("nanmax(self.xray_image_timing_errors) - nanmin(self.xray_image_timing_errors)")
