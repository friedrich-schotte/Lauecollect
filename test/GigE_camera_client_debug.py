#!/usr/bin/env python
"""
Prosilica GigE CCD cameras.
Author: Friedrich Schotte
Date created: 04/13/2017
Date last modified: 02/07/2018
"""
__version__ = "1.5" # camera_ip_address
from logging import debug,info,warn,error

class Camera(object):
    from persistent_property import persistent_property
    ip_address = persistent_property("GigE_camera.{name}.ip_address",
        "pico20.niddk.nih.gov:2000")
    orientation =  persistent_property("GigE_camera.{name}.orientation",0)
    mirror =  persistent_property("GigE_camera.{name}.mirror",False)

    def __init__(self,name):
        self.name = name

    def attr(name,default_value=0):
        def get(self):
            dtype = type(default_value)
            try: return dtype(eval(self.query(name)))
            except: return default_value
        def set(self,value):
            self.query(name+"=%r" % value,count=0)
        propery_object = property(get,set)
        return propery_object

    camera_ip_address = attr("camera.IP_addr","")
    rgb_data_size = attr("len(camera.images[-1])",0)
    acquiring = attr("camera.acquiring",False)
    state = attr("camera.state","Server offline")
    width = attr("camera.width",1360)
    height = attr("camera.height",1024)
    frame_count = attr("camera.frame_count",0)
    frame_counts = attr("camera.frame_counts",0)
    timestamp = attr("camera.timestamp",0.0)
    has_image = attr("len(camera.images)>0",False)
    exposure_time = attr("camera.exposure_time",0.0)
    auto_exposure = attr("camera.auto_exposure",False)
    use_multicast = attr("camera.use_multicast",False)
    external_trigger = attr("camera.external_trigger",False)
    pixel_formats = attr("camera.pixel_formats",[])
    pixel_format = attr("camera.pixel_format","")
    gain = attr("camera.gain",0)
    bin_factor = attr("camera.bin_factor",1)
    stream_bytes_per_second = attr("camera.stream_bytes_per_second",0.0)

    @property
    def rgb_data(self):
        return self.query("camera.rgb_data",count=self.rgb_data_size)

    @property
    def RGB_array(self):
        """Last read image as 3D nmupy array. Dimensions: 3xWxH
        datatype: uint8
        Usage R,G,B = camera.rgb_array"""
        from numpy import frombuffer,uint8,zeros
        w,h = self.width,self.height
        rgb_data = self.rgb_data
        size = 3*w*h
        if len(rgb_data) < size:
            warn("RGB_array %dx%d: padding from %d to %d bytes" % (w,h,len(rgb_data),size))
            rgb_data += "\0"*(size-len(rgb_data))
        if len(rgb_data) > size:
            warn("RGB_array %dx%d: truncating from %d to %d bytes" % (w,h,len(rgb_data),size))
            rgb_data = rgb_data[0:size]
        array = frombuffer(rgb_data,uint8).reshape(h,w,3).T
        return array

    @property
    def wxImage(self):
        """image in wx.Bitmap format"""
        import wx
        image = self.RGB_array
        d,w,h = image.shape
        wximage = wx.EmptyImage(w,h)
        data = image.T.tostring()
        wximage.Data = data
        return wximage

    @property
    def wxBitmap(self):
        """image in wx.Bitmap format"""
        import wx
        image = self.RGB_array
        d,w,h = image.shape
        wximage = wx.EmptyImage(w,h)
        data = image.T.tostring()
        wximage.Data = data
        bitmap = wx.BitmapFromImage(wximage)
        return bitmap

    def acquire_sequence(self,frame_counts=None,filenames=[]):
        """filenames: list of pathnames"""
        if frame_counts is None:
            start = self.frame_count+2
            frame_counts = range(start,start+len(filenames))
        self.query("camera.acquire_sequence(%r,%r)" % (frame_counts,filenames),count=0)

    def query(self,command,terminator="\n",count=None):
        """Evaluate a command in the camera server and return the result.
        """
        from tcp_client import query
        reply = query(self.ip_address,command,terminator,count)
        return reply

    def save_image(self,filename):
        RGB_array = self.transform_image(self.RGB_array,self.orientation,self.mirror)
        from PIL import Image
        image = Image.new('RGB',(self.width,self.height))
        image.frombytes(RGB_array.T.tostring())
        ##image.frombytes(self.rgb_data)
        ##image = self.rotated_image(image)
        from os import makedirs; from os.path import dirname,exists
        if not exists(dirname(filename)): makedirs(dirname(filename))
        info("Saving %r" % filename)
        image.save(filename)

    def transform_image(self,image,angle,mirror):
        """Transform from raw to displayed to displayed image.
        image: 3D numpy array with dimensions 3 x width x height
        angle: in units of deg, positive = counterclockwise, must be a multiple
        of 90 deg
        Return value: rotated version of the input image"""
        from numpy import rint
        angle = rint((angle % 360)/90.)*90
        if mirror: image = image[:,::-1,:] # flip horizonally
        if angle == 90:  image = image.transpose(0,2,1)[:,:,::-1]
        if angle == 180: image = image[:,::-1,::-1]
        if angle == 270: image = image.transpose(0,2,1)[:,::-1,:]
        return image

    def rotated_image(self,image):
        """image: PIL image object"""
        return image.rotate(self.orientation)
       

if __name__ == "__main__":
    camera = Camera("MicroscopeCamera")
    self = camera # for debugging

    ##camera.frame_count
    command = "frame_count"; terminator="\n";count=None
    from tcp_client import query
    ##reply = query(self.ip_address,command,terminator,count)
    
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    from time import time
    
    from tempfile import gettempdir
    dir = "//femto-data//C/Data/2017.04/Test/Test1/camera_images/"
    frame_counts = range(0,20)
    filenames = [dir+"/Test_%03d.jpg" % (i+1) for i in frame_counts]
    print('camera = Camera("WidefieldCamera")')
    print('camera = Camera("MicroscopeCamera")')
    print('camera.ip_address')
    print('camera.state')
    print('camera.camera_ip_address')
    print('camera.acquiring = True')
    
    debug('?')
