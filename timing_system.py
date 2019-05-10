"""
FPGA Timing System

Author: Friedrich Schotte
Date created: 2007-04-02
Date last modified: 2019-03-22
"""
from logging import debug,info,warn,error

__version__ = "8.5" # prefixes

def Parameter(name,default_value=0.0):
    """A propery object to be used inside a class"""
    def get(self):
        class_name = getattr(self,"name",self.__class__.__name__)
        parameter_name = class_name+"."+name
        t = getattr(self,"timing_system",timing_system)
        value = t.parameter(parameter_name,default_value)
        return value
    get.default_value = default_value # save for inspection
    def set(self,value):
        class_name = getattr(self,"name",self.__class__.__name__)
        parameter_name = class_name+"."+name
        t = getattr(self,"timing_system",timing_system)
        t.set_parameter(parameter_name,value,default_value)
    return property(get,set)

from functools import total_ordering

@total_ordering
class Register(object):
  """User-programmable parameter of FPGA timing system"""
  sign = 1

  def __init__(self,timing_system,name,min=None,max=None,
    min_count=None,max_count=None):
    """
    name: mnemonic or hexadecimal address as string
    stepsize: resolution in units of seconds
    min: minimum count
    max: maximum count
    min_count: minimum count
    max_count: maximum count
    """
    self.timing_system = timing_system
    self.name = name
    if min != None: self.min = min
    if max != None: self.max = max
    if min_count != None: self.min_count = min_count
    if max_count != None: self.max_count = max_count
    self.unit = ""
    timing_system.add_register(self)

  # for sorting
  def __eq__(self,other): return self.name == other.name
  def __ne__(self,other): return not self == other
  def __lt__(self,other): return self.name < other.name

  def get_count(self):
    """The content of a register as integer value"""
    return self.timing_system.register_count(self.name)
  def set_count(self,count):
    from numpy import isnan
    if isnan(count): return
    self.timing_system.set_register_count(self.name,self.next_count(count))
  count = property(get_count,set_count)

  def monitor(self,callback,*args,**kwargs):
    """Call callback routine when 'count' property changes"""
    if not self.monitor_active(callback,*args,**kwargs):
        new_thread = kwargs.get("new_thread",True)
        if "new_thread" in kwargs: del kwargs["new_thread"]
        # Make sure caching monitors are set up first:
        from CA_cached import caget_cached 
        caget_cached(self.PV_name)
        from CA import camonitor
        def monitor_callback(PV_name,value,formatted_value):
          callback(*args,**kwargs)
        monitor_callback.callback = callback
        monitor_callback.args = args
        monitor_callback.kwargs = kwargs
        camonitor(self.PV_name,callback=monitor_callback,new_thread=new_thread)
  
  def monitor_clear(self,callback=None,*args,**kwargs):
    from CA import camonitors,camonitor_clear
    if callback is None: camonitor_clear(self.PV_name)
    else:
      for f in camonitors(self.PV_name):
        if getattr(f,"callback",None) == callback \
          and getattr(f,"args",[]) == args \
          and getattr(f,"kwargs",{}) == kwargs:
          camonitor_clear(self.PV_name,f)

  def monitor_active(self,callback,*args,**kwargs):
    from CA import camonitors
    active = False
    for f in camonitors(self.PV_name):
      pass
      if (getattr(f,"callback",None) == callback
        and getattr(f,"args",[]) == args
        and getattr(f,"kwargs",{}) == kwargs):
        active = True
    return active

  @property  
  def monitors(self):
    """list of callback routines"""
    monitors = []
    from CA import camonitors
    for f in camonitors(self.PV_name):
      if hasattr(f,"callback"): monitors += [f.callback]
    return monitors

  @property
  def PV_name(self):
      """Process variable name for EPICS Channel Access"""
      return self.timing_system.prefix+"registers."+self.name+".count"

  def get_min_count(self):
    """Lowest allowed count"""
    if hasattr(self,"__min_count__"): return self.__min_count__
    return 0
  def set_min_count(self,value):
    if value < 0: value = 0
    self.__min_count__ = value
  min_count = property(get_min_count,set_min_count)

  def get_max_count(self):
    """Highest allowed count"""
    if hasattr(self,"__max_count__"): return self.__max_count__
    return 2**self.bits-1
  def set_max_count(self,value):
    self.__max_count__ = value
  max_count = property(get_max_count,set_max_count)

  min = min_count
  max = max_count

  def next_count(self,count):
    """Round value to the next allowed integer count"""
    from numpy import rint,clip,isnan,nan
    if isnan(count): return nan
    if count < self.min_count: count = self.min_count
    if count > self.max_count: count = self.max_count
    count = toint(rint(count))
    return count

  def next(self,value):
    """What is noext closes possible value to the given user value the reigster
    can hold?
    value: user value"""
    count = self.count_from_value(value)
    value = self.value_from_count(count)
    return value

  @property
  def description(self):
    return self.timing_system.register_property(self.name,"description","")

  @property
  def address(self):
    return self.timing_system.register_property(self.name,"address")

  @property
  def bit_offset(self):
    return self.timing_system.register_property(self.name,"bit_offset")

  @property
  def bits(self):
    return self.timing_system.register_property(self.name,"bits")

  def get_value(self):
    """User value of the delay in units of seconds"""
    return self.user_from_dial(self.dial)
  def set_value(self,value): self.dial = self.dial_from_user(value)
  value = property(get_value,set_value)

  def get_dial(self):
    """Delay controlled by the register in units of seconds"""
    return self.dial_from_count(self.count)
  def set_dial(self,value): self.count = self.count_from_dial(value)
  dial = property(get_dial,set_dial)
  
  def count_from_value(self,value):
    """Convert user value to integer register count"""
    return self.count_from_dial(self.dial_from_user(value))

  def value_from_count(self,count):
    """Convert integer register count to user value"""
    return self.user_from_dial(self.dial_from_count(count))

  def count_from_dial(self,dial_value):
    """Convert delay in seconds to integer register count"""
    count = self.next_count(dial_value/self.stepsize)
    return count

  def dial_from_count(self,count):
    """Convert integer register count to delay in seconds"""
    dial_value = count*self.stepsize
    return dial_value

  def user_from_dial(self,value): return value * self.sign + self.offset  
  def dial_from_user(self,value): return (value - self.offset) / self.sign

  stepsize = Parameter("stepsize",1.0)
  offset = Parameter("offset",0.0)

  def __repr__(self): return self.name

  def get_PP_enabled(self):
    value = False
    if self.channel is not None: value = self.channel.PP_enabled
    return value
  def set_PP_enabled(self,value):
    if self.channel is not None: self.channel.PP_enabled = value
  PP_enabled = property(get_PP_enabled,set_PP_enabled)

  def get_special(self):
    value = ""
    if self.channel is not None: value = self.channel.special
    return value
  def set_special(self,value):
    if self.channel is not None: self.channel.special = value
  special = property(get_special,set_special)

  @property
  def channel(self):
    channel = None
    if self.name.startswith("ch") and "_" in self.name:
        count = self.name.split("_")[0].replace("ch","")
        try:
            channel_number = int(count)-1
            channel = timing_system.channels[channel_number]
        except: pass
    return channel

