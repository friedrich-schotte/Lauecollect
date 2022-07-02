"""
Author: Friedrich Schotte
Date created: 2021-09-07
Date last modified: 2021-10-21
Revision comment: Correcting for xray_image_acquire_timestamp_clock_drift_rate
"""
__version__ = "1.2"

from dataset import Dataset
import numpy

numpy.warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')   # for nanargmin
numpy.warnings.filterwarnings('ignore', r'Mean of empty slice')  # for nanmedian


class Corrected_Dataset(Dataset):
    from monitored_property import monitored_property

    def correct_xray_image_filenames(self, dry_run=True):
        from save_rename_files import save_rename_files
        filenames, reassigned_filenames = self.xray_image_filename_reassignments
        save_rename_files(filenames, reassigned_filenames, dry_run)

    @monitored_property
    def xray_image_filename_reassignments(self, logfile_xray_image_filenames, xray_image_reassigned_filenames):
        from exist_files import exist_files
        from numpy import asarray

        filenames = asarray(logfile_xray_image_filenames)
        reassigned_filenames = asarray(xray_image_reassigned_filenames)

        different = filenames != reassigned_filenames
        filenames = filenames[different]
        reassigned_filenames = reassigned_filenames[different]

        existing = exist_files(filenames)
        filenames = filenames[existing]
        reassigned_filenames = reassigned_filenames[existing]

        return filenames, reassigned_filenames

    @monitored_property
    def xray_image_reassigned_filenames(self, logfile_xray_image_filenames, xray_image_sequence_numbers_2):
        from numpy import asarray
        filenames = asarray(logfile_xray_image_filenames + [""])[xray_image_sequence_numbers_2]
        filenames = filenames.tolist()
        return filenames

    @monitored_property
    def xray_image_sequence_numbers_2(self, xray_image_timestamps_2, end_times):
        i = [closest_index_within_tolerance(t, end_times, 0.15) for t in xray_image_timestamps_2]
        return i

    @monitored_property
    def xray_image_order_2(self, xray_image_timestamps_2, end_times):
        i = [closest_index_within_tolerance(t, xray_image_timestamps_2, 0.15) for t in end_times]
        return i

    @monitored_property
    def xray_image_timestamps_2(self, xray_image_acquire_timestamps, xray_image_acquire_timestamp_end_time_offset0_2,
                                xray_image_acquire_timestamp_clock_drift):
        from numpy import asarray
        n = min(len(xray_image_acquire_timestamps), len(xray_image_acquire_timestamp_clock_drift))
        timestamps = asarray(xray_image_acquire_timestamps[0:n]) - asarray(
            xray_image_acquire_timestamp_clock_drift[0:n]) - \
            xray_image_acquire_timestamp_end_time_offset0_2

        return timestamps

    @monitored_property
    def xray_image_acquire_timestamp_end_time_offset0_2(self, xray_image_acquire_timestamp_end_time_offsets_adjusted_2):
        from numpy import nanmedian
        dt = nanmedian(xray_image_acquire_timestamp_end_time_offsets_adjusted_2)
        return dt

    @monitored_property
    def xray_image_acquire_timestamp_end_time_offsets_adjusted_2(self, xray_image_acquire_timestamp_end_time_offsets_2,
                                                                 xray_image_acquire_timestamp_clock_drift):
        from numpy import asarray
        n = min(len(xray_image_acquire_timestamp_end_time_offsets_2), len(xray_image_acquire_timestamp_clock_drift))
        dt = asarray(xray_image_acquire_timestamp_end_time_offsets_2[0:n]) - \
            asarray(xray_image_acquire_timestamp_clock_drift[0:n])
        return dt

    @monitored_property
    def xray_image_acquire_timestamp_end_time_offsets_2(self, xray_image_acquire_timestamps_2, end_times):
        from numpy import asarray
        n = min(len(xray_image_acquire_timestamps_2), len(end_times))
        dt = asarray(xray_image_acquire_timestamps_2[0:n]) - asarray(end_times[0:n])
        return dt

    @monitored_property
    def xray_image_acquire_timestamp_end_time_offsets_1(self, xray_image_acquire_timestamps, end_times):
        from numpy import asarray
        n = min(len(xray_image_acquire_timestamps), len(end_times))
        dt = asarray(xray_image_acquire_timestamps[0:n]) - asarray(end_times[0:n])
        return dt

    @monitored_property
    def xray_image_acquire_timestamps_2(self, xray_image_acquire_timestamps, xray_image_order_1):
        from numpy import asarray, nan
        filenames = asarray(xray_image_acquire_timestamps + [nan])[xray_image_order_1]
        filenames = filenames.tolist()
        return filenames

    @monitored_property
    def xray_image_order_1(self, xray_image_timestamps_1, end_times):
        i = [closest_index(t, xray_image_timestamps_1) for t in end_times]
        i = replace_duplicates(i, -1)
        return i

    @monitored_property
    def xray_image_timestamps_1(self, xray_image_acquire_timestamps,
                                xray_image_acquire_timestamp_header_timestamp_offset):
        from numpy import asarray
        timestamps = asarray(xray_image_acquire_timestamps) - xray_image_acquire_timestamp_header_timestamp_offset - \
            self.image_file_saving_delay
        return timestamps

    image_file_saving_delay = 0.182

    @monitored_property
    def xray_image_acquire_timestamp_header_timestamp_offset(self,
                                                             xray_image_acquire_timestamp_header_timestamp_offsets):
        from numpy import nanmedian
        dt = nanmedian(xray_image_acquire_timestamp_header_timestamp_offsets)
        return dt

    @monitored_property
    def xray_image_acquire_timestamp_header_timestamp_offsets(self, xray_image_acquire_timestamps,
                                                              xray_image_header_timestamps):
        from numpy import asarray
        n = min(len(xray_image_acquire_timestamps), len(xray_image_header_timestamps))
        dt = asarray(xray_image_acquire_timestamps[0:n]) - asarray(xray_image_header_timestamps[0:n])
        return dt

    @monitored_property
    def xray_image_header_timestamps(self, logfile_xray_images):
        timestamps = [image.header_timestamp for image in logfile_xray_images]
        timestamps = [t - self.timezone_offset for t in timestamps]
        return timestamps

    @monitored_property
    def duplicate_xray_image_count(self, xray_image_serial_numbers):
        from numpy import asarray, isnan, unique
        i = asarray(xray_image_serial_numbers)
        i = i[~isnan(i)]
        _, counts = unique(i, return_counts=True)
        duplicate_count = sum(counts > 1)
        return duplicate_count

    @monitored_property
    def xray_images_ordered(self, xray_image_serial_numbers):
        from numpy import asarray, isnan, diff
        i = asarray(xray_image_serial_numbers)
        i = i[~isnan(i)]
        ordered = not any(diff(i) <= 0)
        return ordered

    @monitored_property
    def xray_image_serial_numbers(self, logfile_xray_images):
        header_filename = [image.header_filename for image in logfile_xray_images]
        numbers = [to_float(name.replace(".rx", "")) for name in header_filename]
        return numbers


