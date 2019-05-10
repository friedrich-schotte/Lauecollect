# -*- coding: utf-8 -*-
from __future__ import with_statement
"""
This Python Module is for Programming the Hamilton PSD3 Syringe
Drive Module

Friedrich Schotte, Philip Anfinrud, Naranbaatar Dashdorj,
11 May 2008 - 14 Mar 2018 

PSD3 is jumper-configured to use the Hamilton "Protocol 1/RNO+"
command set, which is used for intruments manufactured by Hamilton
company (diluters,syringe modules,valve positioners).
In this mode device addresses are set automatically,
but the first time after power up the command "1a" needs to
be sent to assign addresses. The PSD3 as first device gets
the address "a".
The RS-232 settings are baud 9600, 7 data bits parity odd,
stop bits: 1, flow control: none. There are no specific
jumpers that configure the RS-232 settings. The settings are
implied by the jumper selecting "Protocol 1/RNO+".
(for the PSD3: dip switches 2-5 all up)
Each command needs to start with an address "a" and terminated
with a <CR>. The command is echoed back, including the carriage
return. If the command does not generate a response, the
reply is only <ACK><CR> (ACK = acknowledge, ASCII 6).
If the command generates a response, the response is preceeded
by <ACK> and terminates with <CR>.
In case of an error they replay is <NAK> (negative acknowledge,
ASCII 21), rather than <ACK>.

The stoke of the Syringe pump is 30 mm which is divided into 1000 steps
with a 1.25 ml syringe, the step size is 1.25 μL

Dead volume of the 8-port valve is 27.4 μL.

Setup:
- Install Pyserial package
  http://pypi.python.org/pypi/pyserial
- Install driver for USB-Serial cable, model Prolific PL2303
  Mac OS X Driver:
  http://www.prolific.com.tw/US/ShowProduct.aspx?p_id=229&pcid=41
  In Console, All Messages, the message "PL-2303/X V1.5.1 start, Prolific"
  should be generated when the USB-serial cable is connected to the computer,
  and the file /dev/tty.usbserial created.
- Assign the communiation port name:
  syringe_pump_driver.serial_port_name = "COM4:"
- Create a Desktop shortcut, named "Syringe Pump IOC"
  Target: C:\Python27\python.exe syringe_pump.py run_server
  Start in: "Z:\All Projects\APS\Instrumentation\Software\Lauecollect"

Usage:

To determine the port being used, execute:
  syringe_pump_driver.serial_port_name
  syringe_pump2_driver.serial_port_name
To change the port to COM4, execute:
  syringe_pump_driver.serial_port_name = "COM3:"
  syringe_pump2_driver.serial_port_name = "COM4:"
send("aXR") - Initializes the PSD3
ask("aYQP") - tell the current syringe position in steps
send("aM100R") - moves syringe to abolute position 100 steps
move(In,100,10) - loads from the input port (0) 100 μL at a speed of 10 μL/s

Jumper Settings: PSD3: 1-5 all up

Cabling: NIH-Instrumentation MacBook, USB port -> 3-port USB hub
port 2 -> Prolific 2303 USB-Serial cable -> PSD3 #1 Com-In
port 3 -> Prolific 2303 USB-Serial cable -> PSD3 #2 Com-In

After power cycling the pump, need to execute the command "set_defaults" or rerun
this script.

To use as stand-alone application, run "run_server()" in the console, then
run init()

To operate both syringe pumps synchronously:
  p1.volume (returns volume of pump1)
  p2.volume (returns volume of pump2)
  pc.V (returns combined volume of two pumps)
  pc.dV (returns differential volume between two pumps)
  p1.volume = 125 (sets volume of pump1 to 125 uL)
  p1.volume += 10 (moves pump1 by +10 uL)
  
"""

from numpy import nan,isnan,ceil
import struct
from thread import allocate_lock,start_new_thread

__version__ = "5.9" # run_server, start_server, stop_server

# Calibration constants
V_syringe = 125.0 # Total capacity of the syringe in uL
syringe_stroke = 30.0 # This linear stroke in mm corresponds to the volume.

# Volume needed to bring sample into the position. 
V_center=50 # The length of the fused silica tubing with ID=325μm and
            # OD=435μm is 40 cm on both sides (~35μL)

# Volume needed to recover unexposed sample
V_unload=40

# Total volume between the sample port and the syringe (μL).
V_dead=100

# Syringe backoff volume
V_backoff=30