register = Register # alias

class Timing_Register(Register):
  """Register representing a time delay, with a scale factor, converting count to a
  delay value in units of seconds"""

  def __init__(self,timing_system,name,stepsize=1.,min=None,max=None,sign=1,
    unit="s",min_count=None,max_count=None):
    """
    name = mnemonic or hexadecimal address as string
    stepsize = resolution in units of seconds
    min = minimum dial value
    max = maximum dial value
    min_count = minimum count
    max_count = maximum count
    sign = +1 or -1, for dial to user value conversion
    offset = for dial to user value conversion
    """
    timing_system.Register.__init__(self,timing_system,name)

    self.stepsize_ref = "parameters."+self.name+".stepsize"
    if stepsize is not None: self.stepsize_ref = stepsize
    self.sign = sign
    self.unit = unit
    if min is not None: self.min_dial = min
    if max is not None: self.max_dial = max
    if min_count != None: self.min_count = min_count
    if max_count != None: self.max_count = max_count

  def get_stepsize(self):
    if type(self.stepsize_ref) == str:
      expr = "self.timing_system."+self.stepsize_ref
      try: stepsize = eval(expr)
      except Exception,msg:
        warn("%s.stepsize: %s: %s" % (self.name,expr,msg)); stepsize = 1
    else: stepsize = self.stepsize_ref # numeric value
    return stepsize 
  def set_stepsize(self,value):
    if type(self.stepsize_ref) == str:
      cmd = "self.timing_system.%s=%r" % (self.stepsize_ref,value)
      try: exec(cmd)
      except Exception,msg: warn("%.stepsize: %s: %s" % (self.name,cmd,msg)) 
    else: self.stepsize_ref = value
  stepsize = property(get_stepsize,set_stepsize)

  def get_dial(self):
    """Delay controlled by the register in units of seconds"""
    return self.count*self.stepsize
  def set_dial(self,value): self.count = int(round(value/self.stepsize))
  dial = property(get_dial,set_dial)

  def get_value(self):
    """User value of the delay in units of seconds"""
    return self.user_from_dial(self.dial)
  def set_value(self,value): self.dial = self.dial_from_user(value)
  value = property(get_value,set_value)
  command_value = value

  def define_value(self,value):
    "modifies the user to dial offset such that the new user value is 'value'"
    self.offset = value - self.dial * self.sign
    # user = dial*sign + offset; offset = user - dial*sign

  def get_min_dial(self): return self.dial_from_count(self.min_count)
  def set_min_dial(self,value):
    try: self.min_count = int(round(value/self.stepsize))
    except: pass
  min_dial = property(get_min_dial,set_min_dial,doc="Lowest allowed value in s")
    
  def get_max_dial(self): return self.dial_from_count(self.max_count)
  def set_max_dial(self,value):
    try: self.max_count = int(round(value/self.stepsize))
    except: pass
  max_dial = property(get_max_dial,set_max_dial,doc="Highest allowed value in s")
    
  def get_min(self): return self.user_from_dial(self.min_dial)
  def set_min(self,value): self.min_dial = self.dial_from_user(value)
  min = property(get_min,set_min,doc="Low limit in user units")

  def get_max(self): return self.user_from_dial(self.max_dial)
  def set_max(self,value): self.max_dial = self.dial_from_user(value)
  max = property(get_max,set_max,doc="High limit in user units")

  def count_from_value(self,value):
    """Convert user value to integer register count"""
    return self.count_from_dial(self.dial_from_user(value))

  def value_from_count(self,count):
    """Convert integer register count to user value"""
    return self.user_from_dial(self.dial_from_count(count))

  def count_from_dial(self,dial_value):
    """Convert user value to integer register count"""
    count = self.next_count(dial_value/self.stepsize)
    return count

  def dial_from_count(self,count):
    """Convert integer register count to user value"""
    dial_value = count*self.stepsize
    return dial_value

  def next(self,value):
    """What is noext closes possible value to the given user value the reigster
    can hold?
    value: user value"""
    count = self.count_from_value(value)
    value = self.value_from_count(count)
    return value

  offset = Parameter("offset",0.0)

  def user_from_dial(self,value): return value * self.sign + self.offset  
  def dial_from_user(self,value): return (value - self.offset) / self.sign

timing_register = Timing_Register # alias


