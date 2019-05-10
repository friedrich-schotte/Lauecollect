"""
Python interface to EPICS-controlled motors.
Friedrich Schotte, APS, 7 Nov 2007 - 18 Apr 2010
"""

__version__ = "1.1"

from CA import caput,caget
from time import time,sleep

NaN = 1e1000/1e1000 # generates Not A Number
def isnan(x): return x!=x # checks for Not A Number

class undulator(object): 
  """Reads and sets the gap of an EPICS control insertion device.
  The undulator drive is in principle a stepper motor, but the EPICS
  record is incompatible with the EPICS motor record.
  Using the following process variables:
  Gap.VAL - actual position read from encoder
  GetSet.VAL - nominal (command) position
  Start.VAL - set to 1 to start a move
  Stop.VAL - set to 1 to stop the motor
  Busy.VAL - 0 = not moving, 1 = moving
  """
  def __init__(self,rec_name):
    """rec_name = prefixe of EPICS record,
    for example "ID14ds", "ID14us".
    """
    object.__init__(self)
    self.rec_name = rec_name

  def get_value(self): return self.readback_value
  def set_value(self,value): self.command_value = value
  value = property(fget=get_value,fset=set_value,
    doc="""Position of motor. If read, readback position;
      if assigned, starts motion to new position (returns before motion is
      done)""")

  def get_command_value(self):
    value = caget(self.rec_name+":GapSet.VAL")
    if value == None: value = NaN
    return value
  def set_command_value(self,value):
    if isnan(value): return
    caput(self.rec_name+":GapSet.VAL",value)
    self.start()
  command_value = property(get_command_value,set_command_value,
    doc="""Position of motor (user value). If read, readback position;
      if assigned, starts motion to new position (returns before motion is
      done)""")

  def get_readback_value(self):
    value = caget(self.rec_name+":Gap.VAL")
    if value == None: value = NaN
    return value
  readback_value = property(get_readback_value,
    doc="""Motor's encoder value""")

  def get_name(self):
    name = caget(self.rec_name+":Device")
    if name == None: name = ""
    return name
  def set_name(self,value): caput(self.rec_name+":Device",value)
  name = property(fset=set_name,fget=get_name,doc="description")

  unit = "mm"

  def get_moving(self):
    return (caget(self.rec_name+":Busy.VAL") != 0)
  def set_moving(self,value):
    "Stops the motor if value == False"
    if value: self.start()
    else: self.stop()
  moving = property(fget=get_moving,fset=set_moving,
    doc="True if currently moving, False if done. "+
      "Stops motor is assigned the value False")

  def start(self):
    "Makes the motor move ot the current command value."
    caput(self.rec_name+":Start.VAL",1)

  def stop(self):
    "Aborts the current move."
    caput(self.rec_name+":Stop.VAL",1)

  def __repr__(self):
    return 'undulator("'+self.rec_name+'")'

if __name__ == "__main__": # for testing
  U23 = undulator("ID14ds")
  U27 = undulator("ID14us")