# Syringe Speed
# Three different speeds are used to support various operations. When loading
# liquid samples, S_slow is used. When drawing solutions into the syringe,
# S_medium is used. When emptying the syringe, S_fast is used.
S_slow=0.6 # Slow syringe plunger speed is set to 1 μL/s.
S_medium=5 # Medium syringe plunger speed is set to 5 μL/s.
S_fast=100 # Fast syringe plunger speed is set to 100 μL/s.

# Port Assignment for Syringe Pump
In = "In"    # left port labelled "In" for loading the sample
Out = "Out"  # right port  labelled "Out" for dumping the waste

# Syringe motor parameters
motor_stepsize = syringe_stroke/30000 # mm
maxsteps = syringe_stroke/motor_stepsize*1.05 # high limit of travel in motor steps
V_step = V_syringe/syringe_stroke*motor_stepsize # μL

# Procedural Interface (for backward-compatibility)

def init():
  """This runs the initialization sequence for the pump.
  It is needed after power on.
  The pump drives the plunger against the
  end stop while opening the ouput valve and sets the absolute
  position to zero."""
  syringe_pump.initialized = True
  log_command("init()")
  wait()

def init2():
  """This runs the initialization sequence for two pumps.
  It is needed after power on.
  The pump drives the plunger against the
  end stop while opening the ouput valve and sets the absolute
  position to zero."""
  syringe_pump_combined.initialized = True
  log_command("init2()")
  wait()

def reload():
  """This sequence reloads the oil for P1 and P2 : Laue oil reload"""
  P1.port = 'Out'
  P2.port = 'Out'
  while(P1.moving or P2.moving): sleep(0.1)
  P1.speed = 10
  P2.speed = 10
  P1.volume = 0
  P2.volume = 0
  while(P1.moving): sleep(0.1)
  P1.speed = 2
  P1.volume = 125
  while(P2.moving): sleep(0.1)
  P1.port = 'In'
  P2.speed = 2
  P2.volume = 131.25-125  
  while(P1.moving or P2.moving): sleep(0.1)
  
  P2.port = 'In'  

def bubble_remover():
  P1.port = 'In'
  P2.port = 'In'
  while(P1.moving or P2.moving): sleep(0.1)
  P2.speed = 1
  P1.speed = 1
  P1.volume -= 5
  sleep(3)
  P2.volume += 5
  while(P1.moving or P2.moving): sleep(0.1)
  
def flush():
  P1.port = 'Out'
  P2.port = 'Out'
  while(P1.moving or P2.moving): sleep(0.1)
  P1.speed = 10
  P2.speed = 4
  P1.volume = 0
  P2.volume = 130
  while(P1.moving or P2.moving): sleep(0.1)
  P1.port = 'In'
  P2.port = 'In'
  while(P1.moving or P2.moving): sleep(0.1)  
  PC.speed = 2
  PC.V = 130
  while(P1.moving or P2.moving): sleep(0.1)
  P1.port = 'Out'
  P2.port = 'Out'
  while(P1.moving or P2.moving): sleep(0.1)
  P1.speed = 10
  P2.speed = 2
  P1.volume = 0
  P2.volume = 131.25-125  
  while(P1.moving or P2.moving): sleep(0.1)
  P1.speed = 2
  P1.volume = 125
  while(P1.moving or P2.moving): sleep(0.1)
  P1.port = 'In'
  P2.port = 'In'
  
def inflate(s, v):
  """infalte (v: positive) or deflate tubing """
  P1.port = 'In'
  P2.port = 'In'
  while(P1.moving or P2.moving): sleep(0.1)
  PC.speed = s
  PC.dV += v
  while(P1.moving or P2.moving): sleep(0.1)
  
def flow(t,r,s,v):
  """deflate tube by starting P2 't' seconds before P1; 
      'r' is ratio of s2/s1 flow rates; s is the speed of P2;
      v is volume of P2"""
  P1.port = 'In'
  P2.port = 'In'
  while(P1.moving or P2.moving): sleep(0.1)
  P2.speed = s
  P1.speed = s/r
  P2.volume += v
  sleep(t)
  #P1.volume -= (v-t*s)/r
  P1.volume -= v/r
  while(P1.moving or P2.moving): sleep(0.1)

def deliver_old(v1,v2,s1,s2,t):
  """This sequence pushes the plunger of syringe pump 1 by volume v at 
  speed s and then reloads the syringe"""
  p1.port = 'In'
  p2.port = 'In'
  wait()
  p1.speed = s1
  p2.speed = s2
  wait()
  p2.volume -= v2
  sleep(t)
  p1.volume -= v1
  sleep (v2/float(s2)+2.)
  p1.port = 'Out'
  p2.port = 'Out'
  wait()
  p1.speed = 10
  p2.speed = 10
  wait()
  p1.volume = 40
  p2.volume = 125
  wait()
  p1.port = 'In'
  p2.port = 'In'