class Channel(object):
  """Output of the timing system"""
  total_count = 24
  __count__ = -1
  __mnemonic__ = ""
  
  def __init__(self,timing_system,count=-1,mnemonic="",name=None):
    """count:  0,1, ... 23
    mnemonic: e.g. 'xosct'
    name: e.g. 'ch1'
    """
    self.timing_system = timing_system
    self.count = count
    self.__mnemonic__ = mnemonic
    if name is not None:
        if self.count < 0:
            try: self.count = int(name.replace("ch",""))-1
            except ValueError: pass
        if self.count < 0:
            try: self.count = int(name.replace("channels(","").replace(")",""))
            except ValueError: pass
        if self.count < 0:
            error("name: expecting ch1..ch24 or channel(0..23), got %r" % name)

  @property
  def name(self): return self.name_of_count(self.count)

  @staticmethod
  def name_of_count(count):
      ##name = "channel(%r)" % count
      name = "ch%d" % (int(count)+1)
      return name

  def get_count(self):
    count = self.__count__
    if count == -1 and self.__mnemonic__:
        count = self.count_of_mnemonic(self.__mnemonic__)
    return count
  def set_count(self,value):
    self.__count__ = value
  count = property(get_count,set_count)

  def count_of_mnemonic(self,mnemonic):
    """Channel index: 0-23"""
    for i in range(0,self.total_count):
      name = self.name_of_count(i)
      if self.timing_system.parameter(name+".mnemonic","") == mnemonic:
          count = i; break
    else: count = -1
    return count

  from numpy import nan
  PP_enabled = Parameter("PP_enabled",False)
  description = Parameter("description","")
  mnemonic = Parameter("mnemonic","")
  offset_HW = Parameter("offset",nan)
  offset_sign = Parameter("offset_sign",1.0)
  offset_sign_choices = 1,-1
  pulse_length_HW = Parameter("pulse_length",nan)
  offset_PP = Parameter("offset_PP",nan)
  pulse_length_PP = Parameter("pulse_length_PP",nan)
  counter_enabled = Parameter("counter_enabled",0)
  sign = Parameter("sign",1)
  timed = Parameter("timed","") # timing relative to pump or probe
  timed_choices = "pump","probe","period"
  gated = Parameter("gated","") # enable?
  gated_choices = "pump","probe","detector"
  repeat_period = Parameter("repeat_period","") # how often?
  repeat_period_choices = "pulse","burst start","burst end","image","50 ms","100 ms",""
  on = Parameter("on",True)
  bit_code = Parameter("bit_code",0)
  special = Parameter("special","") 
  special_choices = (
      "ms",        # X-ray millisecond shutter
      "ms_legacy", # X-ray millisecond shutter
      "trans",     # Sample trannslation trigger
      "pso",       # Picosecond oscillator reference clock
      "nsf",       # Nanosecond laser flashlamp trigger
  )

  def get_pulse_length(self):
      from numpy import nan,isnan
      value = nan
      if not isnan(self.pulse_length_PP):
          value = self.pulse_length_PP*self.timing_system.hsct
      elif not isnan(self.pulse_length_HW): value = self.pulse_length_HW
      return value
  def set_pulse_length(self,value):
      self.pulse_length_HW = value
  pulse_length = property(get_pulse_length,set_pulse_length)

  def get_offset(self):
      from numpy import isnan
      value = 0.0
      if not isnan(self.offset_PP):
          value = self.offset_PP*self.timing_system.hsct
      elif not isnan(self.offset_HW): value = self.offset_HW
      return value
  def set_offset(self,value):
      self.offset_HW = value
  offset = property(get_offset,set_offset)

  @property
  def channel_number(self): return self.count

  def register(name,*args,**kwargs):
    """Define a property corresponding to a register
    name: e.g. "state"
    """
    def get(self):
        return self.timing_system.Register(self.timing_system,self.register_name(name),*args,**kwargs)
    return property(get)

  def timing_register(name,*args,**kwargs):
    """Define a property corresponding to a timing register"""
    def get(self):
        return self.timing_system.Timing_Register(self.timing_system,self.register_name(name),*args,**kwargs)
    return property(get)

  def register_name(self,name):
    """name: e.g. "state","delay" """
    return "ch%d_%s" % (self.count+1,name)

  @property
  def delay(self):
    """Register"""
    return self.timing_system.Timing_Register(self.timing_system,self.register_name("delay"),
      stepsize="bct/2",max_count=712799)

  @property
  def fine(self):
    """Register"""
    return self.timing_system.Register(self.timing_system,self.register_name("fine"))

  @property
  def enable(self):
    """Generate pulse every millisecond?"""
    return self.timing_system.Register(self.timing_system,self.register_name("enable"))

  @property
  def state(self):
    """Current level: 0=low,1=high"""
    return self.timing_system.Register(self.timing_system,self.register_name("state"))

  @property
  def pulse(self):
    """Output pulse duration"""
    return self.timing_system.Timing_Register(self.timing_system,self.register_name("pulse"),
        stepsize="bct*4")

  pulse_choices = [1e-3,2e-3,3e-3,10e-3,30e-3,100e-3]

  @property
  def input(self):
    """Configured as input?"""
    return self.timing_system.Register(self.timing_system,self.register_name("input"))

  @property
  def override(self):
    """Override Piano player? [0=pass,1=overide]"""
    return self.timing_system.Register(self.timing_system,self.register_name("override"))

  @property
  def override_state(self):
    """Override state [0=low,1=high]"""
    return self.timing_system.Register(self.timing_system,self.register_name("override_state"))

  @property
  def trig_count(self):
    """Trigger count [0-4294967295]"""
    return self.timing_system.Register(self.timing_system,self.register_name("trig_count"))

  @property
  def acq_count(self):
    """Acquisition count [0-2147483647]"""
    return self.timing_system.Register(self.timing_system,self.register_name("acq_count"))

  @property
  def acq(self):
    """Acquiring? [0=discard,1=save]"""
    return self.timing_system.Register(self.timing_system,self.register_name("acq"))

  def get_output_status(self):
    """PP = pass piano player state, Low, High = override"""
    if not self.override.count: status = "PP"
    else: status = "Low" if self.override_state.count == 0 else "High"
    return status
  def set_output_status(self,value):
    if value.capitalize() == "High":
        self.override.count = True
        self.override_state.count = True
    if value.capitalize() == "Low":
        self.override.count = True
        self.override_state.count = False
    if value.upper() == "PP":
        self.override.count = False
  output_status = property(get_output_status,set_output_status)

  output_status_choices = ["PP","Low","High"]

  @property
  def specout(self):
    """Special output: 0=normal, 1=70.4 MHz"""
    return self.timing_system.Register(self.timing_system,self.register_name("specout"))

  @property
  def stepsize(self):
    """Resolution in seconds"""
    return 0.5*self.timing_system.bct

  def user_from_dial(self,value): return value * self.sign + self.offset  
  def dial_from_user(self,value): return (value - self.offset) / self.sign

  def count_from_value(self,value):
    """Convert user value to integer register count"""
    return self.count_from_dial(self.dial_from_user(value))

  def value_from_count(self,count):
    """Convert integer register count to user value"""
    return self.user_from_dial(self.dial_from_count(count))

  def count_from_dial(self,dial_value):
    """Convert user value to integer register count"""
    count = self.next_count(dial_value/self.stepsize)
    return count

  def dial_from_count(self,count):
    """Convert integer register count to user value"""
    dial_value = count*self.stepsize
    return dial_value

  from numpy import inf
  min_count = 0
  max_count = inf
  min_dial = 0.0
  max_dial = inf

  def get_min(self): return self.user_from_dial(self.min_dial)
  def set_min(self,value): self.min_dial = self.dial_from_user(value)
  min = property(get_min,set_min,doc="Low limit in user units")

  def get_max(self): return self.user_from_dial(self.max_dial)
  def set_max(self,value): self.max_dial = self.dial_from_user(value)
  max = property(get_max,set_max,doc="High limit in user units")

  def next_count(self,count):
    """Round value to the next allowed integer count"""
    from numpy import rint,clip,isnan,nan
    if isnan(count): return nan
    count = clip(count,self.min_count,self.max_count)
    count = toint(count)
    return count

  def next(self,value):
    """What is noext closes possible value to the given user value the reigster
    can hold?
    value: user value"""
    count = self.count_from_value(value)
    value = self.value_from_count(count)
    return value

  def __repr__(self):
      return self.name


