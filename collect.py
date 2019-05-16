#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2018-10-09
Date last modified: 2019-05-13
"""
__version__ = "1.13" # temperature ramp server

from logging import debug,info,warn,error
import traceback

class Collect(object):
    """Data collection"""
    cancelled = False

    from persistent_property import persistent_property
    delay_configuration = persistent_property("delay","")
    power_configuration = persistent_property("power","power(T0=1.0, N_per_decade=4, N_power=6, reverse=False)")
    temperatures = persistent_property("temperatures","ramp(low=-18,high=120,step=0.5,hold=10,repeat=3)")
    temperature_wait = persistent_property("temperature_wait",0)
    temperature_idle = persistent_property("temperature_idle",22.0)
    
    basename = persistent_property("basename","test")
    xray_image_extension = persistent_property("xray_image_extension","mccd")
    description = persistent_property("description","[Add description here]")
    logfile_basename = persistent_property("logfile_basename","test")
    directory_string = persistent_property("directory","//femto-data/C/Data")

    variables = ["Delay","Laser_on","Temperature","Repeat","Power","Scan_Motor"]
    collection_order = persistent_property("collection_order","")
    finish_series = persistent_property("finish_series",False)
    finish_series_variable = persistent_property("finish_series_variable","Temperature")

    scan_points = persistent_property("scan_points","")
    scan_return = persistent_property("scan_return",0)
    scan_relative = persistent_property("scan_relative",0)
    scan_motor_name = persistent_property("scan_motor","")
    scan_origin = persistent_property("scan_origin",0.0)

    detector_configuration = persistent_property("detector_configuration","")

    def get_directory(self):
        from normpath import normpath
        return normpath(self.directory_string)
    def set_directory(self,value): self.directory_string = value
    directory = property(get_directory,set_directory)

    @property
    def collection_pass_count(self):
        """Into how many passes does the data collection need to be broken up?"""
        count = 1
        for i,variable in enumerate(self.collection_variables):
            wait = self.variable_wait(variable)
            N = len(self.variable_values(i))
            if wait or count > 1: count *= N
        return count

    @property
    def collection_passes(self):
        """List of integers, 0,1,...collection_pass_count-1"""
        from numpy import unique
        collection_passes = unique(self.collection_pass[~self.all_acquired])
        return collection_passes

    @property
    def all_acquired(self):
        """Aquired status for each scan point in the dataset"""
        return self.acquired(range(0,self.n))

    def acquired(self,i):
        """Aquired status for given each scan point"""
        from exists import exist_files
        acquired = exist_files(self.xray_image_filenames[i])
        return acquired

    @property
    def collection_pass(self):
        """To which collection pass does each scan point in the dataset belong?"""
        from numpy import arange
        i = arange(0,self.n)
        pass_length = self.n/self.collection_pass_count
        collection_pass = i/pass_length
        return collection_pass

    def collection_pass_ranges(self,collection_pass):
        """Pairs of starting and ending scan point numbers (range 0,,,n-1)"""
        ranges = self.ranges(self.collection_pass_i(collection_pass))
        return ranges

    @staticmethod
    def ranges(i):
        from numpy import asarray,where,diff,concatenate
        i = asarray(i)
        gaps = where(diff(i)>1)[0]
        firsts = [0] if len(i)>0 else []
        lasts = [len(i)-1] if len(i)>0 else []
        firsts = concatenate((firsts,gaps+1))
        lasts = concatenate((gaps,lasts))
        ranges = [(i[first],i[last]) for (first,last) in zip(firsts,lasts)]
        return ranges

    def collection_pass_i(self,collection_pass):
        """Image numbers of a collection pass
        collection_pass: 0,1,... collection_pass_count-1"""
        from numpy import arange
        pass_length = self.n/self.collection_pass_count
        first = pass_length*collection_pass
        i = arange(first,first+pass_length)
        i = i[~self.acquired(i)]
        return i

    @property
    def collection_first_i(self):
        first,last = self.collection_first_range
        return first

    @property
    def collection_first_range(self):
        from numpy import nan
        first,last = nan,nan
        collection_passes = self.collection_passes
        for collection_pass in self.collection_passes:
            for (first,last) in self.collection_pass_ranges(collection_pass):
                break
            break
        return first,last

    def collection_pass_first_i(self,collection_pass):
        """First image number of a collection pass
        collection_pass: 0,1,... collection_pass_count-1"""
        pass_length = self.n/self.collection_pass_count
        first = pass_length*collection_pass
        return first
    
    def collection_pass_last_i(self,collection_pass):
        """Last image number of a collection pass
        collection_pass: 0,1,...collection_pass_count-1"""
        last = self.collection_pass_first_i(collection_pass+1)-1
        return last

    def set_collection_variables(self,i,wait=False):
        """i: range 0 to self.n"""
        values = self.collection_variable_values(i)
        variables = self.collection_variables
        for variable,value in zip(variables,values):
            self.variable_set(variable,value)
        if wait: self.wait_for_collection_variables()

    def wait_for_collection_variables(self):
        """i: range 0 to self.n"""
        from time import sleep
        variables = self.collection_variables
        while any([self.variable_changing(var) for var in variables]):
            if self.cancelled: break
            self.actual(self.collection_variable_changing_report)
            sleep(0.2)

    @property
    def collection_variable_changing_report(self):
        message = ""
        for variable in self.collection_variables:
            if self.variable_changing(variable):
                value = self.variable_value(variable)
                formatted_value = self.variable_formatted_value(variable,value)
                message += "%s=%s, " % (variable,formatted_value)
        message = message.strip(", ")
        return message

    def collection_variables_dataset_start(self):
        """To be done at the beginning of the data collection"""
        for variable in self.collection_variables:
            if variable == "Scan_Motor":
                self.scan_origin = self.variable_command_value(variable)

    def collection_variables_dataset_stop(self):
        """To be done at the end of the data collection"""
        for variable in self.collection_variables:
            if variable == "Temperature":
                self.variable_set(variable,self.temperature_idle)
            if variable == "Scan_Motor":
                if self.scan_return:
                    self.variable_set(variable,self.scan_origin)

    collection_values = {}
    
    def collection_variables_start(self):
        self.collection_values = {}
        for variable,values in zip(self.collection_variables,self.collection_variable_all_values):
            if variable == "Repeat": continue
            if variable == "Temperature": continue
            self.collection_values[variable] = values
        from timing_system import timing_system
        for variable in self.collection_values:
            timing_system.image_number.monitor(self.collection_variables_handle_image_number_update,variable)

    def collection_variables_stop(self):
        from timing_system import timing_system
        for variable in self.collection_values:
            timing_system.image_number.monitor_clear(self.collection_variables_handle_image_number_update,variable)
        self.collection_values = {}

    def collection_variables_handle_image_number_update(self,variable):
        from timing_system import timing_system
        i = timing_system.image_number.count
        collection_values = dict(self.collection_values)
        if variable in collection_values:
            if 0 <= i < len(collection_values[variable]):
                value = collection_values[variable][i]
                debug("Image %r: Setting collection variable %s=%r..." % (i,variable,value))
                self.variable_set(variable,value)
                debug("Image %r: Setting collection variable %s=%r done" % (i,variable,value))
                
    def variable_value(self,variable):
        """Current read-back value"""
        from numpy import nan
        value = nan
        if variable == "Temperature":
            from instrumentation import temperature_controller
            value = temperature_controller.value
        if variable == "Power":
            from instrumentation import trans2
            value = trans2.value
        if variable == "Scan_Motor":
            return self.scan_motor.value
        return value

    def variable_command_value(self,variable):
        """Nominal value"""
        from numpy import nan
        value = nan
        if variable == "Temperature":
            from instrumentation import temperature_controller
            value = temperature_controller.command_value
        if variable == "Power":
            from instrumentation import trans2
            value = trans2.value # has no attribute 'command_value'
        if variable == "Scan_Motor":
            return self.scan_motor.command_value
        return value

    def variable_set(self,variable,value):
        if variable != "Repeat":
            formatted_value = self.variable_formatted_value(variable,value)
            self.actual("%s=%s" % (variable,formatted_value))

        if variable == "Temperature":
            from instrumentation import temperature_controller
            if temperature_controller.command_value != value:
                temperature_controller.command_value = value
                self.temperature_changed = True
        if variable == "Power":
            from instrumentation import trans2
            trans2.value = value
        if variable == "Scan_Motor":
            self.scan_motor.value = value

    def variable_changing(self,variable):
        changing = False
        if variable == "Temperature":
            from instrumentation import temperature_controller
            changing = temperature_controller.moving or self.temperature_changed
        if variable == "Power":
            from instrumentation import trans2
            changing = trans2.moving
        if variable == "Scan_Motor":
            changing = self.scan_motor.moving
        return changing

    # The "moving" property does not update immediately.
    # As a workaraound keep track of the last change and wait for 2s
    # before consulting the "moving" property.
    temperature_last_changed = 0
    def get_temperature_changed(self):
        from time import time
        return time() - self.temperature_last_changed < 5.0
    def set_temperature_changed(self,value):
        from time import time
        if value: self.temperature_last_changed = time()
    temperature_changed = property(get_temperature_changed,set_temperature_changed)        

    def collection_variable_values(self,i):
        """i: range 0 to self.n"""
        values = []
        for j,n in enumerate(self.collection_variable_indices(i)):
            values += [self.variable_values(j)[n]]
        return values

    def collection_all_values(self,variable):
        """variable: e.g. 'Temperature'"""
        values = []
        if variable in self.collection_variables:
            i = self.collection_variables.index(variable)
            values = self.collection_variable_all_values[i]
        return values

    @property
    def collection_variable_all_values(self):
        """i: variable index: 0 to len(self.collection_variables)-1"""
        from numpy import array,repeat,tile,vstack
        values_list = []
        for (i,variable) in enumerate(self.collection_variables):
            values_list += [self.variable_values(i)]
        all_values = values_list[0]
        for values in values_list[1:]:
            all_values = vstack([
                tile(all_values,len(values)),
                repeat(values,len(all_values)),
            ])
        return all_values

    @property
    def collection_variable_count(self):
        """How many nested loops?"""
        return len(self.collection_variables)

    def collection_variable_indices(self,i):
        """List of integers of length self.collection_variable_count
        range 0 to self.collection_variable_counts
        i: range 0 to self.n"""
        indices = []
        for n in self.collection_variable_counts:
            indices += [i % n]
            i /= n
        return indices

    @property
    def collection_variable_counts(self):
        """Number of scan points for each nested loop"""
        counts = []
        for i in range(0,self.collection_variable_count):
            counts += [len(self.variable_values(i))]
        return counts

    @property
    def n(self):
        """Number of scan points in a dataset"""
        n = 1
        for i in self.collection_variable_counts: n *= i
        return n

    @property
    def collection_variables(self):
        variables = []
        for variable in self.collection_variables_with_options:
            if "=" in variable: variable = variable.split("=")[0]
            variables += [variable]
        return variables

    @property
    def collection_variables_with_options(self):
        """e.g. 'Laser_on=[0,1]', 'Repeat=16' """
        from expand_sequence import split_list
        variables = split_list(self.collection_order.replace(" ",""))
        return variables

    def variable_values(self,i):
        """i range 0 to len(collection_variables)"""
        # For choices encoded in the "collection_order" string
        # e.g. Repeat=16, Laser_on=[0,1]
        variable = self.collection_variables[i]
        if variable == "Repeat": values = range(0,self.repeat_count(i))
        elif variable == "Laser_on": values = self.laser_on_list(i)
        else: values = self.variable_choices(variable)
        return values

    def variable_choices(self,variable):
        # For choices encoded outside the "collection_order" string
        # in searate tables.
        if variable == "Temperature": choices = self.temperature_list
        elif variable == "Power": choices = self.power_list
        elif variable == "Scan_Motor": choices = self.scan_point_list
        elif variable == "Delay": choices = self.delay_sequences
        else: choices = []
        return choices

    def variable_wait(self,variable):
        """Suspend collection while changing this variable?"""
        if variable == "Temperature": wait = self.temperature_wait
        elif variable == "Power": wait = True
        elif variable == "Scan_Motor": wait = False
        else: wait = False
        return wait

    def variable_formatted_value(self,variable,value):
        from time_string import time_string
        text = str(value)
        if variable == "Delay": text = time_string(value.nom_delay)
        if variable == "Temperature": text = "%.3fC" % value
        if variable == "Laser_on": text = "on" if value else "off"
        if variable == "Power": text = "%.4f" % value
        if variable == "Scan_Motor": text = "%.04f" % value
        if variable == "Repeat": text = "%02d" % (value+1)
        return text

    def repeat_count(self,i):
        """i: collection variable number 0...len(collection_variables)"""
        count = 0
        variables = self.collection_variables_with_options
        if 0 <= i <= len(variables):
            variable = variables[i]
            if variable.startswith("Repeat="):
                count_string = variable.split("=")[-1]
                try: count = int(eval(count_string))
                except Exception,msg:
                    error("%s: %s: %s: %s: expecting int" %
                        (collection_order,variable,count_string,msg))
        return count

    def laser_on_list(self,i):
        """i: collection variable number 0...len(collection_variables)"""
        values = [1]
        variables = self.collection_variables_with_options
        if 0 <= i <= len(variables):
            variable = variables[i]
            if variable.startswith("Laser_on="):
                values_string = variable.split("=")[-1]
                try: values = eval(values_string)
                except Exception,msg:
                    error("%s: %s: %s: %s: expecting int" %
                        (collection_order,variable,values_string,msg))
        return values

    @property
    def delay_list(self):
        delay_list = [s.nom_delay for s in self.delay_sequences]
        return delay_list

    @property
    def delay_sequences(self):
        from expand_sequence import delay_sequences
        from Ensemble_SAXS_pp import Sequence
        sequences = Sequence()
        expr = self.delay_configuration
        if expr:
            try: expr = delay_sequences(expr)
            except Exception,msg:
                error("delay_sequences: %r: %s\n%s" % (expr,msg,traceback.format_exc()))
                expr = ""
        if expr:
            try: sequences = eval(expr)
            except Exception,msg:
                error("%s: %s\n%s" % (expr,msg,traceback.format_exc()))
        sequences = self.as_list(sequences)
        return sequences

    @property
    def temperature_list(self):
        """List of temperature setpoints for dataset"""
        values = self.expand_sequence(self.temperatures)
        return values

    def temperature_start(self):
        if "Temperature" in self.collection_variables and \
            self.variable_wait("Temperature") == False:
            self.actual("Temperature start...")
            from linear_ranges import linear_ranges
            image_numbers,temperatures = \
                linear_ranges(self.collection_all_values("Temperature"))
            times = image_numbers * self.image_acquisition_time
            from temperature_Friedrich import temperature
            self.actual("Temperature uploading ramp...")
            temperature.time_points = list(times)
            temperature.temp_points = list(temperatures)
            self.actual("Temperature started")

    def temperature_stop(self):
        if "Temperature" in self.collection_variables and \
            self.variable_wait("Temperature") == False:
            self.actual("Temperature stop...")
            from temperature_Friedrich import temperature
            temperature.time_points = []
            temperature.temp_points = []
            self.actual("Temperature stopped")

    @property
    def image_acquisition_time(self):
        sequences = self.sequences
        N = sum([sequence.period for sequence in sequences])
        ##T = sequences[0].tick_period()
        from timing_system import timing_system
        T = timing_system.hsct
        t = N * T
        return t
            
    @property
    def temperature_count(self):
        """List of temperature setpoints for dataset"""
        return len(self.temperature_list)

    @property
    def power_list(self):
        values = self.expand_sequence(self.power_configuration)
        return values

    @property
    def scan_point_list(self):
        """List of positions of *scan_motor* for dataset"""
        from expand_sequence import expand_sequence
        from numpy import array
        values = self.expand_sequence(self.scan_points)
        values = array(values)
        if self.scan_relative: values += self.scan_origin
        return values

    @staticmethod
    def expand(expr):
        values = []
        from expand_sequence import expand
        if expr:
            try: expr = expand(expr)
            except Exception,msg:
                error("expand_sequence: %r: %s\n%s" % (expr,msg,traceback.format_exc()))
                expr = ""
        if expr:
            try: values = eval(expr)
            except Exception,msg:
                error("%s: %s\n%s" % (expr,msg,traceback.format_exc()))
        values = Collect.as_list(values)
        return values

    @staticmethod
    def expand_sequence(expr):
        values = []
        from expand_sequence import expand_sequence
        if expr:
            try: expr = expand_sequence(expr)
            except Exception,msg:
                error("expand_sequence: %r: %s\n%s" % (expr,msg,traceback.format_exc()))
                expr = ""
        if expr:
            try: values = eval(expr)
            except Exception,msg:
                error("%s: %s\n%s" % (expr,msg,traceback.format_exc()))
        values = Collect.as_list(values)
        return values
    
    @staticmethod
    def as_list(value):
        if not hasattr("__len__",value) or isinstance(value,str):
            value = [value]
        return value

    @property
    def scan_motor(self):
        exec("from instrumentation import *")
        return eval(self.scan_motor_name)

    @property
    def detector_names(self):
        """e.g. 'xray_detector', 'xray_scope', 'laser_scope'"""
        from expand_sequence import split_list
        names = split_list(self.detector_configuration.replace(" ",""))
        return names

    @property
    def info_message(self):
        if self.dataset_complete: message = "Dataset complete"
        elif self.current > self.n: message = "Collection completed"
        else:
            i = self.current if self.acquiring else self.collection_first_i
            message = "%s %s of %s" % (self.scan_point_name,i+1,self.n)
            if i < self.n: message += ": "+self.scan_point_filename(i)
        message = message[0:1].upper()+message[1:]
        return message

    status_message = ""
    actual_message = ""

    def acquisition_status(self,i):
        """Progress Message"""
        message = "Acquiring %s %d of %d" % (self.scan_point_name,i+1,self.n)
        message += ": "+self.scan_point_filename(i)
        values = self.collection_variable_values(i)
        variables = self.collection_variables
        for variable,value in zip(variables,values):
            formatted_value = self.variable_formatted_value(variable,value)
            message += ", %s %s" % (variable,formatted_value)
        return message

    @property
    def scan_point_name(self):
        name = "scan point"
        if "xray_detector" in self.detector_names: name = "image" 
        return name

    def scan_point_filename(self,i):
        self.file_basename(i)
        if "xray_detector" in self.detector_names:
            from os.path import basename
            name = basename(self.xray_image_filename(i))
        elif "xray_scope" in self.detector_names:
            ##filenames = self.xray_scope_trace_filenames
            name = self.file_basename(i)
        else: name = self.file_basename(i)
        return name

    @property
    def current(self):
        """Current image number"""
        from timing_system import timing_system
        current = timing_system.image_number.count
        return current

    @property
    def acquiring(self):
        """Timing system currently in 'acquiring' state'?"""
        from timing_system import timing_system
        acquiring = timing_system.acquiring.count
        return acquiring

    @property
    def dataset_complete(self):
        from exists import exist_files
        filenames = self.xray_image_filenames
        dataset_complete = all(exist_files(filenames))
        return dataset_complete

    @property
    def dataset_started(self):
        started = \
            len(self.xray_images_collected) > 0 or \
            len(self.xray_scope_traces_collected) > 0 or \
            len(self.laser_scope_traces_collected) > 0 or \
            sum(self.logfile_has_entries(self.xray_image_filenames)) > 0
        return started

    from thread_property import thread_property
    erasing_dataset = thread_property("erase_dataset")

    def erase_dataset(self):
        self.actual("Erasing Dataset...")
        for i,filename in enumerate(self.xray_images_collected):
            self.actual("Erasing X-ray image %r" % (i+1))
            if self.cancelled: break
            self.remove(filename)
        for i,filename in enumerate(self.xray_scope_traces_collected):
            self.actual("Erasing X-ray scope trace %r" % (i+1))
            if self.cancelled: break
            self.remove(filename)
        for i,filename in enumerate(self.laser_scope_traces_collected):
            self.actual("Erasing Laser scope trace %r" % (i+1))
            if self.cancelled: break
            self.remove(filename)
        filenames = self.xray_image_filenames
        if sum(self.logfile_has_entries(filenames)) > 0:
            self.actual("Cleaning Logfile...")
            self.logfile_delete_filenames(filenames)
        self.actual("Dataset erased")

    @staticmethod
    def remove(filename):
        from os import remove
        try: remove(filename)
        except Exception,msg: warn("remove %r: %s" % (filename,msg))
        
    @property
    def xray_images_collected(self):
        from exists import exist_files
        filenames = self.xray_image_filenames
        xray_images_collected = filenames[exist_files(filenames)]
        return xray_images_collected

    @property
    def xray_scope_traces_collected(self):
        from exists import exist_files
        filenames = self.xray_scope_trace_filenames
        filenames = filenames[exist_files(filenames)]
        return filenames

    @property
    def xray_scope_all_traces_collected(self):
        from exists import exist_files
        filenames = self.xray_scope_all_trace_filenames
        filenames = filenames[exist_files(filenames)]
        return filenames

    @property
    def laser_scope_traces_collected(self):
        from exists import exist_files
        filenames = self.laser_scope_trace_filenames
        filenames = filenames[exist_files(filenames)]
        return filenames

    def status(self,message):
        if message: info(message)
        self.status_message = message

    def actual(self,message):
        if message: info(message)
        self.actual_message = message

    from thread_property import thread_property
    collecting_dataset = collecting = thread_property("collect_dataset")

    def collect_dataset(self):
        self.status("Collection started")

        self.collection_variables_dataset_start()
        # for temperature equilibration
        self.set_collection_variables(self.collection_first_i,wait=False) 
        
        self.timing_system_start()
        self.timing_system_setup()
        self.xray_detector_start()
        self.xray_scope_start()
        self.laser_scope_start()
        self.diagnostics_start()
        self.logging_start()
        self.temperature_start()
        self.collection_variables_start()
        self.update_status_start()

        for collection_pass in self.collection_passes:
            if self.cancelled: break
            for (first,last) in self.collection_pass_ranges(collection_pass):
                if self.cancelled: break
                self.timing_system_setup(first,last)
                self.set_collection_variables(first,wait=True)
                self.acquisition_start()
                
                for i in range(first,last+1):
                    if self.cancelled: break
                    self.acquire(i)
                self.status("Collection suspended")

        self.update_status_stop()
        self.collection_variables_stop()
        self.temperature_stop()
        self.diagnostics_stop()
        self.timing_system_stop()
        self.collection_variables_dataset_stop()
        self.play_sound()
        self.sleep(5)
        self.logging_stop()
        self.laser_scope_stop()
        self.xray_scope_stop()
        self.sleep(5)
        self.xray_detector_stop()

        self.status("Collection ended")

    def update_status_start(self):
        from timing_system import timing_system
        timing_system.image_number.monitor(self.update_status_handle_image_number_update)

    def update_status_stop(self):
        from timing_system import timing_system
        timing_system.image_number.monitor_clear(self.update_status_handle_image_number_update)

    def update_status_handle_image_number_update(self):
        from timing_system import timing_system
        i = timing_system.image_number.count
        ##debug("image_number %r" % i)
        self.status(self.acquisition_status(i))

    def acquire(self,i):
        """Acquire one scan point"""
        self.status(self.acquisition_status(i))
        self.wait_for(i)

    def wait_for(self,i):
        """Follow the data collection for one image"""
        from time import sleep
        while not self.completed(i) and not self.cancelled: sleep(0.02)

    def completed(self,i):
        from timing_sequence import timing_sequencer
        if self.current > i: completed = True
        elif not timing_sequencer.queue_active: completed = True
        else: completed = False
        if completed: debug("Completed %r" % i)
        return completed

    from thread_property import thread_property
    generating_packets = thread_property("generate_packets")

    def generate_packets(self):
        self.actual("Generating packets: started")
        self.sequencer_packets
        self.actual("Generating packets: done")

    @property
    def sequencer_packets(self):
        """Generate the binary packets for the Piano Player timing sequencer"""
        packets = []
        sequences = self.sequences
        for i,sequence in enumerate(sequences):
            if self.cancelled: break
            ##self.actual("Checking packets: %d/%d" % (i+1,len(sequences)))
            if not sequence.is_cached:
                self.actual("Generating packets: %d/%d" % (i+1,len(sequences)))
            packets += [sequence.data]
        return packets

    def sequence_properites(self,property_name):
        """property_name:
           laser_on
           delay
           nom_delay
           pump_on
           following_pump_on
        """
        properties = [getattr(s,property_name) for s in self.sequences]
        return properties

    @property
    def sequences(self):
        from Ensemble_SAXS_pp import Sequences
        # Update "following_delay" properties
        sequences = Sequences(sequences=self.sequences_simple)[:]
        return sequences

    @property
    def sequences_simple(self):
        from Ensemble_SAXS_pp import Sequences
        sequences = Sequences(acquiring=1,image_number_inc=0)[:]
        sequences[-1].image_number_inc = 1
        
        for i,variable in enumerate(self.sequence_variables):
            choices = self.variable_values(i)
            values = self.repeat(choices,len(sequences))
            sequences = self.tile(sequences,len(choices))
            for s,value in zip(sequences,values):
                if variable == "Laser_on":
                    # Selectively turn the laser OFF if ON in the sequence
                    # configuration, however do not turn in ON if OFF by
                    # default.
                    s.laser_on &= value
                if variable == "Delay": s.update(value)
        return sequences

    @property
    def sequence_variables(self):
        """Which variable changes are handled by the timing sequence?"""
        sequence_variables = []
        for i,variable in enumerate(self.collection_variables):
            if self.variable_wait(variable): break
            else: sequence_variables += [variable]
        while len(sequence_variables) > 0 and sequence_variables[-1] not in ["Delay","Laser_on"]:
            sequence_variables = sequence_variables[:-1]
        return sequence_variables

    @staticmethod
    def tile(list,n):
        """tile([1,2,3],2) -> [1,2,3,1,2,3]"""
        from copy import deepcopy
        new_list = []
        for i in range(0,n):
            for elem in list: new_list.append(deepcopy(elem))
        return new_list

    @staticmethod
    def repeat(list,n):
        """tile([1,2,3],2) -> [1,1,2,2,3,3]"""
        from copy import deepcopy
        new_list = []
        for elem in list:
            for i in range(0,n): new_list.append(deepcopy(elem))
        return new_list

    @staticmethod
    def as_list(x):
        if not hasattr(x,"__len__") or isinstance(x,str): x = [x]
        return x

    @property
    def xray_images_per_sequence_queue(self):
        """How many X-ray images per repeating sequece pattern?"""
        xray_images = sum([s.xdet_on for s in self.sequences])
        return xray_images

    @property
    def sequences_per_xray_image(self):
        """How many single timining sequences (=packets) per X-ray image"""
        sequences = self.sequences
        xray_images = sum([s.xdet_on for s in sequences])
        sequences_per_xray_image = len(sequences)/xray_images
        return sequences_per_xray_image

    @property
    def sequences_per_xray_image2(self):
        """Periodic repeating pattern
        How many single timining sequences (=packets) per X-ray image"""
        xdet_on = [s.xdet_on for s in self.sequences]
        return xdet_on

    def timing_system_start(self):
        self.actual("Timing system start...")
        from timing_sequence import timing_sequencer
        timing_sequencer.set_queue_sequences(self.sequences)
        self.actual("Timing system started")

    def timing_system_stop(self):
        self.actual("Timing system stop...")
        from timing_sequence import timing_sequencer
        # Leave acquistion mode at the next sequence_count (fast). 
        timing_sequencer.next_queue_sequence_count = -1
        timing_sequencer.queue_active = False
        self.actual("Timing system stopped")

    def timing_system_setup(self,first=None,last=None):
        self.actual("Timing system setup...")
        if first is None or last is None:
            first,last = self.collection_first_range

        N = self.xray_images_per_sequence_queue
        from timing_sequence import timing_sequencer
        timing_sequencer.queue_active = False
        from numpy import isnan
        if not isnan(first):
            timing_sequencer.queue_repeat_count = first/N
        if not isnan(last):
            timing_sequencer.queue_max_repeat_count = (last+1)/N
        # Switch from idle to acquistion mode only when sequence_count = 0.
        timing_sequencer.next_queue_sequence_count = 0
        timing_sequencer.queue_sequence_count = 0
        from timing_system import timing_system
        timing_system.image_number.count = first
        timing_system.xdet_acq_count.count = first
        timing_system.pass_number.count = 0
        timing_system.pulses.count = 0
        Ntrace = self.sequences_per_xray_image
        timing_system.xosct_acq_count.count = first * Ntrace
        timing_system.losct_acq_count.count = first * Ntrace
        
        self.actual("Timing system setup complete")

    def acquisition_start(self):
        self.timing_system_acquisition_start()
        
    def timing_system_acquisition_start(self):
        self.actual("Timing system acquisition start...")

        from timing_sequence import timing_sequencer
        timing_sequencer.queue_active = True
        from time import sleep
        while not timing_sequencer.queue_active and not self.cancelled:
            self.actual("Timing system acquisition start: sequence count %s"
                % timing_sequencer.current_queue_sequence_count)
            sleep(0.1)

        self.actual("Timing system acquisition started")

    def xray_detector_start(self):
        if "xray_detector" in self.detector_names:
            filenames = self.xray_image_filenames
            self.actual("X-ray detector acqisition start...")
            from instrumentation import xray_detector
            image_numbers = range(1,self.n+1)
            xray_detector.acquire_images(image_numbers,filenames)
            self.actual("X-ray detector acqisition started")

    def xray_detector_stop(self):
        if "xray_detector" in self.detector_names:
            self.actual("X-ray detector acqisition stop...")
            from instrumentation import xray_detector
            xray_detector.cancel_acquisition()
            self.actual("X-ray detector acqisition stopped")

    def xray_scope_start(self):
        if "xray_scope" in self.detector_names:
            filenames = self.xray_scope_trace_filenames
            self.actual("X-ray Scope Start...")
            filename_dict = dict([(i+1,f) for (i,f) in enumerate(filenames)])
            from instrumentation import xray_scope
            xray_scope.trace_filenames = filename_dict
            xray_scope.trace_acquisition_running = True
            self.actual("X-ray Scope Started")

    def xray_scope_stop(self):
        if "xray_scope" in self.detector_names:
            self.actual("X-ray Scope Stop...")
            from instrumentation import xray_scope
            xray_scope.trace_acquisition_running = False
            xray_scope.trace_filenames = {}
            self.actual("X-ray Scope Stopped")

    def laser_scope_start(self):
        if "laser_scope" in self.detector_names:
            filenames = self.laser_scope_trace_filenames
            self.actual("Laser Scope Start...")
            filename_dict = dict([(i+1,f) for (i,f) in enumerate(filenames)])
            from instrumentation import laser_scope
            laser_scope.trace_filenames = filename_dict
            laser_scope.trace_acquisition_running = True
            self.actual("Laser Scope Started")

    def laser_scope_stop(self):
        if "laser_scope" in self.detector_names:
            self.actual("Laser Scope Stop...")
            from instrumentation import laser_scope
            laser_scope.trace_acquisition_running = False
            laser_scope.trace_filenames = {}
            self.actual("Laser Scope Stopped")

    @property
    def xray_scope_trace_filenames(self):
        from numpy import array,chararray,repeat,tile
        filenames = self.file_basenames
        N = self.sequences_per_xray_image
        suff = array(["_%02d" % (i+1) for i in range(0,N)]).view(chararray)
        filenames = repeat(filenames,len(suff))+tile(suff,len(filenames))
        filenames = self.directory+"/xray_traces/"+filenames+".trc"
        return filenames

    @property
    def xray_scope_all_trace_filenames(self):
        """Filenames including channel suffix if mutiple traces were collected"""
        filenames = self.xray_scope_trace_filenames
        trace_sources = self.xray_scope_trace_sources
        if len(trace_sources) > 1:
            from numpy import repeat,tile
            filenames = filenames.replace(".trc","")
            filenames = repeat(filenames,len(trace_sources))+\
                "_"+tile(trace_sources,len(filenames))
            filenames = filenames+".trc"
        return filenames

    @property
    def xray_scope_trace_sources(self):
        trace_sources = [""]
        if "xray_scope" in self.detector_names:
            from instrumentation import xray_scope
            trace_sources = xray_scope.trace_sources
        from numpy import array
        trace_sources = array(trace_sources)
        return trace_sources

    @property
    def laser_scope_trace_filenames(self):
        filenames = self.xray_scope_trace_filenames
        filenames = filenames.replace("/xray_traces/","/laser_traces/")
        return filenames

    @property
    def missing_xray_scope_trace_filenames(self):
        filenames = self.xray_scope_trace_filenames
        from exists import exist_files
        missing = filenames[~exist_files(filenames)]
        return missing

    def xray_image_filename(self,i):
        ext = "."+self.xray_image_extension.strip(".")
        filename = self.directory+"/xray_images/"+self.file_basename(i)+ext
        return filename

    @property
    def xray_image_filenames(self):
        ext = "."+self.xray_image_extension.strip(".")
        filenames = self.directory+"/xray_images/"+self.file_basenames+ext
        return filenames

    def file_basename(self,i):
        filename = self.basename
        filename += "_"+"%04d" % (i+1)

        values = self.collection_variable_values(i)
        variables = self.collection_variables
        for variable,value in zip(variables,values):
            text = self.variable_formatted_value(variable,value)
            filename += "_"+text  
        return filename

    @property
    def file_basenames(self):
        """numpy chararray"""
        from numpy import array,chararray,repeat,tile
        suffixes = []
        for (i,variable) in enumerate(self.collection_variables):
            vals = self.variable_values(i)
            suff = ["_"+self.variable_formatted_value(variable,val) for val in vals]
            suff = array(suff).view(chararray)
            suffixes += [suff]
        names = array([""]).view(chararray)
        for suff in suffixes:
            names = tile(names,len(suff)) + repeat(suff,len(names))
        serial = ["_%04d" % (i+1) for i in range(0,len(names))]
        serial = array(serial).view(chararray)
        names = self.basename + serial + names
        return names

    def diagnostics_start(self):
        from diagnostics import diagnostics
        diagnostics.running = True
        self.actual("Diagnostics Started")

    def diagnostics_stop(self):
        from diagnostics import diagnostics
        diagnostics.running = False
        self.actual("Diagnostics Stopped")

    def logging_start(self):
        from timing_system import timing_system
        PV_name = timing_system.image_number.PV_name
        from CA import camonitor
        camonitor(PV_name,callback=self.logfile_handle_image_number_update)
        self.actual("Logging Started")

    def logging_stop(self):
        from timing_system import timing_system
        PV_name = timing_system.image_number.PV_name
        from CA import camonitor_clear
        camonitor_clear(PV_name)
        self.actual("Logging Stopped")

    def logfile_handle_image_number_update(self,PV_name,value,formatted_value):
        image_number = value
        ##info("image_number %r" % image_number)
        if image_number > 0: self.logfile_update(image_number-1)

    from thread import allocate_lock
    logfile_lock = allocate_lock()
    
    def logfile_update(self,i):
        """Add image information to the end of the data collection log file"""
        from time import time
        timestamp = time()
        with self.logfile_lock:
            from os.path import exists
            if not exists(self.logfile_name): self.initialize_logfile()

            file(self.logfile_name,"a").write(self.logfile_entry(i,timestamp))

    def logfile_entry(self,i,timestamp=None):
        from time import time
        if timestamp is None: timestamp = time()
        from time_string import date_time
        from diagnostics import diagnostics
        from numpy import isnan
        from os.path import basename

        started  = diagnostics.started(i)
        if isnan(started): started = timestamp
        finished = diagnostics.finished(i)
        if isnan(finished): finished = timestamp

        line = []
        line += [date_time(timestamp)]
        line += [date_time(started)]
        line += [date_time(finished)]
        line += [basename(self.xray_image_filename(i))]
        values = self.collection_variable_values(i)
        values += diagnostics.average_values(i)
        for value in values: line += [str(value)]
        line = "\t".join(line)+"\n"
        return line

    def initialize_logfile(self):
        from os.path import exists,dirname; from os import makedirs
        from diagnostics import diagnostics
        filename = self.logfile_name
        dir = dirname(filename)
        try: makedirs(dir)
        except Exception,msg:
            if not exists(dir): error("%s: %s" % (dir,msg)) 
        header = "# Data collection log file generated by collect "+\
            __version__+"\n"
        header += "# Description: "+self.description+"\n"
        labels = []
        labels += ["date time"]
        labels += ["started"]
        labels += ["finished"]
        labels += ["file"]
        labels += self.collection_variables
        labels += diagnostics.variable_names
        header += "#"+"\t".join(labels)+"\n"
        log = file(filename,"w").write(header)

    @property
    def logfile_name(self):
        return self.directory+"/"+self.logfile_basename
    
    def logfile_has_entries(self,image_filenames):
        """Is there an entry for this image in the log file?
        image_filenames: filenames of images (with or without directory)
        """
        from os.path import basename
        from numpy import array
        entries = self.logfile_entries
        return array([basename(f) in entries for f in image_filenames])

    def logfile_has_entry(self,image_filename):
        """Is there an entry for this image in the log file?
        image_filename: filename of image (with or without directory)
        """
        return self.logfile_has_entries([image_filename])[0]

    @property
    def logfile_entries(self):
        """Is there an entry for this image in the log file?
        """
        filenames = []
        try: log = file(self.logfile_name)
        except: log = None
        if log:
            lines = log.read().split("\n")
            # 'split' makes the last line an empty line.
            if lines and lines[-1] == "": lines.pop(-1)
            for line in lines:
                if line.startswith("#"): continue # Ignore comment lines.
                fields = line.split("\t")
                if len(fields)>3: filenames += [fields[3]]
        return filenames

    def logfile_timestamp(self,filename):
        """When was this image file or scope trace acquired?
        Return value: seconds since 1970-01-01 00:00:00 UTC"""
        date_time = self.logfile_timestamp_string(filename)
        from time_string import timestamp
        from numpy import nan
        seconds = timestamp(date_time) if date_time else nan
        return seconds

    def logfile_timestamp_string(self,filename):
        """When was this image file or scope trace acquired?
        Return value: string, format 1970-01-01 00:00:00"""
        line = self.logfile_line(filename)
        fields = line.split("\t")
        date_time = fields[2] if len(fields)>2 else ""
        if date_time == "": date_time = fields[0] if len(fields)>0 else ""
        return date_time

    def logfile_line(self,filename):
        """Entry for this image or scope trace in the log file
        image_filename: basename of image filename (without directory)
        """
        from os.path import splitext
        file_basename = self.file_basename_of_filename(filename)
        entry = ""
        filenames = []
        try: log = file(self.logfile_name)
        except: log = None
        if log:
            lines = log.read().split("\n")
            # 'split' makes the last line an empty line.
            if lines and lines[-1] == "": lines.pop(-1)
            for line in lines:
                if line.startswith("#"): continue # Ignore comment lines.
                fields = line.split("\t")
                entry_filename = fields[3] if len(fields)>3 else ""
                entry_basename = splitext(entry_filename)[0]
                if entry_basename == file_basename: entry = line
        return entry

    def file_basename_of_filename(self,filename):
        """E.g. 'Sample-1_0001_01_01_C1.trc' -> 'Sample-1_0001_01'"""
        from os.path import basename,splitext
        file_basename = basename(filename)
        file_basename,ext = splitext(file_basename)
        if ext.endswith("trc"):
            suffixes = ["_C%d" % (i+1) for i in range(0,4)]
            for suffix in suffixes:
                if file_basename.endswith(suffix):
                    file_basename = file_basename[0:-len(suffix)]
                    break
            suffixes = ["_%02d" % (i+1) for i in range(0,20)]
            for suffix in suffixes:
                if file_basename.endswith(suffix):
                    file_basename = file_basename[0:-len(suffix)]
                    break
        return file_basename

    def logfile_delete_filenames(self,image_filenames):
        """Make sure that there are no duplicate entries in the
        data collection logfile, in the case an image is recollected.
        image_filename: basename of image filename (without directory)
        """
        from os.path import basename
        image_filenames = [basename(f) for f in image_filenames]

        try: log = file(self.logfile_name)
        except: log = None
        if log:
            lines = log.read().split("\n")
            # 'split' makes the last line an empty line.
            if lines and lines[-1] == "": lines.pop(-1)
            output_lines = list(lines)
            # Remove matching lines.
            for line in lines:
                if line.startswith("#"): continue # Ignore comment lines.
                fields = line.split("\t")
                if len(fields)>3 and fields[3] in image_filenames:
                    output_lines.remove(line)
            # Update the log file if needed.
            if output_lines != lines:
                log = file(self.logfile_name,"w")
                for line in output_lines: log.write(line+"\n")

    def sleep(self,delay):
        """Interruptible delay"""
        from time import time,sleep
        t = time()
        while time()-t < delay and not self.cancelled: sleep(0.050)

    def exec_delayed(self,time,command):
        """Execute a command on background after a certain delay
        time: seconds
        command: string, executable Python code"""
        from thread import start_new_thread
        start_new_thread(self.exec_delayed_thread,(time,command))

    def exec_delayed_thread(self,time,command):
        """Execute a command after a certain delay
        time: seconds
        command: string, executable Python code"""
        from time import sleep
        sleep(time)
        exec(command)

    def play_sound(self):
        from sound import play_sound
        if not self.cancelled: play_sound("ding")


