"""
Data base save and recall motor positions
Author: Friedrich Schotte
Date created: 2013-11-29
Date last modified: 2019-05-28
"""
__version__ = "4.1.1" # "%s.line%d.%s" %d format: a number is required, not float
from logging import debug,info,warn,error

import numpy
numpy.warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
numpy.warnings.filterwarnings('ignore', r'Mean of empty slice.')

from classproperty import classproperty,ClassPropertyMetaClass
class Configuration(object):
##class Bar(metaclass=ClassPropertyMetaClass): # Python 3+
    """Data base save and recall motor positions"""
    __metaclass__ = ClassPropertyMetaClass # Python 2.7
    
    from persistent_property import persistent_property
    from numpy import nan
    nrows = persistent_property("nrows",2) # How many configurations?
    motor_names = persistent_property("motor_names",[]) # Python expression for motor
    __names__ = persistent_property("names",[]) # mnemonics for columns
    serial = persistent_property("serial",False) # Move one motor after the other?
    __command_rows__ = persistent_property("command_rows",[]) # last selected state
    # GUI properties
    title = persistent_property("title","Configuration")  
    __motor_labels__ = persistent_property("motor_labels",[])
    __formats__ = persistent_property("formats",[])
    __widths__ = persistent_property("widths",[])
    __tolerance__ = persistent_property("tolerance",[])
    description_width = persistent_property("description_width",150)  
    row_height = persistent_property("row_height",20)  
    show_apply_buttons = persistent_property("show_apply_buttons",True)  
    apply_button_label = persistent_property("apply_button_label","Select")  
    show_define_buttons = persistent_property("show_define_buttons",True)  
    define_button_label = persistent_property("define_button_label","Update")  
    show_stop_button = persistent_property("show_stop_button",False)  
    show_in_list = persistent_property("show_in_list",True)  
    vertical = persistent_property("vertical",False)  
    multiple_selections = persistent_property("multiple_selections",False)  
    
    def __init__(self,
        name="configuration_test",
        motor_names=None,
        motor_labels=None,
        formats=None,
        nrows=None,
        serial=None,
        locals=None,
        globals=None,
    ):
        """name: basename of settings file"""
        self.register(name)
        self.name = name
        if motor_names  is not None: self.motor_names  = motor_names
        if motor_labels is not None: self.motor_labels = motor_labels
        if formats      is not None: self.formats      = formats
        if nrows        is not None: self.nrows        = nrows
        if serial       is not None: self.serial       = serial
        self.locals = locals
        self.globals = globals

    def get_globals(self):
        if not hasattr(self,"__globals__") or self.__globals__ is None:
            exec("from instrumentation import *") # -> locals()
            self.__globals__ = globals()
        return self.__globals__
    def set_globals(self,value): self.__globals__ = value
    globals = property(get_globals,set_globals)

    def get_locals(self):
        if not hasattr(self,"__locals__") or self.__locals__ is None:
            exec("from instrumentation import *") # -> locals()
            self.__locals__ = locals()
        return self.__locals__
    def set_locals(self,value): self.__locals__ = value
    locals = property(get_locals,set_locals)

    @classmethod
    def register(cls,name):
        if not name in cls.configuration_names:
            cls.configuration_names += [name]

    @classproperty
    def configuration_names(cls):
        from DB import db
        return db("configuration.names",[])
    @configuration_names.setter
    def configuration_names(cls,names):
        from DB import dbset
        dbset("configuration.names",names)

    @classproperty
    def configurations(cls):
        return [configuration(n) for n in configuration.configuration_names]

    def get_motor_labels(self):
        return self.resize(self.__motor_labels__,self.n_motors,default_value="?")
    def set_motor_labels(self,values): self.__motor_labels__ = values
    motor_labels = property(get_motor_labels,set_motor_labels)

    def get_names(self):
        """Column mnemonics"""
        return self.resize(self.__names__,self.n_motors,template="motor%d")
    def set_names(self,values): self.__names__ = values
    names = property(get_names,set_names)

    def get_formats(self):
        return self.resize(self.__formats__,self.n_motors,default_value="%s")
    def set_formats(self,values): self.__formats__ = values
    formats = property(get_formats,set_formats)

    def get_widths(self):
        """Horizontal size for each motor columns in pixels"""
        widths = self.resize(self.__widths__,self.n_motors,default_value=100)
        if self.vertical: widths = [self.description_width]*self.n_motors
        return widths
    def set_widths(self,values): self.__widths__ = values
    widths = property(get_widths,set_widths)

    def get_tolerance(self):
        return self.resize(self.__tolerance__,self.n_motors,default_value=0)
    def set_tolerance(self,values): self.__tolerance__ = values
    tolerance = property(get_tolerance,set_tolerance)

    def get_command_rows(self):
        from numpy import isnan,nan
        rows = self.__command_rows__
        rows = [row for row in rows if 0 <= row < self.nrows]
        return rows
    def set_command_rows(self,values): self.__command_rows__ = values
    command_rows = property(get_command_rows,set_command_rows)

    @property
    def n_motors(self):
        """How many motors are there?"""
        return len(self.motor_names)

    @property
    def motors(self):
        """List of objects with propery "value"""
        return [self.motor(name) for name in self.motor_names]

    @property
    def are_configuration(self):
        return [self.is_configuration(i) for i in range(0,self.n_motors)]

    def is_configuration(self,i):
        """Is this column a linked configuration?"""
        is_configuration = self.configuration_name(i) in self.configuration_names
        return is_configuration

    @property
    def motor_configuration_names(self):
        return [self.motor_configuration_name(i) for i in range(0,self.n_motors)]

    def motor_configuration_name(self,i):
        """If this column a linked configuration, what it its name?"""
        name = self.motor_names[i]
        name = name.replace(".value","")
        return name
    configuration_name = motor_configuration_name

    def configuration(self,i):
        """Linked configuration"""
        return configuration(name=self.configuration_name(i),
            locals=self.locals,globals=self.globals)

    def motor(self,name):
        import traceback
        try: motor = eval(name,self.globals,self.locals)
        except Exception,msg:
            error("motor %r: %s" % (name,msg))
            ##error("motor %r: %s\n%s" % (name,msg,traceback.format_exc()))
            motor = self.Dummy_motor()
        return motor

    class Dummy_motor:
        from numpy import nan
        value = nan

    def get_current_positions(self): return self.CurrentPositions(self)
    def set_current_positions(self,value): self.current_positions[:] = value
    current_positions = property(get_current_positions,set_current_positions)
    current_position = current_positions

    class CurrentPositions(object):
        def __init__(self,configuration):
            self.configuration = configuration
        def __getitem__(self,i):
            if type(i) == slice: value = [x for x in self]
            else: value = self.configuration.get_current_position(i)
            return value
        def __setitem__(self,i,value):
            if type(i) == slice:
                for j in range(0,len(value)): self[j] = value[j]
            else: self.configuration.set_current_position(i,value)
        def __len__(self): return len(self.configuration.motor_names)
        def __iter__(self):
            for i in range(0,len(self)):
                if i < len(self): yield self[i]

    def get_current_position(self,i):
        """Report the current position of a motor 
        i: zero-based index"""
        name = self.motor_names[i]
        value = self.motor_position(name)
        if self.is_numeric(i):
            from numpy import nan
            try: value = float(value)
            except Exception,msg:
                warn("%r: float(%r): %s" % (name,value,msg))
                value = nan
        else:
            try: value = str(value)
            except Exception,msg:
                warn("%r: str(%r): %s" % (name,value,msg))
                value = ""
        return value
        
    def set_current_position(self,i,value):
        """Move a motor
        i: zero-based index
        value: new position"""
        self.set_motor_position(self.motor_names[i],value)

    @property
    def nominal_positions(self):
        """Where should the motors be if the commanded configuration
        were applied? list of positions"""
        rows = self.command_rows
        positions = []
        for m in range(0,self.n_motors):
            position = self.combined([self.positions[m][row] for row in rows],m)
            positions += [position]
        return positions

    def combined(self,values,motor_num):
        if self.is_numeric(motor_num): combined = self.combined_positions(values)
        else: combined = self.combined_string(values)
        return combined

    def combined_positions(self,values):
        from numpy import average,nan
        combined = nan
        if len(values)>0: combined = average(values)
        return combined

    def combined_string(self,values):
        return ", ".join(values)
    
    def nominal_position(self,motor_number):
        """Where should the motor be if the commanded configuration
        were applied?
        motor_number: zero-based index"""
        m = motor_number
        rows = self.command_rows
        position = self.combined([self.positions[m][row] for row in rows],m)
        return position

    @property
    def command_positions(self): return self.CommandPositions(self)

    class CommandPositions(object):
        def __init__(self,configuration):
            self.configuration = configuration
        def __getitem__(self,i):
            if type(i) == slice: value = [x for x in self]
            else: value = self.configuration.command_position(i)
            return value
        def __setitem__(self,i,value):
            if type(i) == slice:
                for j in range(0,len(value)): self[j] = value[j]
            else: self.configuration.set_current_position(i,value)
        def __len__(self): return len(self.configuration.motor_names)
        def __iter__(self):
            for i in range(0,len(self)):
                if i < len(self): yield self[i]

    def command_position(self,motor_number):
        """Report the commanded nominal position of a motor (or target if moving)
        motor_number: zero-based index"""
        return self.motor_command_position(self.motor_names[motor_number])

    def motor_position(self,name):
        """Report the current position of a motor
        name: string"""
        from numpy import nan
        try: value = eval(name+".value",self.globals,self.locals)
        except AttributeError: # object has no attribute 'value'
            try: value = eval(name,self.globals,self.locals)
            except Exception,msg:
                error("%s: %s" % (name,msg))
                value = nan
        except Exception,msg:
            error("%s: %s" % (name,msg))
            value = nan
        return value

    def motor_command_position(self,name):
        """Report the nominal position of a motor
        name: string"""
        from numpy import nan
        try: value = eval(name+".command_value",self.globals,self.locals)
        except AttributeError: # object has no attribute 'value'
            try: value = eval(name,self.globals,self.locals)
            except Exception,msg:
                error("%s: %s" % (name,msg))
                value = nan
        except Exception,msg:
            error("%s: %s" % (name,msg))
            value = nan
        return value

    def set_motor_position(self,name,value):
        """name: string"""
        if self.is_valid_position(value):
            from numpy import nan # for exec
            import traceback
            try: exec("%s.value = %r" % (name,value),self.globals,self.locals)
            except AttributeError: # object has no attribute 'value'
                try: exec("%s = %r" % (name,value),self.globals,self.locals)
                except Exception,msg:
                    error("%s = %r: %s\n%s" % (name,value,msg,traceback.format_exc()))
            except Exception,msg:
                error("%s = %r: %s\n%s" % (name,value,msg,traceback.format_exc()))

    def is_valid_position(self,value):
        from numpy import isfinite,nan
        if isinstance(value,str):
            valid = True
            ##valid = value != ""
        else: valid = isfinite(value)
        return valid

    def position(self,row_or_description):
        """Saved motor positions.
        row: zero-based index or description string"""
        if not isinstance(row_or_description,basestring):
            position = self.position_of_row(row_or_description)
        else: position = self.position_of_description(row_or_description)
        return position

    def position_of_row(self,row):
        """List of saved motor positions"""
        position = [self.positions[im][row] for im in self.n_motor]
        return position
    
    def position_of_description(self,description):
        from numpy import nan
        for row in range(0,self.nrows):
            if self.descriptions[row] == description:
                return self.position_of_row(row)
        return [nan]*self.n_motors

    def get_command_description(self):
        from numpy import isnan,nan
        rows = self.command_rows
        rows = [row for row in rows if 0 <= row < self.nrows]
        description = self.combined_string([self.descriptions[row] for row in rows])
        return description
    def set_command_description(self,description):
        rows = self.rows(description)
        self.command_rows = rows
        self.applying = True
    command_description = property(get_command_description,set_command_description)

    def get_closest_description(self):
        from numpy import isnan
        rows = []
        if self.multiple_selections: rows = self.closest_rows
        elif not isnan(self.closest_row): rows = [self.closest_row]
        description = self.combined_string([self.descriptions[row] for row in rows])
        return description
    def set_closest_description(self,value): self.command_description = value
    closest_description = property(get_closest_description,set_closest_description)

    def rows(self,descriptions):
        """ 'NIH:H-1_ps,NIH:H-56_ps' > [0,1]"""
        from numpy import isnan
        list = self.description_list(descriptions)
        rows  = [self.row(d) for d in list if not isnan(self.row(d))]
        return rows

    def row(self,description):
        from numpy import nan
        row = nan
        descriptions = self.descriptions[:]
        if description in descriptions: row = descriptions.index(description)
        return row 

    def description_list(self,descriptions):
        """ 'NIH:H-1_ps,NIH:H-56_ps' > ['NIH:H-1_ps','NIH:H-56_ps']"""
        descriptions = descriptions.split(",")
        descriptions = [d.strip() for d in descriptions]
        return descriptions

    @property
    def closest_descriptions(self):
        descriptions = [self.descriptions[row] for row in self.closest_rows]
        return descriptions

    def get_matching_description(self):
        from numpy import isnan
        rows = self.matching_rows
        # Use the last selection to make it unambiguous if possible.
        if len(self.command_rows) == 1 and self.command_rows[0] in rows:
            rows = self.command_rows
        description = self.combined_string([self.descriptions[row] for row in rows])
        return description
    def set_matching_description(self,value): self.command_description = value
    matching_description = property(get_matching_description,set_matching_description)

    def get_descriptions(self): return self.Values(self,"description","")
    def set_descriptions(self,value): self.descriptions[:] = value
    descriptions = property(get_descriptions,set_descriptions)

    def get_description(self):
        description = self.closest_description
        if self.command_description == "": description = ""
        return description
    def set_description(self,value): self.command_description = value
    description = property(get_description,set_description)
    
    value = description
    command_value = command_description
    @property
    def values(self): return self.descriptions[:]

    def get_matching_row(self):
        """Row that matches the actual settings, as 0-based integer"""
        from numpy import nan
        matching_rows = self.matching_rows
        matching_command_rows = [row for row in matching_rows if row in self.command_rows]
        if matching_command_rows: matching_rows = matching_command_rows
        if len(matching_rows) > 0: matching_row = matching_rows[0]
        else: matching_row = nan
        return matching_row
    def set_matching_row(self,row):
        self.goto(row)
    matching_row = property(get_matching_row,set_matching_row)

    def get_matching_rows(self):
        """List of rows that matches the actual settings, as 0-based integer"""
        matching_rows = []
        from numpy import nan
        positions  = self.current_positions[:]
        for row in range(0,self.nrows):
            if self.row_matches(row,positions=positions):
                matching_rows += [row]
        return matching_rows
    def set_matching_rows(self,rows):
        for row in rows: self.define(row)
    matching_rows = property(get_matching_rows,set_matching_rows)

    def row_matches(self,row,positions=None):
        """Does this row match the actual settings?
        row: 0-based integer"""
        if positions is None: positions = self.current_positions[:]
        matches = all([self.matches(row,im,positions[im]) for im in range(0,self.n_motors)])
        return matches

    @property
    def closest_row(self):
        """Find the row the is closest to the actual settings,
        as 0-based integer"""
        from numpy import nan
        closest_rows = self.closest_rows
        closest_command_rows = [row for row in closest_rows if row in self.command_rows]
        if len(closest_command_rows)>0: closest_rows = closest_command_rows
        if len(closest_rows) > 0: closest_row = closest_rows[0]
        else: closest_row = nan
        return closest_row

    @property
    def closest_rows(self):
        """Find the row the is closest to the actual settings,
        as 0-based integer"""
        from numpy import zeros,array,average,sqrt,nanmin,where,isfinite,isnan,nan
        closest = []
        pos = self.current_positions[:]
        dist = zeros(self.nrows)
        for row in range(0,self.nrows):
            distances = array([self.distance(row,im,pos[im])
                for im in range(0,self.n_motors)])
            distances = distances[~isnan(distances)]
            dist[row] = sqrt(average(distances**2))
        min_dist = nanmin(dist)
        if isfinite(min_dist): closest = list(where(dist == min_dist)[0])
        return closest

    def stop(self):
        """To cancel any move"""
        for j in range(0,self.n_motors):
            motor = self.motors[j]
            if hasattr(motor,"stop"): motor.stop()

    def goto(self,row):
        self.command_rows = [row]
        self.applying = True

    from thread_property import thread_property
    applying = thread_property("apply")

    def apply(self):
        """Move all motors motors to nominal positions
        row: zero-based index"""
        for motor_number in range(0,self.n_motors):
            ##if not self.motor_applied(motor_number): 
                self.current_positions[motor_number] = self.nominal_positions[motor_number]
                if self.serial:
                    from time import sleep
                    while getattr(self.motors[motor_number],"moving",False): sleep(0.1)

    def get_applied(self):
        """Is the nominal configuration currently active?"""
        applied = True
        for motor_number in range(0,self.n_motors):
            if not self.motor_applied(motor_number): applied = False; break
        return applied
    def set_applied(self,value):
        if value: self.applying = True
    applied = property(get_applied,set_applied)

    @property
    def motors_applied(self):
        return [self.motor_applied(motor_number) for motor_number in range(0,self.n_motors)]

    def motor_applied(self,motor_number):
        """Reassert current posistion for this motor number?"""
        actual_pos = self.current_positions[motor_number]
        nominal_pos = self.nominal_positions[motor_number]
        if self.is_numeric(motor_number):
            motor_applied = self.position_matches(nominal_pos,actual_pos,motor_number)
        else: # string-valued
            motor_applied = (nominal_pos == actual_pos)
            if self.is_configuration(motor_number):
                if not self.configuration(motor_number).applied: motor_applied = False
        return motor_applied

    def define(self,row):
        """Remember the current motor positions
        row: zero-based index"""
        for i in range(0,self.n_motors):
            self.positions[i][row] = self.command_positions[i]

    def update_timestamp(self,row):
        self.updated[row] = self.current_timestamp

    @property
    def current_timestamp(self):
        from time import strftime
        timestamp = strftime("%Y-%m-%d %H:%M:%S") # 2019-01-28 13:24:52
        return timestamp

    def get_positions_match(self):
        """Usage: self.positions_match[motor_number][row]"""
        return self.Positions_Match(self)
    def set_positions_match(self,value): pass
    positions_match = property(get_positions_match,set_positions_match)

    class Positions_Match(object):
        """Usage: self.positions[motor_number][row]
        or: self.positions[motor_number][row] = value"""
        def __init__(self,configuration):
            self.configuration = configuration
        def __getitem__(self,i):
            if type(i) == slice: value = [x for x in self]
            else:
                motor_number = i
                rows = range(0,self.configuration.nrows)
                value = [self.configuration.matches(row,motor_number) for row in rows]
            return value
        def __len__(self): return self.configuration.n_motors
        def __iter__(self):
            for i in range(0,len(self)):
                if i < len(self): yield self[i]

    def matches(self,row,motor_number,actual_pos=None):
        """True of False
        row: 0-based index
        motor_number: column, 0-based index
        actual_pos: current position of motor number *motor_number*
            (optional, given to speed up calculation)
        """
        if actual_pos is None:
            actual_pos = self.current_positions[motor_number]
        nominal_pos = self.positions[motor_number][row]
        if self.is_numeric(motor_number):
            matches = self.position_matches(nominal_pos,actual_pos,motor_number)
        else: # string-valued
            matches = self.string_matches(nominal_pos,actual_pos,motor_number)
        ##debug("%s, row %r, col %r: %r==%r? %r" %
        ##    (self.name,row,motor_number,actual_pos,nominal_pos,matches))
        return matches

    def position_matches(self,nominal_pos,actual_pos,motor_number):
        tolerance = self.tolerance[motor_number]
        matches = not abs(nominal_pos - actual_pos) > tolerance
        return matches

    def distance(self,row,motor_number,actual_pos):
        """Positional difference
        row: 0-based index
        motor_number: column, 0-based index
        actual_pos: current position of motor
        """
        from numpy import inf,nan
        nominal_pos = self.positions[motor_number][row]
        if self.is_numeric(motor_number):
           distance = abs(nominal_pos - actual_pos)
        else: # string-valued
            if actual_pos == "" or nominal_pos == "": distance = nan
            elif self.string_matches(nominal_pos,actual_pos,motor_number): distance = 0
            else: distance = inf
        return distance

    def string_matches(self,nominal_pos,actual_pos,motor_number):
        matches = (nominal_pos == actual_pos)
        if self.multiple_selections:
            # e.g. actual_pos='NIH:H-1_ps,NIH:H-56_ps', nominal_pos='NIH:H-1_ps'
            matches = nominal_pos in actual_pos and nominal_pos != ""
            if actual_pos == "" and nominal_pos == "": matches = True
        ##debug("matches(%r,%r): %r" % (nominal_pos,actual_pos,matches))
        return matches

    def default_value(self,motor_number):
        """Not a Number (nan) or empty string ("")
        motor_number: 0-based index"""
        from numpy import nan
        default_value = nan if self.is_numeric(motor_number) else ""
        return default_value

    @property
    def are_numeric(self):
        return [self.is_numeric(i) for i in range(0,self.n_motors)]

    def is_numeric(self,motor_number):
        """If the motor position a number?
        motor_number: 0-based index"""
        format = self.formats[motor_number]
        # "%s" -> False, "%.3f" -> True
        is_numeric = False if "s" in format else True
        return is_numeric

    def get_updated(self): return self.Values(self,"updated","")
    def set_updated(self,value): self.updated[:] = value
    updated = property(get_updated,set_updated)

    def get_positions(self):
        """Usage: self.positions[motor_number][row]
        or: self.positions[motor_number][row] = value"""
        return self.Positions(self)
    def set_positions(self,value): self.positions[:] = value
    positions = property(get_positions,set_positions)

    class Positions(object):
        """Usage: self.positions[motor_number][row]
        or: self.positions[motor_number][row] = value"""
        def __init__(self,configuration):
            self.configuration = configuration
        def __getitem__(self,i):
            from numpy import nan
            if type(i) == slice: value = [x for x in self]
            else: value = self.configuration.Values(self.configuration,
                self.configuration.motor_names[i],
                self.configuration.default_value(i))
            return value
        def __setitem__(self,i,value):
            if type(i) == slice:
                for j in range(0,len(value)): self[j] = value[j]
            else: self[i][:] = value
        def __len__(self): return self.configuration.n_motors
        def __iter__(self):
            for i in range(0,len(self)):
                if i < len(self): yield self[i]

    class Values(object):
        def __init__(self,configuration,name,default_value):
            self.configuration = configuration
            self.name = name
            self.default_value = default_value
        def __getitem__(self,row):
            from DB import db
            if type(row) == slice: value = [x for x in self]
            else: value = db(self.db_key(row),self.default_value)
            return value
        def __setitem__(self,row,value):
            ##debug("configuration.Values[%r] = %r" % (row,value))
            if type(row) == slice:
                for i in range(0,len(value)): self[i] = value[i]
            elif value != self[row]:
                from DB import dbset
                dbset(self.db_key(row),value)
                if self.name not in ["description","updated"]:
                    debug("self.configuration.update_timestamp(%r)" % row)
                    self.configuration.update_timestamp(row)
        def db_key(self,row):
            key = "%s.line%d.%s" % (self.configuration.name,int(row),self.name)
            return key
        def __len__(self): return self.configuration.nrows
        def __repr__(self): return "%s.Values(%r,%r)" % \
            (self.configuration.name,self.name,self.default_value)
        def __iter__(self):
            for i in range(0,len(self)):
                if i < len(self): yield self[i]

    def __repr__(self): return "configuration(%r)" % self.name

    def __getattr__(self,name):
        """Usage example: SAXS_WAXS_methods.passes_per_image.value"""
        if name in self.names: return self.Property(self,name)
        else: raise AttributeError("Is %r a name?" % name)

    class Property(object):
        """Usage example: SAXS_WAXS_methods.passes_per_image.value"""
        def __init__(self,configuration,name):
            self.configuration = configuration
            self.name = name

        def get_value(self):
            return self.configuration.current_positions[self.motor_num]
        def set_value(self,value):
            self.configuration.current_positions[self.motor_num] = value
        value = property(get_value,set_value)

        def get_command_value(self):
            return self.configuration.nominal_positions[self.motor_num]
        command_value = property(get_command_value,set_value)

        @property
        def motor_num(self): return self.configuration.names.index(self.name)
        def __repr__(self): return "%r.%s" % (self.configuration,self.name)

    def resize(self,values,length,default_value=None,template=None):
        """Change the length of a list by truncating it or appending new items
        using default_value.
        template: e.g. "motor%d", will be expanded to "motor0","motor1",...
        """
        values = list(values)
        while len(values) < length:
            if template: value = self.format_string(template,len(values))
            else: value = default_value
            values.append(value)
        while len(values) > length: values.pop()
        return values

    def format_string(self,string,value):
        """ format="motor%d",value=1 -> "motor1" """
        try: formatted_string = string % value
        except: formatted_string = string
        return formatted_string
           
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
    ##from instrumentation import * # -> globals()

    ##name = ""
    name = "beamline_configuration"
    ##name = "sequence_modes"
    ##name = "Julich_chopper_modes"
    ##name = "heat_load_chopper_modes"
    ##name = "timing_modes"
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
    ##self = configuration(name=name,locals=locals(),globals=globals())
    print("self.name=%r" % self.name)
    print("self.motor_names[:]")
    print("self.current_positions[:]")
    print("self.goto(0)")
    ##print("self.define(4)")
    print("self.matching_description")
    print("self.closest_description")
    print("self.command_description")
    print("self.value")
    print("self.command_value")
    print("self.command_rows")
    print("self.matching_rows")
    print("self.closest_rows")
    print("self.apply()")
    print("self.applied")
    print("self.motors_applied")
    
