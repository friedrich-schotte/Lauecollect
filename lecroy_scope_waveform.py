"""Read LeCroy binary waveform file.
For offline analysis of wavform files, not for waveform data acqisition.
Friedrich Schotte, 30 Jan 2012 - 14 Apr 2017

Found documentation about the LeCroy binary waveform format in form of Matlab
code:
File ReadLeCroyBinaryWaveform.m by Alan Blankman, LeCroy, 2006
Extended by Jean-Daniel Deschenes, 13 Jan 2010, to read multisegment waveforms.
http://www.mathworks.com/matlabcentral/fileexchange/26375

Structure of a LeCroy binary waveform file:
Magic number "#9001120146", length: 11 bytes
Binary wave descriptor, starting with WAVEDESC", length: 346 bytes
Optional comment section, usully length 0 bytes
Trigger time/trigger offset array, length: 16 bytes times number of segments
  pairs of 64-bit floating point numbers
Waveform data, length: number of samples per trigger, plus two,
  times number of segments
  signed 8-bit integers
"""
__version__ = "1.4" # sub sampling rate ajustments to time scales
from logging import debug,info,warn,error

def read_waveform(filename):
    """Filename: path of .trc file.
    Return value: tuple of two arrays, time, voltage"""
    content = file(filename,"rb").read()
    wavedesc_offset = content.find("WAVEDESC")
    wavedesc = content[wavedesc_offset:wavedesc_offset+346]

    from struct import unpack
    comm_type, = unpack("<H",wavedesc[32:34]) # 0 = 8-bit, 1=16-bit
    comm_order, = unpack("<H",wavedesc[34:36]) # 0=big endian, 1=little endian
    # Check if format is indeed little-endian.
    assert(comm_order != 0)
    wave_descriptor_length, = unpack("<i",wavedesc[36:40])
    user_text_length, = unpack("<i",wavedesc[40:44])
    trig_time_array_size, = unpack("<i",wavedesc[48:52])
    wave_array_1, = unpack("<i",wavedesc[60:64])
    wave_array_count, = unpack("<i",wavedesc[116:120])
    subarray_count, = unpack("<i",wavedesc[144:148]) # number of trigger events

    vertical_gain, = unpack("<f",wavedesc[156:160])
    vertical_offset, = unpack("<f",wavedesc[160:164])
    horiz_interval, = unpack("<f",wavedesc[176:180])
    horiz_offset, = unpack("<d",wavedesc[180:188])

    data_offset = wavedesc_offset + wave_descriptor_length + user_text_length + \
        trig_time_array_size

    from numpy import frombuffer,int8,int16,float64,concatenate,zeros,nan
    dtype = int8 if comm_type == 0 else int16
    data = frombuffer(content[data_offset:],dtype).astype(float)
    Nsamples = wave_array_count/subarray_count
    expected_size = subarray_count*Nsamples
    if len(data) < expected_size:
        warn("%s: expecting %d*%d=%d samples, file truncated at %d samples." %
            (filename,subarray_count,Nsamples,expected_size,len(data)))
        data = concatenate((data,nan*zeros(expected_size-len(data))))
    data = data.reshape((subarray_count,Nsamples))
    # Convert counts to voltage.
    U = data*vertical_gain - vertical_offset

    # Reconstruct time scales.
    trigger_time_array_offset = wavedesc_offset + wave_descriptor_length + user_text_length
    trigger_time_array = content[trigger_time_array_offset:trigger_time_array_offset+trig_time_array_size]

    data = frombuffer(trigger_time_array,float64)
    data = data.reshape((subarray_count,2))
    relative_trigger_times,trigger_offsets = data.T

    from numpy import arange,row_stack,array
    t = array([arange(0,Nsamples)*horiz_interval+t0 for t0 in trigger_offsets])
    ##t = array([arange(0,Nsamples)*horiz_interval for t0 in trigger_offsets])+trigger_offsets[0]
    
    return t,U