collect = Collect()


def basenames(filenames):
    from os.path import basename
    from numpy import array,chararray
    basenames = [basename(f) for f in filenames]
    basenames = array(basenames).view(chararray)
    return basenames


if __name__ == '__main__':
    from pdb import pm # for debugging
    from time import time # for timing
    import logging # for debugging
    logging.basicConfig(
        level=logging.DEBUG,
        format=
            "%(asctime)s "
            "%(levelname)s "
            "%(module)s"
            ".%(funcName)s"
            ", line %(lineno)d"
            ": %(message)s"
    )
    self = collect # for debugging
    ##from Ensemble_SAXS_pp import Sequence,Sequences
    
    ##print('collect.scan_points')
    ##print('self.scan_point_list')
    ##print("self.power_configuration")
    ##print('self.collection_order')
    ##print('self.collection_variables')
    ##print('self.collection_variable_counts')
    print('self.temperatures')
    ##print('self.temperature_list')
    print('self.collection_all_values("Temperature")')
    from linear_ranges import linear_ranges
    print('linear_ranges(self.collection_all_values("Temperature"))')
    from temperature_Friedrich import temperature
    print('temperature.time_points,temperature.temp_points')
    print('')
    ##print('self.temperature_list')
    ##print('self.scan_point_list')
    ##print('self.power_list')
    ##print('')
    ##print('self.delay_configuration')
    ##print('self.delay_sequences')
    ##print('self.delay_list')
    ##print('self.sequence_properites("laser_on")')
    ##print('self.sequence_properites("delay")')
    ##print('self.sequence_properites("nom_delay")')
    ##print('self.sequence_properites("pump_on")')
    ##print('self.sequence_properites("following_pump_on")')
    ##print('self.directory')
    ##print('self.n')
    ##print('self.sequences_simple')
    print('self.sequences')
    ##print('Sequences(sequences=self.sequences)')
    ##print(r'print self.sequences[0].description.replace(",","\n")')
    ##print('')
    ##print('self.xray_image_filename(0)')
    ##print('self.file_basenames')
    ##print('self.xray_image_filenames')
    ##print('self.xray_scope_trace_filenames')
    ##print('len(self.xray_scope_trace_filenames)')
    ##print('len(self.missing_xray_scope_trace_filenames)')
    ##print('for f in basenames(self.missing_xray_scope_trace_filenames): print f')
    ##print('self.collection_pass_count')
    ##print('self.collection_passes')
    ##print('self.collection_pass_ranges(self.collection_passes[0])')
    ##print('self.collection_first_i')
    print('')
    print('self.generate_packets()')
    print('')
    ##print('self.collection_variables_dataset_start()')
    ##print('self.set_collection_variables(0)')
    print('self.timing_system_start()')
    print('self.timing_system_setup()')
    ##print('self.xray_detector_start()')
    ##print('self.xray_scope_start()')
    ##print('self.laser_scope_start()')
    ##print('self.diagnostics_start()')
    ##print('self.logging_start()')
    print('self.temperature_start()')
    ##print('self.collection_variables_start()')
    ##print('self.update_status_start()')
    print('')
    ##print('self.acquisition_start()')
    print('self.timing_system_acquisition_start()')
    print('')
    ##print('self.update_status_stop()')
    ##print('self.collection_variables_stop()')
    print('self.temperature_stop()')
    ##print('self.logging_stop()')
    ##print('self.diagnostics_stop()')
    ##print('self.xray_scope_stop()')
    ##print('self.laser_scope_stop()')
    ##print('self.xray_detector_stop()')
    print('self.timing_system_stop()')
    ##print('self.collection_variables_dataset_stop()')
    print('')
    ##print('self.generating_packets = True')
    ##print('self.collect_dataset()')
    print('self.collecting_dataset = True')
    ##print('self.erasing_dataset = True')
    ##print('sum(self.logfile_has_entries(self.xray_image_filenames))')
    ##print('self.logfile_delete_filenames(self.xray_image_filenames)')
