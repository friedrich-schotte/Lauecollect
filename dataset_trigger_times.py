"""Examine waveform data for completeness.
Friedrich Schotte, Jun 25, 2016 - Jun 30, 2016
"""
from os.path import exists
from os import listdir
from numpy import concatenate,array,sort,diff,round,unique
from time_string import date_time
__version__ = "1.1"

def trigger_times(pathname):
    """Pathname: directory where the trace files are stored"""
    from lecroy_scope_waveform import trigger_times
    t = concatenate([trigger_times(f) for f in files(pathname)])
    return t

def trigger_counts(pathname):
    """Pathname: directory where the trace files are stored"""
    from lecroy_scope_waveform import trigger_times
    from numpy import array
    t = array([len(trigger_times(f)) for f in files(pathname)])
    return t

def sizes(pathname):
    """Pathname: directory where the trace files are stored"""
    from os.path import getsize
    from numpy import array
    sizes = array([getsize(f) for f in files(pathname)])
    return sizes

def file_timestamps(pathname):
    """Pathname: directory where the trace files are stored"""
    from os.path import getmtime
    from numpy import array
    timestamps = array([getmtime(f) for f in files(pathname)])
    return timestamps

def files(pathname):
    """List of file in a dirctory, sorted by timestamp."""
    from os.path import getsize,getmtime
    from numpy import array,argsort
    files = array([pathname+"/"+f for f in listdir(pathname)])
    order = argsort(array([getmtime(f) for f in files]))
    files = files[order]
    return files

if __name__ == "__main__":
    from pdb import pm # for debugging
    from lecroy_scope_waveform import read_waveform
    from numpy import *
    def frac(x): return x-trunc(x)
    pathname = "//Femto/C/All Projects/APS/Experiments/2016.06/Temp/WAXS/AlCl3/AlCl3-2"
    pathname = "/net/mx340hs/data/anfinrud_1606/Data/WAXS/Villin/Villin-static-2"
    pathname = "/net/mx340hs/data/anfinrud_1606/Data/WAXS/Villin/Villin-Temp-Ramp1"
    pathname = "/net/mx340hs/data/anfinrud_1606/Data/WAXS/Villin-Gdn/Villin-Gdn-Buffer-2"
    pathname = "/net/mx340hs/data/anfinrud_1606/Data/WAXS/Villin/Villin-1"
    print('s = sizes("%s/xray_traces")' % pathname)
    print('f = files("%s/xray_traces")' % pathname)
    print('N = trigger_counts("%s/xray_traces")' % pathname)
    print('t = trigger_times("%s/xray_traces")' % pathname)
    print('t = file_timestamps("%s/xray_traces")' % pathname)
    print('date_time(t[0])')
    print('dt = round(diff(t),5)')
    print('i = (where(dt > 0.075)[0]+1)/41.0')
    print('average(frac(i) != 0)')
    
