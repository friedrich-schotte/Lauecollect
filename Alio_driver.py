#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 27 08:43:11 2019

Setup:
Downlaod https://github.com/dls-controls/dls-pmac-lib/tree/python3
-> ~/Downloads/dls-pmac-lib-python3.zip
$ unzip dls-pmac-lib-python3.zip
$ cd dls-pmac-lib-python3
$ pip install .
@author: henning
"""
# Figure out a way to use names for the different modes


import pkg_resources
pkg_resources.require("dls-pmaclib")
import dls_pmaclib.dls_pmacremote as dls

parameters=[('phi_step_size','P255')]

class alio(object):
    def __init__(self,name="Alio"):
        self.name = name
        self.alio = dls.PmacEthernetInterface()
        self.alio.setConnectionParams('164.54.161.40', 1025)
        self.alio.connect()

    @property   
    def mode(self):
        """Coordinated motions. 0 to disable. 1 to enable XYZ. 2 for phi. 3 for X.
        4 for Y. 5 for Z. 6 for grid scanning. P250"""
        return self.alio.sendCommand("P250")[0].rstrip('\r\x06')
    
    @mode.setter
    def mode(self,value):
        cmd="P250=%d" % value
        self.alio.sendCommand(cmd,shouldWait=True)
    
    @property
    def speed(self):
        """Speed in mm/s. P251"""
        return self.alio.sendCommand("P251")[0].rstrip('\r\x06')

    @speed.setter
    def speed(self,value):
        cmd="P251=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)
    
    @property
    def accel(self):
        """Acceleration in msec. P252"""
        return self.alio.sendCommand("P252")[0].rstrip('\r\x06')

    @accel.setter
    def accel(self,value):
        cmd="P252=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)
    #accel = property(get_accel,set_accel)

    @property
    def phi_step_size(self):
        """Phi step size in degrees. P255"""
        return self.alio.sendCommand("P255")[0].rstrip('\r\x06')

    @phi_step_size.setter
    def phi_step_size(self,value):
        cmd="P255=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def x_step_size(self):
        """X step size in mm. P256"""
        return self.alio.sendCommand("P256")[0].rstrip('\r\x06')

    @x_step_size.setter
    def x_step_size(self,value):
        cmd="P256=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def y_step_size(self):
        """Y step size in mm. P257"""
        return self.alio.sendCommand("P257")[0].rstrip('\r\x06')

    @y_step_size.setter
    def y_step_size(self,value):
        cmd="P257=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def z_step_size(self):
        """Z step size in mm. P258"""
        return self.alio.sendCommand("P258")[0].rstrip('\r\x06')

    @z_step_size.setter
    def z_step_size(self,value):
        cmd="P258=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def steps_expected(self):
        """Number of steps/counts to watch for. P259"""
        return self.alio.sendCommand("P259")[0].rstrip('\r\x06')

    @steps_expected.setter
    def steps_expected(self,value):
        cmd="P259=%i" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def phi_starting(self):
        """Phi starting position. P260"""
        return self.alio.sendCommand("P260")[0].rstrip('\r\x06')

    @phi_starting.setter
    def phi_starting(self,value):
        cmd="P260=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def x_starting(self):
        """X starting position. P261"""
        return self.alio.sendCommand("P261")[0].rstrip('\r\x06')

    @x_starting.setter
    def x_starting(self,value):
        cmd="P261=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def y_starting(self):
        """Y starting position. P262"""
        return self.alio.sendCommand("P262")[0].rstrip('\r\x06')

    @y_starting.setter
    def y_starting(self,value):
        cmd="P262=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def z_starting(self):
        """Z starting position. P263"""
        return self.alio.sendCommand("P263")[0].rstrip('\r\x06')

    @z_starting.setter
    def z_starting(self,value):
        cmd="P263=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def trigger_delay(self):
        """Delay in msec to wait after it receives a trigger. P266"""
        return self.alio.sendCommand("P266")[0].rstrip('\r\x06')

    @trigger_delay.setter
    def trigger_delay(self,value):
        cmd="P266=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)
       
    @property
    def row_number(self):
        """Row number. P267"""
        return self.alio.sendCommand("P267")[0].rstrip('\r\x06')

    @row_number.setter
    def row_number(self,value):
        cmd="P267=%i" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def xstep_size_in_row(self):
        """Step size in X direction. P270"""
        return self.alio.sendCommand("P270")[0].rstrip('\r\x06')

    @xstep_size_in_row.setter
    def xstep_size_in_row(self,value):
        cmd="P270=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def ystep_size_in_row(self):
        """Step size in Y direction. P271"""
        return self.alio.sendCommand("P271")[0].rstrip('\r\x06')

    @ystep_size_in_row.setter
    def ystep_size_in_row(self,value):
        cmd="P271=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def zstep_size_in_row(self):
        """Step size in Z direction. P272"""
        return self.alio.sendCommand("P272")[0].rstrip('\r\x06')

    @zstep_size_in_row.setter
    def zstep_size_in_row(self,value):
        cmd="P272=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def xshift_per_row(self):
        """Shift in X direction per row. P273"""
        return self.alio.sendCommand("P273")[0].rstrip('\r\x06')

    @xshift_per_row.setter
    def xshift_per_row(self,value):
        cmd="P273=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def yshift_per_row(self):
        """Shift in Y direction per row. P274"""
        return self.alio.sendCommand("P274")[0].rstrip('\r\x06')

    @yshift_per_row.setter
    def yshift_per_row(self,value):
        cmd="P274=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def zshift_per_row(self):
        """Shift in Z direction per row. P275"""
        return self.alio.sendCommand("P275")[0].rstrip('\r\x06')

    @zshift_per_row.setter
    def zshift_per_row(self,value):
        cmd="P275=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def translation_dir(self):
        """Translation direction. P276"""
        return self.alio.sendCommand("P276")[0].rstrip('\r\x06')

    @translation_dir.setter
    def translation_dir(self,value):
        cmd="P276=%f" % value
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def z(self):
        """Z motor position in mm. Have to set jog speed (I122) and
            job acceleration time (I120) before move."""
        cts=self.alio.sendCommand("M162")[0].rstrip('\r\x06')
        return float(cts)/(6400 * 96 *32) # Has to be converted from counts to mm

    @z.setter
    def z(self,value):
        cts=value*6400
        cmd="I122=64I120=100#1 J=%i" % cts
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def phi(self):
        """phi motor position in mm. Have to set jog speed (I222) and
            job acceleration time (I220) before move."""
        cts=self.alio.sendCommand("M262")[0].rstrip('\r\x06')
        return float(cts)/(5597.8667 * 96 *32)-120.0 # Has to be converted from counts to mm

    @phi.setter
    def phi(self,value):
        cts=(value+120.0)*5597.8667
        cmd="I222=64I220=100#2 J=%i" % cts
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def x(self):
        """X motor position in mm. Have to set jog speed (I322) and
            job acceleration time (I320) before move."""
        cts=self.alio.sendCommand("M362")[0].rstrip('\r\x06')
        return -float(cts)/(6400 * 96 *32) # Has to be converted from counts to mm

    @x.setter
    def x(self,value):
        cts=-value*6400
        cmd="I322=64I320=100#3 J=%i" % cts
        self.alio.sendCommand(cmd,shouldWait=True)

    @property
    def y(self):
        """Y motor position in mm. Have to set jog speed (I422) and
            job acceleration time (I420) before move."""
        cts=self.alio.sendCommand("M462")[0].rstrip('\r\x06')
        return float(cts)/(6400 * 96 *32) # Has to be converted from counts to mm

    @y.setter
    def y(self,value):
        cts=value*6400
        cmd="I422=64I420=100#4 J=%i" % cts
        self.alio.sendCommand(cmd,shouldWait=True)
    
    def in_position(self):
        m1=int(self.alio.sendCommand("M144")[0].rstrip('\r\x06'))
        m2=int(self.alio.sendCommand("M244")[0].rstrip('\r\x06'))
        m3=int(self.alio.sendCommand("M344")[0].rstrip('\r\x06'))
        m4=int(self.alio.sendCommand("M444")[0].rstrip('\r\x06'))
        #print(m1,m2,m3,m4)
        if m1==0 or m2==0 or m3==0 or m4==0:
            return 0
        else:
            return 1

alio=alio()        
if __name__ == "__main__":
    print("Testing!")
    #alio.set_speed(2)
    #print alio.speed