def deliver(v1,v2,s1,s2):
  """This sequence pushes the plunger of syringe pump 1 by volume v at 
  speed s and then reloads the syringe"""
  #p1.port = 'In'
  p2.port = 'In'
  wait()
  p1.speed = s1
  p2.speed = s2
  wait()
  p2.volume -= v2
  #sleep(t)
  p1.volume -= v1
  #sleep (v2/float(s2)+2.)
  #print "p1.volume = ", p1.volume
  #print "p2.volume = ", p2.volume
  #p1.port = 'Out'
  #p2.port = 'Out'
  #wait()
  #p1.speed = 10
  #p2.speed = 10
  #wait()
  #p1.volume = 40
  #p2.volume = 125
  #wait()
  #p1.port = 'In'
  #p2.port = 'In'

def dispense(v1,v2,s1,s2,b):
  """This sequence pushes the plunger of syringe pumps 1 and 2 by volume v1 and v2 at 
  speeds s1 and s2, and backs off after the move to relieve the pressure"""
  P1.stop()
  P2.stop()
  #p1.port = 'In'
  P2.port = 'In'
  while(P1.moving or P2.moving): sleep(0.1)
  P1.speed = 1
  P2.speed = 1
  P1.volume -= b
  P2.volume -= b
  while(P1.moving or P2.moving): sleep(0.1)
  P1.speed = s1
  P2.speed = s2
  P1.volume -= v1
  P2.volume -= v2
  while(P1.moving or P2.moving): sleep(0.1)
  P1.speed = 1
  P2.speed = 1
  P1.volume += b
  P2.volume += b
  
def deliver2(v,s):
  """This sequence pushes the plunger of syringe pump 2 by volume v at 
  speed s and then reloads the syringe"""
  p2.port = 'In'
  sleep(2)
  p2.speed = s
  sleep(2)
  p2.volume -= v
  sleep (v/float(s)+2.)
  p2.port = 'Out'
  sleep(3)
  p2.speed = 10
  sleep(2)
  p2.volume = 125
  sleep((125-p2.volume)/10.+2.)
  p2.port = 'In'


def deliver1(v,s):
  """This sequence pushes the plunger of syringe pump 1 by volume v at 
  speed s """
  #p1.port = 'In'
  #wait()
  p1.speed = s
  wait()
  p1.volume -= v
  #wait()
  #sleep (v/float(s)+2.)
  #p1.port = 'Out'
  #wait()
  #p1.speed = 10
  #wait()
  #p1.volume = 40
  #wait()
  #p1.port = 'In'


  
def move(n,l,m):
  """ With the valve set to position n, move syringe plunger by l μL at a speed
  of m μL/s. Positive move fills the syringe; negative move empties it.
  When n = In, valve connects to upstream (Port valve) direction;
  when n = Out, valve connects to downstream (Waste container) direction.
  """
  log_command("move(%r,%r,%r)" % (n,l,m))
  select_syringe_port(n)
  set_speed(m)
  V = volume()
  if isnan(V):
    log_error("move(%r,%r,%r): volume unreadable, command not executed" % (n,l,m));
    return
  set_volume(V+l,m)

def empty(): # 6 seconds
  """Empties the syring pump to the output port"""
  log_command("empty()")
  select_syringe_port(Out)
  set_speed(S_fast)
  set_volume(0)
  set_volume(V_backoff)
  select_syringe_port(In)
  
# Basic commands

def select_syringe_port(port):
  """switches between input and output port of the syringe pump
  port: "In" = left port, used to load sample,
  "Out" = right port, used to dump waste"""
  syringe_pump.port = port
  wait(1)

set_port = select_syringe_port

def syringe_port():
  """Tell which of the three ports of the syring pump is currently active.
  "In" = left port, used to load sample,
  "Out" = right port, used to dump waste"""
  return syringe_pump.port

port = syringe_port

def volume():
  """The current remaining volume of syringe, in units of μL"""
  return syringe_pump.read_V

def set_volume(volume,speed=None):
  """Move the plunger until the volume is the given number of μL"""
  dV = abs(volume-syringe_pump.setV)
  if speed is not None: set_speed(speed)
  else: speed = syringe_pump.speed
  syringe_pump.setV = volume
  wait(dV/speed)

def set_speed(speed):
  """Defines the syringe plunger speed in μL/s."""
  syringe_pump.speed = speed

def speed():
  """Tell the currently configured syringe plunger speed in μL/s."""
  return syringe_pump.speed

def stop():
  """Cancels current move or program."""
  syringe_pump.moving = False