class Variable(object):
  """Software-defined parameter controlling the timing,
  not associated with any hardware register in the FPGA"""
  
  def __init__(self,timing_system,name,stepsize=None,sign=1):
    """name: common base name for registers
    sign: user to dial scale factor
    stepsize: e.g. 1 or "hlct"
    """
    self.timing_system = timing_system
    self.name = name
    self.stepsize_ref = "parameters."+self.name+".stepsize"
    if stepsize is not None: self.stepsize_ref = stepsize
    self.sign = sign
    timing_system.add_variable(self)

  def get_stepsize(self):
    if type(self.stepsize_ref) == str:
      expr = "self.timing_system."+self.stepsize_ref
      try: stepsize = eval(expr)
      except Exception,msg:
        warn("%s.stepsize: %s: %s" % (self.name,expr,msg)); stepsize = 1
    else: stepsize = self.stepsize_ref # numeric value
    return stepsize 
  def set_stepsize(self,value):
    if type(self.stepsize_ref) == str:
      cmd = "self.timing_system.%s=%r" % (self.stepsize_ref,value)
      try: exec(cmd)
      except Exception,msg: warn("%.stepsize: %s: %s" % (self.name,cmd,msg)) 
    else: self.stepsize_ref = value
  stepsize = property(get_stepsize,set_stepsize)

  def get_dial(self):
    """Delay controlled by the register in units of seconds"""
    return self.count*self.stepsize
  def set_dial(self,value): self.count = int(round(value/self.stepsize))
  dial = property(get_dial,set_dial)

  def next(self,value):
    """Round user value to the next possible value, given the step size"""
    dial_value = self.dial_from_user(value)
    count = int(round(dial_value/self.stepsize))
    dial_value = count*self.stepsize
    value = self.user_from_dial(dial_value)
    return value

  def get_value(self):
    "User value of the delay in units of seconds"
    return self.user_from_dial(self.dial)
  def set_value(self,value): self.dial = self.dial_from_user(value)
  value = property(get_value,set_value)

  count = Parameter("count",0)
  offset = Parameter("offset",0.0)

  def user_from_dial(self,value): return value * self.sign + self.offset  
  def dial_from_user(self,value): return (value - self.offset) / self.sign

  from numpy import inf
  min = -inf
  max = inf

  def __repr__(self): return self.name


class Parameters(object):
  def __init__(self,timing_system):
    self.__timing_system__ = timing_system
    
  def __getattr__(self,name):
    """The value of a parameter stored on the timing system"""
    # Called when 'x.name' is evaluated.
    # It is only invoked if the attribute wasn't found the usual ways.
    # __members__ is used for auto completion, browsing and "dir".
    if name == "__members__": return self.__timing_system__.parameter_names

    if name.startswith("__") and name.endswith("__"):
      raise RuntimeError("attribute %r not found" % name)
    return self.__timing_system__.parameter(name)

  def __setattr__(self,name,value):
    if name.startswith("__") and name.endswith("__"):
      object.__setattr__(self,name,value)
    else: self.__timing_system__.set_parameter(name,value)


class Configuration(object):
  """Settings"""
  parameters = [
    "clk_src.count",   # Bunch clock source [0=RF IN,1=Ch1,...24=Ch24,25=RJ45:1,29=350MHz]
    "sbclk_src.count", # Single-bunch clock source [1=Ch1,...24=Ch24,27=RJ45:3]
    "clk_div.count",   # Clock divider? [0=1,1=2,2=3,...7=8]
    "clk_dfs_mode.count", # Clock DFS frequency mode [0=low freq,1=high freq]
    "clk_dll_mode.count", # Clock DLL frequency mode [0=low freq,1=high freq]
    "clk_mul.count",      # Clock multiplier [0=N/A,1=2,2=3,...31=32]
    "clk_shift_stepsize",
    "clock_period_external",
    "clock_period_internal",
    "p0_div_1kHz.count",
    "clk_88Hz_div_1kHz.count",
    "hlc_div",
    "nsl_div",
    "p0fd2.count",
    "p0d2.count",
    "p0_shift.offset",
    "psod3.offset",
    "hlcnd.count",
    "hlcnd.offset",
    "hlcad.offset",
    "hlctd.offset",
  ]
  channel_parameters = [
    "PP_enabled",
    "input.count",
    "description",
    "mnemonic",
    "special",
    "specout.count",
    "offset_HW",
    "offset_sign",
    "pulse_length_HW",
    "offset_PP",
    "pulse_length_PP",
    "counter_enabled",
    "enable.count",
    "timed",
    "gated",
    "override.count",
    "state.count",
  ]
  
  def __init__(self,name):
    """name: 'BioCARS', or 'LaserLab'"""
    self.name = name

  def save(self):
    """Store current FPGA settings on local file system"""
    from DB import dbset
    for par in self.parameters:
      value = eval("timing_system."+par)
      dbset("timing_system_configurations/%s.%s" % (self.name,par),value)
    for channel in timing_system.channels:
      for name in self.channel_parameters:
        value = eval("channel."+name)
        db_name = "timing_system_configurations/%s.%s.%s" % (self.name,channel.name,name)
        dbset(db_name,value)

  def load(self):
    """Upload save settings to FPGA timign system"""
    from DB import db
    from numpy import nan,inf # for eval
            
    for par in self.parameters:
      default_value = eval("timing_system.%s" % par)
      value = db("timing_system_configurations/%s.%s" % (self.name,par),default_value)
      if not equal(value,default_value):
          execute("timing_system.%s = %r" % (par,value),locals=locals(),globals=globals())
    for channel in timing_system.channels:
      for name in self.channel_parameters:
        default_value = eval("channel."+name)
        db_name = "timing_system_configurations/%s.%s.%s" % (self.name,channel.name,name)
        value = db(db_name,default_value)
        if not equal(value,default_value):
          execute("channel.%s = %r" % (name,value),locals=locals(),globals=globals())

  def __repr__(self): return "Configuration(%r)" % self.name