def closest_index_within_tolerance(value, values, tolerance=0.15):
    i = closest_index(value, values)
    if i >= 0:
        dt = abs(value - values[i])
        if dt > tolerance:
            i = -1
    return i


def closest_index(value, values):
    from numpy import asarray, nanargmin
    differences = abs(value - asarray(values))
    try:
        i = nanargmin(differences)
    except ValueError:
        i = -1
    return i


def replace_duplicates(values, replacement):
    new_values = []
    unique_values = set()
    for value in values:
        new_values.append(value if value not in unique_values else replacement)
        unique_values.add(value)
    return new_values


def to_float(x):
    """Convert x to float if possible, else return nan"""
    from numpy import nan
    try:
        x = float(x)
    except ValueError:
        x = nan
    return x


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # directory_name = "/net/femto-data2/C/Data/2021.10/WAXS/Ca-CaM/Ca-CaM_PumpProbe_PC1-1"
    # directory_name = "/net/femto-data2/C/Data/2021.10/WAXS/Ca-CaM/Ca-CaM-Buffer_Tramp_B-2"
    # directory_name = "/net/femto-data2/C/Data/2021.10/WAXS/Pb-CaM/Pb-CaM_Tramp_PC0-1"
    # directory_name = "/net/femto-data2/C/Data/2021.10/WAXS/apo-CaM/apo-CaM_Tramp_PC2-2"
    # directory_name = "/net/femto-data2/C/Data/2021.10/WAXS/Pb-CaM/Pb-CaM-Buffer_Tramp_B-1"
    directory_name = "/net/mx340hs/data/hekstra_2206/Test/test_1a"
    self = Corrected_Dataset(directory_name)

    print("from save_rename_files import rollback_directory")
    print("rollback_directory(directory_name, dry_run=True)")
    print("")
    print("self.duplicate_xray_image_count")
    print("self.xray_images_ordered")
    print("")
    print("self.correct_xray_image_filenames(dry_run=True)")
