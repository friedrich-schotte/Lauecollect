"""
Data base to save and recall motor positions
Author: Friedrich Schotte
Date created: 2019-05-24
Date last modified: 2019-05-31
"""
__version__ = "1.3" # monitor

from logging import debug,info,warn,error

class Configuration_Property(property): pass
class Motor_Property(property): pass

from classproperty import classproperty,ClassPropertyMetaClass
class Configuration(object):
##class Bar(metaclass=ClassPropertyMetaClass): # Python 3+
    """Data base save and recall motor positions"""
    __metaclass__ = ClassPropertyMetaClass # Python 2.7

    from configuration_server import Configuration_Server
    prefix = Configuration_Server.prefix

    def __init__(self,name,**kwargs):
        # kwargs for backward-compatbility
        self.name = name

    @classmethod
    def register(cls,name):
        if not name in cls.configuration_names:
            cls.configuration_names += [name]

    @classproperty
    def configuration_names(cls):
        return Configuration.get_global_value("configuration_names",[])
    @configuration_names.setter
    def configuration_names(cls,value):
        Configuration.set_global_value("configuration_names",value)

    @classproperty
    def configurations(cls):
        return [configuration(n) for n in configuration.configuration_names]

    def configuration_property(name,default_value=None):
        def PV_name(self): return self.configuration_PV_name(name)
        def get(self):
            if type(default_value) == list: value = self.array_PV(PV_name(self))
            else: value = self.get_PV(PV_name(self),default_value)
            return value
        def set(self,value): self.set_PV(PV_name(self),value)
        prop = Configuration_Property(get,set)
        return prop

    value                = configuration_property("value","")
    values               = configuration_property("values",[])
    command_value        = configuration_property("command_value","")
    title                = configuration_property("title","")
    description          = configuration_property("description","")
    matching_description = configuration_property("matching_description","")
    closest_descriptions = configuration_property("closest_descriptions","")
    command_description  = configuration_property("command_description","")
    command_rows         = configuration_property("command_rows",[])
    matching_rows        = configuration_property("matching_rows",[])
    closest_rows         = configuration_property("closest_rows",[])
    n_motors             = configuration_property("n_motors",0)
    descriptions         = configuration_property("descriptions",[])
    updated              = configuration_property("updated",[])
    formats              = configuration_property("formats",[])
    nrows                = configuration_property("nrows",0)
    motor_names          = configuration_property("motor_names",[])
    names                = configuration_property("names",[])
    motor_labels         = configuration_property("motor_labels",[])
    widths               = configuration_property("widths",[])
    formats              = configuration_property("formats",[])
    tolerance            = configuration_property("tolerance",[])
    description_width    = configuration_property("description_width",200)
    row_height           = configuration_property("row_height",20)
    show_apply_buttons   = configuration_property("show_apply_buttons",True)
    apply_button_label   = configuration_property("apply_button_label","Select")
    show_define_buttons  = configuration_property("show_define_buttons",True)
    define_button_label  = configuration_property("define_button_label","Update")
    show_stop_button     = configuration_property("show_stop_button",False)
    serial               = configuration_property("serial",False)
    vertical             = configuration_property("vertical",False)
    multiple_selections  = configuration_property("multiple_selections",False)
    are_configuration    = configuration_property("are_configuration",[])
    motor_configuration_names = configuration_property("motor_configuration_names",[])
    are_numeric          = configuration_property("are_numeric",[])
    current_timestamp    = configuration_property("current_timestamp","")
    applying             = configuration_property("applying",False)
    show_in_list         = configuration_property("show_in_list",True)

    def motor_property(name,default_value=None):
        def get(self): return self.Motor_Property(self,name,default_value)
        def set(self,value): get(self)[:] = value
        return Motor_Property(get,set)

    from numpy import nan
    current_position = motor_property("current_position")
    positions        = motor_property("positions",[])
    positions_match  = motor_property("positions_match",[])

    class Motor_Property(object):
        def __init__(self,configuration,name,default_value=None):
            self.configuration = configuration
            self.name = name
            self.default_value = default_value
        def PV_name(self,i): return self.configuration.motor_PV_name(self.name,i)
        def __getitem__(self,i):
            if type(i) == slice: value = [x for x in self]
            else:
                if type(self.default_value) == list:
                    value = self.configuration.array_PV(self.PV_name(i))
                else: value = self.configuration.get_PV(self.PV_name(i),self.default_value)
            return value
        def __setitem__(self,i,value):
            if type(i) == slice:
                for j in range(0,len(value)): self[j] = value[j]
            else:
                self.configuration.set_PV(self.PV_name(i),value)
        def __len__(self): return self.configuration.n_motors
        def __iter__(self):
            for i in range(0,len(self)):
                if i < len(self): yield self[i]
        def __repr__(self):
            return "%s(%s,%r)" % (type(self).__name__,self.configuration,self.name)

    class array_PV(object):
        def __init__(self,PV_name):
            self.PV_name = PV_name
        def __getitem__(self,i):
            if type(i) == slice: value = self.array
            else: value = self.array[i]
            return value
        def __setitem__(self,i,value):
            if type(i) == slice: self.array = value
            else:
                array = self.array
                array[i] = value
                self.array = array
        def get_array(self):
            return Configuration.get_PV(self.PV_name,[])
        def set_array(self,value):
            from CA import caput
            caput(self.PV_name,value)
        array = property(get_array,set_array)
        def __len__(self): return len(self.array)
        def __iter__(self):
            for i in range(0,len(self)):
                if i < len(self): yield self[i]
        def __repr__(self):
            return "%s(%r)" % (type(self).__name__,self.PV_name)
        def index(self,value): return self.array.index(value)
        def __eq__(self,array):
            if not hasattr(array,"__len__"): return False
            if len(self) != len(array): return False
            return all([self[i] == array[i] for i in range(0,len(self))])
        def __ne__(self,array): return not self == array

    @staticmethod
    def get_global_value(name,default_value=None):
        return Configuration.get_PV(Configuration.global_PV_name(name),default_value)

    @staticmethod
    def set_global_value(name,value):
        from CA import caput
        caput(Configuration.global_PV_name(name),value)

    @staticmethod
    def global_PV_name(name):
        return (Configuration.prefix+"."+name).upper()    

    def configuration_PV_name(self,name):
        return (self.prefix+"."+self.name+"."+name).upper()    

    def set_motor_value(self,name,motor_num,value):
        from CA import caput
        caput(self.motor_PV_name(name,motor_num),value)

    def motor_PV_name(self,name,motor_num):
        return (self.prefix+"."+self.name+".MOTOR"+str(motor_num+1)+"."+name).upper()    

    @staticmethod
    def get_PV(PV_name,default_value=None):
        from CA_cached import caget_cached as caget
        value = caget(PV_name)
        if value is None: value = default_value
        if default_value is not None and type(value) != type(default_value):
            if type(default_value) == list: value = [value]
            else:
                try: value = type(default_value)(value)
                except: value = default_value
        return value

    @staticmethod
    def set_PV(PV_name,value):
        from CA import caput
        caput(PV_name,value)

    def monitor(self,property_name,callback,*args,**kwargs):
        from CA import camonitor
        for PV_name in self.PV_names(property_name):
            def monitor_callback(PV_name,value,formatted_value):
                callback(*args,**kwargs)
            monitor_callback.callback = callback
            monitor_callback.args = args
            monitor_callback.kwargs = kwargs
            camonitor(PV_name,callback=monitor_callback,new_thread=True)

    def PV_names(self,property_name):
        PV_names = []
        if hasattr(type(self),property_name):
            prop = getattr(type(self),property_name)
            if type(prop) == Configuration_Property:
                PV_names = [self.configuration_PV_name(property_name)]
            if type(prop) == Motor_Property:
                PV_names = [self.motor_PV_name(property_name,i)
                    for i in range(0,self.n_motors)]
        return PV_names

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__,self.name)
        