def wait(min_time=2.0):
  """Waits for the current move to complete."""
  try:
    sleep(min_time)
    while busy(): sleep(0.1)
  except KeyboardInterrupt:
    stop()
    raise KeyboardInterrupt

def busy():
  """Is either the syringe drive or valve currently moving?
  Return value: True or False"""
  return syringe_pump.moving != 0

def status():
  """Displays syringe pump status as clear text"""
  code = syringe_pump.status_byte
  print ((code>>0) & 1),"Instrument idle, command buffer not empty"
  print ((code>>1) & 1),"Syringe Drive Busy"
  print ((code>>2) & 1),"Valve Drive Busy"
  print ((code>>3) & 1),"Syntax Error"
  print ((code>>4) & 1),"Instrument error (valve or syringe)"
  print ((code>>5) & 1),"Always 0"
  print ((code>>6) & 1),"Always 1"
  print ((code>>7) & 1),"Always 0"
  
def log_error(message):
  """For critical errors. Generate an entry in the error log."""
  from sys import stderr,stdout
  if len(message) == 0 or message[-1] != "\n": message += "\n"
  stderr.write(message)
  t = timestamp()
  if syringe_pump.log_all: file(error_logfile(),"a").write("%s: %s" % (t,message))

def log_command(message):
  """Add command to command history"""
  from sys import stderr,stdout
  if len(message) == 0 or message[-1] != "\n": message += "\n"
  t = timestamp()
  if syringe_pump.log_all: file(command_logfile(),"a").write("%s: %s" % (t,message))

def command_logfile():
  """File name error messages."""
  from tempfile import gettempdir
  return gettempdir()+"/syringe_commands.log"

def error_logfile():
  """File name error messages."""
  from tempfile import gettempdir
  return gettempdir()+"/syringe_pump_error.log"

def sleep(dt):
  """Like time.sleep, but interruptable with Control-C.
  dt: time in seconds"""
  from time import sleep,time
  end = time()+dt
  while time() < end:
    sleep(min(end-time(),0.1))


