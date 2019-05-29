"""
Python interface to EPICS-controlled motors.
Author: Friedrich Schotte
Date created: 2007-11-07
Date last modified: 2019-05-28
"""

from CA import Record,caget,caput
from time import time,sleep
from logging import debug,info,warn,error

__version__ = "3.1.6" # no debug messages

nan = 1e1000/1e1000 # generates Not A Number
def isnan(x): return x!=x # checks for Not A Number

class EPICS_motor(Record):
  """EPICS-controlled motor
  Using the following process variables:
  VAL - nominal position
  RBV - read back value
  DRBV - dial read back value
  HLM - high limit
  LLM - low limit
  DESC - description
  EGU - unit
  DMOV - 0 if currently moving, 1 if done
  STOP - set to 1 momentarily to stop ?
  VELO - speed in mm/s
  CNEN - enabled
  DIR - user to dial sign
  OFF - user to dial offset
  HLS - at high limit switch
  LLS = at low limit switch
  """
  def __init__(self,prefix,name=None,command="VAL",readback="RBV",
    readback_slop = 0.001,timeout=20.0,min_step=0):
    """prefix = EPICS motor record
    If is assumed that command value process varialbe is named 'VAL'
    and the readback process variable 'RBV', unless specified otherwise
    by the optional 'command' and 'readback' keywords.

    readback slop: A motion is considered finished when the difference
    between the command value and the readback value is smaller than this
    amount.

    timeout: The motion is considered finished when the readback value has
    not changed within the readback slop for this amount of time.

    min_step: only if the new position deviates from the current position by
    at least this ammount will a command to move to motor be sent to the
    IOC.
    """
    Record.__init__(self,prefix)

    if name is not None: self.__db_name__ = name

    self.__command__ = command
    self.__readback__ = readback

    self.__readback_slop__ = readback_slop
    self.__timeout__ = timeout
    self.__min_step__ = min_step

    self.__last_command_value__ = nan
    self.__new_command_value__ = nan
    self.__motion_started__ = 0
    self.__move_done__ = True
    self.__last_moving__ = 0

  def get_prefix(self):
    from DB import dbget
    dbname = getattr(self,"__db_name__","")
    try: prefix = eval(dbget("EPICS_motor/"+dbname+".prefix"))
    except: prefix = ""
    if not prefix: prefix = getattr(self,"__my_prefix__","")
    return prefix
  def set_prefix(self,value):
    ##debug("EPICS_motor.prefix = %r" % value)
    from DB import dbput
    dbname = getattr(self,"__db_name__","")
    if dbname:
      ##debug("EPICS_motor/"+dbname+".prefix: "+repr(value))
      dbput("EPICS_motor/"+dbname+".prefix" , repr(value))
    else:
      ##debug("EPCIS_motor.__my_prefix__ = %r" % value)
      self.__my_prefix__ = value
  prefix = property(get_prefix,set_prefix)
  __prefix__ = prefix

  def get_command_PV(self):
    """Process variable value for the motor target position.
    Ususually the value of the VAL process variable, but may me overriden."""
    if not ":" in self.__command__: return getattr(self,self.__command__)
    else: return caget(self.__command__)
  def set_command_PV(self,value):
    if not ":" in self.__command__:
      ##debug("setattr(%r,%r)" % (self.__command__,value))
      setattr(self,self.__command__,value)
    else:
      ##debug("caput(%r,%r)" % (self.__command__,value))
      caput(self.__command__,value)
  command_PV = property(get_command_PV,set_command_PV)

  def get_readback_PV(self):
    """Process variable value for the actual position as measured.
    Ususually the value of the RBV process variable, but may me overriden."""
    if not ":" in self.__readback__: return getattr(self,self.__readback__)
    else: return caget(self.__readback__)
  def set_readback_PV(self,value):
    if not ":" in self.__readback__: setattr(self,self.__readback__,value)
    else: caput(self.__readback__,value)
  readback_PV = property(get_readback_PV,set_readback_PV)

  def get_command_value(self):
    # Found that the Aerotech "Ensemble" EPICS driver is slow updating
    # the command value. Make that not an old command value is returned.
    # Wait 0.05 s from the command value to update. - F. Schotte, 7 Mar 2013
    if time() - self.__motion_started__ < 0.05 \
      and not isnan(self.__new_command_value__):
      value = self.__new_command_value__
    else: value = self.command_PV
    return asfloat(value)
  def set_command_value(self,value):
    ##debug("value = %r" % value)
    try: value = float(value)
    except: return
    if isnan(value): return
    if abs(value - self.value) < self.__min_step__: return
    # Found that the Aerotech "Ensemble" EPICS driver is slow updating
    # the command value.
    # Cache the new command value for a short period.
    self.__new_command_value__ = value
    # Record the time the last motion was initiated.
    self.__motion_started__ = time()
    # Enable the motor (in case it was disabled)
    #self.CNEN = 1
    # Initiate the motion by setting a new commond value.
    ##debug("command_PV = %r" % value)
    self.command_PV = value
    self.__last_command_value__ = value
    self.__move_done__ = False
  command_value = property(get_command_value,set_command_value,
    doc="""Position of motor (user value). If read, readback position;
      if assigned, starts motion to new position (but does not wait for the
      motion to complete)""")

  def set_value(self,value): self.command_value = value
  def get_value(self): return asfloat(self.readback_PV)
  value = property(get_value,set_value,
    doc="""Position of motor (user value). If read, readback position;
      if assigned, starts motion to new position (but does not wait for the
      motion to complete)""")

  def get_command_dial(self):
    """Target position as unscaled dial value."""
    return asfloat(self.DVAL)
  def set_command_dial(self,value):
    value = asfloat(value)
    if isnan(value): return
    # Record the time the last motion was initiated.
    self.__motion_started__ = time()
    self.DVAL = value
  command_dial = property(get_command_dial,set_command_dial)

  def get_dial(self):
    return asfloat(self.DRBV)
  dial = property(get_dial,set_command_dial,
    doc="""Position of motor as reported by the encoder (dial value).
    If read, readback position; if assigned, starts motion to new position""")

  def get_min(self):
    """Low limit in user units"""
    return asfloat(self.LLM)
  def set_min(self,value): self.LLM = value
  min = property(get_min,set_min)
  low_limit = min

  def get_max(self):
    """Positive and of travel in user units"""
    return asfloat(self.HLM)
  def set_max(self,value): self.HLM = value
  max = property(get_max,set_max)
  high_limit = max

  def get_at_low_limit(self):
    """Is motor at end switch?"""
    return asbool(self.LLS)
  at_low_limit = property(get_at_low_limit)

  def get_at_high_limit(self):
    """Is motor at end switch?"""
    return asbool(self.HLS)
  at_high_limit = property(get_at_high_limit)

  def get_name(self):
    """Description"""
    name = self.DESC
    if name == None: name = ""
    return name
  def set_name(self,value): self.DESC = value
  name = property(get_name,set_name)

  def get_unit(self):
    """mm,deg or mrad"""
    unit = self.EGU
    if unit == None: unit = ""
    unit = unit.strip("()") # Somtimes the unit is included in parenthses.
    return unit
  def set_unit(self,value): self.EGU = value
  unit = property(get_unit,set_unit)

  def get_moving(self):
    """True if currently moving, False if done. Stops motor is assigned the
    value False"""
    # EPICS provides the DMOV flag in the motor record to tell when
    # the motion has finished. However I found this to be unreliable
    # because there can be a variable delay between the time
    # the VAL variable is written, and the DMOV flag goes from the value 1
    # to 0. (0 if currently moving, 1 if done).
    # Does DMOV flag indicate that motor is moving?
    DMOV = self.DMOV
    if DMOV == 0: self.__last_moving__ = time()
    if DMOV == 0: return not DMOV
    if self.__last_moving__ > self.__motion_started__: return not DMOV
    # Is motor at target position?
    if self.__move_done__: return False;
    if isnan(self.__last_command_value__): return False
    if abs(self.value - self.__last_command_value__) < self.__readback_slop__:
      self.__move_done__ = True; return False
    # If the DMOV flag indicates that the motor is not moving and the
    # motor is still not at the target position, give up after the
    # timeout (default: 20s) expires.
    if time()-self.__motion_started__ > self.__timeout__:
      self.log("move timed out after %g s "\
        "(target: %g %s, readback value: %g %s, readback slop: %g %s)" %
        (self.__timeout__,self.__last_command_value__,self.unit,self.value,self.unit,
         self.__readback_slop__,self.unit))
      self.__move_done__ = True; return False
    else: return True
  def set_moving(self,value):
    """Stops the motor if value == False"""
    if not value: self.stop()
  moving = property(get_moving,set_moving)

  def get_speed(self):
    """Velocity in mm/s or deg/s"""
    return asfloat(self.VELO)
  def set_speed(self,value):
    try: value = float(value)
    except: return
    self.VELO = value
  speed = property(get_speed,set_speed)

  def get_acceleration(self):
    """Accelation in mm/s^2 or deg/s^2"""
    T = asfloat(self.ACCL) # acceleration time
    acceleration = self.speed/T
    return acceleration
  def set_acceleration(self,acceleration):
    try: value = float(value)
    except: return
    T = self.speed/acceleration
    self.ACCL = T
  acceleration = property(get_acceleration,set_acceleration)

  def get_enabled(self):
    value = self.CNEN
    if value == None: value = nan
    return value
  def set_enabled(self,value):
    self.CNEN = value
  enabled = property(get_enabled,set_enabled)

  def get_homing(self):
    """Current executing a home calibaion? If set execute the home
    calibration."""
    if self.HOMR: value = True
    elif self.HOMF: value = True
    else: value = False
    return value
  def set_homing(self,value):
    self.HOMF = value
  homing = property(get_homing,set_homing)

  def get_homed(self):
    """Current executing a home calibaion? If set execute the home
    calibration."""
    status_bits = self.MSTA
    if status_bits == None: homed = nan
    else: homed = bool((status_bits>>15)&1)
    return homed
  def set_homed(self,value): pass
  homed = property(get_homed,set_homed)

  def get_sign(self):
    """Dial to user direction: +1 or -1"""
    value = self.DIR
    if value == 0: return 1
    elif value == 1: return -1
    else: return nan
  def set_sign(self,sign):
    self.DIR = 0 if sign>=0 else 1
  sign = property(get_sign,set_sign)

  def get_offset(self):
    """Dial to user direction: +1 or -1"""
    return asfloat(self.OFF)
  def set_offset(self,value):
    self.OFF = value
  offset = property(get_offset,set_offset)

  def define_value(self,value):
    "modifies the user to dial offset such that the new user value is 'value'"
    self.offset = value - self.dial * self.sign
    # user = dial*sign + offset; offset = user - dial*sign

  def get_readback_slop(self):
    """Maxmimum allowed difference between readback value and command value
    for the motion to be considered complete."""
    return self.__readback_slop__
  def set_readback_slop(self,value):
    self.__readback_slop__ = value
  readback_slop = property(get_readback_slop,set_readback_slop)

  def wait(self):
    """If the motor is moving, returns control after current move move is
    complete."""
    while self.moving: sleep(0.01)

  def stop(self):
    self.STOP = 1

  def __repr__(self):
    return 'EPICS_motor("'+self.__prefix__+'")'

  def log(self,message):
    """Append a message to the log file (/tmp/EPICS_motor.log)"""
    from tempfile import gettempdir
    from time import strftime
    from sys import stderr
    timestamp = strftime("%d-%b-%y %H:%M:%S")
    if len(message) == 0 or message[-1] != "\n": message += "\n"
    name = self.name
    if not name: name = repr(self)
    message = timestamp+" "+name+": "+message
    stderr.write(message)
    logfile = gettempdir()+"/EPICS_motor.log"
    file(logfile,"a").write(message)

motor = EPICS_motor

def asfloat(x):
  """Convert x to a floating point number without rasing an exception.
  Return nan instead if conversion fails"""
  try: return float(x)
  except: return nan

def asbool(x):
  """Convert x to a boolean without rasing an exception.
  Return False instead if conversion fails"""
  try: return bool(int(x))
  except: return False

if __name__ == "__main__": # for testing
  from pdb import pm # for debugging
  import logging
  logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")

  shg = motor("14IDB:m25",name="shg")
  MirrorV = motor("14IDA:DAC1_4",readback="VAL",name="MirrorV")
  print('shg.prefix = %r' % shg.prefix)
  print('shg.command_value')
  print('shg.value')
  print('MirrorV.prefix = %r' % MirrorV.prefix)
  print('MirrorV.command_value')
  print('MirrorV.value')