configuration = Configuration
config = configuration

class Configurations(object):
    """Name space containing all defined configurations"""
    def __getattr__(self,name):
        if name == "__members__": return configuration.configuration_names
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("%s" % name)
        return configuration(name)

configurations = Configurations()
configs = configurations


if __name__ == '__main__': # for testing
    from pdb import pm # for debugging
    from time import time # for performance testing
    import logging
    for h in logging.root.handlers[:]: logging.root.removeHandler(h)
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    ##name = "beamline_configuration"
    ##name = "sequence_modes"
    ##name = "heat_load_chopper_modes"
    ##name = "Julich_chopper_modes"
    name = "timing_modes"
    ##name = "sequence_modes"
    ##name = "delay_configuration" 
    ##name = "temperature_configuration" 
    ##name = "power_configuration" 
    ##name = "scan_configuration" 
    ##name = "alio_diffractometer_saved"
    ##name = "detector_configuration"
    ##name = "diagnostics_configuration"
    ##name = "method"

    self = configuration(name=name)

    print('self.positions[0][0]')
    ##print('self.positions[0][:]')
    print('self.current_position[0]')
    print('self.positions_match[0][0]')
    ##print('self.positions_match[0][:]')
    print('self.descriptions[:]')
    ##print('self.descriptions[5]')
    ##print('self.descriptions.index("S-1")')
    ##print('self.widths != self.widths')
    ##print('self.widths == self.widths')
    ##print('self.are_numeric[:]')
    def callback(property_name):
        value = getattr(self,property_name)
        if hasattr(value,"__getitem__"):
            value = value[:]
            for i in range(0,len(value)):
                if hasattr(value[i],"__getitem__"): value[i] = value[i][:]
        info("%s = %r" % (property_name,value))
    print('self.monitor("nrows",callback,"nrows")')
    print('self.monitor("descriptions",callback,"descriptions")')
    print('self.monitor("command_rows",callback,"command_rows")')
    print('self.monitor("current_position",callback,"current_position")')
    print('self.monitor("positions",callback,"positions")')