class SyringePump(object):
  """Hamilton PSD3 Syringe Drive"""
  attempts = 5 # Attempts to repeat a command in case it failed, must be >0.
  verbose_logging = False # Display log messages in terminal.
  log_all = False # Log all communication to a file.
  serial_port = None # serial port object
  defaults_set = False
  from persistent_property import persistent_property

  def __init__(self,name="syringe_pump"):
    """name: string"""
    self.name = name
    # This is to make the query method multi-thread safe.
    self.lock = allocate_lock()

  def get_serial_port_name(self):
    """Which serial port to use to communication with the pump?
    "COM4" for NIH MacBook running Windows
    "14IDB:serial16" for BioCARS, VME crate
    "14IDB-NIH:serial7" for NIH Linux box 
    """
    from DB import dbget
    port_name = dbget(self.name+".serial_port")
    if port_name == "": port_name = "COM4"
    return port_name
  
  def set_serial_port_name(self,value):
    from DB import dbput
    dbput(self.name+".serial_port",value)
  serial_port_name = property(get_serial_port_name,set_serial_port_name)

  def init_defaults(self):
    """Sets default settings, if not done already"""
    if not self.defaults_set: self.set_defaults()

  def set_defaults(self):
    """Sets default settings"""
    # 1a = use auto-address mode
    # after this, the first device, the syring pump is assigned the address "a"
    # and the second device, the valve positionioner the address "b"
    self.send("1a")
    self.send("1a") # In case the first command failed.
    # The speed of the backlash correction is still too fast.
    # Turn off the backlash correction by setting it to 0 steps (default 6).
    self.send("aYSN0")
    self.defaults_set = True

  def init(self):
    """This runs the initialization sequency for the PSD3 and MVP.
    It is needed after power on.
    The PSD3 drives the plunger against the
    end stop while opening the ouput valve and sets the absolute
    position to zero.
    The MVP rotates its valve by one turn and stops at position 1."""
    self.set_defaults()
    self.speed = S_fast #S_fast
    # Turn off "backoff" during the "init" sequence by setting is to 0 steps
    self.send("aYSB30")
    self.send("aYSM5") # full resultion + high resolution step mode: 30,000 steps
    self.send("aXR") # initialize PSD3

  def get_initialized(self):
    """Has the initialization sequence been run?"""
    return not isnan(self.volume)
  
  def set_initialized(self,value):
    if value: self.init()
  initialized = property(get_initialized,set_initialized)

  def get_readback_volume(self):
    """The current remaining volume of syringe, in units of μL"""
    for attempt in range(0,self.attempts):
      reply = self.ask("aYQP")
      if reply == "":
        self.log_error("Volume: no reply (attempt %d/%d)"
          % (attempt+1,self.attempts))
        continue
      try: nsteps = int(reply)
      except ValueError:
        self.log_error("Volume: expecting numeric string, got %r (attempt %d/%d)"
          % (reply,attempt+1,self.attempts))
        continue
      volume = nsteps*V_step # Convert from motor steps to μL.
      self.log("Volume: Read %g uL" % volume)
      return volume
    self.log_error("Volume: read failed (after %d attempts)" % self.attempts)
    return nan
  readback_volume = property(get_readback_volume)
  read_V = readback_volume # shortcut

  def get_command_volume(self):
    """The target volume of the last move, in units of  uL"""
    if not hasattr(self,"last_command_volume"): return self.readback_volume
    return self.last_command_volume
  
  def set_command_volume(self,volume):
    """Move the plunger until the volume is the given number of μL"""
    nsteps = round(volume/V_step) # convert from μL to motor steps
    volume = nsteps*V_step
    if nsteps < 0: nsteps = 0
    if nsteps > maxsteps: nsteps = maxsteps
    self.send("aM%dR" % nsteps) # M = move absolute
    volume = nsteps*V_step
    self.last_command_volume = volume
  command_volume = property(get_command_volume,set_command_volume)
  setV = command_volume # shortcut
  command_dial = command_volume

  volume = property(get_readback_volume,set_command_volume)
  V = volume # shortcut
  dial = volume

  def get_value(self): return self.user_from_dial(self.dial)
  def set_value(self,value): self.dial = self.dial_from_user(value)
  value = property(get_value,set_value)

  def get_command_value(self): return self.user_from_dial(self.command_dial)
  def set_command_value(self,value): self.command_dial = self.dial_from_user(value)
  command_value = property(get_command_value,set_command_value)

  min_dial = persistent_property("min_dial",0.0)
  max_dial = persistent_property("max_dial",maxsteps*V_step)

  def get_min(self):
    if self.sign>0: return self.user_from_dial(self.min_dial)
    else: return self.user_from_dial(self.max_dial)
  def set_min(self,value):
    if self.sign>0: self.min_dial = self.dial_from_user(value)
    else: self.max_dial = self.dial_from_user(value)
  min = property(get_min,set_min)
  
  def get_max(self):
    if self.sign>0: return self.user_from_dial(self.max_dial)
    else: return self.user_from_dial(self.min_dial)
  def set_max(self,value):
    if self.sign>0: self.max_dial = self.dial_from_user(value)
    else: self.min_dial = self.dial_from_user(value)
  max = property(get_max,set_max)

  def user_from_dial(self,value): return value * self.sign + self.offset  
  def dial_from_user(self,value): return (value - self.offset) / self.sign

  sign = persistent_property("sign",1)
  offset = persistent_property("offset",0.0)

  def get_port(self):
    """Which of the three ports of the syring pump is currently active.
    "In" = left port, used to load sample,
    "Out" = right port, used to dump waste"""
    port = "?"
    for attempt in range(0,self.attempts):
      reply = self.ask("aLQP")
      if reply == '4': port = "Out"
      if reply == '1': port = "In"
      if port != "?": self.log("Port: %r" % port); return port
      self.log_error("Port: got reply %r (attempt %d/%d)" %
        (reply,attempt+1,self.attempts))
    self.log_error("Port read failed (after %d attempts)" % self.attempts)
    return "?"
  
  def set_port(self,port):
    """Switche between input and output port of the syringe pump
    port: "In" = left port, used to load sample,
    "Out" = right port, used to dump waste"""
    if port == "In": self.send("aIR")
    elif port == "Out": self.send("aOR")
    else: return
  port = property(get_port,set_port)
  
  def get_speed(self):
    """Currently configured syringe plunger speed in μL/s."""
    # YQS = request syringe drive speed, parameter = divisor of 1000 steps/s
    for attempt in range(0,self.attempts):
      reply = self.ask("aYQS")
      if reply == "":
        self.log_error("Speed: no reply (attempt %d/%d)"
          % (attempt+1,self.attempts))
        continue
      try: step_rate = float(reply)
      except ValueError:
        self.log_error("Speed: expecting numeric string, got %r (attempt %d/%d)"
          % (reply,attempt+1,self.attempts))
        continue
      full_stroke_steps = syringe_stroke/motor_stepsize
      speed = full_stroke_steps*V_step/float(step_rate)
      self.log("Speed: Read %g uL/s" % speed)
      return speed
    self.log_error("Speed read failed (after %d attempts)" % self.attempts)
    return nan
  
  def set_speed(self,speed):
    """Change plunger speed. Unit: μL/s."""
    steps_per_s = speed/V_step 
    full_stroke_steps = syringe_stroke/motor_stepsize
    # YSS = set syringe speed, parameter = divisor of 1000 steps/s
    step_rate = round(full_stroke_steps/steps_per_s)
    self.send("aYSS%d" % step_rate)
  speed = property(get_speed,set_speed)

  @property
  def firmware_version(self):
    """Firmware version"""
    return  self.ask("aU")

  def stop(self):
    """Cancels current move or program."""
    self.send("aKR")
    if hasattr(self,"last_command_volume"): del self.last_command_volume

  def wait(self):
    """Waits for the current move to complete."""
    while self.moving: sleep(0.1)

  def get_moving(self):
    """Are either the syringe drive or valve currently busy?"""
    x = self.status_byte
    if x == 0: return True # read failed, assume moving
    # Instrument status byte: bit 1 = syringe drive, 2 = valve drive
    moving = (((x>>1) & 1) or ((x>>2) & 1)) != 0
    self.log("Moving: %r" % moving)
    return moving
  
  def set_moving(self,moving):
    if not moving: self.stop()
    
  moving = property(get_moving,set_moving)

  @property
  def status_byte(self):
    """Instrument status byte"""
    for attempt in range(0,self.attempts):
      reply = self.ask("aE1")
      if reply == "":
        self.log_error("Status byte: no reply (attempt %d/%d)"
          % (attempt+1,self.attempts))
        continue
      if len(reply) != 1:
        self.log_error("Status byte: expecting 1 char, got %r (attempt %d/%d)"
          % (reply,attempt+1,self.attempts))
        continue
      status_byte, = struct.unpack("B",reply)
      self.log("Status byte: %d" % status_byte)
      return status_byte
    self.log_error("Status byte read failed (after %d attempts)" % self.attempts)
    return 0

  def send(self,command):
    """Transmit an RS-232 command to the syringe pump, which does not generate a
    reply"""
    reply = self.ask(command)
    if reply:
      self.log_error("Info: Command %r generated unexpected reply %r." %
        (command,reply))
    
  def ask(self,command):
    """Transmit an RS-232 command to the syringe pump, which generates a reply
    and return the reply"""
    self.init_communication()
    if self.serial_port is None: return ""
    if command == ""  or command[-1] != "\r": command += "\r"
    reply = self.query(command)
    if reply == "":
      self.log_error("Info: Command %r was not echoed." % command); return ""
    if reply.find(command) > 0:
      self.log_error("Ignoring extra %r at beginning of %r"\
      % (reply[0:reply.find(command)],reply))
    if reply.find(command) == -1:
      self.log_error("Command %r: expecting echo, got %r" % (command,reply))
      return ""
    reply = reply[reply.find(command)+len(command):] # remove echo of coinit_communicationmmand
    if reply == "":
      self.log_error("Command %r not acknowledged." % command); return ""
    if reply[0] == chr(21):
      self.log_error("Command %r failed." % command); return ""
    if reply[0] != chr(6):
      self.log_error("Command %r: expecting %r, got %r." %
        (command,chr(6),reply[0]))
      return ""
    reply = reply[1:] # remove <ACK> character.
    reply = reply.strip("\r")
    if reply: self.log("Command %r, reply %r." % (command,reply))
    else: self.log("Command %r, no reply." % command)
    return reply

  def query(self,command):
    """Send a command to the controller and return the reply"""
    with self.lock: # Allow only one thread at a time inside this function.
      if hasattr(self.serial_port,"query"):
        reply = self.serial_port.query(command)
      else:
        self.serial_port.write(command)
        reply = self.serial_port.read(80)
      # Worzk-around for a bug in OS X where te parity bit for odd parity
      # is not stripped by the "pyserial" driver.
      reply = string_7bit(reply)
      return reply

  def init_communication(self):
    """Initializes the RS-323 communication"""
    if self.serial_port is not None and \
      self.serial_port.port == self.serial_port_name: return
    if self.serial_port_name.startswith("COM") or \
      self.serial_port_name.startswith("/dev/"):
      # Assume local port
      from serial import Serial
    else: from EPICS_serial_CA import Serial
    try: self.serial_port = Serial(self.serial_port_name)
    except Exception,msg:
      self.log_error("serial port %s: %s" % (self.serial_port_name,msg))
      return
    self.serial_port.baudrate = 9600
    self.serial_port.bytesize = 7
    self.serial_port.parity = "O"
    self.serial_port.stopbits = 1
    self.serial_port.rtscts = 0 # Hardware flow control: off
    self.serial_port.xonxoff = 0 # Software flow control: off
    self.serial_port.dsrdtr = None # Modem handshake: off
    self.serial_port.timeout = 0.1

  def log(self,message):
    """For non-critical messages.
    Timestamp message and append it to the log file"""
    from sys import stderr,stdout
    if len(message) == 0 or message[-1] != "\n": message += "\n"
    t = timestamp()
    if self.verbose_logging: stdout.write("%s: Syringe pump: %s" % (t,message))
    if self.log_all: file(self.logfile,"a").write("%s: %s" % (t,message))

  def log_error(self,message):
    """For error messages.
    Display the message and append it to the error log file."""
    from sys import stderr
    if len(message) == 0 or message[-1] != "\n": message += "\n"
    t = timestamp()
    stderr.write("%s: Syringe pump: %s" % (t,message))
    file(self.error_logfile,"a").write("%s: %s" % (t,message))
    if self.log_all: file(self.logfile,"a").write("%s: %s" % (t,message))

  def log_command(self,message):
    """Add command to command history"""
    from sys import stderr,stdout
    if len(message) == 0 or message[-1] != "\n": message += "\n"
    t = timestamp()
    if self.log_all: file(self.command_logfile,"a").write("%s: %s" % (t,message))

  @property
  def error_logfile(self):
    """File name error messages."""
    from tempfile import gettempdir
    return gettempdir()+"/syringe_pump_error.log"

  @property
  def logfile(self):
    """File name for transcript if verbose logging is enabled."""
    from tempfile import gettempdir
    return gettempdir()+"/syringe_pump.log"

  @property
  def command_logfile(self):
    """File name error messages."""
    from tempfile import gettempdir
    return gettempdir()+"/syringe_commands.log"

