"""
Author: Friedrich Schotte
Date created: 2021-08-22
Date last modified: 2022-05-12
Revision comment: Renamed lecroy_scope_trace_file
"""
__version__ = "2.1"

from glob import glob
from os.path import getmtime
from numpy import diff, array, average, std
from lecroy_scope_trace_file import lecroy_scope_trace_file


def trigger_time(filename):
    return lecroy_scope_trace_file(filename).trigger_time


# pattern = "//femto-data2/C/Data/2022.03/WAXS/GB3/GB3_PumpProbe_PC0-1/xray_traces/GB3_PumpProbe_PC0-1_*_-16.000C_07_01_C1.trc"
# pattern = "/net/femto-control/data/anfinrud_2203/Data/WAXS/RNA-Dumbbell-8BP/RNA-Dumbell-8BP_PumpProbe_PC0-8/xray_traces/*_00??_*_C1.trc"
# pattern = "/net/femto-control/data/anfinrud_2203/Data/WAXS/RNA-Dumbbell-8BP/RNA-Dumbell-8BP_PumpProbe_PC0-9/xray_traces/*_00??_*_C1.trc"
# pattern = "/net/femto-control/data/anfinrud_2203/Data/WAXS/RNA-Dumbbell-8BP/RNA-Dumbell-8BP_PumpProbe_PC0-10/xray_traces/*_00??_*_C1.trc"
pattern = "/net/femto-control/data/anfinrud_2203/Data/WAXS/RNA-Dumbbell-8BP/RNA-Dumbell-8BP_PumpProbe_PC0-11/xray_traces/*_????_*_C1.trc"
filenames = sorted(glob(pattern))

file_timestamps = array([getmtime(filename) for filename in filenames])
file_dt = diff(file_timestamps)

trigger_timestamps = array([trigger_time(filename) for filename in filenames])
# trigger_timestamps += 3600

trigger_dt = diff(trigger_timestamps)

dt = trigger_timestamps - file_timestamps
dt_low = dt[dt < average(dt)]
dt_high = dt[dt >= average(dt)]
fraction_dt_high = average(dt >= average(dt))
std_dt = std(dt)
std_dt_low = std(dt_low)
std_dt_high = std(dt_high)
spread = average(dt_high) - average(dt_low)

print(f"{len(dt)} traces, outlier fraction: {fraction_dt_high:.3f}, offset: {spread:.6f}s")
print(f"timing jitter: all {std(dt):.6f}s, normal {std(dt_low):.6f}s, outlier {std(dt_high):.6f}s")