class TimingSystem(object):
  """FPGA Timing system"""
  name = "timing_system"
  from persistent_property import persistent_property
  prefix = persistent_property("prefix","NIH:TIMING.")
  prefixes = persistent_property("prefixes",[
      "NIH:TIMING.",
      "TESTBENCH:TIMING.",
      "LASERLAB:TIMING.",
  ])

  all_register_names = persistent_property("all_register_names",[])

  Register = Register
  Timing_Register = Timing_Register
  Channel = Channel
  Variable = Variable
  Parameters = Parameters
  Configuration = Configuration

  def __init__(self):
    from CA import camonitor
    camonitor(self.prefix+"registers",callback=self.register_names_callback)

  def register_names_callback(self,PV_name,value,char_value):
    self.all_register_names = value.split(";")

  def __repr__(self): return "timing_system"

  def get_ip_address(self):
    from CA import cainfo
    ip_address = cainfo(self.prefix+"registers","IP_address")
    return ip_address
  def set_ip_address(self,value): pass
  ip_address = property(get_ip_address,set_ip_address)

  from persistent_property import persistent_property
  port = persistent_property("port","2002")

  def get_ip_address_and_port(self):
    ip_address_and_port = self.ip_address+":"+self.port
    return ip_address_and_port
  def set_ip_address_and_port(self,ip_address_and_port):
    self.port = ip_address_and_port.split(":")[-1]
  ip_address_and_port = property(get_ip_address_and_port,set_ip_address_and_port)

  @property
  def online(self):
    online = self.ip_address != ""
    return online

  def register_monitor(self,name,callback,*args,**kwargs):
    from CA import camonitor
    def monitor_callback(PV_name,value,formatted_value):
      callback(*args,**kwargs)
    monitor_callback.callback = callback
    monitor_callback.args = args
    monitor_callback.kwargs = kwargs
    camonitor(self.register_PV_name(name),callback=monitor_callback)
  
  def register_monitor_clear(self,name):
    from CA import camonitor_clear
    camonitor_clear(self.register_PV_name(name))

  def register_PV_name(self,name):
    """Process variable name for EPICS Channel Access"""
    return self.prefix+"registers."+name+".count"

  def variable_property(name,*args,**kwargs):
    """A propery object that is a timing register"""
    def get(self): return self.Variable(self,name,*args,**kwargs)
    return property(get)

  def timing_register(name,*args,**kwargs):
    """A propery object that is a timing register"""
    def get(self): return self.Timing_Register(self,name,*args,**kwargs)
    return property(get)

  def Parameter(name,default_value=0.0):
    """A propery object that is te value if a timing parameter stored
    in the timing system"""
    def get(self): return self.parameter(name,default_value)
    def set(self,value): self.set_parameter(name,value,default_value)
    return property(get,set)

  register_dict = {}

  def add_register(self,register):
    """register: register object"""
    self.register_dict[repr(register)] = register
    self.__dict__[repr(register)] = register # helpful for auto-complete
    
  def register(self,name):
    if name in self.register_dict: return self.register_dict[name]
    else: return self.Register(self,name)
    ##elif name in self.all_register_names: return self.Register(self,name)
    ##else: raise RuntimeError("Is %r a register?" % name)
    
  from collections import MutableMapping
  class Registers(MutableMapping):
    def __init__(self,timing_system): self.timing_system = timing_system
    def __getitem__(self,name): return self.timing_system.register(name)
    def __getattr__(self,name): return self.timing_system.register(name)
    def __len__(self): return len(self.timing_system.all_register_names)
    def __contains__(self,name): return name in self.timing_system.all_register_names
    def __iter__(self):
     for name in self.timing_system.all_register_names: yield name
    def __repr__(self): return "timing_system.registers"
    def __setitem__(self,name,value): pass
    def __delitem__(self,name): pass

  @property
  def registers(self): return self.Registers(self)

  ##@property
  ##def registers(self): return self.register_dict.values()

  @property
  def register_names(self): return self.register_dict.keys()

  @property
  def _all_register_names(self): return self.get_property("registers").split(";")

  @property
  def channel_names(self):
    return ["ch%d" % (i+1) for i in range(0,self.Channel.total_count)]

  def channel(self,i): return self.Channel(self,i)

  class Channels(object):
    Channel = Channel
    def __init__(self,timing_system): self.timing_system = timing_system
    def __getitem__(self,i): return self.Channel(self.timing_system,i)
    def __getattr__(self,mnemonic): return self.Channel(self.timing_system,mnemonic=mnemonic)
    def __len__(self): return self.Channel.total_count
    def __iter__(self):
        for i in range(0,len(self)):
            if i < len(self): yield self[i]

  @property
  def channels(self): return self.Channels(self)

  @property
  def channel_mnemonics(self):
      return [self.channels[i].mnemonic for i in range(len(self.channels))]

  def channel_register_name(self,name):
      register_name = ""
      properties = [p for p in dir(Channel) if type(getattr(self.Channel,p)) == property]
      for channel in self.channels:
          if name.startswith(channel.mnemonic+"_"):
              for prop in properties:
                  if name == channel.mnemonic+"_"+prop:
                      register_name = channel.name+"_"+prop
      return register_name

  variable_dict = {}
  def add_variable(self,variable):
    """register: register object"""
    self.variable_dict[repr(variable)] = variable
    self.__dict__[repr(variable)] = variable # helpful for auto-complete
  def variable(self,name): return self.variable_dict[name]
  @property
  def variables(self): return self.variable_dict.values()
  @property
  def variable_names(self): return self.variable_dict.keys()

  def __getattr__(self,name):
    """A register object"""
    ##warn("__getattr__(%r)" % name)
    # Called when 'x.name' is evaluated.
    # It is only invoked if the attribute wasn't found the usual ways.
    if name.startswith("__") and name.endswith("__"):
      raise AttributeError("attribute %r not found" % name)
    ##debug("Is %r a register?" % name)
    if name in self.channel_names: return self.Channel(self,name=name)
    elif name in self.register_dict: return self.register_dict[name]
    elif name in self.variable_dict: return self.variable_dict[name]
    elif name in self.all_register_names: return self.Register(self,name)
    elif self.channel_register_name(name): return self.Register(self,self.channel_register_name(name))
    elif name in self.channel_mnemonics: return self.channels[self.channel_mnemonics.index(name)]
    else: raise AttributeError("Is %r a register?" % name)
    ##else: return self.parameter(name)

  def register_count(self,name):
    """Reads the content of a register as integer value"""
    from numpy import nan
    name = "registers.%s.count" % name
    value = self.get_property(name)
    try: return int(value)
    except ValueError: return nan

  def set_register_count(self,name,value):
    """Loads an integer value into the register"""
    from numpy import isnan
    if isnan(value): return
    value = "%d" % value
    name = "registers.%s.count" % name
    self.set_property(name,value)

  def register_property(self,name,property_name,default_value=0):
    """Information about the register
    property_name: 'address','bit_offset','bits'"""
    from numpy import nan
    full_name = "registers.%s.%s" % (name,property_name)
    string_value = self.get_property(full_name)
    try: value = type(default_value)(eval(string_value))
    except Exception,msg:
      if type(default_value) != str:
        if string_value != "":
            debug("%s: %r(%r): %s" % (full_name,type(default_value),string_value,msg))
        value = default_value
      else: value = string_value
    if string_value == "": error("%r defaulting to %r" % (full_name,value))
    # Convert from signed to unsigned int
    # (Channel Access does not support unsigend int)
    if type(value) == int: value = unsigned_int(value)
    return value

  def set_register_property(self,name,property_name,value):
    """Information about the register.
    property_name: 'address','bit_offset','bits'"""
    from numpy import isnan
    if isnan(value): return
    value = "%d" % value
    name = "registers.%s.%s" % (name,property_name)
    self.set_property(name,value)

  def parameter(self,name,default_value=0.0):
    """This retreives a calibration constant from non-volatile memory of the
    FPGA."""
    from numpy import nan,inf
    value = self.get_property("parameters."+name)
    try: value = type(default_value)(eval(value))
    except Exception,msg:
      if value != "": debug("timing_system: parameter: %s: %r(%r): %s" %
        (name,type(default_value),value,msg))
      value = default_value
    return value

  def set_parameter(self,name,value,default_value=None):
    """This stores a calibration constant in non-volatile memory in the FPGA."""
    ##debug("set_parameter(%r,%r)" % (name,value))
    property_name = "parameters.%s" % name
    from same import same
    str_value = repr(value)
    if default_value is not None and same(value,default_value): str_value = "" # deletes property
    self.set_property(property_name,str_value)

  @property
  def parameter_names(self): return self.get_property("parameters").split(";")

  @property
  def parameters(self): return self.Parameters(self)

  def get_property(self,name):
    """Retreive a register content ot parameter, using Channel Access
    return value: string"""
    PV_name = self.prefix+name
    ##from CA import caget
    ##value = caget(PV_name)
    from CA_cached import caget_cached 
    value = caget_cached(PV_name)
    if value is None:
        debug("Failed to get PV %r" % PV_name)
        value = ""
    # Convert from signed to unsigned int (Channel Access does not support unsigend int)
    if type(value) == int and value < 0: value = value+0x100000000
    if type(value) != str: value = str(value)
    ##debug("%r: returning %.80r" % (name,value))
    return value

  def set_property(self,name,value):
    """Modify a register content ot parameter, using Channel Access
    value: string"""
    from CA import caput
    ##debug("caput(%r,%r,wait=True)" % (self.prefix+name,value))
    caput(self.prefix+name,value,wait=True)


  # Clock periods
  def get_clock_period(self):
    """Clock period in s (ca. 2.8 ns)"""
    if self.clk_src.count == 29: return self.clock_period_internal
    else: return self.clock_period_external
  def set_clock_period(self,value):
    if self.clk_src.count == 29: self.clock_period_internal = value
    else: self.clock_period_external = value
  clock_period = property(get_clock_period,set_clock_period)

  clock_period_external = Parameter("clock_period_external",1/351933984.)
  clock_period_internal = Parameter("clock_period_internal",1/350000000.)

  def get_bct(self):
    """Bunch clock period in s (ca. 2.8 ns)"""
    if self.clk_on.count == 0: T = self.clock_period
    else: T = self.clock_period/self.clock_multiplier*self.clock_divider
    return T
  def set_bct(self,value):
    if self.clk_on.count == 0: self.clock_period = value
    else: self.clock_period = value*self.clock_multiplier/self.clock_divider
  bct = property(get_bct,set_bct)

  def get_clock_divider(self):
    """Clock scale factor"""
    value = self.clk_div.count+1
    return value
  def set_clock_divider(self,value):
    from numpy import rint
    value = int(rint(value))
    if 1 <= value <= 32: self.clk_div.count = value-1
    else: warn("%r must be in range 1 to 32.")
  clock_divider = property(get_clock_divider,set_clock_divider)

  def get_clock_multiplier(self):
    """Clock scale factor"""
    value = (self.clk_mul.count+1)/2
    return value
  def set_clock_multiplier(self,value):
    from numpy import rint
    value = int(rint(value))
    if 1 <= value <= 32: self.clk_mul.count = 2*value-1
    else: warn("%r must be in range 1 to 32.")
  clock_multiplier = property(get_clock_multiplier,set_clock_multiplier)

  def get_P0t(self):
    """Single-bunch clock period (ca. 3.6us)"""
    from numpy import nan
    try: value = self.hsct/self.p0_div_1kHz.count
    except ZeroDivisionError: value = nan
    return value
  def set_P0t(self,value):
    from numpy import rint
    try: self.p0_div_1kHz.count = rint(self.hsct/value)
    except ZeroDivisionError: pass
  P0t = property(get_P0t,set_P0t)

  def get_hsct(self):
    """High-speed chopper rotation period (ca. 1 ms)"""
    return self.bct*4*self.clk_88Hz_div_1kHz.count
  def set_hsct(self,value):
    from numpy import rint
    try: self.clk_88Hz_div_1kHz.count = rint(value/(self.bct*4))
    except ZeroDivisionError: pass
  hsct = property(get_hsct,set_hsct)

  def get_hlct(self):
    """X-ray pulse repetiton period.
    Selected by the heatload chopper.
    Depends on the nummber of slots in the X-ray beam path:
    period = hlct / 12 * number of slots
    (ca 12 ms with one slot) Number of slots: 1,4,12"""
    return self.hsct*self.hlc_div 
  def set_hlct(self,value):
    from numpy import rint
    try: self.hlc_div = rint(value/self.hsct) 
    except ZeroDivisionError: pass
  hlct = property(get_hlct,set_hlct)

  hlc_div = Parameter("hlc_div",12)

  def get_hlc_nslots(self):
    """Number of slots of the heatload chopper in the X-ray beam"""
    from numpy import rint,nan
    try: nslots = rint(12./self.hlc_div)
    except ZeroDivisionError: nslots = nan
    return nslots
  def set_hlc_nslots(self,nslots):
    from numpy import rint
    try: self.hlc_div = rint(12./nslots)
    except ZeroDivisionError: pass
  hlc_nslots = property(get_hlc_nslots,set_hlc_nslots)

  def get_nslt(self):
    """ns laser flash lamp period (ca. 100 ms)"""
    return self.hsct*self.nsl_div
  def set_nslt(self,value):
    from numpy import rint
    self.nsl_div = rint(value/self.hsct)
  nslt = property(get_nslt,set_nslt)

  nsl_div = Parameter("nsl_div",96)
  
  clk_shift_stepsize = Parameter("clk_shift_stepsize",8.594e-12)

  def reset_dcm(self):
    """Reinitialize digital clock mananger"""
    from time import sleep
    self.clk_shift_reset.count = 1 
    sleep(0.2)
    self.clk_shift_reset.count = 0

  delay = variable_property("delay",stepsize=1e-12) # Ps laser to X-ray delay
  lxd = ps_lxd = delay # For backward compatibility
  laser_on = Parameter("laser_on",False) # fire ps and ns lasers?
  laseron = laser_on # For backward compatibility
  waitt   = variable_property("waitt",stepsize="hlct")
  npulses = Parameter("npulses",1) # pulses per burst
  burst_waitt = variable_property("burst_waitt",stepsize="hlct") 
  burst_delay = variable_property("burst_delay",stepsize="hlct")
  bursts_per_image = Parameter("bursts_per_image",1)
  sequence = Parameter("sequence","") # more flexible replacement for bursts_per_image
  acquisition_sequence = Parameter("acquisition_sequence","") # used when acquiring data
  temp_inc_on = Parameter("temp_inc_on",False)  
  image_number_inc_on = Parameter("image_number_inc_on",False)
  pass_number_inc_on = Parameter("pass_number_inc_on",False)
  
  # For sample translation stage
  translate_mode = Parameter("translate_mode","")
  transc = Parameter("transc",0)
  pump_on = Parameter("pump_on",False)

  transon = variable_property("trans.on",stepsize=1) # For backward compatibility
  mson    = variable_property("ms.on",   stepsize=1) # For backward compatibility
  xoscton = variable_property("xosct.on",stepsize=1) # For backward compatibility

  # Ps oscillator coarse delay [0-11.2 ns, step 2.8 ns]
  psod1 = timing_register("psod1",stepsize="bct",max_count=4)
  # Ps oscillator fine delay [0-2.8ns, step 9 ps]
  psod2 = timing_register("psod2",stepsize="clk_shift_stepsize")
  # Ps oscillator coarse delay [0-7.1 ns, step 7.1 ns]
  psod3 = timing_register("psod3",stepsize="bct*2.5",max_count=1)

  # P0 fine tune delay [0-8.4ns,step 2.8ns]
  p0fd = timing_register("p0fd",stepsize="bct")
  # P0 delay [0-5.8us,step 11ns]
  p0d = timing_register("p0d",stepsize="bct*4")

  # P0 actual fine delay [0-8.4ns,step 2.8ns,read-only]
  p0afd = timing_register("p0afd",stepsize="bct")
  # P0 actual delay [0-3.6us,step 11ns,read-only]
  p0ad = timing_register("p0ad",stepsize="bct*4")

  # P0 fine tune delay [0-8.4ns,step 2.8ns]
  p0fd2 = timing_register("p0fd2",stepsize="bct")
  # P0 delay 2 [0-5.8us,step 11ns]
  p0d2 = timing_register("p0d2",stepsize="bct*4")

  def object_property(type,*args,**kwargs):
    """Define a property corresponding to a timing register"""
    ##info("object_property(%r,%r)" % (args,kwargs))
    def get(self): return type(self,*args,**kwargs)
    return property(get)

  class P0_shift(Timing_Register):
    def __init__(self,timing_system,*args,**kwargs):
        timing_system.Timing_Register.__init__(self,timing_system,*args,**kwargs)
    def get_count(self):
      count = self.timing_system.p0d2.count*4 + (self.timing_system.p0fd2.count + 2) % 4
      return count
    def set_count(self,count):
      from numpy import rint
      count = int(rint(count))
      self.timing_system.p0d2.count = count / 4
      self.timing_system.p0fd2.count = (count - 2) % 4
    count = property(get_count,set_count)

    max_count = 1296-1

  p0_shift = object_property(P0_shift,"p0_shift",stepsize="bct")

  # Ps laser delay 1 [0-20.47ns,step 10ps] (phase of seed beam)
  psd1 = timing_register("psd1",stepsize=10.048e-12)
  # The "psd1.offset" parameter needs to be determined empirically and changes with
  # the length of the cables that route the clock and trigger signals 
  # from the FPGA to the Lok-to-Clock and Spitfire TDG.
  # tweak psd1.offset on both directions, until the amplifier
  # output pulse timing toggles between two delays, spaced by 14.2 ns, with equal
  # probability. Then set psd1.offset to the midpoint of the two values.
  #psd1.offset = 1.2630336e-08 # Schotte, Mar 3, 2015

  # Heatload choppernominal delay 
  hlcnd = timing_register("hlcnd",stepsize="bct*4")
  # This offset determines when the heatload chopper opening window is centered
  # on the high speed chopper opening window.
  # At 82.3 Hz the opening window should be centered on the 12th high speed
  # chopper transmission after the FPGA t=0.
  #hlcnd.offset = -0.0056959639810284885 # Schotte, 4 Mar 2015, 82-Hz mode
   
  # Heatload chopper transient delay
  hlctd = timing_register("hlctd",stepsize="bct*4")
  # Heatload chopper actual delay, read only [0-24ms,step 12ns]
  hlcad = timing_register("hlcad",stepsize="bct*4")

  # ChemMat chopper nominal delay 
  cmcnd = timing_register("cmcnd",stepsize="bct*4")
  # ChemMat chopper transient delay
  cmctd = timing_register("cmctd",stepsize="bct*4")
  # ChemMat chopper actual delay, read only [0-24ms,step 12ns]
  cmcad = timing_register("cmcad",stepsize="bct*4")

  configuration = Parameter("configuration","BioCARS")

  def save_configuration(self):
    self.Configuration(self.configuration).save()
  
  def load_configuration(self):
    self.Configuration(self.configuration).load()

  @property
  def configurations(self): return configuration_names()

  class CMCD(object):
    """ChemMat chopper delay (=phase)"""
    def __init__(self,timing_system):
      self.timing_system = timing_system

    def get_command_value(self):
      return self.timing_system.cmcnd.value
    def set_command_value(self,value):
      self.timing_system.cmcnd.value = value
    command_value = property(get_command_value,set_command_value)

    def get_value(self):
      return self.timing_system.cmcad.value
    set_value = set_command_value
    value = property(get_value,set_value)

    @property
    def moving(self): return not self.settled

    @property
    def settled(self):
      settled = abs(self.value - self.command_value) <= self.tolerance
      return settled

    default_tolerance = "200e-9"
    def get_tolerance(self):
      return self.timing_system.parameter("cmc.tolerance",self.default_tolerance)
    def set_tolerance(self,value):
      self.timing_system.set_parameter("cmc.tolerance",value,self.default_tolerance)
    tolerance = property(get_tolerance)

  @property
  def cmcd(self):
    """ChemMat chopper delay (=phase)"""
    return self.CMCD(self)

  high_speed_chopper = Parameter("chopper","ChemMat")
  high_speed_chopper_choices = "Julich","ChemMat"

  @property
  def high_speed_chopper_phase(self):
    register = self.hsc.delay
    if self.high_speed_chopper == "Julich": register = self.hsc.delay
    if self.high_speed_chopper == "ChemMat": register = self.cmcnd
    return register

  cache = 0 # for backwards compatbility
  cache_timeout = 0 # for backwards compatbility
  use_CA = True # for backwards compatbility