def timestamp():
  """Current date and time as formatted ASCCI text, precise to 1 ms"""
  from datetime import datetime
  timestamp = str(datetime.now())
  return timestamp[:-3] # omit microsconds

def isnan(x):
  from numpy import isnan
  try: return isnan(x)
  except TypeError: return True

def number_of_ones(n):
  """number of 1 bits in the number n"""
  c = 0
  while n:
    c += n%2
    n /= 2
  return c

def parity(n):
  """even: 0, odd: 1"""
  return number_of_ones(n) % 2

def odd_parity(string):
  """Which of te characters in string have odd parity?"""
  return [parity(ord(c)) for c in string]

def string_7bit(string):
  """Strip hte highest bit of evey character in string"""
  s = ""
  for c in string: s += chr(ord(c) & 0x7f)
  return s


syringe_pump_driver = SyringePump("syringe_pump")
syringe_pump2_driver = SyringePump("syringe_pump2")

class SyringePumpCombined(object):
  """Move two syringe pumps synchronously"""
  def __init__(self,name,p1,p2):
    """name: string
    p1,p2: syringe_pump instances"""
    self.name = name
    self.p1 = p1
    self.p2 = p2

  def get_read_V(self):
    """in units of μL"""
    V = (self.p1.value + self.p2.value)/2
    return V
  read_V = property(get_read_V)

  def get_V(self):
    """in units of μL"""
    return self.V_from_V1_V2(self.p1.command_value,self.p2.command_value)
  def set_V(self,V):
    self.p2.speed = self.p1.speed
    V1,V2 = self.V1_V2_from_V(V)
    # The two commands need to be executed simultaneouly.
    start_new_thread(setattr,(self.p1,"command_value",V1))
    start_new_thread(setattr,(self.p2,"command_value",V2))
  V = property(get_V,set_V)

  def get_V_min(self):
    """in units of μL"""
    V1_lim,V2_lim = [self.p1.min,self.p1.max],[self.p2.min,self.p2.max]
    dV_min = min([self.V_from_V1_V2(V1,V2) for V1 in V1_lim for V2 in V2_lim])
    return dV_min
  def set_V_min(self,V_min):
    self.p1.min,self.p2.min = self.V1_V2_from_V(V_min)
  V_min = property(get_V_min,set_V_min)

  def get_V_max(self):
    """in units of μL"""
    V1_lim,V2_lim = [self.p1.min,self.p1.max],[self.p2.min,self.p2.max]
    dV_max = max([self.V_from_V1_V2(V1,V2) for V1 in V1_lim for V2 in V2_lim])
    return dV_max
  def set_V_max(self,V_max):
    self.p1.max,self.p2.max = self.V1_V2_from_V(V_max)
  V_max = property(get_V_max,set_V_max)

  def V_from_V1_V2(self,V1,V2):
    V = (V1+V2)/2
    return V

  def V1_V2_from_V(self,V):
    dV = V - self.V
    V1 = self.p1.command_value + dV
    V2 = self.p2.command_value + dV
    return V1,V2

  def get_read_dV(self):
    """in units of μL"""
    V = self.p2.value - self.p1.value
    return V
  read_dV = property(get_read_dV)

  def get_dV(self):
    """in units of μL"""
    return self.dV_from_V1_V2(self.p1.command_value,self.p2.command_value)
  def set_dV(self,dV):
    self.p2.speed = self.p1.speed
    V1,V2 = self.V1_V2_from_dV(dV)
    # The two commands need to be executed simultaneouly.
    start_new_thread(setattr,(self.p1,"command_value",V1))
    start_new_thread(setattr,(self.p2,"command_value",V2))
  dV = property(get_dV,set_dV)

  def get_dV_min(self):
    """in units of μL"""
    V1_lim,V2_lim = [self.p1.min,self.p1.max],[self.p2.min,self.p2.max]
    dV_min = min([self.dV_from_V1_V2(V1,V2) for V1 in V1_lim for V2 in V2_lim])
    return dV_min
  def set_dV_min(self,dV_min):
    self.p1.min,self.p2.min = self.V1_V2_from_dV(dV_min)
  dV_min = property(get_dV_min,set_dV_min)

  def get_dV_max(self):
    """in units of μL"""
    V1_lim,V2_lim = [self.p1.min,self.p1.max],[self.p2.min,self.p2.max]
    dV_max = max([self.dV_from_V1_V2(V1,V2) for V1 in V1_lim for V2 in V2_lim])
    return dV_max
  def set_dV_max(self,V_max):
    self.p1.max,self.p2.max = self.V1_V2_from_dV(V_max)
  dV_max = property(get_dV_max,set_dV_max)

  def dV_from_V1_V2(self,V1,V2):
    dV = V2 - V1
    return dV

  def V1_V2_from_dV(self,dV):
    ddV = dV - self.dV
    V1 = self.p1.command_value - ddV/2
    V2 = self.p2.command_value + ddV/2
    return V1,V2

  def get_speed(self):
    """Currently configured syringe plunger speed in μL/s."""
    return self.p1.speed
  def set_speed(self,speed):
    self.p1.speed = speed
    self.p2.speed = speed
  speed = property(get_speed,set_speed)

  def get_initialized(self):
    """Currently configured syringe plunger initialized in μL/s."""
    return self.p1.initialized and self.p2.initialized
  def set_initialized(self,initialized):
    start_new_thread(setattr,(self.p1,"initialized",initialized))
    start_new_thread(setattr,(self.p2,"initialized",initialized))
  initialized = property(get_initialized,set_initialized)

