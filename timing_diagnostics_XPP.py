#! /usr/bin/env ipython 
#-nobanner
"""Henrik Lemke, 25 Nov 2013 """
__version__ = 1.0
import virtualmotor
import motor_newport

# make dummy object that holds motors
class Motors(object):
  pass
xppmotors = Motors()

#import xppmotors
#xppmotors = xppmotors.XppMotors()
# initialize newport controller
xpsL2=motor_newport.XPS("xpp-las2")
# initialize delay stage
newportL2_8=motor_newport.Motor(xpsL2,8)
# add motor object
virtualmotor.VirtualMotor(xppmotors,"las_tt_delay",newportL2_8.move_and_wait,newportL2_8.get_position,newportL2_8.wait,pvpos="XPP:USER:LAS:TT_DELAY_POS",pvoff="XPP:USER:LAS:TT_DELAY_OFF",backlash_dist=.2)

# laser stuff, delay etc.
import lasersystem
xpplaser=lasersystem.LaserSystem(system=3,beamline="xpp")

# laser delay macros
import laserdelaystage_new as laserdelaystage
xppTTdelay = laserdelaystage.DelayStage2time("ttDelay",xppmotors.las_tt_delay,direction=-1)

# make time delay motor, NB: this one does the lowgain high gain stuff if you like to use it
virtualmotor.VirtualMotor(xppmotors,"lxt",xpplaser.move_delay,xpplaser.get_delay,set=xpplaser.set_delay,tolerance=30e-15,wait=xpplaser.wait)
# motor object that moves time tool stage in seconds
virtualmotor.VirtualMotor(xppmotors,"txt",xppTTdelay.mv,xppTTdelay.wm,set=xppTTdelay.set,wait=xppTTdelay.wait)
# make the compensating motor
lxt_compensate = laserdelaystage.timeStageSeries_Compensate('lxt_ttc',xppmotors.lxt,xppmotors.txt)
virtualmotor.VirtualMotor(xppmotors,"lxt_ttc",lxt_compensate.mv,lxt_compensate.wm,wait=lxt_compensate.wait)

# that's it!

