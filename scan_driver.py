"""
Author: Friedrich Schotte
Date created: 2021-10-22
Date last modified: 2022-07-16
Revision comment: Issue: When collecting discreet temperatures, hanging at first
   temperature_change
"""
__version__ = "1.8.1"

import logging
from cached_function import cached_function
from handler import handler
from reference import reference
from alias_property import alias_property
from db_property import db_property
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property
from numpy import nan


@cached_function()
def scan_driver(domain_name): return Scan_Driver(domain_name)


class Scan_Driver:
    def __init__(self, domain_name):
        self.domain_name = domain_name

    @property
    def running(self):
        return all([
            self.handling_value_index,
            self.handling_collecting_dataset,
        ])

    @running.setter
    def running(self, running):
        self.handling_value_index = running
        self.handling_collecting_dataset = running

    # PVs to be hosted
    values_string = db_property("values_string", "", local=True)
    wait = db_property("wait", False, local=True)
    return_value = db_property("return_value", nan, local=True)

    @monitored_property
    def ready(self, values, values_index, motor_value, motor_moving):
        if 0 <= values_index < len(values):
            set_value = values[values_index]
        else:
            set_value = nan
        ready = not motor_moving and abs(set_value - motor_value) < self.tolerance
        return ready

    @monitored_property
    def values(self, values_string):
        from expand_scan_points import safe_expand_scan_points
        values = safe_expand_scan_points(values_string)
        if len(values) == 0:
            values = [self.motor_command_value]
        return values

    @values.setter
    def values(self, values):
        if len(values) == 0:
            self.values_string = ""
        else:
            self.values_string = repr(list(values))

    @monitored_property
    def value_count(self, values):
        return len(values)

    @monitored_property
    def formatted_values(self, values):
        return [self.format(value) for value in values]

    @monitored_property
    def formatted_command_value(self, motor_command_value):
        return self.format(motor_command_value)

    @formatted_command_value.setter
    def formatted_command_value(self, formatted_value):
        try:
            value = self.value_of_formatted_value(formatted_value)
        except Exception as x:
            logging.error(f"{formatted_value!r}: {x}")
        else:
            self.motor_command_value = value

    @monitored_property
    def formatted_value(self, motor_value):
        return self.format(motor_value)

    @formatted_value.setter
    def formatted_value(self, formatted_value):
        self.formatted_command_value = formatted_value

    def format(self, value):
        return (self.format_string % value) + self.unit

    def value_of_formatted_value(self, formatted_value):
        formatted_value = formatted_value.replace(self.unit, "")
        return float(formatted_value)

    format_string = db_property("format_string", "%s")
    unit = db_property("unit", "")

    # Imported PVs
    enabled = alias_property("acquisition.scanning.scan_motor")
    scan_point_divider = alias_property("acquisition.scan_point_dividers.scan_motor")
    scan_point_number = alias_property("timing_system.registers.image_number.count")
    acquiring = alias_property("timing_system.sequencer.acquiring")
    collecting_dataset = alias_property("acquisition.collecting_dataset")

    acquisition = alias_property("domain.acquisition_client")
    timing_system = alias_property("domain.timing_system_client")

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @property
    def db_name(self):
        return f"domains/{self.domain_name}/{self.db_basename}"

    @property
    def db_basename(self):
        return self.class_name.replace("_driver", "")

    @monitored_property
    def scanning(self, enabled, acquiring, wait):
        return enabled and acquiring and not wait

    @scanning.setter
    def scanning(self, scanning):
        if not scanning:
            self.acquiring = False

    @monitored_property
    def trajectory_array(self, trajectory_times_values):
        return trajectory_times_values.flatten()

    @monitored_property
    def trajectory_times_values(self, trajectory_relative_times_values, start_time):
        from numpy import array
        relative_times, values = trajectory_relative_times_values
        times = relative_times + start_time
        return array([times, values], dtype=float)

    start_time = db_property("start_time", 0.0, local=True)

    @monitored_property
    def trajectory_relative_times_values(self, values, scan_point_acquisition_time):
        from linear_ranges import linear_ranges
        from numpy import array
        scan_point_numbers, values = linear_ranges(values)
        relative_times = scan_point_numbers * scan_point_acquisition_time
        return array([relative_times, values], dtype=float)

    scan_point_acquisition_time = alias_property("timing_system.composer.scan_point_acquisition_time")

    @monitored_property
    def values_index(self, scan_point_number, scan_point_divider, values):
        try:
            index = (scan_point_number // scan_point_divider) % len(values)
        except ZeroDivisionError:
            index = 0
        return index

    def handle_values_index_event(self, event):
        values_index = event.value
        # logging.info(f"values_index = {values_index}")
        self.handle_values_index_change(values_index, event.time)

    def handle_values_index_change(self, values_index, time):
        # if self.collecting_dataset and self.acquiring and self.enabled:
        if self.collecting_dataset and self.enabled:
            values = self.values
            if 0 <= values_index < len(values):
                self.motor_command_value = values[values_index]
            self.update_slewing(values_index)
            self.update_start_time(time, values_index)

    def handle_collecting_dataset_event(self, event):
        collecting_dataset = event.value
        self.handle_collecting_dataset_change(collecting_dataset)

    def handle_collecting_dataset_change(self, collecting_dataset):
        if self.enabled:
            if collecting_dataset:
                values_index = self.values_index
                values = list(self.values)
                if 0 <= values_index < len(values):
                    self.motor_command_value = values[values_index]
                    self.update_slewing(values_index)
            else:
                self.motor_command_value = self.return_value

    @property
    def handling_value_index(self):
        return self.values_index_handler in self.value_index_handlers

    @handling_value_index.setter
    def handling_value_index(self, enabled):
        if enabled:
            self.value_index_handlers.add(self.values_index_handler)
        else:
            self.value_index_handlers.remove(self.values_index_handler)

    @property
    def handling_collecting_dataset(self):
        return self.collecting_dataset_handler in self.collecting_dataset_handlers

    @handling_collecting_dataset.setter
    def handling_collecting_dataset(self, enabled):
        if enabled:
            self.collecting_dataset_handlers.add(self.collecting_dataset_handler)
        else:
            self.collecting_dataset_handlers.remove(self.collecting_dataset_handler)

    @property
    def values_index_handler(self):
        return handler(self.handle_values_index_event)

    @property
    def collecting_dataset_handler(self):
        return handler(self.handle_collecting_dataset_event)

    @property
    def value_index_handlers(self):
        return reference(self, "values_index").monitors

    @property
    def collecting_dataset_handlers(self):
        return reference(self, "collecting_dataset").monitors

    def update_slewing(self, values_index):
        values = self.values
        if 0 <= values_index < len(values) and len(values) > 0:
            value = values[values_index]
            next_values_index = (values_index + 1) % len(values)
            next_value = values[next_values_index]
            self.slewing = next_value != value

    slewing = monitored_value_property(False)

    def update_start_time(self, time, values_index):
        new_start_time = time - values_index * self.scan_point_acquisition_time
        if abs(new_start_time - self.start_time) > 10:
            self.start_time = new_start_time

    motor_value = alias_property("motor.value")
    motor_command_value = alias_property("motor.command_value")
    tolerance = alias_property("motor.readback_slop")
    motor_moving = alias_property("motor.moving")

    @monitored_property
    def motor(self, motor_name):
        # noinspection PyBroadException
        try:
            motor = getattr(self.domain, motor_name)
        except Exception:
            from dummy_motor import Dummy_Motor
            if motor_name:
                motor_name = f"{self.domain_name}.{motor_name}"
            motor = Dummy_Motor(motor_name)
        return motor

    motor_name = db_property("motor_name", "HuberPhi", local=True)

    def __repr__(self):
        return "%s(%r)" % (self.class_name, self.domain_name)


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"

    self = scan_driver(domain_name)