syringe_pump_combined_driver = SyringePumpCombined("syringe_pump_combined",
    syringe_pump_driver,syringe_pump2_driver)


def run_server():
  """Serve the Syringe pump up on the network as EPCIS IOC.
  Keep running forever."""
  from time import sleep
  start_server()
  while True: sleep(0.25)

def start_server():
  """Serve the Syringe pump up on the network as EPCIS IOC.
  Return control when started."""
  import CAServer
  CAServer.verbose = False
  CAServer.verbose_logging = False
  print("log: %s" % CAServer.logfile())
  for obj in syringe_pump_driver,syringe_pump2_driver,\
    syringe_pump_combined_driver:
    CAServer.register_object(obj,"NIH:"+obj.name)

def stop_server():
  """Serve the Syringe pump up on the network as EPCIS IOC.
  Return control when started."""
  import CAServer
  print("stopping server")
  for obj in syringe_pump_driver,syringe_pump2_driver,\
    syringe_pump_combined_driver:
    CAServer.unregister_object(obj,"NIH:"+obj.name)

from CA import Record
syringe_pump = Record("NIH:syringe_pump")
syringe_pump2 = Record("NIH:syringe_pump2")
syringe_pump_combined = Record("NIH:syringe_pump_combined")
# Shortcuts:
p = p1 = syringe_pump
p2 = syringe_pump2
pc = syringe_pump_combined
P = P1 = syringe_pump_driver
P2 = syringe_pump2_driver
PC = syringe_pump_combined_driver

##p2.log_all = False
##p1.log_all = False

if __name__ == "__main__":
  from pdb import pm
  from sys import argv
  if "run_server" in argv:
    run_server()
    from time import sleep
    while True: sleep(0.1)

  self = PC # for debugging
  print('start_server()')
  print('stop_server()')
  import threading
  print('threading.enumerate()')

