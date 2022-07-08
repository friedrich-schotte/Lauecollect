#!/usr/bin/env python
"""
Data Collection

Author: Friedrich Schotte
Date created: 2018-10-09
Date last modified: 2022-06-28
Revision comment: Issue:
    line 155, in collection_pass_i
    i = arange(first, first + self.collection_pass_length)
    ValueError: arange: cannot compute length
"""
__version__ = "7.0.2"

from logging import debug, info, warning, error
from typing import List, Iterable, Sized

from cached_function import cached_function
from reference import reference
from alias_property import alias_property
from db_property import db_property
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property
from monitored_method import monitored_method
from function_property import function_property
from attribute_property import attribute_property
from type_property import type_property
from file import file as file_object
from run_async import run_async


@cached_function()
def acquisition_driver(domain_name):
    return Acquisition_Driver(domain_name)


class Acquisition_Driver(object):
    """Data collection"""
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name
        self.logging = False  # to suppress "attribute logging defined outside __init__"

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__.lower(), self.domain_name)

    @property
    def db_name(self):
        return "acquisition/%s" % self.domain_name

    delay_configuration = db_property("delay", "")
    power_configuration = db_property("power", "power(T0=1.0, N_per_decade=4, N_power=6, reverse=False)")

    xray_image_extension = db_property("xray_image_extension", "mccd")
    description = db_property("description", "[Add description here]")
    directory_string = db_property("directory", "//femto-data/C/Data")

    variables = ["Delay", "Laser_on", "Temperature", "Repeat", "Power", "Scan_Motor"]
    collection_order = db_property("collection_order", "")

    detector_configuration = db_property("detector_configuration", "")

    cancelled = monitored_value_property(default_value=False)

    @monitored_property
    def directory(self, directory_string):
        from normpath import normpath
        return normpath(directory_string)

    @directory.setter
    def directory(self, value):
        self.directory_string = value

    @monitored_property
    def basename(self, directory):
        from os.path import basename
        return basename(directory)

    @basename.setter
    def basename(self, basename):
        from os.path import dirname
        self.directory = dirname(self.directory) + "/" + basename

    @monitored_property
    def collection_pass_count(self, collection_variables):
        """Into how many passes does the data collection need to be broken up?"""
        count = 1
        for i, variable in enumerate(collection_variables):
            wait = self.variable_wait(variable)
            N = len(self.variable_values(i))
            if wait or count > 1:
                count *= N
        return count

    @collection_pass_count.dependency_references
    def collection_pass_count(self):
        return [
            reference(self, "variable_wait"),
            reference(self, "variable_values"),
        ]

    @monitored_property
    def collection_pass_length(self, n, collection_pass_count):
        from floordiv import floordiv
        return floordiv(n, collection_pass_count)

    @monitored_property
    def collection_passes(self, acquired, collection_pass):
        """List of integers, 0,1,...collection_pass_count-1"""
        from numpy import unique
        acquired, collection_pass = make_same_length(acquired, collection_pass)
        collection_passes = unique(collection_pass[~acquired])
        return collection_passes

    @monitored_property
    def acquired(self, logfile_entries_generated):
        """Acquired status for each scan point in the dataset"""
        return logfile_entries_generated

    @monitored_property
    def collection_pass(self, n, collection_pass_length):
        """To which collection pass does each scan point in the dataset belong?"""
        from numpy import arange
        i = arange(0, n)
        collection_pass = i // collection_pass_length
        return collection_pass

    @monitored_method
    def collection_pass_ranges(self, collection_pass):
        """Pairs of starting and ending scan point numbers (range 0,,,n-1)"""
        ranges = self.ranges(self.collection_pass_i(collection_pass))
        return ranges

    @collection_pass_ranges.dependencies
    def collection_pass_ranges(self):
        return [reference(self, "collection_pass_i")]

    @staticmethod
    def ranges(i):
        from numpy import asarray, where, diff, concatenate
        i = asarray(i)
        gaps = where(diff(i) > 1)[0]
        firsts = [0] if len(i) > 0 else []
        lasts = [len(i) - 1] if len(i) > 0 else []
        firsts = concatenate((firsts, gaps + 1))
        lasts = concatenate((gaps, lasts))
        ranges = [(i[first], i[last]) for (first, last) in zip(firsts, lasts)]
        return ranges

    @monitored_method
    def collection_pass_i(self, collection_pass):
        """Image numbers of a collection pass
        collection_pass: 0,1,... collection_pass_count-1"""
        from numpy import array, isnan, arange, resize
        i = array([], dtype=int)
        collection_pass_length = self.collection_pass_length
        if not isnan(collection_pass_length):
            first = self.collection_pass_length * collection_pass
            i = arange(first, first + self.collection_pass_length)
            acquired = self.acquired
            if len(i) > 0 and max(i) >= len(acquired):
                acquired = resize(acquired, max(i) + 1)
                acquired[max(i):] = False
            i = i[~acquired[i]]
        return i

    @collection_pass_i.dependencies
    def collection_pass_i(self):
        return [
            reference(self, "collection_pass_length"),
            reference(self, "acquired"),
        ]

    @monitored_property
    def collection_first_i(self, collection_first_range) -> int:
        first, last = collection_first_range
        return first

    @monitored_property
    def collection_first_range(self, collection_passes):
        from numpy import nan
        first, last = nan, nan
        for collection_pass in collection_passes:
            for (first, last) in self.collection_pass_ranges(collection_pass):
                break
            break
        return first, last

    @collection_first_range.dependency_references
    def collection_first_range(self):
        return [reference(self, "collection_pass_ranges")]

    override_repeat = db_property("override_repeat", False)
    override_repeat_count = db_property("override_repeat_count", 1)

    @monitored_property
    def finish_series(self, __finish_series__):
        return __finish_series__

    @finish_series.setter
    def finish_series(self, value):
        self.__finish_series__ = value
        self.decide_n_collect()

    __finish_series__ = db_property("finish_series", False)

    @monitored_property
    def finish_series_variable(self, __finish_series_variable__):
        return __finish_series_variable__

    @finish_series_variable.setter
    def finish_series_variable(self, value):
        self.__finish_series_variable__ = value
        self.decide_n_collect()

    __finish_series_variable__ = db_property("finish_series_variable", "Temperature")

    def decide_n_collect(self):
        if self.finish_series:
            self.n_collect = self.n_finish_series(self.current_i)
        else:
            self.n_collect = self.n

    @monitored_property
    def n_collect(self, n, finish_series, __n_collect__):
        n_collect = n
        if finish_series:
            n_collect = __n_collect__
        return n_collect

    @n_collect.setter
    def n_collect(self, value):
        self.__n_collect__ = value

    __n_collect__ = db_property("__n_collect__", 0)

    def n_finish_series(self, image_number):
        n_finish_series = self.n
        if self.finish_series:
            period = 1
            for i, variable in enumerate(self.collection_variables):
                period *= len(self.variable_values(i))
                if variable == self.finish_series_variable:
                    break
            n_finish_series = (int(image_number) // period + 1) * period
        return n_finish_series

    def set_collection_variables(self, i, wait=False):
        """i: range 0 to self.n"""
        values = self.collection_variable_values(i)
        variables = self.collection_variables
        for variable, value in zip(variables, values):
            self.variable_set(variable, value)
        if wait:
            self.wait_for_collection_variables()

    def wait_for_collection_variables(self):
        """i: range 0 to self.n"""
        from time import sleep
        variables = self.collection_variables
        while any([self.variable_changing(var) for var in variables]):
            if self.cancelled:
                break
            self.actual(self.collection_variable_changing_report)
            sleep(0.2)

    @property
    def collection_variable_changing_report(self):
        message = ""
        for variable in self.collection_variables:
            if self.variable_changing(variable):
                value = self.variable_value(variable)
                formatted_value = self.variable_formatted_value(variable, value)
                message += "%s=%s, " % (variable, formatted_value)
        message = message.strip(", ")
        return message

    def collection_variables_dataset_start(self):
        """To be done at the beginning of the data collection"""

    def collection_variables_dataset_stop(self):
        """To be done at the end of the data collection"""

    collection_values = {}

    def collection_variables_start(self, wait=True):
        for variable in self.collection_variables:
            self.collection_variable_start(variable)
        if wait:
            self.collection_variables_wait()

    def collection_variables_stop(self):
        for variable in self.collection_variables:
            self.collection_variable_stop(variable)

    def collection_variables_wait(self):
        from time import sleep
        while not self.collection_variables_started and not self.cancelled:
            sleep(0.2)

    @property
    def collection_variables_started(self):
        value = all([self.collection_variable_started(variable)
                     for variable in self.collection_variables])
        return value

    @property
    def collection_variables_stopped(self):
        value = all([self.collection_variable_stopped(variable)
                     for variable in self.collection_variables])
        return value

    def collection_variable_start(self, variable):
        if not self.variable_wait(variable):
            if variable in ["Repeat", "Delay", "Laser_on", "Temperature", "Scan_Motor"]:
                pass
            elif variable == "Alio":
                self.actual("%s start..." % variable)
                self.Alio.acquiring.command_value = True
                self.actual("%s started" % variable)
            else:
                self.variable_set_scanning(variable, True)

    def collection_variable_started(self, variable):
        if not self.variable_wait(variable):
            if variable in ["Repeat", "Delay", "Laser_on", "Temperature", "Scan_Motor"]:
                value = True
            elif variable == "Alio":
                value = bool(self.Alio.acquiring.value) is True
            else:
                value = self.variable_get_scanning(variable)
        else:
            value = True
        return value

    def collection_variable_stop(self, variable):
        if not self.variable_wait(variable):
            if variable in ["Repeat", "Delay", "Laser_on", "Temperature", "Scan_Motor"]:
                pass
            elif variable == "Alio":
                self.Alio.acquiring.command_value = False
            else:
                self.variable_set_scanning(variable, False)

    def collection_variable_stopped(self, variable):
        if not self.variable_wait(variable):
            if variable in ["Repeat", "Delay", "Laser_on", "Temperature", "Scan_Motor"]:
                value = True
            elif variable == "Alio":
                value = bool(self.Alio.acquiring.value) is False
            else:
                value = not self.variable_get_scanning(variable)
        else:
            value = True
        return value

    def variable_set_scanning(self, variable, value):
        from reference import reference
        from handler import handler
        event_handlers = reference(self.timing_system.registers.image_number, "count").monitors
        event_handler = handler(self.collection_variables_handle_image_number_update, variable)
        if bool(value) is True:
            self.collection_values[variable] = self.collection_all_values(variable)
            event_handlers.add(event_handler)
        if bool(value) is False:
            event_handlers.remove(event_handler)
            if variable in self.collection_values:
                del self.collection_values[variable]

    def variable_get_scanning(self, variable):
        from reference import reference
        from handler import handler
        event_handlers = reference(self.timing_system.registers.image_number, "count").monitors
        event_handler = handler(self.collection_variables_handle_image_number_update, variable)
        scanning = all([
            event_handler in event_handlers,
            variable in self.collection_values,
        ])
        return scanning

    def collection_variables_handle_image_number_update(self, variable):
        i = self.timing_system.registers.image_number.count
        collection_values = dict(self.collection_values)
        if variable in collection_values:
            if 0 <= i < len(collection_values[variable]):
                value = collection_values[variable][i]
                debug("Image %r: Setting collection variable %s=%r..." % (i, variable, value))
                self.variable_set(variable, value)
                debug("Image %r: Setting collection variable %s=%r done" % (i, variable, value))

    def variable_value(self, variable):
        """Current read-back value"""
        from numpy import nan
        value = nan
        if variable == "Temperature":
            value = self.temperature_scan.motor_value
        if variable == "Power":
            from instrumentation import trans2
            value = trans2.value
        if variable == "Scan_Motor":
            return self.motor_scan.motor_value
        return value

    def variable_command_value(self, variable):
        """Nominal value"""
        from numpy import nan
        value = nan
        if variable == "Temperature":
            value = self.temperature_scan.motor_command_value
        if variable == "Power":
            from instrumentation import trans2
            value = trans2.value  # has no attribute 'command_value'
        if variable == "Scan_Motor":
            return self.motor_scan.command_value
        return value

    def variable_set(self, variable, value):
        from time import sleep

        if variable != "Repeat":
            formatted_value = self.variable_formatted_value(variable, value)
            self.actual("%s=%s" % (variable, formatted_value))

        if variable == "Temperature":
            self.temperature_scan.motor_command_value = value
        if variable == "Power":
            from instrumentation import trans2
            trans2.value = value
        if variable == "Scan_Motor":
            self.motor_scan.value = value
            sleep(0.01)

    def variable_changing(self, variable):
        changing = False
        if variable == "Temperature":
            changing = not self.temperature_scan.ready
        if variable == "Power":
            from instrumentation import trans2
            changing = trans2.moving
        if variable == "Scan_Motor":
            changing = not self.motor_scan.ready
        return changing

    def collection_variable_values(self, i):
        """i: range 0 to self.n"""
        from numpy import nan
        values = []
        for j, n in enumerate(self.collection_variable_indices(i)):
            variable_values = self.variable_values(j)
            n_max = len(variable_values) - 1
            if 0 <= n <= n_max:
                value = variable_values[n]
            else:
                warning(f"Variable {j}: index {n} not in range 0..{n_max}")
                value = nan
            values += [value]
        return values

    def collection_all_values(self, variable):
        """variable: e.g. 'Temperature'"""
        values = []
        if variable in self.collection_variables:
            i = self.collection_variables.index(variable)
            values = self.collection_variable_all_values[i]
        return values

    @property
    def collection_variable_all_values(self):
        from numpy import array, repeat, tile, vstack
        values_list = []
        for (i, variable) in enumerate(self.collection_variables):
            values_list += [self.variable_values(i)]
        all_values = array([values_list[0]])
        for values in values_list[1:]:
            all_values = vstack([
                tile(all_values, len(values)),
                repeat(values, len(all_values[0])),
            ])
        return all_values

    @monitored_property
    def collection_variable_count(self, collection_variables):
        return len(collection_variables)

    def collection_variable_indices(self, i):
        """List of integers of length self.collection_variable_count
        range 0 to self.collection_variable_counts
        i: range 0 to self.n"""
        indices = []
        for n in self.collection_variable_counts:
            indices += [i % n]
            i //= n
        return indices

    @monitored_property
    def collection_variable_counts(self, collection_variable_value_lists):
        """Number of scan points for each nested loop"""
        counts = [max(len(values), 1) for values in collection_variable_value_lists]
        return counts

    @monitored_property
    def n(self, collection_variable_counts) -> int:
        """Number of scan points in a dataset"""
        n = 1
        for i in collection_variable_counts:
            n *= i
        return n

    @type_property
    class scanning:
        def __init__(self, instance):
            self.instance = instance

        def __repr__(self):
            return f"{repr(self.instance)}.{self.class_name}"

        @property
        def class_name(self):
            return type(self).__name__

        @monitored_property
        def delay(self, collection_variables):
            return "Delay" in collection_variables

        @monitored_property
        def laser_on(self, collection_variables):
            return "Laser_on" in collection_variables

        @monitored_property
        def temperature(self, collection_variables):
            return "Temperature" in collection_variables

        @monitored_property
        def power(self, collection_variables):
            return "Power" in collection_variables

        @monitored_property
        def scan_motor(self, collection_variables):
            return "Scan_Motor" in collection_variables

        @monitored_property
        def alio(self, collection_variables):
            return "Alio" in collection_variables

        collection_variables = alias_property("instance.collection_variables")

    @type_property
    class scan_point_dividers:
        def __init__(self, instance):
            self.instance = instance

        def __repr__(self):
            return f"{repr(self.instance)}.{self.class_name}"

        @property
        def class_name(self):
            return type(self).__name__

        @monitored_property
        def delay(self, divider_list):
            return self.divider(divider_list, "Delay")

        @monitored_property
        def laser_on(self, divider_list):
            return self.divider(divider_list, "Laser_on")

        @monitored_property
        def temperature(self, divider_list):
            return self.divider(divider_list, "Temperature")

        @monitored_property
        def power(self, divider_list):
            return self.divider(divider_list, "Power")

        @monitored_property
        def scan_motor(self, divider_list):
            return self.divider(divider_list, "Scan_Motor")

        @monitored_property
        def alio(self, divider_list):
            return self.divider(divider_list, "Alio")

        divider_list = alias_property("instance.scan_point_divider_list")

        def divider(self, divider_list, variable_name):
            divider = 1
            if variable_name in self.instance.collection_variables:
                i = self.instance.collection_variables.index(variable_name)
                if i < len(divider_list):
                    divider = divider_list[i]
            return divider

    def scan_point_divider(self, variable_name):
        divider = 1
        if variable_name in self.collection_variables:
            i = self.collection_variables.index(variable_name)
            if i < len(self.scan_point_divider_list):
                divider = self.scan_point_divider_list[i]
        return divider

    @monitored_property
    def scan_point_divider_list(self, collection_variable_counts):
        """Number of scan points in a dataset"""
        divider_list = []
        divider = 1
        for i in collection_variable_counts:
            divider_list.append(divider)
            divider *= i
        return divider_list

    @monitored_property
    def collection_variables(self, collection_variables_with_options) -> Iterable:
        variables = []
        for variable in collection_variables_with_options:
            if "=" in variable:
                variable = variable.split("=")[0]
            variables += [variable]
        return variables

    @monitored_property
    def collection_variables_with_options(self, collection_order) -> Sized:
        """e.g. 'Laser_on=[0,1]', 'Repeat=16' """
        from split_list import split_list
        variables = split_list(collection_order.replace(" ", ""))
        return variables

    @monitored_property
    def variable_formatted_value_lists(self, collection_variables, collection_variable_value_lists):
        lists = []
        collection_variables, collection_variable_value_lists = make_same_length(collection_variables, collection_variable_value_lists)
        for (i, values) in enumerate(collection_variable_value_lists):
            variable = collection_variables[i]
            lists += [[self.variable_formatted_value(variable, val) for val in values]]
        return lists

    @monitored_property
    def collection_variable_value_lists(self):
        return [self.variable_values(i) for i in range(0, len(self.collection_variables))]

    @collection_variable_value_lists.dependency_references
    def collection_variable_value_lists(self):
        return [reference(self, "variable_values")]

    @monitored_method
    def variable_values(self, i):
        """i range 0 to len(collection_variables)"""
        # For choices encoded in the "collection_order" string
        # e.g. Repeat=16, Laser_on=[0,1]
        values = []
        if 0 <= i < len(self.collection_variables):
            variable = self.collection_variables[i]
            if variable == "Repeat":
                values = list(range(0, self.repeat_count(i)))
            else:
                values = self.variable_choices(variable)
        return values

    @variable_values.dependencies
    def variable_values(self):
        return [
            reference(self, "collection_variables"),
            reference(self, "repeat_count"),
            reference(self, "laser_on_list"),
            reference(self, "variable_choices"),
        ]

    @monitored_method
    def variable_choices(self, variable):
        # For choices encoded outside the "collection_order" string
        # in separate tables.
        if variable == "Temperature":
            choices = self.temperature_scan.values
        elif variable == "Power":
            choices = self.power_list
        elif variable == "Scan_Motor":
            choices = self.motor_scan.values
        elif variable == "Delay":
            choices = self.delay_scan.values
        elif variable == "Laser_on":
            choices = self.laser_on_scan.values
        elif variable == "Alio":
            choices = self.Alio.scan_points.value
        else:
            choices = []
        return choices

    @variable_choices.dependencies
    def variable_choices(self):
        return [
            reference(self, "temperature_scan_values"),
            reference(self, "power_list"),
            reference(self, "motor_scan_values"),
            reference(self, "delay_scan_values"),
            reference(self, "laser_on_scan_values"),
            reference(self, "Alio_scan_points_value"),
        ]

    temperature_scan_values = alias_property("temperature_scan.values")
    motor_scan_values = alias_property("motor_scan.values")
    delay_scan_values = alias_property("delay_scan.values")
    laser_on_scan_values = alias_property("laser_on_scan.values")
    Alio_scan_points_value = alias_property("Alio.scan_points.value")

    @monitored_method
    def variable_wait(self, variable):
        """Suspend collection while changing this variable?"""
        if variable == "Temperature":
            wait = self.temperature_scan_wait
        elif variable == "Power":
            wait = True
        elif variable == "Scan_Motor":
            wait = self.motor_scan_wait
        else:
            wait = False
        return wait

    @variable_wait.dependencies
    def variable_wait(self):
        return [
            reference(self, "temperature_scan_wait"),
            reference(self, "motor_scan_wait"),
        ]

    temperature_scan_wait = alias_property("temperature_scan.wait")
    motor_scan_wait = alias_property("motor_scan.wait")

    @staticmethod
    def variable_formatted_value(variable, value):
        from time_string import time_string
        text = str(value)
        if variable == "Delay":
            text = time_string(value)
        if variable == "Temperature":
            text = "%.3fC" % value
        if variable == "Laser_on":
            text = "on" if value else "off"
        if variable == "Power":
            text = "%.4f" % value
        if variable == "Scan_Motor":
            text = "%.04f" % value
        if variable == "Repeat":
            text = "%02.0f" % (value + 1)
        if variable == "Alio":
            text = ",".join(["%+1.3f" % x for x in value])
        return text

    @staticmethod
    def variable_log_value(variable, value):
        text = str(value)
        if variable == "Delay":
            text = "%g" % value
        if variable == "Temperature":
            text = "%.3f" % value
        if variable == "Laser_on":
            text = "1" if value else "0"
        if variable == "Power":
            text = "%.4f" % value
        if variable == "Scan_Motor":
            text = "%.04f" % value
        if variable == "Repeat":
            text = "%02.0f" % (value + 1)
        if variable == "Alio":
            text = "\t".join(["%+1.3f" % x for x in value])
        return text

    def variable_log_label(self, variable):
        if variable == "Scan_Motor":
            text = self.motor_scan.motor_name
        elif variable == "Alio":
            text = "\t".join(self.Alio.scan_points.name)
        else:
            text = variable
        return text

    @monitored_property
    def final_repeat_count(self, repeat_counts):
        if len(repeat_counts) > 0:
            final_repeat_count = repeat_counts[-1]
        else:
            final_repeat_count = 0
        return final_repeat_count

    @final_repeat_count.setter
    def final_repeat_count(self, count):
        self.override_repeat_count = count
        self.override_repeat = True

    @monitored_property
    def repeat_counts(self, collection_variables_with_options, override_repeat, override_repeat_count):
        counts = []
        for variable in collection_variables_with_options:
            count = 0
            if variable.startswith("Repeat="):
                count_string = variable.split("=")[-1]
                try:
                    count = int(eval(count_string))
                except Exception as msg:
                    error("%s: %s: %s: %s: expecting int" %
                          (self.collection_order, variable, count_string, msg))
            counts.append(count)
        if override_repeat:
            if len(counts) > 0:
                counts[-1] = override_repeat_count
        return counts

    @monitored_method
    def repeat_count(self, i):
        """i: collection variable number 0...len(collection_variables)"""
        repeat_counts = self.repeat_counts
        if i < len(repeat_counts):
            count = repeat_counts[i]
        else:
            count = 0
        return count

    @repeat_count.dependencies
    def repeat_count(self):
        return [
            reference(self, "repeat_counts"),
        ]

    @monitored_method
    def laser_on_list(self, i):
        """i: collection variable number 0...len(collection_variables)"""
        values = [1]
        variables = self.collection_variables_with_options
        if 0 <= i <= len(variables):
            variable = variables[i]
            if variable.startswith("Laser_on="):
                values_string = variable.split("=")[-1]
                from numpy import nan  # for eval
                try:
                    values = eval(values_string)
                except Exception as msg:
                    error("%s: %s: %s: %s: expecting int" %
                          (self.collection_order, variable, values_string, msg))
        return values

    @laser_on_list.dependencies
    def laser_on_list(self):
        return [reference(self, "collection_variables_with_options")]

    @monitored_property
    def time_to_finish(self, scan_point_acquisition_time, n_remaining):
        return scan_point_acquisition_time * n_remaining

    scan_point_acquisition_time = alias_property("timing_system.composer.scan_point_acquisition_time")
    sequences_per_scan_point = alias_property("timing_system_acquisition.sequences_per_scan_point")

    @monitored_property
    def n_remaining(self, current_i, n_collect):
        from numpy import isnan
        i = current_i
        n_remaining = n_collect - i if not isnan(i) else 0
        return n_remaining

    @monitored_property
    def current_i(self, current, acquiring, collection_first_i):
        i = current if acquiring else collection_first_i
        return i

    @monitored_property
    def power_list(self, power_configuration):
        from expand_scan_points import safe_expand_scan_points
        values = safe_expand_scan_points(power_configuration)
        return values

    @monitored_property
    def detector_names(self, detector_configuration) -> List[str]:
        """e.g. 'xray_detector', 'xray_scope', 'laser_scope'"""
        from split_list import split_list
        names = split_list(detector_configuration.replace(" ", ""))
        return names

    @monitored_property
    def info_message(self, dataset_complete, current_i, n_collect, scan_point_name, file_basenames):
        if dataset_complete:
            message = "Dataset complete"
        elif current_i > n_collect:
            message = "Collection completed"
        else:
            i = current_i
            message = "%s %s of %s" % (scan_point_name, i + 1, n_collect)
            if i < n_collect and i < len(file_basenames):
                message += ": " + file_basenames[i]
        message = message[0:1].upper() + message[1:]
        return message

    status_message = monitored_value_property(default_value="")
    actual_message = monitored_value_property(default_value="")

    @monitored_property
    def acquisition_status(self, current, file_basenames):
        i = current
        if i < self.n_collect:
            message = "Acquiring %s %.0f of %.0f" % (self.scan_point_name, i + 1, self.n_collect)
            if 0 <= i < len(file_basenames):
                message += ": " + file_basenames[i]
            values = self.collection_variable_values(i)
            variables = self.collection_variables
            for variable, value in zip(variables, values):
                formatted_value = self.variable_formatted_value(variable, value)
                message += ", %s %s" % (variable, formatted_value)
        else:
            message = "Collection Completed"
        return message

    @monitored_property
    def scan_point_name(self, detector_names):
        name = "scan point"
        if "xray_detector" in detector_names:
            name = "image"
        return name

    current = alias_property("timing_system.registers.image_number.count")
    acquiring = alias_property("timing_system.registers.acquiring.count")

    @monitored_property
    def dataset_complete(self, logfile_entries_generated, configuration_saved):
        dataset_complete = all([
            # all(self.files_generated),
            all(logfile_entries_generated),
            configuration_saved,
        ])
        return dataset_complete

    def get_files_generated(self):
        from exists import exist_files
        return exist_files(self.filenames)

    files_generated = property(get_files_generated)

    @monitored_property
    def dataset_started(self, logfile_entries_generated, configuration_saved):
        started = any([
            # len(self.xray_images_collected) > 0,
            # len(self.scope_traces_collected("xray_scope")) > 0,
            # len(self.scope_traces_collected("laser_scope")) > 0,
            sum(logfile_entries_generated) > 0,
            configuration_saved,
        ])
        return started

    from thread_property import thread_property
    erasing_dataset = thread_property("erase_dataset")

    def erase_dataset(self):
        self.actual("Erasing Dataset...")
        for i, filename in enumerate(self.xray_images_collected):
            self.actual("Erasing X-ray image %r" % (i + 1))
            if self.cancelled:
                break
            self.remove(filename)
        for i, filename in enumerate(self.scope_traces_collected("xray_scope")):
            self.actual("Erasing X-ray scope trace %r" % (i + 1))
            if self.cancelled:
                break
            self.remove(filename)
        for i, filename in enumerate(self.scope_traces_collected("laser_scope")):
            self.actual("Erasing Laser scope trace %r" % (i + 1))
            if self.cancelled:
                break
            self.remove(filename)
        filenames = self.xray_image_filenames
        if sum(self.logfile_has_entries(filenames)) > 0:
            self.actual("Cleaning Logfile...")
            self.logfile_delete_filenames(filenames)
        self.configuration_erase()
        self.actual("Dataset erased")

    @staticmethod
    def remove(filename):
        from os.path import exists
        if exists(filename):
            from os import remove
            try:
                remove(filename)
            except Exception as x:
                warning("%s: %s" % (filename, x))

    @property
    def filenames(self):
        """Names of all files of the dataset (images and traces)"""
        filenames = [[]]
        if "xray_detector" in self.detector_names:
            filenames.append(self.xray_image_filenames_to_collect)
        for scope_name in self.scope_names:
            filenames.append(self.scope_trace_filenames(scope_name))
        from numpy import concatenate
        filenames = concatenate(filenames)
        return filenames

    @property
    def scope_names(self):
        scope_names = []
        for detector_name in self.detector_names:
            if "scope" in detector_name:
                scope_name = detector_name.split(".")[0]
                if scope_name not in scope_names:
                    scope_names.append(scope_name)
        return scope_names

    def filename(self, detector_name, i):
        """
        detector-name: "xray_detector","xray_scope.C1","xray_scope.C2",
            "xray_scope","laser_scope"
        i: image_number (for xray_detector), xscope_acq_count (for xray_scope),
            lscope_acq_count (for laser_scope)
        """
        filename = ""
        if detector_name == "xray_detector":
            filename = self.xray_image_filename(i)
        if "scope" in detector_name:
            N = self.sequences_per_scan_point
            i = i // N
            filename = self.file_basenames[i]
            suffix = "_%02.0f" % (i % N + 1)
            filename = filename + suffix

            scope_name = detector_name.split(".")[0]
            source = detector_name.split(".")[-1] if "." in detector_name else ""
            source = "_" + source if source != "" else ""
            filename = filename + source

            subdir = scope_name.replace("_scope", "") + "_traces"
            filename = self.directory + "/" + subdir + "/" + filename + ".trc"
        return filename

    @property
    def xray_images_collected(self):
        from exists import exist_files
        filenames = self.xray_image_filenames
        xray_images_collected = filenames[exist_files(filenames)]
        return xray_images_collected

    def status(self, message):
        if message:
            info(message)
        self.status_message = message

    def actual(self, message):
        if message:
            info(message)
        self.actual_message = message

    from thread_property import thread_property
    collecting_dataset = collecting = thread_property("collect_dataset")

    def collect_dataset(self):
        from time import sleep

        self.status("Collection started")

        self.configuration_save()
        self.collection_variables_dataset_start()
        # for temperature equilibration
        self.set_collection_variables(self.collection_first_i, wait=False)

        self.timing_system_sequences_load()
        self.actual("Timing system setup...")
        first, last = self.collection_first_range
        self.timing_system_acquisition.first_scan_point = first
        self.timing_system_acquisition.last_scan_point = last
        self.xray_detector_start()
        self.xray_detector_timing_system_setup()
        self.scope_start("xray_scope")
        self.scope_timing_system_setup("xray_scope")
        self.scope_start("laser_scope")
        self.scope_timing_system_setup("laser_scope")
        self.diagnostics_start()
        self.logging_start()
        self.instrumentation_start()
        self.collection_variables_start()
        self.update_status_start()

        while len(self.collection_passes) > 0:
            for collection_pass in self.collection_passes:
                if self.cancelled:
                    break
                for (first, last) in self.collection_pass_ranges(collection_pass):
                    if first >= self.n_collect:
                        break

                    self.timing_system_acquisition.first_scan_point = first
                    self.timing_system_acquisition.last_scan_point = last
                    self.xray_detector_timing_system_setup(first)
                    self.scope_timing_system_setup("xray_scope", first)
                    self.scope_timing_system_setup("laser_scope", first)
                    self.set_collection_variables(first, wait=False)

                    sleep(1)  # needed for temperature?
                    self.wait_for_collection_variables()

                    self.timing_system_acquisition_start()

                    while not self.completed(last) and not self.cancelled:
                        if self.current >= self.n_collect:
                            break
                        sleep(0.1)

                    self.timing_system_acquisition_stop()

                    self.status("Collection suspended")
                    if self.current >= self.n_collect:
                        break

            if self.cancelled:
                break
            if self.current >= self.n_collect:
                break

        self.update_status_stop()
        self.instrumentation_stop()
        self.collection_variables_stop()
        self.diagnostics_stop()
        self.timing_system_cleanup()
        self.collection_variables_dataset_stop()
        self.sleep(5)
        self.logging_stop()
        self.scope_stop("laser_scope")
        self.scope_stop("xray_scope")
        self.sleep(5)
        self.xray_detector_stop()
        self.configuration_save()

        self.finish_series = False

        self.status("Collection ended")

    def update_status_start(self):
        from reference import reference
        from handler import handler
        reference(self, "acquisition_status").monitors.add(
            handler(self.update_status_handle_update))

    def update_status_stop(self):
        from handler import handler
        from reference import reference
        reference(self, "acquisition_status").monitors.remove(
            handler(self.update_status_handle_update))

    def update_status_handle_update(self, event):
        self.status(event.value)

    def completed(self, i):
        if self.current > i:
            completed = True
        elif not self.timing_system_sequencer.queue_active:
            completed = True
        else:
            completed = False
        if completed:
            debug("Completed %r" % i)
        return completed

    generating_packets = alias_property("timing_system_acquisition.generating_packets")

    timing_system = alias_property("domain.timing_system_client")
    timing_system_sequencer = alias_property("timing_system.sequencer")
    timing_system_acquisition = alias_property("timing_system.acquisition")
    delay_scan = alias_property("timing_system.delay_scan")
    laser_on_scan = alias_property("timing_system.laser_on_scan")
    motor_scan = alias_property("domain.motor_scan")
    temperature_scan = alias_property("domain.temperature_scan")

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    @property
    def Alio(self):
        from Alio import Alio
        return Alio

    def instrumentation_start(self, wait=True):
        """Other instrumentation that needs setup on-related to scans and
        detectors"""
        if self.Alio.cmd.value != "" and "Alio" not in self.collection_variables:
            self.Alio.acquiring.command_value = True
            self.actual("Alio started")
        if wait:
            self.instrumentation_wait()

    @property
    def instrumentation_started(self):
        started = True
        if self.Alio.cmd.value != "" and "Alio" not in self.collection_variables:
            started = started and bool(self.Alio.acquiring.command_value) is True
        return started

    def instrumentation_stop(self):
        if self.Alio.cmd.value != "" and "Alio" not in self.collection_variables:
            self.Alio.acquiring.command_value = False
            self.actual("Alio stopped")

    def instrumentation_wait(self):
        from time import sleep
        while not self.instrumentation_started and not self.cancelled:
            self.actual("Waiting for instrumentation...")
            sleep(0.25)

    def timing_system_sequences_load(self):
        from time import sleep
        self.actual("Timing system sequences loading...")
        self.timing_system_acquisition.sequences_loading = True
        while self.timing_system_acquisition.sequences_loading:
            sleep(0.25)
            if self.cancelled:
                self.timing_system_acquisition.sequences_loading = False
                break
        self.actual("Timing system sequences loaded")

    def timing_system_cleanup(self):
        self.actual("Timing system cleaning up...")
        # Leave acquisition mode at the next sequence_count (fast).
        self.timing_system.sequencer.next_queue_sequence_count = -1
        self.timing_system.sequencer.queue_active = False
        self.actual("Timing system cleaned up.")

    def timing_system_acquisition_start(self):
        from time import sleep
        self.actual("Timing system acquisition start...")

        self.timing_system.sequencer.queue_active = True
        while not self.timing_system.sequencer.queue_active and not self.cancelled:
            self.actual("Timing system: Idle > Acquiring: Waiting %s"
                        % self.timing_system.sequencer.current_queue_sequence_count)
            sleep(1.0)
            self.timing_system.sequencer.queue_active = True

        self.actual(f"Timing system acquisition started: {self.timing_system.sequencer.queue_active}")

    def timing_system_acquisition_stop(self):
        from time import sleep
        self.actual("Timing system acquisition stop...")

        self.timing_system.sequencer.queue_active = False
        while self.timing_system.sequencer.queue_active and not self.cancelled:
            self.actual("Timing system: Acquiring > Idle: Waiting %s"
                        % self.timing_system.sequencer.current_queue_sequence_count)
            sleep(1.0)

        self.actual(f"Timing system acquisition stopped: {not self.timing_system.sequencer.queue_active}")

    def xray_detector_start(self):
        if "xray_detector" in self.detector_names:
            self.actual("X-ray detector acquisition start...")
            self.xray_detector.acquiring_images = True
            self.actual("X-ray detector acquisition started")

    def xray_detector_stop(self):
        if "xray_detector" in self.detector_names:
            self.actual("X-ray detector acquisition stop...")
            self.xray_detector.acquiring_images = False
            self.actual("X-ray detector acquisition stopped")

    @property
    def xray_detector(self):
        from rayonix_detector import rayonix_detector
        return rayonix_detector(self.domain_name)

    def xray_detector_timing_system_setup(self, first=None):
        if "xray_detector" in self.detector_names:
            if first is None:
                first = self.collection_first_range[0]
            count = first
            channel_mnemonic = "xdet"
            if channel_mnemonic in self.timing_system.channel_mnemonics:
                channel = getattr(self.timing_system.channels, channel_mnemonic)
                channel.acq_count.count = count

    def scope_start(self, name):
        """name: "xray_scope" or "laser_scope" """
        if self.scope_enabled(name):
            self.actual("%s start..." % self.scope_title(name))
            self.scope(name).trace_acquisition_running = True
            self.actual("%s started" % self.scope_title(name))

    def scope_timing_system_setup(self, name, first=None):
        """first,last: image numbers (0-based)
        name: "xray_scope" or "laser_scope" """
        if self.scope_enabled(name):
            if first is None:
                first = self.collection_first_range[0]
            N_traces = self.sequences_per_scan_point
            count = first * N_traces
            channel_mnemonic = name
            if name == "xray_scope":
                channel_mnemonic = "xosct"
            if name == "laser_scope":
                channel_mnemonic = "losct"
            if channel_mnemonic in self.timing_system.channel_mnemonics:
                channel = getattr(self.timing_system.channels, channel_mnemonic)
                channel.acq_count.count = count

    def scope_stop(self, name):
        """name: "xray_scope" or "laser_scope" """
        if self.scope_enabled(name):
            self.actual("%s stop..." % self.scope_title(name))
            self.scope(name).trace_acquisition_running = False
            self.actual("%s stopped" % self.scope_title(name))

    @staticmethod
    def scope(name):
        """name: "xray_scope" or "laser_scope" """
        import instrumentation
        scope = getattr(instrumentation, name)
        return scope

    @staticmethod
    def scope_title(name):
        title = name.replace("xray", "x-ray").title().replace("_", " ")
        return title

    def scope_trace_filename(self, name, acq_count, channel_name):
        """
        name: "xray_scope" or "laser_scope"
        acq_count: 0-based index
        channel_name: "C1", "C2", ...
        """
        N = self.sequences_per_scan_point
        i = acq_count // N
        filename = self.file_basenames[i]
        suffix = "_%02.0f" % (acq_count % N + 1)
        filename = filename + suffix
        filename = filename + "_" + channel_name
        subdir = name.replace("_scope", "") + "_traces"
        filename = self.directory + "/" + subdir + "/" + filename + ".trc"
        return filename

    def scope_trace_filenames(self, name):
        from numpy import isnan, array, chararray, repeat, tile, where
        filenames = array([], dtype=str).view(chararray)
        N = self.sequences_per_scan_point
        if name in self.scope_names and not isnan(N):
            N = int(N)
            filenames = self.file_basenames
            suffix = array(["_%02.0f" % (i + 1) for i in range(0, N)], dtype=str).view(chararray)
            filenames = repeat(filenames, len(suffix)) + tile(suffix, len(filenames))
            sources = self.scope_trace_sources(name)
            sources = where(sources != "", "_" + sources, "")
            filenames = repeat(filenames, len(sources)) + tile(sources, len(filenames))
            subdir = name.replace("_scope", "") + "_traces"
            filenames = self.directory + "/" + subdir + "/" + filenames + ".trc"
        return filenames

    def scope_trace_sources(self, name):
        """
        name: "xray_scope" or "laser_scope"
        Return value: e.g. "C1","CH2" for channel-cut scan
        """
        trace_sources = []
        for detector_name in self.detector_names:
            # e.g. "xray_scope" or "xray_scope.C1"
            if detector_name.startswith(name + "."):
                trace_sources += [detector_name.replace(name + ".", "", 1)]
        if not trace_sources:
            trace_sources = [""]
        from numpy import array, chararray
        trace_sources = array(trace_sources, dtype=str).view(chararray)
        return trace_sources

    def scope_enabled(self, name):
        """
        name: "xray_scope" or "laser_scope"
        Return value: True or False
        """
        enabled = False
        for detector_name in self.detector_names:
            # e.g. "xray_scope" or "xray_scope.C1"
            if detector_name == name:
                enabled = True
            if detector_name.startswith(name + "."):
                enabled = True
        return enabled

    def scope_traces_collected(self, name):
        """
        name: "xray_scope" or "laser_scope"
        """
        from exists import exist_files
        filenames = self.scope_trace_filenames(name)
        filenames = filenames[exist_files(filenames)]
        return filenames

    @run_async
    def configuration_save(self):
        """Create dump of methods configuration table"""
        self.configuration_saved = True

    def configuration_erase(self):
        self.configuration_saved = False

    def get_configuration_saved(self):
        saved = len(self.configuration_file_content) > 0
        return saved

    @monitored_property
    def configuration_saved(self, configuration_file_content):
        saved = len(configuration_file_content) > 0
        return saved

    @configuration_saved.setter
    def configuration_saved(self, state):
        if bool(state) is True:
            self.actual("Saving configuration...")
            self.configuration_file_content = self.configuration_tables.state
            self.actual("Saved configuration.")
        if bool(state) is False:
            self.configuration_file_content = ""

    configuration_file = function_property(file_object, "configuration_filename")
    configuration_file_content = attribute_property("configuration_file", "content")

    @property
    def configuration_tables(self): return self.domain.configuration_tables

    @monitored_property
    def configuration_filename(self, directory):
        from os.path import basename
        return directory + "/" + basename(directory) + ".conf"

    def xray_image_filename(self, i):
        filename = ""
        from numpy import isnan
        file_basenames = self.file_basenames
        if not isnan(i) and i in range(0, len(file_basenames)):
            ext = "." + self.xray_image_extension.strip(".")
            filename = self.directory + "/xray_images/" + file_basenames[i] + ext
        return filename

    @property
    def xray_image_filenames(self):
        ext = "." + self.xray_image_extension.strip(".")
        filenames = self.directory + "/xray_images/" + self.file_basenames + ext
        return filenames

    @property
    def xray_image_filenames_to_collect(self):
        from numpy import array, chararray
        filenames = array([], dtype=str).view(chararray)
        if "xray_detector" in self.detector_names:
            filenames = self.xray_image_filenames
        return filenames

    @monitored_property
    def file_basenames(self, basename, variable_formatted_value_lists):
        """numpy chararray"""
        from numpy import array, chararray, repeat, tile
        suffixes = []
        for value_list in variable_formatted_value_lists:
            suffix = ["_" + val for val in value_list]
            suffix = array(suffix, dtype=str).view(chararray)
            suffixes += [suffix]
        names = array([""]).view(chararray)
        for suffix in suffixes:
            names = tile(names, len(suffix)) + repeat(suffix, len(names))
        serial = ["_%04.0f" % (i + 1) for i in range(0, len(names))]
        serial = array(serial, dtype=str).view(chararray)
        names = basename + serial + names
        return names

    def diagnostics_start(self):
        self.diagnostics.running = True
        self.actual("Diagnostics Started")

    def diagnostics_stop(self):
        self.diagnostics.running = False
        self.actual("Diagnostics Stopped")

    @property
    def diagnostics(self):
        from diagnostics import diagnostics
        return diagnostics(self.domain_name)

    def logging_start(self):
        self.logging = True

    def logging_stop(self):
        self.logging = False

    logged = {}

    from thread_property_2 import thread_property

    @thread_property
    def logging(self):
        from thread_property_2 import cancelled
        self.actual("Logging Started")
        self.logged = {}
        while not cancelled():
            for i in range(0, self.n):
                if i not in self.logged and self.diagnostics.is_finished(i):
                    self.logfile_update(i)
                    self.logged[i] = True
            self.sleep(1)
        self.actual("Logging Stopped")

    def logfile_update(self, i):
        """Add image information to the end of the data collection log file"""
        self.logfile_add_line(self.logfile_entry(i))

    def logfile_add_line(self, line):
        with self.logfile_lock:
            filenames = line.split("\t")[3:4]
            self.logfile_delete_filenames(filenames)
            if not self.logfile_content:
                self.initialize_logfile()
            self.logfile_content += line

    from threading import Lock
    logfile_lock = Lock()

    def logfile_entry(self, i):
        from time import time
        from date_time import date_time
        from numpy import isfinite
        from os.path import basename

        started = self.diagnostics.started(i)
        finished = self.diagnostics.finished(i)
        timestamp = finished if isfinite(finished) else time()

        line = []
        line += [date_time(timestamp)]
        line += [date_time(started)]
        line += [date_time(finished)]
        line += [basename(self.xray_image_filename(i))]
        names = self.collection_variables
        values = self.collection_variable_values(i)
        line += [self.variable_log_value(n, v) for (n, v) in zip(names, values)]
        values = self.diagnostics.average_values(i)
        line += [str(v) for v in values]
        line = "\t".join(line) + "\n"
        return line

    def initialize_logfile(self):
        self.logfile_content = self.logfile_header

    @property
    def logfile_header(self):
        header = "# Data collection log file generated by acquisition " + \
                 __version__ + "\n"
        header += "# Description: " + self.description + "\n"
        labels = []
        labels += ["date time"]
        labels += ["started"]
        labels += ["finished"]
        labels += ["file"]
        labels += [self.variable_log_label(v) for v in self.collection_variables]
        labels += self.diagnostics.variable_names
        header += "#" + "\t".join(labels) + "\n"
        return header

    @monitored_property
    def logfile_name(self, directory):
        from os.path import basename
        return directory + "/" + basename(directory) + ".log"

    def logfile_has_entries(self, image_filenames):
        """Are there an entries for these images in the log file?
        image_filenames: filenames of images (with or without directory)
        Return value: boolean array
        """
        from os.path import basename
        from numpy import array
        filenames = self.logfile_filenames
        return array([basename(f) in filenames for f in image_filenames], dtype=bool)

    def logfile_has_entry(self, image_filename):
        """Is there an entry for this image in the log file?
        image_filename: filename of image (with or without directory)
        """
        return self.logfile_has_entries([image_filename])[0]

    logfile = function_property(file_object, "logfile_name")
    logfile_content = attribute_property("logfile", "content")

    @monitored_property
    def logfile_filenames(self, logfile_content):
        filenames = []
        lines = logfile_content.splitlines()
        for line in lines:
            if not line.startswith("#"):
                fields = line.split("\t")
                if len(fields) > 3:
                    filenames.append(fields[3])
        return filenames

    @monitored_property
    def logfile_basenames(self, logfile_filenames):
        from os.path import splitext
        filenames = [splitext(f)[0] for f in logfile_filenames]
        return filenames

    @monitored_property
    def logfile_entries_generated(self, logfile_basenames, file_basenames):
        from numpy import array
        common_names = set(logfile_basenames) & set(file_basenames)
        generated = array([f in common_names for f in file_basenames], dtype=bool)
        return generated

    def logfile_timestamp(self, filename):
        """When was this image file or scope trace acquired?
        Return value: seconds since 1970-01-01 00:00:00 UTC"""
        date_time = self.logfile_timestamp_string(filename)
        from time_string import timestamp
        from numpy import nan
        seconds = timestamp(date_time) if date_time else nan
        return seconds

    def logfile_timestamp_string(self, filename):
        """When was this image file or scope trace acquired?
        Return value: string, format 1970-01-01 00:00:00"""
        line = self.logfile_line(filename)
        fields = line.split("\t")
        date_time = fields[2] if len(fields) > 2 else ""
        if date_time == "":
            date_time = fields[0] if len(fields) > 0 else ""
        return date_time

    def logfile_line(self, filename):
        """Entry for this image or scope trace in the log file
        image_filename: basename of image filename (without directory)
        """
        from os.path import splitext
        file_basename = self.file_basename_of_filename(filename)
        entry = ""
        lines = self.logfile_content.split("\n")
        # 'split' makes the last line an empty line.
        if lines and lines[-1] == "":
            lines.pop(-1)
        for line in lines:
            if line.startswith("#"):
                continue  # Ignore comment lines.
            fields = line.split("\t")
            entry_filename = fields[3] if len(fields) > 3 else ""
            entry_basename = splitext(entry_filename)[0]
            if entry_basename == file_basename:
                entry = line
        return entry

    @staticmethod
    def file_basename_of_filename(filename):
        """E.g. 'Sample-1_0001_01_01_C1.trc' -> 'Sample-1_0001_01'"""
        from os.path import basename, splitext
        file_basename = basename(filename)
        file_basename, ext = splitext(file_basename)
        if ext.endswith("trc"):
            suffixes = ["_C%.0f" % (i + 1) for i in range(0, 4)]
            for suffix in suffixes:
                if file_basename.endswith(suffix):
                    file_basename = file_basename[0:-len(suffix)]
                    break
            suffixes = ["_%02.0f" % (i + 1) for i in range(0, 20)]
            for suffix in suffixes:
                if file_basename.endswith(suffix):
                    file_basename = file_basename[0:-len(suffix)]
                    break
        return file_basename

    def logfile_delete_scan_point(self, i):
        """Make sure that there are no duplicate entries in the
        data collection logfile, in the case an image is recollected.
        i: 0 to self.n-1
        """
        filename = self.xray_image_filename(i)
        self.logfile_delete_filenames([filename])

    def logfile_delete_filenames(self, image_filenames):
        """Make sure that there are no duplicate entries in the
        data collection logfile, in the case an image is recollected.
        image_filename: basename of image filename (without directory)
        """
        from os.path import basename
        image_filenames = [basename(f) for f in image_filenames]

        logfile = self.logfile_content
        lines = logfile.split("\n")
        # 'split' makes the last line an empty line.
        if lines and lines[-1] == "":
            lines.pop(-1)
        output_lines = list(lines)
        # Remove matching lines.
        for line in lines:
            if line.startswith("#"):
                continue  # Ignore comment lines.
            fields = line.split("\t")
            if len(fields) > 3 and fields[3] in image_filenames:
                output_lines.remove(line)
        n_entries = sum([self.logfile_line_is_entry(line) for line in output_lines])
        if n_entries == 0:
            output_lines = []
        new_logfile = "".join([line + "\n" for line in output_lines])
        # Update the log file if needed.
        if new_logfile != logfile:
            self.logfile_content = new_logfile

    @staticmethod
    def logfile_line_is_entry(line):
        return len(line) > 0 and not line.startswith("#")

    def sleep(self, delay):
        """Interruptable delay"""
        from time import time, sleep
        t = time()
        while time() - t < delay and not self.cancelled:
            sleep(0.050)


def basenames(filenames):
    from os.path import basename
    from numpy import array, chararray
    basenames = [basename(f) for f in filenames]
    basenames = array(basenames, dtype=str).view(chararray)
    return basenames


def make_same_length(*args):
    n = min([len(arg) for arg in args])
    return [arg[0:n] for arg in args]


if __name__ == '__main__':
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    self = acquisition_driver(domain_name)
    print('self.domain_name = %r' % self.domain_name)
    print('')

    property_names = [
        "file_basenames",
    ]

    from handler import handler as _handler


    @_handler
    def report(event=None):
        info(f'event = {event}')


    for property_name in property_names:
        reference(self, property_name).monitors.add(report)
