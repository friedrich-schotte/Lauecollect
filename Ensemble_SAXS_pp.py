"""SAXS/WAXS data collection setup for Aerotech Ensemble motion controller.
"Fly-thru" and "Setting" mode are implemented using "piano player" mode
for the FPGA.
"Exotic mode" implements an optimized sample translation for multishot laser
pump X-ray probe data aquisition.
Author: Friedrich Schotte
Date created: 2015-05-27
Date last modified: 2019-04-26
"""
import numpy; numpy.seterr(invalid="ignore",divide="ignore") # Turn off IEEE-754 warnings
from logging import debug,info,warn,error
from traceback import format_exc
from time import time

__version__ = "4.20" # sequence.generated_data
genenerator_version = "4.19.1" 

class Sequence(object):
    def __init__(self,delay=None,**kwargs):
        from collections import OrderedDict
        self.__parameters__ = OrderedDict()
        if delay is not None: self.delay = delay
        for name in kwargs: self.setattr(name,kwargs[name])
        ##self.set_defaults()

    def set_defaults(self):
        for name in self.properties:
            if not name in self.__parameters__:
                self.__parameters__[name] = Ensemble_SAXS.get_default(name)

    def update(self,sequence):
        """Copy parameters from another Sequence object
        sequence: another Sequence object"""
        self.__parameters__.update(sequence.__parameters__)

    def __getattr__(self,name):
        """A property"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute wasn't found the usual ways.
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("Sequence object has no attribute %r" % name)
        if name in self.__parameters__: value = self.__parameters__[name]
        else: value = Ensemble_SAXS.get_default(name)
        return value

    def __setattr__(self,name,value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self,name,value)
        try:
            object.__getattribute__(self,name)
            object.__setattr__(self,name,value)
        except AttributeError: self.setattr(name,value)
    
    def setattr(self,name,value):
        ##self.__parameters__[name] = value
        parameters = dict([(name,value)])
        parameters = self.normalize(parameters)
        self.__parameters__.update(parameters)

    @staticmethod
    def normalize(par):
        """translate parameters dictionary"""
        from collections import OrderedDict
        parameters = OrderedDict()
        for name in par:
            value = par[name]
            if name == "delay":
                from numpy import isnan
                # Philip Anfinrud, 2018-10-04: nan means not save image
                if isnan(value): parameters["acquire"] = 0
                # Philip Anfinrud, 2018-10-01: integer value means nominal delay
                # for logging purposes in multiples of 1 ms clock ticks.
                elif value == int(value) and  value >= 48:
                    parameters["nom_delay"] = value*Sequence.tick_period()
                else: parameters["delay"] = value
            elif name in ["S","SEQ","enable"]:
                # Philip Anfinrud, 2018-10-01: "Sequence Configuration"
                # 1010: xdet_on=1, laser_on=0, ms_on=0, pump_on=0 [dump_on not specified]
                if len(value) >0: parameters["xdet_on"]  = int(value[0]) 
                if len(value) >1: parameters["laser_on"] = int(value[1]) 
                if len(value) >2: parameters["ms_on"]    = int(value[2]) 
                if len(value) >3: parameters["pump_on"]  = int(value[3])
                if len(value) >4: parameters["dump_on"]  = int(value[4])
            # Philip Anfinrud, 2018-10-01...2018-10-05: "Player-Piano Modes"
            elif name in ["PLP","PP","pp"]: parameters["mode"] = value
            # Philip Anfinrud, 2018-09-28: circulate liquid sample
            elif name in ["circulate"]: parameters["pump_on"] = value
            # Philip Anfinrud, 2018-10-04...2018-10-05: short for of "acquire"
            elif name in ["acq","image"]: parameters["acquire"] = value
            elif name in ["laser","pump"]: parameters["laser_on"] = value
            elif name in ["probe","xray","xray_on"]: parameters["ms_on"] = value
            elif name in ["xdet"]: parameters["xdet_on"] = value
            else: parameters[name] = value
        return parameters

    @staticmethod
    def tick_period():
        from timing_system import timing_system
        ##T = timing_system.hsct
        T = 0.0010126898793523787
        return T
            
    @property
    def values(self):
        """Values of all parameters as tuple"""
        return tuple(self.__parameters__.values())

    @property
    def packet_description(self):
        """Binary data and descriptive string as tuple"""
        packet,description = Ensemble_SAXS.sequencer_packet(self)
        return packet,description

    @property
    def register_counts(self):
        """Register objects and count arrays as tuple"""
        registers,counts = Ensemble_SAXS.register_counts(self)
        return registers,counts

    @property
    def description(self):
        """The parameters for generating a packet represented as text string."""
        description = ""
        description += "delay=%.3g,"          % self.delay
        description += "nom_delay=%.3g,"      % self.nom_delay
        description += "laser_on=%r,"         % self.laser_on
        description += "ms_on=%r,"            % self.ms_on
        description += "pump_on=%r,"          % self.pump_on
        description += "xdet_on=%r,"          % self.xdet_on
        description += "pass_number=%r,"      % self.pass_number
        description += "image_number_inc=%r," % self.image_number_inc
        description += "pass_number_inc=%r,"  % self.pass_number_inc
        description += "acquiring=%r,"        % self.acquiring   
        description += "mode_number=%r,"      % self.mode_number 
        description += "N=%r,"                % self.N 
        description += "period=%r,"           % self.period 
        description += "transd=%r,"           % self.transd 
        description += "dt=%r,"               % self.dt 
        description += "t0=%r,"               % self.t0 
        description += "z=%r,"                % self.z 
        
        transc = Ensemble_SAXS.trigger_code_of(
            self.mode_number,
            self.ms_on,
            self.following_sequence.pump_on,
            self.following_sequence.delay,
            self.z,
        )
        description += "transc=%r," % transc
        
        description += "preceeding_sequence.delay=%.3g,"  % self.preceeding_sequence.delay

        description += self.parameter_description
        return description

    descriptor = description

    @property
    def parameter_description(self):
        if hasattr(self.sequences,"parameter_description"):
            description = self.sequences.parameter_description
        else:
            if not hasattr(self,"__parameter_description__"):
                self.__parameter_description__ = parameter_description()
            return self.__parameter_description__
        return description
    
    @property
    def id(self):
        """Binary data and descriptive string as tuple"""
        from timing_sequence import hash
        id = hash(self.description)
        return id

    @property
    def packet_representation(self):
        """Sequence data as formatted text"""
        from timing_sequence import packet_representation
        return packet_representation(self.data)

    @property
    def is_cached(self):
        """Packet is generated"""
        is_cached = len(self.cached_data) > 0
        return is_cached

    def get_data(self):
        """Binary sequence data"""
        data = self.cached_data
        if len(data) == 0:
            data = self.generated_data
            self.cached_data = data
        return data
    data = property(get_data)
            
    packet = packet_data = data

    def get_cached_data(self):
        from timing_sequencer import timing_sequencer
        data = timing_sequencer.cache_get(self.description)
        return data
    def set_cached_data(self,data):
        from timing_sequencer import timing_sequencer
        timing_sequencer.cache_set(self.description,data)
    cached_data = property(get_cached_data,set_cached_data)

    @property
    def generated_data(self):
        from timing_sequencer import sequencer_packet
        registers,counts = self.register_counts
        data = sequencer_packet(registers,counts,self.descriptor)
        return data

    def __repr__(self):
        p = Sequence.ordered_parameters(self.__parameters__)
        s = "Sequence("+", ".join(["%s=%r" % (key,p[key]) for key in p])+")"
        return s

    @staticmethod
    def ordered_parameters(parameters):
        from collections import OrderedDict
        ordered_parameters = OrderedDict()
        for name in Sequence.order:
            if name in parameters: ordered_parameters[name] = parameters[name]
        for name in parameters:
            if not name in Sequence.order: ordered_parameters[name] = parameters[name]
        return ordered_parameters        

    order = [
        "delay",
        "nom_delay",
        "xdet_on",
        "laser_on",
        "ms_on",
        "pump_on",
        "image_number_inc",
        "pass_number_inc",
        "acquiring",
    ]

    properties = [
        "delay",
        ##"nom_delay",
        "xdet_on",
        "laser_on",
        "ms_on",
        "pump_on",
        "image_number_inc",
        "pass_number_inc",
        "acquiring",  
        "pass_number",
        "mode_number", 
        "N",
        "period", 
        "transd",
        "dt",
        "t0",
        "z",
    ]

    @property
    def nom_delay(self):
        from numpy import isnan
        if "nom_delay" in self.__parameters__ and not isnan(self.__parameters__["nom_delay"]):
            return self.__parameters__["nom_delay"]
        else: return self.delay

    def get_sequences(self):
        """Which list of sequences is this sequence part of?"""
        return getattr(self,"__sequences__",[self])
    def set_sequences(self,value): self.__sequences__ = value
    sequences = property(get_sequences,set_sequences)

    def get_count(self):
        """At which place in the list of sequences it belongs to is this
        sequence?"""
        return getattr(self,"__count__",0)
    def set_count(self,value): self.__count__ = value
    count = property(get_count,set_count)

    @property
    def following_sequence(self):
        return self.sequences[(self.count+1) % len(self.sequences)]

    @property
    def preceeding_sequence(self):
        return self.sequences[(self.count-1) % len(self.sequences)]

s = seq = sequence = Sequence # shorthand notation
    

class Sequences(object):
    def __init__(self,delay=None,sequences=None,**kwargs):
        from collections import OrderedDict
        self.__parameters__ = OrderedDict()
        self.set_defaults()

        acquiring = "acquiring" in kwargs and kwargs["acquiring"]
        params = self.default_parameters(acquiring)
        for name in params: self.setattr(name,params[name])
        if delay is not None: self.setattr("delay",delay)
        for name in kwargs: self.setattr(name,kwargs[name])

        if sequences is not None: self.set_sequences(sequences)

        self.update_parameter_description()
        
    def set_defaults(self):
        for name in Sequence.properties:
            if not name in self.__parameters__:
                self.__parameters__[name] = Ensemble_SAXS.get_default(name)

    def set_sequences(self,sequences):
        keys = self.common_keys(sequences)
        from numpy import nan
        for key in keys:
            self.__parameters__[key] = [nan]*len(sequences)
        for i,sequence in enumerate(sequences):
            for key in keys:
                if key in sequence.__parameters__:
                    self.__parameters__[key][i] = sequence.__parameters__[key]

    @staticmethod
    def common_keys(sequences):
        keys = set()
        for sequence in sequences: keys |= set(sequence.__parameters__.keys())
        return keys

    @staticmethod
    def default_parameters(acquiring=False):
        """Dictionary"""
        from expand_sequence import expand
        if not acquiring: parameter_string = Ensemble_SAXS.sequence
        else: parameter_string = Ensemble_SAXS.acquisition_sequence
        parameter_string = expand(parameter_string)
        parameters = {}
        if parameter_string:
            try: parameters = dict(eval(parameter_string))
            except Exception,msg: warn("%s: %s" % (parameter_string,msg))
        return parameters

    def __getattr__(self,name):
        """A property"""
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("Sequences object has no attribute %r" % name)
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute wasn't found the usual ways.
        if name in self.__parameters__: value = self.__parameters__[name]
        else: value = Ensemble_SAXS.get_default(name)
        return value

    def __setattr__(self,name,value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self,name,value)
        try:
            object.__getattribute__(self,name)
            object.__setattr__(self,name,value)
        except AttributeError: self.setattr(name,value)
    
    def setattr(self,name,value):
        parameters = dict([(name,value)])
        parameters = self.normalize(parameters)
        self.__parameters__.update(parameters)

    @staticmethod
    def normalize(par):
        """translate parameters dictionary"""
        from collections import OrderedDict
        parameters = OrderedDict()
        for name in par:
            value = par[name]
            if not isinstance(value,str) and hasattr(value,"__len__"):
                for v in value:
                    p = Sequence.normalize(dict([(name,v)]))
                    for n in p: parameters[n] = []
                for v in value:
                    p = Sequence.normalize(dict([(name,v)]))
                    for n in p: parameters[n] += [p[n]]
            else:
                p = Sequence.normalize(dict([(name,value)]))
                for n in p: parameters[n] = p[n]
        return parameters
            
    def __repr__(self):
        p = Sequence.ordered_parameters(self.__parameters__)
        s = "Sequences("+", ".join(["%s=%r" % (key,p[key]) for key in p])+")"
        return s

    def __len__(self): return self.count

    def __getitem__(self,item):
        if type(item) == slice:
            start = item.start if item.start is not None else 0
            stop  = item.stop  if item.stop  is not None else len(self)
            step  = item.step  if item.step  is not None else 1
            value = [self.sequence(i) for i in range(start,stop,step)]
        else: value = self.sequence(item)
        return value

    @property
    def sequences(self):
        """Expand to list of Sequence objects"""
        sequences = [self.sequence(count) for count in range(0,self.count)]
        return sequences

    def sequence(self,count):
        """Sequence object number *count*
        Not taking into account order of collection"""
        from collections import OrderedDict
        parameters = OrderedDict()
        for key in self.__parameters__:
            value = self.__parameters__[key]
            if not isinstance(value,str) and hasattr(value,"__len__"):
                parameters[key] = value[count % len(value)]
            else: parameters[key] = value
        sequence = Sequence()
        for key in parameters: setattr(sequence,key,parameters[key])
        sequence.count = count
        sequence.sequences = self
        return sequence

    @property
    def count(self):
        """How many sequences are there?"""
        N = 1
        parameters = self.__parameters__
        for key in parameters:
            value = parameters[key]
            if not isinstance(value,str) and hasattr(value,"__len__"):
                N = max(N,len(value))
        return N

    def update_parameter_description(self):
        if not hasattr(self,"__parameter_description__"):
            self.__parameter_description__ = parameter_description()

    @property
    def parameter_description(self):
        self.update_parameter_description()
        return self.__parameter_description__

S = sequences = Sequences # shorthand notation


def parameter_description():
    """The parameters for generating a packet represented as text string."""
    description = ""
    # Calibration constants and parameters
    from timing_system import timing_system
    description += "high_speed_chopper_phase=%.12f,"        % timing_system.high_speed_chopper_phase.value
    description += "high_speed_chopper_phase.offset=%.12f," % timing_system.high_speed_chopper_phase.offset
    description += "hsc.delay.offset=%.12f,"                % timing_system.hsc.delay.offset

    # Channel configuration-based parameters
    for i_channel in range(0,len(timing_system.channels)):
        channel = timing_system.channels[i_channel]
        if channel.PP_enabled:
            if channel.special == "pso": 
                description += "psod3.offset=%.12f,"   % (timing_system.psod3.offset)
            elif channel.special == "trans": 
                description += "%s.pulse_length=%.4g," % (channel.name,channel.pulse_length)
            elif channel.special == "nsf": 
                description += "%s.offset=%.12f,"      % (channel.name,channel.offset)
            else: description += Ensemble_SAXS.channel_description(i_channel)

    description += "generator=%r," % "Ensemble_SAXS"
    description += "generator_version=%r," % genenerator_version
    import timing_sequence
    description += "timing_sequence_version=%r," % timing_sequence.__version__

    return description


class EnsembleSAXS(object):
    """SAXS/WAXS data collection with linear stage, controlled by Aerotech Ensemble"""
    name = "Ensemble_SAXS"
    from timing_sequence import timing_sequencer

    def sequence_property(name):
        def get(self):
            return self.current_sequence_property(name,self.default_values[name])
        def set(self,value):
            self.set_command_value(name,value)
            self.update_later = True
        return property(get,set)

    mode_number = sequence_property("mode_number")
    # Packet length in 987-Hz cycles
    period = sequence_property("period")
    # Number of X-ray pulses
    N = sequence_property("N")
    # X-ray pulse repetition period, in 987-Hz cycles
    dt = sequence_property("dt")
    # Trigger rising edge to first X-ray pulse, in 987-Hz cycles
    t0 = sequence_property("t0")
    # Sample translation trigger delay
    transd = sequence_property("transd")
    # Laser focusing optics translation stage setting to compensate
    # moving sample lateral offset as function of pump-probe delay,,
    # when collecting in "Flythru" mode.
    z = sequence_property("z")

    default_values = {
        "mode_number": 0,
        "period": 264,
        "N": 40,
        "dt": 4,
        "t0": 100,
        "transd": 17,
        "z": 1,
    }

    def command_value(self,name):
        from timing_system import timing_system
        value = timing_system.parameter(name,self.default_values[name])
        ##debug("%s=%r" % (name,value))
        return value

    def set_command_value(self,name,value):
        debug("%s=%r" % (name,value))
        from timing_system import timing_system
        timing_system.set_parameter(name,value)

    from thread_property_2 import thread_property
    @thread_property
    def update_later(self):
        from time import sleep
        sleep(0.1)
        self.update()
        
    def get_default(self,name):
        """Default value for the  parameter given by name
        name: "delay","laser_on","ms_on","pump_on"
        "image_number_inc","pass_number_inc",
        "xdet_on"
        """
        name = self.standard_name(name)
        if name in self.default_values: value = self.command_value(name)
        else: value = self.timing_sequencer.get_default(name)
        return value
    def set_default(self,name,value):
        """Default value for the  parameter given by name
        name: "delay","laser_on","ms_on","pump_on",
        "image_number_inc","pass_number_inc"
        """
        name = self.standard_name(name)
        if name in self.default_values: value = self.set_command_value(name,value)
        else: self.timing_sequencer.set_default(name,value,update=False)

    def standard_name(self,name):
        """'mode' -> 'translate_mode'"""
        ##if name == "mode": name = "translate_mode"
        return name
        
    from persistent_property import persistent_property
    buffer_size = persistent_property("buffer_size",256*1024)

    def get_delay(self):
        """Current Laser pump X-ray probe time delay"""
        return self.current_sequence_property("delay")
    def set_delay(self,delay):
        self.set_default("delay",delay)
        self.set_default_sequences()        
    delay = property(get_delay,set_delay)

    def get_nom_delay(self):
        """Current Laser pump X-ray probe time delay"""
        return self.current_sequence_property("nom_delay")
    def set_nom_delay(self,delay): pass
    nom_delay = property(get_nom_delay,set_nom_delay)

    def get_mode(self):
        """Current mode name as string"""
        mode = self.timing_modes.value
        return mode
    def set_mode(self,value):
        self.timing_modes.value = value
    mode = property(get_mode,set_mode)

    @property
    def modes(self):
        """Possible operation modes as list of strings"""
        return self.timing_modes.values

    @property
    def timing_modes(self):
        from configuration import configuration
        return configuration("timing_modes",locals=locals(),globals=globals())

    def get_sequence(self):
        """Sequence mode description (for idle mode)"""
        return self.get_default("sequence")
    def set_sequence(self,value):
        self.set_default("sequence",value)
        self.set_default_sequences()        
    sequence = property(get_sequence,set_sequence)

    def get_acquisition_sequence(self):
        """Sequence mode description for acquisition mode"""
        return self.get_default("acquisition_sequence")
    def set_acquisition_sequence(self,value):
        self.set_default("acquisition_sequence",value)
        self.set_default_sequences()        
    acquisition_sequence = property(get_acquisition_sequence,set_acquisition_sequence)

    def get_trigger_period_in_1kHz_cycles(self):
        """Sample translation trigger period in units of the 1-kHz (997 Hz) clock"""
        return self.current_sequence_property("period",dtype=int)
    trigger_period_in_1kHz_cycles = property(get_trigger_period_in_1kHz_cycles)

    def get_trigger_enabled(self):
        """Is a trigger signal being sent by the FPGA to the Ensemble
        Controller? True or False"""
        return self.queue_length > 0 or self.timing_sequencer.enabled
    trigger_enabled = property(get_trigger_enabled)

    def get_laser_on(self):
        """Is the laser trigger enabled?"""
        return self.current_sequence_property("laser_on",dtype=bool)
    def set_laser_on(self,laser_on):
        self.set_default("laser_on",laser_on)
        self.set_default_sequences()        
    laser_on = property(get_laser_on,set_laser_on)
    laseron = laser_on # for backward compatibility

    def get_ms_on(self):
        """Is the X-ray ms shutter operated while the stage is moving?"""
        return self.current_sequence_property("ms_on",dtype=bool)
    def set_ms_on(self,ms_on):
        self.set_default("ms_on",ms_on)
        self.set_default_sequences()        
    ms_on = property(get_ms_on,set_ms_on)
    xray_shutter_enabled = xray_on = mson = ms_on # for backward compatibility

    def get_pump_on(self):
        """Is circulating pump operated while the stage is moving?"""
        return self.current_sequence_property("pump_on",dtype=bool)
    def set_pump_on(self,pump_on):
        self.set_default("pump_on",pump_on)
        self.set_default_sequences()        
    pump_on = property(get_pump_on,set_pump_on)
    pumpA_enabled = pumpon = pump_on # for backward compatibility

    def get_xdet_on(self):
        """Is the X-ray detector being triggered?"""
        return self.current_sequence_property("xdet_on",dtype=bool)
    def set_xdet_on(self,value):
        from timing_system import timing_system
        self.set_default("xdet_on",value)
        self.set_default_sequences()        
    xdet_on = property(get_xdet_on,set_xdet_on)

    def get_image_number_inc(self):
        """Is Pump A operated while the stage is moving?"""
        return self.current_sequence_property("image_number_inc",dtype=bool)
    def set_image_number_inc(self,value):
        self.set_default("image_number_inc",value)
        self.set_default_sequences()        
    image_number_inc = property(get_image_number_inc,set_image_number_inc)

    def get_pass_number_inc(self):
        """Is Pump A operated while the stage is moving?"""
        return self.current_sequence_property("pass_number_inc",dtype=bool)
    def set_pass_number_inc(self,value):
        self.set_default("pass_number_inc",value)
        self.set_default_sequences()        
    pass_number_inc = property(get_pass_number_inc,set_pass_number_inc)

    def get_trigger_code(self):
        """transation program code:
        8-bit integer number transmitted to the Aerobasic program
        running on the Ensemble controller by the FPGA timing system
        as serial bit sequence following the trigger pulse."""
        return self.current_sequence_property("transc",dtype=int)
    def set_trigger_code(self,value): pass
    trigger_code = property(get_trigger_code,set_trigger_code)
    transc = trigger_code

    @property
    def generator(self):
        """Sequence generator Python module name"""
        return self.current_sequence_property("generator","")

    @property
    def generator_version(self):
        """Sequence generator Python module version number"""
        return self.current_sequence_property("generator_version","")

    from numpy import nan
    def current_sequence_property(self,name,default_value=nan,dtype=None):
        """
        name: e.g. 'mode','delay','laseron','count'
        dtype: data type
        """
        descriptor = self.timing_sequencer.descriptor
        if dtype is not None: default_value = dtype()
        if len(descriptor) == 0: return default_value
        return self.property_value(descriptor,name,default_value,dtype)

    def property_value(self,property_string,name,default_value=nan,dtype=None):
        """Extract a value from a comma-separated list
        property_string: comma separated list
        e.g. 'mode=Stepping-48,delay=0.0316,laseron=True,count=6'
        name: e.g. 'mode','delay','laseron','count'
        default_value: e.g. ''
        dtype: data type
        """
        if dtype is None: dtype = type(default_value)
        for record in property_string.split(","):
            parts = record.split("=")
            key = parts[0]
            if key != name: continue
            if len(parts) < 2: return default_value
            value = parts[1]
            try: return dtype(eval(value))
            except: return default_value
        return default_value

    def get_configured(self):
        """Configure the FPGA for 'Player Piano' mode at 1 kHz."""
        from timing_system import timing_system,timing_sequencer
        ##if not timing_system.inton.count      == 1:  return False
        if not timing_system.IPIRE.count      == 1:  return False
        if not timing_system.DEVICE_GIE.count == 1:  return False
        if not timing_system.IPIER.count      == 1:  return False
        if not timing_sequencer.buffer_size   == self.buffer_size: return False
        return True
    def set_configured(self,value):
        """Configure the FPGA for 'Player Piano' mode at 1 kHz."""
        from timing_system import timing_system,timing_sequencer
        if value:
            ##timing_system.inton.count      = 1
            timing_system.IPIRE.count      =  1
            timing_system.DEVICE_GIE.count =  1
            timing_system.IPIER.count      =  1
            timing_sequencer.buffer_size = self.buffer_size
    configured = property(get_configured,set_configured)

    def sequencer_packet(self,sequence):
        """Binary data for one stroke of operation.
        Return value: binary data + descriptive string
        """
        if self.timing_sequencer.cache_enabled:
            method = self.sequencer_packet_cached
        else: method = self.sequencer_packet_generate
        packet,description = method(sequence)
        return packet,description

    def sequencer_packet_cached(self,sequence):
        """Binary data for one stroke of operation.
        Return value: binary data + descriptive string
        """
        description = sequence.description

        packet = self.timing_sequencer.cache_get(description)
        if len(packet) == 0:
            packet,description = self.sequencer_packet_generate(sequence)
            self.timing_sequencer.cache_set(description,packet)
        return packet,description

    def sequencer_packet_generate(self,sequence):
        """Binary data for one stroke of operation.
        Return value: binary data + descriptive string
        """
        info("Generating packet...")
        description = sequence.description
        registers,counts = self.register_counts(sequence)
        from timing_sequence import sequencer_packet
        data = sequencer_packet(registers,counts,description)
        return data,description

    def register_counts(self,sequence):
        """list of registers and lists of counts
        """
        # delay: laser to X-ray pump-probe delay in seconds
        # laseron: trigger the laser?
        # ms_on: operate the X-ray milliscond shutter?
        # pump_on: operate the peristaltic pump?
        # pass_number=1 for the first pass
        # image_number_inc: increment the image count? True or False
        # pass_number_inc: increment the pass count? True or False

        delay             = sequence.delay
        nom_delay         = sequence.nom_delay
        laser_on          = sequence.laser_on
        ms_on             = sequence.ms_on
        pump_on           = sequence.pump_on
        xdet_on           = sequence.xdet_on
        pass_number       = sequence.pass_number
        image_number_inc  = sequence.image_number_inc
        pass_number_inc   = sequence.pass_number_inc
        acquiring         = sequence.acquiring

        mode_number       = sequence.mode_number
        period            = sequence.period
        N                 = sequence.N
        dt                = sequence.dt
        t0                = sequence.t0
        transd            = sequence.transd
        z                 = sequence.z

        from timing_system import timing_system
        from numpy import isnan,where,arange,rint,floor,ceil,array,cumsum,\
            maximum,clip,concatenate,zeros
        from sparse_array import sparse_array

        Tbase = timing_system.hsct
        n = period

        # The high-speed chopper determines the X-ray pulse timing. 
        xd = -timing_system.hsc.delay.offset
        # If the chopper timing shift is more than 100 ns,
        # assume the chopper selects a different bunch with a different timing.
        # (e.g super bunch versus single bunch)
        # However, if the time shift is more than 4 us, assume the tunnel
        # 1-unch selection mode is used so the transmitted X-ray pulse
        # arrives at nominally t=0.
        phase = timing_system.high_speed_chopper_phase.value
        if 100e-9 < abs(phase) < 4e-6: xd += phase

        it_xray = t0 + arange(0,N*dt,dt)
        t_xray = it_xray*Tbase+xd
        t_laser = t_xray - delay

        registers,counts=[],[]

        if not isnan(pass_number):
            pass_number_counts = sparse_array(n,pass_number)
            registers += [timing_system.pass_number];  counts += [pass_number_counts]
        elif not pass_number_inc:
            pass_number_counts = sparse_array(n,0)
            registers += [timing_system.pass_number];  counts += [pass_number_counts]
        if image_number_inc:
            image_number_inc_counts = sparse_array(n)
            image_number_inc_counts[n-1] = 1
            registers += [timing_system.image_number_inc]; counts += [image_number_inc_counts]
        if pass_number_inc:
            pass_inc_counts = sparse_array(n,0)
            pass_inc_counts[0] = pass_number_inc
            registers += [timing_system.pass_number_inc];  counts += [pass_inc_counts]
        if ms_on:
            pulses_counts = sparse_array(n,0)
            pulses_inc_counts = sparse_array(n)
            pulses_inc_counts[it_xray] = 1
            registers += [timing_system.pulses_inc];   counts += [pulses_inc_counts]
            registers += [timing_system.pulses];       counts += [pulses_counts]
        # Indicate whether data acquisition is running.
        acquiring_counts = sparse_array(n,acquiring)
        registers += [timing_system.acquiring];        counts += [acquiring_counts]
        
        # Channel configuration-based sequence generation        
        for i_channel in range(0,len(timing_system.channels)):
            channel = timing_system.channels[i_channel]

            if channel.PP_enabled:
                if channel.special == "trans": # Sample translation trigger
                    # Transmit the mode number to the motion controller as bit pattern.
                    # 2 or 3 clock cycles start, 2 or 3 clock cycles per bit.
                    bit_length = int(rint(channel.pulse_length/Tbase))
                    transc = self.trigger_code_of(
                        mode_number,
                        ms_on,
                        sequence.following_sequence.pump_on,
                        sequence.following_sequence.delay,
                        z,
                    )
                    it_transst = range(0,bit_length)
                    for i in range(0,32):
                        if (transc>>i) & 1:
                            it_transst += range(bit_length*(i+1),bit_length*(i+2))
                    it_transst = array(it_transst)
                    it_transst += transd
                    it_transst %= period
                    trans_state_counts = sparse_array(n)
                    trans_state_counts[it_transst] = 1
                    registers += [channel.state];  counts += [trans_state_counts]
                elif channel.special == "pso": # Picosecond oscillator reference clock
                    # Picosecond oscillator reference clock (course, 7.1 ns resolution)
                    pso_period = 5*timing_system.bct
                    pso_coarse_step = timing_system.psod3.stepsize
                    pst_dial_values = t_laser - timing_system.pst.offset
                    pst_dial = pst_dial_values[0] % Tbase
                    pso_dial = timing_system.psod3.dial_from_user(pst_dial) % pso_period
                    psod3_dial = floor(pso_dial/pso_coarse_step)*pso_coarse_step
                    psod3_count = timing_system.psod3.count_from_dial(psod3_dial)
                    psod3_counts = sparse_array(n,psod3_count)
                    # Picosecond oscillator reference clock (fine, 9 ps resolution)
                    psod2_dial = pso_dial % pso_coarse_step
                    clk_shift_count = timing_system.psod2.count_from_dial(psod2_dial)
                    psod2_counts = sparse_array(n,clk_shift_count)
                    registers += [timing_system.psod3]; counts += [psod3_counts]
                    registers += [timing_system.psod2]; counts += [psod2_counts]
                elif channel.special == "nsf": # Nanosecond laser flashlamp trigger
                    nsf_nperiod = 48 # 20 Hz operation (10 Hz would be 96 counts)
                    T_nsf = nsf_nperiod * Tbase # flashlamp trigger period
                    N_nsf = n/nsf_nperiod # number of flashlamp triggers per image
                    t_nsf0 = (t_laser[0] + channel.offset_sign * channel.offset) % T_nsf # first trigger
                    t_nsf = t_nsf0 + arange(0,N_nsf) * T_nsf
                    # Abrupt timing jumps at the end of an image might cause the ns laser
                    # to trip. Make sure that no to trigger pulses arrive within less
                    # than 80% of the nominal period.
                    preceeding_t_laser = t_xray - sequence.preceeding_sequence.delay
                    preceeding_t_nsf0 = (preceeding_t_laser[0] - channel.offset_sign * channel.offset) % T_nsf
                    preceeding_t_nsf = preceeding_t_nsf0 + arange(0,N_nsf) * T_nsf
                    preceeding_t_nsf -= n*Tbase
                    if len(t_nsf) > 0 and t_nsf[0] - preceeding_t_nsf[-1] < 0.80 * T_nsf:
                        t_nsf = t_nsf[1:]
                    nsf_delay_dial = t_nsf[0] % Tbase if len(t_nsf)>0 else 0
                    nsf_count = channel.count_from_dial(nsf_delay_dial)
                    nsf_delay_counts = sparse_array(n,nsf_count)
                    it_nsf = floor(t_nsf/Tbase).astype(int)
                    nsf_enable_counts = sparse_array(n)
                    nsf_enable_counts[it_nsf] = 1
                    registers += [channel.delay];    counts += [nsf_delay_counts]
                    registers += [channel.enable];   counts += [nsf_enable_counts]
                else:
                    try:
                        r,c = self.channel_register_counts(i_channel,sequence)
                        registers += r; counts += c
                    except Exception,msg: error("Ensemble_SAXS: Channel %r: %s\n%s" %
                        (i_channel,msg,format_exc()))

        return registers,counts

    def channel_register_counts(self,i_channel,sequence):
        """list of registers and lists of counts
        i: channel number (0-based)
        """
        # delay: laser to X-ray pump-probe delay in seconds
        # laseron: trigger the laser?
        # ms_on: operate the X-ray milliscond shutter?
        # pump_on: operate the peristaltic pump?
        # pass_number=1 for the first pass
        # image_number_inc: increment the image count? True or False
        # pass_number_inc: increment the pass count? True or False
        # acquiring: is this packet used for data collection?

        delay             = sequence.delay
        nom_delay         = sequence.nom_delay
        laser_on          = sequence.laser_on
        ms_on             = sequence.ms_on
        pump_on           = sequence.pump_on
        xdet_on           = sequence.xdet_on
        acquiring         = sequence.acquiring

        mode_number       = sequence.mode_number
        period            = sequence.period
        N                 = sequence.N
        dt                = sequence.dt
        t0                = sequence.t0
        transd            = sequence.transd
        z                 = sequence.z

        from timing_system import timing_system
        from numpy import isnan,where,arange,rint,floor,ceil,array,cumsum,\
            maximum,clip,concatenate,zeros,array,diff,all
        from sparse_array import sparse_array

        channel = timing_system.channels[i_channel]

        Tbase = timing_system.hsct
        n = period
        T = n*Tbase # packet period

        # The high-speed chopper determines the X-ray pulse timing. 
        xd = -timing_system.hsc.delay.offset
        # If the chopper timing shift is more than 100 ns,
        # assume the chopper selects a different bunch with a different timing.
        # (e.g super bunch versus single bunch)
        # However, if the time shift is more than 4 us, assume the tunnel
        # 1-unch selection mode is used so the transmitted X-ray pulse
        # arrives at nominally t=0.
        phase = timing_system.high_speed_chopper_phase.value
        if 100e-9 < abs(phase) < 4e-6: xd += phase

        it_xray = t0 + arange(0,N*dt,dt)

        t_xray = it_xray*Tbase+xd
        t_laser = t_xray - delay

        counts = []
        registers = []

        if channel.gated == "pump": on = laser_on
        elif channel.gated == "probe": on = ms_on
        elif channel.gated == "detector": on = xdet_on
        else: on = True

        if channel.timed == "pump": t_ref = t_laser
        elif channel.timed == "probe": t_ref = t_xray
        elif channel.timed == "period": t_ref = array([0.0])
        else: t_ref = array([])

        if on and len(t_ref) > 0:
            if not isnan(channel.offset_HW): # precision-timed sub-ms pulses
                t = t_ref + channel.offset_sign * channel.offset_HW
                fine_delay = t[0] % Tbase
                delay_count = channel.next_count(fine_delay/channel.stepsize)
                delay_counts = sparse_array(n,delay_count)
                it = floor(t/Tbase).astype(int)
                enable_counts = sparse_array(n)
                enable_counts[it] = 1

                counts += [enable_counts,delay_counts]
                registers += [channel.enable,channel.delay]

                it_on = it # for trigger count
            else: # ms-resolution multi-ms pulses
                t0 = channel.offset
                pulse_length = channel.pulse_length
                timed = channel.timed
                
                if isnan(pulse_length): pulse_length = 0

                t = array([t_ref+t0,t_ref+t0+pulse_length]).T.flatten()

                t = self.t_special(t,channel.special)
                
                Noutside = sum((t<0)|(t>=T))
                initial_value = 1 if Noutside % 2 == 1 else 0
                t = t % T

                it = clip(rint(t/Tbase),0,n-1).astype(int)
                it_on,it_off = it.reshape((-1,2)).T
                inc = sparse_array(n)
                inc[it_on]  += 1
                inc[it_off] -= 1
                state_counts = clip(cumsum(inc)+initial_value,0,1)
                state_counts = sparse_array(state_counts)
        
                counts += [state_counts]
                registers += [channel.state]

            if channel.counter_enabled:
                # Increment the trigger count on the rising edge of the last
                # trigger pulse within the measure.
                it_last_trigger = it_on[-1:]
                count_inc  = sparse_array(n)
                count_inc[it_last_trigger] = 1
                registers += [channel.trig_count]
                counts += [count_inc]
                if acquiring: 
                    registers += [channel.acq]
                    counts += [count_inc]
                    registers += [channel.acq_count]
                    counts += [count_inc]
                    

        return registers,counts

    def t_special(self,t,special):
        """Process time delays for channels that have special functions
        t: array of time delays in seconds for rising and falling edges,
           alternating
        special: e.g. "ms" for X-ray millisecond shutter
        """
        from numpy import array
        t_special = t
        t_rise,t_fall = t[0::2],t[1::2]
        if special == "ms":
            if len(t) >= 2:
                if len(t_rise) >= 2:
                    burst_period = (max(t_rise)-min(t_rise))/(len(t_rise)-1)
                else: burst_period = 0
                if 0 < burst_period < 0.024: # Open continuously for a burst
                    t_special = array([min(t_rise),max(t_rise)])
        return t_special

    def channel_description(self,i_channel):
        """The parameters for generating a packet represented as text string."""
        from timing_system import timing_system
        description = ""
        channel = timing_system.channels[i_channel]
        name = channel.mnemonic if channel.mnemonic else channel.name
        description += name+".special=%r," % channel.special
        description += name+".offset_PP=%r," % channel.offset_PP
        description += name+".offset_sign=%r," % channel.offset_sign
        description += name+".pulse_length_PP=%r," % channel.pulse_length_PP
        description += name+".offset_HW=%r," % channel.offset_HW
        description += name+".pulse_length_HW=%r," % channel.pulse_length_HW
        description += name+".timed=%r," % channel.timed
        description += name+".gated=%r," % channel.gated
        description += name+".counter_enabled=%r," % channel.counter_enabled
        return description        

    def trigger_code_of(self,mode_number,ms_on,pump_on,delay,z):
        """Byte code to be transmitted to the Ensemble motion controller
        as bit pattern
        ms_on: operate the X-ray milliscond shutter?
        pump_on: operate the peristaltic pump?
        """
        # mode: 4 bits: pump_on: 1 bit, delay 6 bits
        delay_count = self.delay_count(delay) if z else 0
        transc = (
            (int(mode_number)<<0) |
            (int(pump_on)<<4) |
            (int(delay_count)<<5)
        )
        return transc

    def delay_count(self,delay):
        """Count to indicate the linear translation of the laser beam on a
        logarithmic scale
        delay: delay in seconds, range 0-17.8 ms 
        Return value: integer, range 0-63"""
        from numpy import log10,rint
        delay_count = min(int(rint(8*log10(max(delay,10e-6)/10e-6))),63)
        return delay_count
        
    def acquisition_start(self,image_number=1):
        """To be called after 'acquire'
        image_number: 1-based integer
        """
        self.image_number = image_number-1
        self.pass_number = 0
        self.pulses = 0
        self.queue_sequence_count = 0
        self.queue_repeat_count = 0
        self.queue_active = True

    def acquisition_cancel(self):
        """End current data collection"""
        self.queue_active = False

    def set_default_sequences(self,sequences=None):
        """Set a sequece to be execute when the queue is empty.
        """
        if sequences is None: sequences = Sequences()[:]
        self.configured = True
        self.timing_sequencer.set_default_sequences(sequences)

    def get_queue(self): return self.timing_sequencer.queue
    def set_queue(self,value):self.timing_sequencer.queue = value
    queue = property(get_queue,set_queue)

    def get_queue_length(self): return self.timing_sequencer.queue_length
    def set_queue_length(self,value): self.timing_sequencer.queue_length = value
    queue_length = property(get_queue_length,set_queue_length)

    def get_queue_active(self): return self.timing_sequencer.queue_active
    def set_queue_active(self,value): self.timing_sequencer.queue_active = value
    queue_active = property(get_queue_active,set_queue_active)

    def get_buffer_length(self): return self.timing_sequencer.buffer_length
    def set_buffer_length(self,value): self.timing_sequencer.buffer_length = value
    buffer_length = property(get_buffer_length,set_buffer_length)

    def get_cache_enabled(self): return self.timing_sequencer.cache_enabled
    def set_cache_enabled(self,value): self.timing_sequencer.cache_enabled = value
    cache_enabled = property(get_cache_enabled,set_cache_enabled)

    def cache_clear(self): return self.timing_sequencer.cache_clear()

    def get_cache_size(self): return self.timing_sequencer.cache_size
    def set_cache_size(self,value): self.timing_sequencer.cache_size = value
    cache_size = property(get_cache_size,set_cache_size)

    def get_acquiring(self):
        from timing_system import timing_system
        return timing_system.acquiring.count != 0
    def set_acquiring(self,value):
        if not value: self.update()
    acquiring = property(get_acquiring,set_acquiring)

    def get_running(self): return self.timing_sequencer.running
    def set_running(self,value):
        self.timing_sequencer.set_running(value,update=self.update)
    running = property(get_running,set_running)

    def update(self):
        """Execute sequence using the current default parameters"""
        self.set_default_sequences()
        self.timing_sequencer.enabled = True

    def clear_queue(self):
        """Cancel current data acaquisstion"""
        self.timing_sequencer.clear_queue()

    def get_default_sequence_active(self):
        return self.timing_sequencer.default_sequence_active
    def set_default_sequence_active(self,value):
        self.timing_sequencer.default_sequence_active = value
    default_sequence_active = property(get_default_sequence_active,
        set_default_sequence_active)

    def get_image_number(self):
        from timing_system import timing_system
        return timing_system.image_number.count
    def set_image_number(self,value):
        from timing_system import timing_system
        timing_system.image_number.count = value
    image_number = property(get_image_number,set_image_number)
    
    def get_pass_number(self):
        from timing_system import timing_system
        return timing_system.pass_number.count
    def set_pass_number(self,value):
        from timing_system import timing_system
        timing_system.pass_number.count = value
    pass_number = property(get_pass_number,set_pass_number)

    def get_pulses(self):
        from timing_system import timing_system
        return timing_system.pulses.count
    def set_pulses(self,value):
        from timing_system import timing_system
        timing_system.pulses.count = value
    pulses = property(get_pulses,set_pulses)

    def get_cmcnd(self):
        from timing_system import timing_system
        return timing_system.cmcnd.value
    def set_cmcnd(self,value):
        from timing_system import timing_system
        if timing_system.cmcnd.value != value:
            timing_system.cmcnd.value = value
            self.update()
    cmcnd = property(get_cmcnd,set_cmcnd)

    def get_cmcd(self):
        from timing_system import timing_system
        return timing_system.cmcd.value
    def set_cmcd(self,value):
        from timing_system import timing_system
        if timing_system.cmcd.command_value != value:
            timing_system.cmcd.command_value = value
            self.update()
    cmcd = property(get_cmcd,set_cmcd)

    def __getattr__(self,name):
        """A property"""
        # Called when 'x.name' is evaluated.
        # It is only invoked if the attribute was not found the usual ways.
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("EnsembleSAXS object has no attribute %r" % name)
        from timing_system import timing_system
        alt_name = name.replace("_",".") # hsc_delay > hsc.delay
        if hasattr(timing_system,name):
            attr = getattr(timing_system,name)
            if hasattr(attr,"value"): attr = attr.value
            return attr
        elif self.hasattr(timing_system,alt_name):
            attr = eval("timing_system.%s" % alt_name)
            if hasattr(attr,"value"): attr = attr.value
            return attr
        elif hasattr(self.timing_sequencer,name):
            return getattr(self.timing_sequencer,name)
        else: return object.__getattribute__(self,name)

    @staticmethod
    def hasattr(object,name):
        """name: e.g. 'hsc.delay'"""
        try: eval("object.%s" % name); return True
        except AttributeError: return False

    def __setattr__(self,name,value):
        """Set a  property"""
        # Called when 'x.name = y' is evaluated.
        from timing_system import timing_system
        alt_name = name.replace("_",".") # hsc_delay > hsc.delay
        if name.startswith("__") and name.endswith("__"):
            object.__setattr__(self,name,value)
        elif name in self.__class__.__dict__.keys():
            object.__setattr__(self,name,value)
        elif hasattr(timing_system,name):
            attr = getattr(timing_system,name)
            if hasattr(attr,"value"): attr.value = value
            else: setattr(timing_system,name,value) 
        elif self.hasattr(timing_system,alt_name):
            attr = eval("timing_system.%s" % alt_name)
            if hasattr(attr,"value"): attr.value = value
            else: exec("timing_system.%s = %r" % (alt_name,value)) 
        elif hasattr(self.timing_sequencer,name):
           setattr(self.timing_sequencer,name,value)
        else: object.__setattr__(self,name,value)

    def __repr__(self): return "Ensemble_SAXS"

Ensemble_SAXS = EnsembleSAXS()

def sorted_lists(lists):
    from numpy import argsort
    order = argsort(lists[0])
    def reorder(list,order): return [list[i] for i in order]
    sorted_lists = [reorder(list,order) for list in lists]
    return sorted_lists


if __name__ == "__main__": # for testing
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s: %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    import timing_system as t; t.DEBUG = True
    from timing_system import timing_system
    self = Ensemble_SAXS # for debugging
    from time import time # for performace measuring
    # parameters for Ensemble_SAXS.register_counts:
    from numpy import nan
    # parameters for "register_counts"
    sequences = Sequences(acquiring=False)
    sequence = sequences[0]
    ##sequence = Sequence(acquiring=False)
    # parameters for "channel_register_counts"
    ##i_channel = 6-1 # ms
    print('timing_system.prefix = %r' % timing_system.prefix)
    print('timing_system.ip_address_and_port = %r' % timing_system.ip_address_and_port)
    print('')
    print('Ensemble_SAXS.cache_size = %r' % Ensemble_SAXS.cache_size)
    print('Ensemble_SAXS.remote_cache_size = %r' % Ensemble_SAXS.remote_cache_size)
    print('Ensemble_SAXS.running = True')
    print('Ensemble_SAXS.update()')
    print('')
    ##print('registers,counts = Ensemble_SAXS.register_counts()')
    ##print('registers,counts = sequence.register_counts')
    print('t=time(); descriptor = sequence.descriptor; time()-t')
    print('t=time(); registers,counts = sequence.register_counts; time()-t')
    from timing_sequence import sequencer_packet
    print('t=time(); data = sequencer_packet(registers,counts,descriptor); time()-t')
    print('t=time(); id = sequence.id; time()-t')
    print('t=time(); data = sequence.data; time()-t')

