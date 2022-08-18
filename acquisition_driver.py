#!/usr/bin/env python
"""
Data Collection

Author: Friedrich Schotte
Date created: 2018-10-09
Date last modified: 2022-08-04
Revision comment: Issue: Added debug messages
"""
__version__ = "7.5"

import logging
from warnings import filterwarnings
from numpy import VisibleDeprecationWarning
from typing import List, Iterable, Sized

from cached_function import cached_function
from alias_property import alias_property
from db_property import db_property
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property
from function_property import function_property
from attribute_property import attribute_property
from type_property import type_property
from file import file as file_object
from run_async import run_async

# Creating a ndarray from ragged nested sequences.
# If you meant to do this, you must specify 'dtype=object' when creating the ndarray.
filterwarnings('ignore', category=VisibleDeprecationWarning)


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
        return f"{type(self).__name__.lower()}({self.domain_name!r})"

    @property
    def db_name(self):
        return f"domains/{self.domain_name}/acquisition"

    description = db_property("description", "[Add description here]", local=True)
    directory_string = db_property("directory", "//mx340hs/data/anfinrud_2207/Test/Test1", local=True)

    variables = ["Delay", "Laser_on", "Temperature", "Repeat", "Power", "Scan_Motor"]
    collection_order = db_property("collection_order", "", local=True)

    detector_configuration = db_property("detector_configuration", "", local=True)

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
    def collection_first_i(self, acquired):
        from numpy import where, nan
        i_not_acquired = where(~acquired)[0]
        if len(i_not_acquired) > 0:
            first = i_not_acquired[0]
        else:
            first = nan
        return first

    @property
    def collection_first_range(self):
        from numpy import nan
        ranges = self.ranges(self.collection_first_pass_i)
        if len(ranges) > 0:
            first, last = ranges[0]
        else:
            first, last = nan, nan
        return first, last

    def collection_pass_ranges(self, i_pass):
        """Pairs of starting and ending scan point numbers (range 0, 1, ... n-1)"""
        return self.ranges(self.collection_pass_i(i_pass))

    @property
    def collection_first_pass_i(self):
        from numpy import arange

        acquired, collection_pass = make_same_length(self.acquired, self.collection_pass)

        passes_non_acquired = collection_pass[~acquired]
        if len(passes_non_acquired) > 0:
            i_pass = passes_non_acquired[0]
            all_i = arange(0, len(acquired))
            i = all_i[(collection_pass == i_pass) & ~acquired]
        else:
            i = []

        return i

    def collection_range_first_i(self, i):
        """i: current scan point number (0-based)"""
        from numpy import arange

        acquired = self.acquired
        all_i = arange(0, len(acquired))
        all_i_not_acquired = all_i[(all_i >= i) & ~acquired]
        if len(all_i_not_acquired) > 0:
            next_i = all_i_not_acquired[0]
        else:
            next_i = len(acquired)

        return next_i

    def collection_range_last_i(self, i):
        """i: current scan point number (0-based)"""
        from numpy import arange

        i = self.collection_range_first_i(i)
        acquired, collection_pass = make_same_length(self.acquired, self.collection_pass)
        if 0 <= i < len(collection_pass):
            i_pass = collection_pass[i]
            all_i = arange(0, len(acquired))
            i = all_i[(collection_pass == i_pass) & (all_i >= i) & ~acquired]
            ranges = self.ranges(i)
            if len(ranges) > 0:
                last_i = ranges[0][1]
            else:
                last_i = len(acquired)
        else:
            last_i = len(acquired)

        return last_i

    @monitored_property
    def collection_pass_count(
        self,
        collection_variable_wait,
        collection_variable_value_lists,
    ):
        """Into how many passes does the data collection need to be broken up?"""
        count = 1
        N_var = min(len(collection_variable_value_lists), len(collection_variable_wait))
        for i in range(0, N_var):
            wait = collection_variable_wait[i]
            if wait or count > 1:
                count *= len(collection_variable_value_lists[i])
        return count

    @monitored_property
    def collection_pass_length(self, n, collection_pass_count):
        from floordiv import floordiv
        return floordiv(n, collection_pass_count)

    @property
    def collection_passes(self,):
        """List of integers, 0,1,...collection_pass_count-1"""
        from numpy import unique
        acquired, collection_pass = make_same_length(self.acquired, self.collection_pass)
        passes = unique(collection_pass[~acquired])
        return passes

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

    def collection_pass_i(self, i_pass):
        from numpy import arange

        acquired, collection_pass = make_same_length(self.acquired, self.collection_pass)

        all_i = arange(0, len(acquired))
        i = all_i[(collection_pass == i_pass) & ~acquired]
        return i

    override_repeat = db_property("override_repeat", False, local=True)
    override_repeat_count = db_property("override_repeat_count", 1, local=True)

    @monitored_property
    def finish_series(self, __finish_series__):
        return __finish_series__

    @finish_series.setter
    def finish_series(self, value):
        self.__finish_series__ = value
        self.decide_n_collect()

    __finish_series__ = db_property("finish_series", False, local=True)

    @monitored_property
    def finish_series_variable(self, __finish_series_variable__):
        return __finish_series_variable__

    @finish_series_variable.setter
    def finish_series_variable(self, value):
        self.__finish_series_variable__ = value
        self.decide_n_collect()

    __finish_series_variable__ = db_property("finish_series_variable", "Temperature", local=True)

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

    __n_collect__ = db_property("__n_collect__", 0, local=True)

    def n_finish_series(self, image_number):
        n_finish_series = self.n
        if self.finish_series:
            period = 1
            for i, variable in enumerate(self.collection_variables_with_count):
                period *= len(self.collection_variable_value_lists[i])
                if variable == self.finish_series_variable:
                    break
            n_finish_series = (int(image_number) // period + 1) * period
        return n_finish_series

    def wait_for_collection_variables(self):
        """i: range 0 to self.n"""
        from time import sleep
        variables = self.collection_variables_with_count
        while any([self.variable_changing(var) for var in variables]):
            if self.cancelled:
                break
            self.actual(self.collection_variable_changing_report)
            sleep(1.0)

    @property
    def collection_variable_changing_report(self):
        message = ""
        for variable in self.collection_variables_with_count:
            if self.variable_changing(variable):
                formatted_value = self.variable_formatted_value(variable)
                message += f"{variable}={formatted_value}, "
        message = message.strip(", ")
        return message

    def collection_variable_values(self, i):
        all_values = self.collection_variable_all_values
        n_var, n = all_values.shape
        if n > 0:
            values = list(all_values[:, i % n])
        else:
            from numpy import nan
            values = [nan] * n_var
        return values

    @monitored_property
    def collection_variable_all_values(self, collection_variable_value_lists):
        from numpy import array, repeat, tile, vstack
        all_values = array([collection_variable_value_lists[0]])
        for values in collection_variable_value_lists[1:]:
            all_values = vstack([
                tile(all_values, len(values)),
                repeat(values, len(all_values[0])),
            ])
        return all_values

    @monitored_property
    def collection_variable_all_formatted_values(self, collection_variable_formatted_value_lists):
        from numpy import array, repeat, tile, vstack, chararray
        all_values = array([collection_variable_formatted_value_lists[0]])
        for values in collection_variable_formatted_value_lists[1:]:
            all_values = vstack([
                tile(all_values, len(values)),
                repeat(values, len(all_values[0])),
            ])
        all_values = all_values.view(chararray)
        return all_values

    @monitored_property
    def collection_variable_count(self, collection_variables_with_count):
        return len(collection_variables_with_count)

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
        def delay(self, collection_variables_with_count):
            return "Delay" in collection_variables_with_count

        @monitored_property
        def laser_on(self, collection_variables_with_count):
            return "Laser_on" in collection_variables_with_count

        @monitored_property
        def temperature(self, collection_variables_with_count):
            return "Temperature" in collection_variables_with_count

        @monitored_property
        def power(self, collection_variables_with_count):
            return "Power" in collection_variables_with_count

        @monitored_property
        def scan_motor(self, collection_variables_with_count):
            return "Scan_Motor" in collection_variables_with_count

        @monitored_property
        def alio(self, collection_variables_with_count):
            return "Alio" in collection_variables_with_count

        collection_variables_with_count = alias_property("instance.collection_variables_with_count")

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
            if variable_name in self.instance.collection_variables_with_count:
                i = self.instance.collection_variables_with_count.index(variable_name)
                if i < len(divider_list):
                    divider = divider_list[i]
            return divider

    def scan_point_divider(self, variable_name):
        divider = 1
        collection_variables_with_count = self.collection_variables_with_count
        if variable_name in collection_variables_with_count:
            i = collection_variables_with_count.index(variable_name)
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
    def collection_variables_with_count(self, collection_variables_with_options) -> Iterable:
        variables = []
        repeat_count = 0
        for variable in collection_variables_with_options:
            if "=" in variable:
                variable = variable.split("=")[0]
            if variable == "Repeat":
                variable = f"Repeat{repeat_count + 1}"
                repeat_count += 1
            variables.append(variable)
        return variables

    @monitored_property
    def collection_variables_with_options(self, collection_order) -> Sized:
        """e.g. 'Laser_on=[0,1]', 'Repeat=16' """
        from split_list import split_list
        variables = split_list(collection_order.replace(" ", ""))
        return variables

    @monitored_property
    def collection_variable_value_lists(self, variable_values_dict, collection_variables_with_count):
        return [variable_values_dict[v] for v in collection_variables_with_count]

    @monitored_property
    def variable_values_dict(
            self,
            temperature_scan_values,
            power_scan_values,
            motor_scan_values,
            delay_scan_values,
            laser_on_scan_values,
            alio_scan_values,
            repeat_count_lists,
    ):
        values = {
            "Temperature": temperature_scan_values,
            "Power": power_scan_values,
            "Scan_Motor": motor_scan_values,
            "Delay": delay_scan_values,
            "Laser_on": laser_on_scan_values,
            "Alio": alio_scan_values,
        }
        for (i, count_list) in enumerate(repeat_count_lists):
            values[f"Repeat{i + 1}"] = count_list
        return values

    temperature_scan_values = alias_property("temperature_scan.values")
    power_scan_values = alias_property("power_scan.values")
    motor_scan_values = alias_property("motor_scan.values")
    delay_scan_values = alias_property("delay_scan.values")
    laser_on_scan_values = alias_property("laser_on_scan.values")
    alio_scan_values = alias_property("alio_scan.values")

    @monitored_property
    def repeat_count_lists(self, repeat_count_list):
        return [list(range(0, count)) for count in repeat_count_list]

    @monitored_property
    def collection_variable_formatted_value_lists(self, variable_formatted_values_dict, collection_variables_with_count):
        return [variable_formatted_values_dict[v] for v in collection_variables_with_count]

    @monitored_property
    def variable_formatted_values_dict(
            self,
            temperature_scan_formatted_values,
            power_scan_formatted_values,
            motor_scan_formatted_values,
            delay_scan_formatted_values,
            laser_on_scan_formatted_values,
            alio_scan_formatted_values,
            repeat_count_formatted_lists,
    ):
        values = {
            "Temperature": temperature_scan_formatted_values,
            "Power": power_scan_formatted_values,
            "Scan_Motor": motor_scan_formatted_values,
            "Delay": delay_scan_formatted_values,
            "Laser_on": laser_on_scan_formatted_values,
            "Alio": alio_scan_formatted_values,
        }
        for (i, count_list) in enumerate(repeat_count_formatted_lists):
            values[f"Repeat{i + 1}"] = count_list
        return values

    temperature_scan_formatted_values = alias_property("temperature_scan.formatted_values")
    power_scan_formatted_values = alias_property("power_scan.formatted_values")
    motor_scan_formatted_values = alias_property("motor_scan.formatted_values")
    delay_scan_formatted_values = alias_property("delay_scan.formatted_values")
    laser_on_scan_formatted_values = alias_property("laser_on_scan.formatted_values")
    alio_scan_formatted_values = alias_property("alio_scan.formatted_values")

    @monitored_property
    def repeat_count_formatted_lists(self, repeat_count_lists):
        formatted_lists = []
        for count_list in repeat_count_lists:
            formatted_list = [f"{count + 1:02.0f}" for count in count_list]
            formatted_lists.append(formatted_list)
        return formatted_lists

    @monitored_property
    def variable_formatted_value_dict(
            self,
            temperature_scan_formatted_value,
            power_scan_formatted_value,
            motor_scan_formatted_value,
            delay_scan_formatted_value,
            laser_on_scan_formatted_value,
            alio_scan_formatted_value,
            current_repeat_count_formatted_values,
    ):
        values = {
            "Temperature": temperature_scan_formatted_value,
            "Power": power_scan_formatted_value,
            "Scan_Motor": motor_scan_formatted_value,
            "Delay": delay_scan_formatted_value,
            "Laser_on": laser_on_scan_formatted_value,
            "Alio": alio_scan_formatted_value,
        }
        for (i, value) in enumerate(current_repeat_count_formatted_values):
            values[f"Repeat{i + 1}"] = value
        return values

    temperature_scan_formatted_value = alias_property("temperature_scan.formatted_value")
    power_scan_formatted_value = alias_property("power_scan.formatted_value")
    motor_scan_formatted_value = alias_property("motor_scan.formatted_value")
    delay_scan_formatted_value = alias_property("delay_scan.formatted_value")
    laser_on_scan_formatted_value = alias_property("laser_on_scan.formatted_value")
    alio_scan_formatted_value = alias_property("alio_scan.formatted_value")

    @monitored_property
    def current_repeat_count_formatted_values(self, current_repeat_count_values):
        return [self.formatted_repeat_count(count) for count in current_repeat_count_values]

    @staticmethod
    def formatted_repeat_count(count):
        try:
            formatted_count = "%02d" % (count + 1)
        except ValueError:
            formatted_count = ""
        return formatted_count

    @monitored_property
    def current_repeat_count_values(
            self,
            current,
            collection_variable_is_repeat,
            scan_point_divider_list,
    ):
        counts = []
        for i, is_repeat in enumerate(collection_variable_is_repeat):
            if is_repeat:
                scan_point_divider = scan_point_divider_list[i]
                count = current // scan_point_divider
                counts.append(count)
        while len(counts) < 5:
            counts.append(0)
        return counts

    def variable_formatted_value(self, variable):
        return self.variable_formatted_value_dict[variable]

    @monitored_property
    def collection_variable_wait(self, variable_wait_dict, collection_variables_with_count):
        return [variable_wait_dict[v] for v in collection_variables_with_count]

    @monitored_property
    def variable_wait_dict(
            self,
            temperature_scan_wait,
            power_scan_wait,
            motor_scan_wait,
            delay_scan_wait,
            laser_on_scan_wait,
            alio_scan_wait,
            repeat_count_list,
    ):
        values = {
            "Temperature": temperature_scan_wait,
            "Power": power_scan_wait,
            "Scan_Motor": motor_scan_wait,
            "Delay": delay_scan_wait,
            "Laser_on": laser_on_scan_wait,
            "Alio": alio_scan_wait,
        }
        for i in range(0, len(repeat_count_list)):
            values[f"Repeat{i + 1}"] = False
        return values

    temperature_scan_wait = alias_property("temperature_scan.wait")
    power_scan_wait = alias_property("power_scan.wait")
    motor_scan_wait = alias_property("motor_scan.wait")
    delay_scan_wait = alias_property("delay_scan.wait")
    laser_on_scan_wait = alias_property("laser_on_scan.wait")
    alio_scan_wait = alias_property("alio_scan.wait")

    def variable_wait(self, variable):
        return self.variable_wait_dict[variable]

    @monitored_property
    def collection_variable_ready(self, variable_ready_dict, collection_variables_with_count):
        return [variable_ready_dict[v] for v in collection_variables_with_count]

    @monitored_property
    def variable_ready_dict(
            self,
            temperature_scan_ready,
            power_scan_ready,
            motor_scan_ready,
            delay_scan_ready,
            laser_on_scan_ready,
            alio_scan_ready,
            repeat_count_list,
    ):
        values = {
            "Temperature": temperature_scan_ready,
            "Power": power_scan_ready,
            "Scan_Motor": motor_scan_ready,
            "Delay": delay_scan_ready,
            "Laser_on": laser_on_scan_ready,
            "Alio": alio_scan_ready,
        }
        for i in range(0, len(repeat_count_list)):
            values[f"Repeat{i + 1}"] = True
        return values

    temperature_scan_ready = alias_property("temperature_scan.ready")
    power_scan_ready = alias_property("power_scan.ready")
    motor_scan_ready = alias_property("motor_scan.ready")
    delay_scan_ready = alias_property("delay_scan.ready")
    laser_on_scan_ready = alias_property("laser_on_scan.ready")
    alio_scan_ready = alias_property("alio_scan.ready")

    def variable_ready(self, variable):
        return self.variable_ready_dict[variable]

    def variable_changing(self, variable):
        return not self.variable_ready(variable)

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
        if variable.startswith("Repeat"):
            text = "%02.0f" % (value + 1)
        if variable == "Alio":
            text = "\t".join(["%+1.3f" % x for x in value])
        return text

    def variable_log_label(self, variable):
        if variable == "Scan_Motor":
            text = self.motor_scan.motor_name
        elif variable == "Alio":
            text = "\t".join(self.alio_scan.scan_points.name)
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
                    logging.error(f"{self.collection_order}: {variable}: {count_string}: {msg}: expecting int")
            counts.append(count)
        if override_repeat:
            if len(counts) > 0:
                counts[-1] = override_repeat_count
        return counts

    @monitored_property
    def repeat_count_list(self, collection_variables_with_options, override_repeat, override_repeat_count):
        counts = []
        for variable in collection_variables_with_options:
            if variable.startswith("Repeat="):
                count_string = variable.split("=")[-1]
                try:
                    count = int(eval(count_string))
                except Exception as msg:
                    logging.error(f"{self.collection_order}: {variable}: {count_string}: {msg}: expecting int")
                else:
                    counts.append(count)
        if override_repeat:
            if len(counts) > 0:
                counts[-1] = override_repeat_count
        while len(counts) < 5:
            counts.append(1)
        return counts

    @monitored_property
    def collection_variable_is_repeat(self, collection_variables_with_options):
        return [v.startswith("Repeat=") for v in collection_variables_with_options]

    @monitored_property
    def time_to_finish(self, scan_point_acquisition_time, n_remaining):
        return scan_point_acquisition_time * n_remaining

    scan_point_acquisition_time = alias_property("timing_system.composer.scan_point_acquisition_time")
    sequences_per_scan_point = alias_property("timing_system_acquisition.sequences_per_scan_point")

    @monitored_property
    def n_remaining(self, current_i, n_collect):
        from numpy import isnan
        n_remaining = n_collect - current_i if not isnan(current_i) else 0
        return n_remaining

    @monitored_property
    def current_i(self, current, acquiring, collection_first_i):
        from numpy import nan

        current_i = nan

        if acquiring:
            if current is not None:
                current_i = current
        else:
            if collection_first_i is not None:
                current_i = collection_first_i

        return current_i

    @monitored_property
    def detector_names(self, detector_configuration) -> List[str]:
        """e.g. 'xray_detector', 'xray_scope', 'laser_scope'"""
        from split_list import split_list
        names = split_list(detector_configuration.replace(" ", ""))
        return names

    @monitored_property
    def info_message(self, dataset_complete, current_i, n_collect, scan_point_name, file_basenames):
        from numpy import isnan

        if dataset_complete:
            message = "Dataset complete"
        elif current_i > n_collect:
            message = "Collection completed"
        else:
            if not isnan(current_i):
                message = f"{scan_point_name} {current_i + 1} of {n_collect}"
                if current_i < n_collect and current_i < len(file_basenames):
                    message += ": " + file_basenames[current_i]
            else:
                message = ""
        message = message[0:1].upper() + message[1:]
        return message

    status_message = monitored_value_property(default_value="")
    actual_message = monitored_value_property(default_value="")

    @monitored_property
    def acquisition_status(
            self,
            acquiring,
            current,
            n_collect,
            scan_point_name,
            file_basenames,
            collection_variables_with_count,
            collection_variable_all_formatted_values,
    ):
        if acquiring and current < n_collect:
            message = f"Acquiring {scan_point_name} {current + 1:.0f} of {n_collect:.0f}"
            if 0 <= current < len(file_basenames):
                message += ": " + file_basenames[current]
            if 0 <= current < collection_variable_all_formatted_values.shape[1]:
                formatted_values = collection_variable_all_formatted_values[:, current]
                for variable, formatted_value in zip(collection_variables_with_count, formatted_values):
                    message += f", {variable} {formatted_value}"
        elif not acquiring and current < n_collect:
            message = "Collection suspended"
        else:
            message = "Collection completed"
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
            self.actual(f"Erasing X-ray image {i + 1!r}")
            if self.cancelled:
                break
            self.remove(filename)
        for i, filename in enumerate(self.scope_traces_collected("xray_scope")):
            self.actual(f"Erasing X-ray scope trace {i + 1!r}")
            if self.cancelled:
                break
            self.remove(filename)
        for i, filename in enumerate(self.scope_traces_collected("laser_scope")):
            self.actual(f"Erasing Laser scope trace {i + 1!r}")
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
                logging.warning(f"{filename}: {x}")

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
            suffix = f"_{i % N + 1:02.0f}"
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
            logging.info(message)
        self.status_message = message

    def actual(self, message):
        if message:
            logging.info(message)
        self.actual_message = message

    from thread_property import thread_property
    collecting_dataset = collecting = thread_property("collect_dataset")

    def collect_dataset(self):
        from time import sleep

        self.status("Collection started")

        self.configuration_save()

        self.timing_system_sequences_load()
        self.actual("Timing system setup...")
        first = self.collection_range_first_i(0)
        last = self.collection_range_last_i(0)
        self.current = first
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
        self.update_status_start()

        while True:
            if self.cancelled:
                logging.info("Ending because cancelled")
                break

            if self.current >= self.n_collect:
                logging.info(f"Ending because current {self.current} >= n_collect {self.n_collect}")
                break

            first = self.collection_range_first_i(self.current)
            last = self.collection_range_last_i(self.current)
            logging.info(f"Starting collection range first {first}, last {last}")

            if first >= self.n_collect:
                logging.info(f"Ending because first {first} >= n_collect {self.n_collect}")
                break

            self.timing_system_acquisition.first_scan_point = first
            self.timing_system_acquisition.last_scan_point = last
            self.xray_detector_timing_system_setup(first)
            self.scope_timing_system_setup("xray_scope", first)
            self.scope_timing_system_setup("laser_scope", first)

            sleep(1)  # needed for temperature?
            self.wait_for_collection_variables()

            self.timing_system_acquisition_start()

            while True:
                if not self.timing_system_sequencer.queue_active:
                    logging.info("Acquisition completed.")
                    break
                if self.cancelled:
                    logging.info("Cancelled. Stopping acquisition.")
                    break
                if self.data_collection_completed:
                    logging.info("Data collection completed. Stopping acquisition.")
                    break
                sleep(0.1)

            self.timing_system_acquisition_stop()

            self.status("Collection suspended")

        self.update_status_stop()
        self.diagnostics_stop()
        self.timing_system_cleanup()
        self.sleep(5)
        self.logging_stop()
        self.scope_stop("laser_scope")
        self.scope_stop("xray_scope")
        self.sleep(5)
        self.xray_detector_stop()
        self.configuration_save()

        self.finish_series = False

        self.status("Collection ended")

    @property
    def data_collection_completed(self):
        return self.current >= self.n_collect

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

    generating_packets = alias_property("timing_system_acquisition.generating_packets")

    timing_system = alias_property("domain.timing_system_client")
    timing_system_sequencer = alias_property("timing_system.sequencer")
    timing_system_acquisition = alias_property("timing_system.acquisition")
    delay_scan = alias_property("timing_system.delay_scan")
    laser_on_scan = alias_property("timing_system.laser_on_scan")
    motor_scan = alias_property("domain.motor_scan")
    power_scan = alias_property("domain.power_scan")
    temperature_scan = alias_property("domain.temperature_scan")
    alio_scan = alias_property("domain.alio_scan")

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

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
        from time import sleep, time
        self.actual("Timing system acquisition start...")

        self.timing_system.sequencer.queue_active = True
        t = time()
        while not self.timing_system.sequencer.queue_active and not self.cancelled:
            count = self.timing_system.sequencer.current_queue_sequence_count
            self.actual(f"Timing system: Idle > Acquiring: {time()-t:.3f} s (seq {count})")
            sleep(0.25)

        self.actual(f"Timing system acquisition started: {self.timing_system.sequencer.queue_active}")

    def timing_system_acquisition_stop(self):
        from time import sleep, time
        self.actual("Timing system acquisition stop...")

        self.timing_system.sequencer.queue_active = False
        t = time()
        while self.timing_system.sequencer.queue_active and not self.cancelled:
            count = self.timing_system.sequencer.current_queue_sequence_count
            self.actual(f"Timing system: Acquiring > Idle: {time()-t:.3f} s (seq {count})")
            sleep(0.25)

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
                first = self.collection_first_i
            count = first
            channel_mnemonic = "xdet"
            if channel_mnemonic in self.timing_system.channels.mnemonics:
                channel = getattr(self.timing_system.channels, channel_mnemonic)
                channel.acq_count.count = count
            else:
                logging.warning(f"Timing system channel {channel_mnemonic!r} not found")

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
                first = self.collection_first_i
            N_traces = self.sequences_per_scan_point
            count = first * N_traces
            channel_mnemonic = name
            if name == "xray_scope":
                channel_mnemonic = "xosct"
            if name == "laser_scope":
                channel_mnemonic = "losct"
            if channel_mnemonic in self.timing_system.channels.mnemonics:
                channel = getattr(self.timing_system.channels, channel_mnemonic)
                channel.acq_count.count = count
            else:
                logging.warning(f"Timing system channel {channel_mnemonic!r} not found")

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
        pass_count = acq_count % N
        suffix = f"_{pass_count + 1:02.0f}"
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
    def configuration_tables(self):
        return self.domain.configuration_tables

    @monitored_property
    def configuration_filename(self, directory):
        from os.path import basename
        return directory + "/" + basename(directory) + ".conf"

    def xray_image_filename(self, i):
        filename = ""
        from numpy import isnan
        file_basenames = self.file_basenames
        if not isnan(i) and i in range(0, len(file_basenames)):
            filename = self.directory + "/xray_images/" + file_basenames[i] + ".mccd"
        return filename

    @property
    def xray_image_filenames(self):
        filenames = self.directory + "/xray_images/" + self.file_basenames + ".mccd"
        return filenames

    @property
    def xray_image_filenames_to_collect(self):
        from numpy import array, chararray
        filenames = array([], dtype=str).view(chararray)
        if "xray_detector" in self.detector_names:
            filenames = self.xray_image_filenames
        return filenames

    @monitored_property
    def file_basenames(self, basename, file_suffixes):
        """numpy chararray"""
        return basename + file_suffixes

    @monitored_property
    def file_suffixes_new(self, collection_variable_all_formatted_values):
        from numpy import chararray, array
        suf = "_" + collection_variable_all_formatted_values
        suffixes = suf[0]
        for s in suf[1:]:
            suffixes = suffixes + s
        serial = [f"_{i + 1:04.0f}" for i in range(0, len(suffixes))]
        serial = array(serial, dtype=str).view(chararray)
        suffixes = serial + suffixes
        return suffixes

    @monitored_property
    def file_suffixes(self, collection_variable_formatted_value_lists):
        """numpy chararray"""
        from numpy import array, chararray, repeat, tile
        suffixes = []
        for value_list in collection_variable_formatted_value_lists:
            suffix = ["_" + val for val in value_list]
            suffix = array(suffix, dtype=str).view(chararray)
            suffixes += [suffix]
        names = array([""]).view(chararray)
        for suffix in suffixes:
            names = tile(names, len(suffix)) + repeat(suffix, len(names))
        serial = ["_%04.0f" % (i + 1) for i in range(0, len(names))]
        serial = array(serial, dtype=str).view(chararray)
        names = serial + names
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
        names = self.collection_variables_with_count
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
        labels += [self.variable_log_label(v) for v in self.collection_variables_with_count]
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
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.INFO, format=msg_format)

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    from IOC import ioc as _ioc

    self = acquisition_driver(domain_name)
    ioc = _ioc(driver=self)
    print('ioc.running = True')
    # ioc.run()

    from handler import handler as _handler
    from reference import reference as _reference

    @_handler
    def report(event=None):
        logging.info(f'event = {event}')

    property_names = [
        # "acquisition_status",
    ]
    for property_name in property_names:
        _reference(self, property_name).monitors.add(report)
