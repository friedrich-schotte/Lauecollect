"""marccd decoding. Hyun Sun Cho, Jan 24 2015
HS High Speed Series X-ray Detector Manual by Ross A. Doyle and Justin Anderson
Rayonix_HS_detector_manual-0.3a.pdf
"""
__version__ = "1.0"

def read_mccd(filename):
    """read mccd file and get data"""
    import mmap
    with open(filename,"rb") as f:
        # try to map to reduce any overhead to read file.
        content = mmap.mmap(f.fileno(),0,prot=mmap.ACCESS_READ) #PROT_READ) #2048+512
        f.close()
        
    #content = file(filename,"rb").read()
    fileparam_offset = content.find("MarCCD X-ray Image File")
    fileparam = content[fileparam_offset:fileparam_offset+1024]
    detectorparam_offset = fileparam_offset-256 #
    head_offset = 1024
    #print fileparam_offset, detectorparam_offset, head_offset
    detectorparam = content[detectorparam_offset:detectorparam_offset+128]
    headparam = content[head_offset:head_offset+256]
    data = content[4096:]
    
    from struct import unpack
    head_nfast, = unpack("i",headparam[80:84])
    head_nslow, = unpack("i",headparam[84:88])
    #print head_nfast, head_nslow
    detector_type, = unpack("i",detectorparam[0:4])
    pixelsize_x, = unpack("i",detectorparam[4:8])
    pixelsize_y, = unpack("i",detectorparam[8:12])

    from numpy import frombuffer,int16
    data = frombuffer(data,int16)
    data = data.reshape((head_nfast,head_nslow))

    return data

def timestamp_mccd(filename):
    """read mccd file and decode information"""
    import mmap
    with open(filename,"rb") as f:
        # try to map to reduce any overhead to read file.
        content = mmap.mmap(f.fileno(),0,prot=mmap.ACCESS_READ) #PROT_READ) #2048+512
        f.close()
        
    fileparam_offset = content.find("MarCCD X-ray Image File")
    fileparam = content[fileparam_offset:fileparam_offset+1024]
    
    from struct import unpack
    acquire_timestamp = fileparam[320:352] 
    header_timestamp = fileparam[352:384] 
    save_timestamp = fileparam[384:416] 

    months = int(acquire_timestamp[:2])
    days = int(acquire_timestamp[2:4])
    hours = int(acquire_timestamp[4:6])
    mins = int(acquire_timestamp[6:8])
    year = int(acquire_timestamp[8:12])
    seconds = int(acquire_timestamp[13:15])
    # old version rayonix mccd file on before Feb 6 2015 does not have microseconds
    try: 
        microseconds = int(acquire_timestamp[16:22])
    except ValueError: microseconds = 0 
    
    from datetime import datetime 
    date_time = datetime(year,months,days,hours,mins,seconds,microseconds)
    #print date_time
    #ts_format = date_time.strftime("%d-%b-%y %H:%M:%S.%f")
    ts = toseconds(date_time)    
    return ts

def toseconds(dt):
    """convert datetime format (dt) to seconds"""
    import datetime
    from time import mktime
    return mktime(dt.timetuple()) + dt.microsecond*1.e-6

def todatetime(ts):
    import datetime
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S.%f')

if __name__ == "__main__": # for testing
    #filename = "/Mirror/Femto/C/Data/2014.08/Setup/Beamstop/3mm/Sapphire_3mm_24bunch_001.mccd"
    #filename = "/Mirror/Femto/C/Data/2014.03/WAXS/GB3/GB3-1/GB3-1_offBT1_003.mccd"
    #filename = "/Volumes/data-1/pub/rob/testing/testing.mccd"
    filename = "/data/anfinrud_1502/Data/WAXS/Reference/Reference1/Reference1_offWT1_100.mccd"
    #filename = "/data/anfinrud_1502/Test/Test19/Test19_64.mccd"
    ts = timestamp_mccd(filename)
    data = read_mccd(filename)
    print "%6f" % ts