timing_system = TimingSystem()

parameters = Parameters(timing_system)


def equal(a,b):
  """Do a and b have the same value?"""
  return repr(a) == repr(b) 
  
def execute(command,locals=None,globals=None):
  from numpy import nan,inf
  debug("timing_system: %r: %s" % (self.name,command))
  try: exec(command,locals,globals)
  except Exception,msg: error("timing_system: %r failed:%s" % (command,msg))

def configuration_names():
  """All saved settings"""
  from DB import dbdir
  names = dbdir("timing_system_configurations")
  return names

def configurations():
  """All saved settings"""
  configurations = [Configuration(name) for name in configuration_names()]
  return configurations 


def round_next (x,step):
  """Rounds x up or down to the next multiple of step."""
  if step == 0: return x
  return round(x/step)*step

def toint(x):
  """Try to convert x to an integer number without raising an exception."""
  try: return int(x)
  except: return x

def unsigned_int(value):
  """Convert from signed to unsigned int
  (Channel Access does not support unsigend int)"""
  if type(value) == int and value < 0: value = value+0x100000000
  return value

from timing_sequence import timing_sequencer


def update_channels():
    """Convert parametert from format 'channel(0).special' to 'ch1.special'"""
    def default_value(obj): return getattr(getattr(obj,"fget",None),"default_value",None)
    properties = [n for n in dir(Channel) if default_value(getattr(Channel,n)) is not None]
    default_values = [repr(default_value(getattr(Channel,n))) for n in properties]
    for i in range(0,24):
        for prop,default_value in zip(properties,default_values):
            name = "parameters.channel(%d).%s" % (i,prop)
            value = timing_system.get_property(name)
            if value and value != default_value:
                new_name = "parameters.ch%d.%s" % (i+1,prop)
                new_value = timing_system.get_property(new_name)
                if new_value != value:
                    info("%s=%s" % (new_name,value))
                    timing_system.set_property(new_name,value)
            if value:
                    none = ""
                    info("%s=%s" % (name,none))
                    timing_system.set_property(name,none)


if __name__ == "__main__": # for testing
    from pdb import pm # for debugging
    ##from time import sleep,time
    ##from CA import caget,caput,cainfo,camonitor,camonitors
    ##import logging
    ##logging.basicConfig(level=logging.DEBUG,
    ##    format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    ##)
    print('timing_system.prefix = %r' % timing_system.prefix)
    print('timing_system.prefixes = %r' % timing_system.prefixes)
    print('timing_system.ip_address = %r' % timing_system.ip_address)
    print('')
    print('timing_system.configuration = %r' % timing_system.configuration)
    print('timing_system.configurations = %r' % timing_system.configurations)
    print('timing_system.save_configuration()')
    print('timing_system.load_configuration()')
    print('')