def trigger_times(filename):
    """Filename: path of .trc file.
    Return value: tuple of two arrays, time, voltage"""
    content = file(filename,"rb").read()
    wavedesc_offset = content.find("WAVEDESC")
    wavedesc = content[wavedesc_offset:wavedesc_offset+346]

    from struct import unpack
    second, = unpack("<d",wavedesc[296+0:296+8])
    minute, = unpack("B" ,wavedesc[296+8:296+9])
    hour, =   unpack("B" ,wavedesc[296+9:296+10])
    day, =    unpack("B" ,wavedesc[296+10:296+11])
    month, =  unpack("B" ,wavedesc[296+11:296+12])
    year, =   unpack("H" ,wavedesc[296+12:296+14])
    from time import mktime
    from numpy import floor,rint
    trigger_time = mktime((year,month,day,hour,minute,int(floor(second)),-1,-1,-1))\
        +(second-floor(second))

    from struct import unpack
    comm_type, = unpack("<H",wavedesc[32:34]) # 0 = 8-bit, 1=16-bit
    comm_order, = unpack("<H",wavedesc[34:36]) # 0=big endian, 1=little endian
    # Check if format is indeed little-endian.
    assert(comm_order != 0)
    wave_descriptor_length, = unpack("<i",wavedesc[36:40])
    user_text_length, = unpack("<i",wavedesc[40:44])
    trig_time_array_size, = unpack("<i",wavedesc[48:52])
    subarray_count, = unpack("<i",wavedesc[144:148]) # number of trigger events

    trigger_time_array_offset = wavedesc_offset + wave_descriptor_length + user_text_length
    trigger_time_array = content[trigger_time_array_offset:trigger_time_array_offset+trig_time_array_size]

    from numpy import frombuffer,int8,float64
    data = frombuffer(trigger_time_array,float64)
    data = data.reshape((subarray_count,2))
    relative_trigger_times,trigger_offsets = data.T

    trigger_times = trigger_time+relative_trigger_times

    return trigger_times

def trigger_time(filename):
    """Filename: path of .trc file.
    Return value: time in seconds since 1 jan 1970 0:00 UTC"""
    content = file(filename,"rb").read()
    wavedesc_offset = content.find("WAVEDESC")
    wavedesc = content[wavedesc_offset:wavedesc_offset+346]

    from struct import unpack
    second, = unpack("<d",wavedesc[296+0:296+8])
    minute, = unpack("B" ,wavedesc[296+8:296+9])
    hour, =   unpack("B" ,wavedesc[296+9:296+10])
    day, =    unpack("B" ,wavedesc[296+10:296+11])
    month, =  unpack("B" ,wavedesc[296+11:296+12])
    year, =   unpack("H" ,wavedesc[296+12:296+14])
    from time import mktime
    from numpy import floor,rint
    trigger_time = mktime((year,month,day,hour,minute,int(floor(second)),-1,-1,-1))\
        +(second-floor(second))
    return trigger_time

def show_waveform(filename,first=0,N=2):
    """for testing"""
    t,U = read_waveform(filename)
    if first > len(U): first = len(U)-1
    if first+N > len(U): N = len(U)-first
    from pylab import plot,grid,xlabel,ylabel,ylim,show
    plot(t[first:first+N].T/1e-9,U[first:first+N].T,linestyle="-",marker="o",
        ms=3,mew=0)
    grid()
    xlabel("t [ns]")
    ylabel("U [V]")
    ##ylim(-4,4)
    show()

def time_string(seconds):
    from datetime import datetime
    from time import gmtime,localtime,strftime
    t = datetime.fromtimestamp(seconds).strftime("%d %b %Y %H:%M:%S.%f")
    return t
    
    
if __name__ == "__main__": # for testing
    from glob import glob
    from numpy import array,diff,sort,concatenate
    filename = "//femto-data/C/Data/2017.03/WAXS/RNA-VA1-WT/RNA-VA1-WT-1/"\
        "laser_traces/RNA-VA1-WT-1_1_31C_1_-10.1us_02_laser.trc"
    filenames = glob("//femto-data/C/Data/2017.03/WAXS/RNA-VA1-WT/RNA-VA1-WT-1/"\
        "laser_traces/RNA-VA1-WT-1_1_31C_1_*_laser.trc")
    from os.path import getmtime
    from numpy import diff,where
    print("show_waveform(filename,first=0,N=41)")
    ##print("time_string(getmtime(filename))")
    print("t = sort(concatenate([trigger_times(f) for f in filenames]))")
    print("dt = diff(sort(concatenate([trigger_times(f) for f in filenames])))")
    ##print("where(diff(trigger_times(filename))>0.025)")
    ##print("[time_string(t) for t in trigger_times(filename)]")

