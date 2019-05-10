"""
Load an image and convert it into a numpy array for processing.

Author: Friedrich Schotte
Date created: 4 Sep 2013
Date last modified: Nov 1, 2017
"""
__version__ = "1.9.6" # conditional debug

DEBUG = False

from logging import debug,warn,info,error
import numpy

class numimage(numpy.ndarray):
    """An image represented as a 2D image numpy array."""
    from numpy import nan
    # "numimage" is a subclass of "recarray".  
    # Because "recarray" uses a __new__ rather than an __init__ constructor,
    # __new__ rather than __init__ needs to be overridden.
    def __new__(subclass,arg=None,filename="",dtype=numpy.float32,shape=(0,0),
        format="",array=None,pixelsize=nan):
        """filename: TIFF,PNG,JPEG or GIF image."""
        ##print "numimage.__new__(%r,%r)" % (subclass,filename) 
        from numpy import zeros,ndarray,nan
        import numpy

        if isinstance(arg,basestring): filename = arg
        elif isinstance(arg,ndarray): array = arg
        elif isinstance(arg,tuple) and len(arg) == 2: shape = arg
        else: raise(RuntimeError,"%s: expecting str,array or (w,h)" % type(arg))

        info = {}
        
        self = None

        if filename:
            from normpath import normpath
            filename = normpath(filename)
            # A MAR CCD or Rayonix image is a TIFF image with NxN pixels,
            # depth 16 bit and a fixed-size 4096-byte TIFF header.
            # N = Nmax/bin_factor
            # Nmax = 7680 for MX340HS
            # Nmax = 4096 for MAR CCD 
            image_sizes = [3840,1920,960,480,2048,1024,512] # pixels
            headersize = 4096 # bytes
            TIFF_header_size = 1024
            from os.path import getsize
            filesize = getsize(filename) 
            for image_size in image_sizes:
                image_nbytes = 2*image_size**2
                if filesize == headersize+image_nbytes:
                    format = "RX"
                    if DEBUG: debug("using memmap")
                    from numpy import memmap,uint16,int32
                    self = memmap(filename,uint16,'r',headersize,(image_size,image_size),'F')
                    # Read TIFF header.
                    from struct import pack,unpack
                    header = file(filename).read(headersize)
                    offset, = unpack("I",header[4:8])
                    ntags, = unpack("h",header[offset:offset+2])
                    offset = offset+2; size = 12
                    class tag():
                        def __init__(self,type,dtype,length,data):
                            self.type,self.dtype,self.length,self.data = type,dtype,length,data
                        def __repr__(self):
                            return "%r,%r,%r,%r" % (self.type,self.dtype,self.length,self.data)
                    tags = {}
                    for i in range(0,ntags):
                        data = header[offset+i*size:offset+(i+1)*size]
                        type,dtype,length,data = unpack("<HHII",data)
                        tags[type] = tag(type,dtype,length,data)
                    if 283 in tags: # x resolution, type rational, data = pointer
                        offset = tags[283].data
                        num,den = unpack("II",header[offset:offset+8])
                        res = float(num)/den # in dpi
                        if DEBUG: debug("TIFF: 283: resolution num/den %r/%r=%g" % (num,den,res))
                    unit = nan
                    if 296 in tags: # resolution unit, code 2 = inch, 3 = cm
                        code = tags[296].data
                        if code == 2: unit = 25.4 # inch
                        elif code == 3: unit = 10 # cm
                        if DEBUG: debug("TIFF: 296: resolution unit %r = %r mm" % (code,unit))
                    pixelsize = unit/res
                    if DEBUG: debug("TIFF: pixelsize (%r mm)/%g = %.6f mm" % (unit,res,pixelsize))
                    # Rayonix High Speed Detector Manual v. 0.3, Ross Doyle, Justin Anderson
                    # Chapter 8: Image Format (marccd)
                    # Rayonix_HS_detector_manual-0.3a.pdf
                    start = TIFF_header_size+193*4; end = start+4
                    if DEBUG: debug("RX: pixelsize [nm]: header[%r:%r] = %r" % (start,end,header[start:end]))
                    frame_header = memmap(filename,int32,'r',TIFF_header_size,
                        (headersize-TIFF_header_size),'F')
                    pixelsize_nm = frame_header[193]
                    pixelsize = pixelsize_nm*1e-9/1e-3 # convert from nm to mm
                    if DEBUG: debug("RX: int 193: pixelsize = %r nm = %.6f mm" % (pixelsize_nm,pixelsize))
            if self is None:
                if filename.upper().endswith(".EDF"):
                    header = file(filename).read(1024)
                    headersize = header.find("}\n")+2
                    header = header[0:headersize]
                    lines = header.split("\n")
                    for line in lines:
                        line = line.strip(" ;")
                        if line.startswith("Dim_1 = "): w = int(line.replace("Dim_1 = ",""))
                        if line.startswith("Dim_2 = "): h = int(line.replace("Dim_2 = ",""))
                    from numpy import memmap,uint16,int32
                    self = memmap(filename,uint16,'r',headersize,(w,h),'F')
                    format = "EDF"
                else:
                    from PIL import Image
                    from numpy import uint8,uint16,uint32,float32
                    PIL_image = Image.open(filename)
                    mode = PIL_image.mode
                    ##PIL_image = PIL_image.convert("I")
                    if mode == "1": self = numpy.array(PIL_image,bool).T
                    elif mode == "I;8": self = numpy.array(PIL_image,uint8).T
                    elif mode == "I;16": self = numpy.array(PIL_image,uint16).T
                    elif mode == "I;32": self = numpy.array(PIL_image,uint32).T
                    elif mode == "F;32": self = numpy.array(PIL_image,float32).T
                    else:
                        warn("Unknown data type %s" % mode)
                    format = PIL_image.format
                    info = PIL_image.info
                    if "dpi" in info: pixelsize = 25.4/info["dpi"][0] # convert from DPI to mm
        elif array is not None: self = array
        else: self = zeros(shape,dtype)

        self = self.view(subclass)
        self.filename = filename
        self.format = format
        self.info = info
        self.pixelsize = pixelsize
        return self

    def __array_finalize__(self,x):
        """Called after an oject has been copied.
        Passes non-array attributes from the original to the new 
        object."""
        from numpy import nan
        self.filename = getattr(x,"filename","")
        self.format = getattr(x,"format","")
        self.info = getattr(x,"info",{})
        self.pixelsize = getattr(x,"pixelsize",nan)

    def get_width(self): return self.shape[0]
    width = property(get_width)

    def get_height(self): return self.shape[1]
    height = property(get_height)
 
    def save(self,filename=None,format=""):
        from numpy import array,uint16,uint32,uint8,rint,clip,nan_to_num,nanmax,isnan
        from PIL import Image
        from os.path import splitext,dirname,exists
        from os import makedirs
        if filename != None: self.filename = filename
        dir = dirname(self.filename)
        if dir:
            try: makedirs(dir)
            except OSError: pass
        if format == "": format = self.format
        format = format.upper()
        if format == "":
            format = splitext(self.filename)[-1].strip(".").upper()
            if format == "TIF": format = "TIFF"
            if format == "": format = self.format
        if format in ("TIFF","TIF"):
            if nanmax(self) > 255:
                data_16bit = array(clip(nan_to_num(rint(self)),0,65535),uint16)
                PIL_image = Image.fromarray(data_16bit.T,"I;16")
            elif nanmax(self) > 1:
                data_8bit = array(clip(nan_to_num(rint(self)),0,255),uint8)
                PIL_image = Image.fromarray(data_8bit.T,"L")
            else:
                # When converting 8-bit to 1-bit, the threshold is 128.
                data_8bit = array(clip(nan_to_num(rint(self)),0,1)*255,uint8)
                PIL_image = Image.fromarray(data_8bit.T,"L").convert("1")
            if not isnan(self.pixelsize):
                dpi = 25.4/self.pixelsize
                PIL_image.info["dpi"] = (dpi,dpi)
            # PIL only generates uncompressed TIFF image. There are no options.
            PIL_image.save(self.filename,format)
        elif format in ("MCCD","RX","RAYONIX"):
            # Rayonix images have a 4096-byte TIFF-compatible header,
            # with a custom non-standard tag containing diffractometer
            # information (phi angle, oscillation range, detector distance...).
            # The program "ADXV" reads only impages with Rayonix header,
            # not plain TIFF images.
            from rayonix_image_header import header # for size 1920x1920
            # Update header for current image size:
            # offset   18: width (4-byte little-endian integer)
            # offset   30: height (4-byte integer)
            # offset  102: rows per strip (=height) (4-byte integer)
            # offset 1104: width (4-byte integer)
            # offset 1108: height (4-byte integer)
            # offset 1116: strip byte count (4-byte integer)
            w,h = self.shape
            from struct import pack
            width,height = pack("<I",w),pack("<I",h)
            rows_per_strip = height
            strip_byte_count = pack("<I",w*2)
            # Convert pixel size from mm to nm.
            pixelsize_nm = toint(rint(self.pixelsize*1e-3/1e-9)) 
            ##if DEBUG: debug("pixelsize [nm] = %r" % pixelsize_nm)
            pixelsize = pack("<I",pixelsize_nm) 
            ##if DEBUG: debug("pixelsize [nm] = %r" % pixelsize)
            from time import time
            t = time()
            from datetime import datetime
            timestamp = datetime.fromtimestamp(t).strftime("%m%d%H%M%Y.%S %f")\
                .replace(" ","\0").ljust(32,"\0")
            acquire_timestamp = header_timestamp = save_timestamp = timestamp
            header = \
                header[   0:  18]+width+\
                header[  22:  30]+height+\
                header[  34: 102]+rows_per_strip+\
                header[ 106:1104]+width+height+\
                header[1112:1116]+strip_byte_count+\
                header[1120:1796]+pixelsize+\
                header[1800:2048+320]+acquire_timestamp+\
                header_timestamp+\
                save_timestamp+\
                header[2048+416:]
            # Convert image to 16-bit depth
            data_16bit = array(clip(nan_to_num(rint(self)),0,65535),uint16)
            image_data = header + data_16bit.tostring()
            file(self.filename,"wb").write(image_data)
        else: # e.g. PNG file format
            if nanmax(self) > 255:
                # PIL's PNG driver does not support mode I;16 but I (32-bit)
                data_32bit = array(clip(nan_to_num(rint(self)),0,2**32-1),uint32)
                PIL_image = Image.fromarray(data_32bit.T,"I")
            elif nanmax(self) > 1:
                data_8bit = array(clip(nan_to_num(rint(self)),0,255),uint8)
                PIL_image = Image.fromarray(data_8bit.T,"L")
            else:
                # When converting 8-bit to 1-bit, the theshold is 128.
                data_8bit = array(clip(nan_to_num(rint(self)),0,1)*255,uint8)
                PIL_image = Image.fromarray(data_8bit.T,"L").convert("1")
            # Optimize = True: the PNG output driver will try dfferent
            # output filters to achive the optimal compression.
            PIL_image.save(self.filename,format,optimize=True)
        self.format = format
    write = save

def toint(x):
    """Convert x to an integer value without throwing an expection"""
    try: return int(x)
    except: return 0

if __name__ == "__main__": # for testing
    from numpy import uint16
    from marccd_image import timestamp_mccd
    from time_string import date_time
    ##import logging; logging.basicConfig(level=logging.DEBUG)
    filename = "/tmp/test.rx"
    size = 1920; pixelsize = 0.08
    self = numimage((size,size),dtype=uint16,pixelsize=pixelsize)
    print('self.save(filename)')
    print('self = numimage(filename)')
    print('date_time(timestamp_mccd(filename))')
    
