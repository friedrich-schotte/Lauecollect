"""
Optical Scattering client wrapper

Authors: Valentyn Stadnytskyi
Date created: 26 Feb 2018 - original optical freeze detection agent
Date last modified: March 2 2019

Utilizes center 50x50 pixels to measure mean value within
"""
__version__ = "1.0" # write a comment


from CAServer import casput,casdel, casget
from CA import caget
from datetime import datetime
from thread import start_new_thread
from pdb import pm
import os
from time import sleep,time
from persistent_property import persistent_property
from numpy import nan
from logging import debug,info,warn,error
import traceback

import matplotlib.pyplot as plt

class Optical_Scattering(object):

    prefix = persistent_property('prefix','NIH:OPTICAL_SCATTERING')

    def __init__(self):
        pass

    @property
    def mean(self):
        from CA import caget
        value = caget(self.prefix+'.MEAN')
        return value

    @property
    def stdev(self):
        from CA import caget
        value = caget(self.prefix+'.STDEV')
        return value

    def get_region_size_x(self):
        from CA import caget
        value = caget(self.prefix+'.region_size_x')
        return value
    def set_region_size_x(self,value):
        from CA import caput
        caput(self.prefix+'.region_size_x',int(value))
    region_size_x = property(get_region_size_x,set_region_size_x)

    def get_region_size_y(self):
        from CA import caget
        value = caget(self.prefix+'.region_size_y')
        return value
    def set_region_size_y(self,value):
        from CA import caput
        caput(self.prefix+'.region_size_y',int(value))
    region_size_y = property(get_region_size_y,set_region_size_y)

    @property
    def get_region_size_xy(self):
        value = (self.region_size_x,self.region_size_y)
        return value


    def get_region_offset_x(self):
        from CA import caget
        value = caget(self.prefix+'.region_offset_x')
        return value
    def set_region_offset_x(self,value):
        from CA import caput
        caput(self.prefix+'.region_offset_x',int(value))
    region_offset_x = property(get_region_offset_x,set_region_offset_x)

    def get_region_offset_y(self):
        from CA import caget
        value = caget(self.prefix+'.region_offset_y')
        return value
    def set_region_offset_y(self,value):
        from CA import caput
        caput(self.prefix+'.region_offset_y',int(value))
    region_offset_y = property(get_region_offset_y,set_region_offset_y)
    @property
    def region_offset_xy(self):
        value = (self.region_offset_x,self.region_offset_y)
        return value

    @property
    def list_all_pvs(self):
        from CA import caget
        value = caget(self.prefix+'.LIST_ALL_PVS')
        return value

    def shutdown_server(self):
        from CA import caput
        caput(self.prefix+'.KILL','shutdown')


    def is_boolean(self,value):
        import types
        return type(value) == types.BooleanType

optical_scattering = Optical_Scattering()







if __name__ == "__main__":
    import logging
    from tempfile import gettempdir

    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        filename=gettempdir()+"/scattering_optical.log",
    )
    self = optical_scattering # for testing
    print('optical_scattering.mean')
    print('optical_scattering.stdev')
