#!/usr/bin/env python
"""
Database save and recall motor positions
Author: Friedrich Schotte
Date created: 2022-06-16
Date last modified: 2022-07-10
Revision comment: Fixed: Issue:
    configuration_name:
    Was: 'BioCARS.configuration_table.timing_modes'
    Should be: 'BioCARS.timing_modes'
"""
__version__ = "2.0.10"

import logging
from traceback import format_exc

from alias_property import alias_property
from cached_function import cached_function
from db_property import db_property
from handler import handler
from monitored_method import monitored_method
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property
from reference import reference
from value_property import value_property


@cached_function()
def configuration_table_motor_driver(configuration, index):
    return Configuration_Table_Motor_Driver(configuration, index)


class Configuration_Table_Motor_Driver:
    def __init__(self, configuration, index):
        self.configuration = configuration
        self.index = index
        super().__init__()

    def __repr__(self):
        return f"{self.configuration}.motor[{self.index}]"

    @property
    def db_name(self):
        return f"{self.configuration.db_name}/motor{self.index+1}"

    motor_name = db_property("motor_name", "")  # Python expression
    name = db_property("name", "motorX")  # mnemonic for column
    format_string = db_property("format_string", "%s")
    tolerance = db_property("tolerance", 0.0)

    @monitored_property
    def formatted_position(self, current_position, format_string):
        return formatted_value_from_value(current_position, format_string)

    @formatted_position.setter
    def formatted_position(self, formatted_position):
        value = value_from_formatted_value(formatted_position, self.format_string)

        if not (formatted_position == "" and self.formatted_position == ""):
            self.current_position = value
        else:
            logging.debug(f"Reasserting {self.position_reference} = {value!r} not necessary")

    @monitored_property
    def current_position(self, position):
        if self.is_numeric:
            from numpy import nan
            try:
                value = float(position)
            except Exception as x:
                logging.warning(f"{self}: float({position}): {x}")
                value = nan
        else:
            try:
                value = str(position)
            except Exception as x:
                logging.warning(f"{self}: str({position}): {x}")
                value = ""
        return value

    @current_position.setter
    def current_position(self, value):
        logging.debug(f"{self.position_reference} = {value!r}")
        self.position = value

    position = value_property("position_reference")

    @monitored_property
    def position_reference(self, object_name):
        attribute_name = ""
        if object_name.endswith(".value"):
            object_name = object_name.replace(".value", "")
            attribute_name = "value"
        try:
            motor_object = eval(object_name)
        except Exception as x:
            logging.error(f"{object_name}: {x}\n{format_exc()}")
            motor_object = self.Dummy_motor()
        if hasattr(type(motor_object), "value"):
            attribute_name = "value"
        if not hasattr(type(motor_object), "value"):
            if "." in object_name:
                parts = object_name.split(".")
                object_name, attribute_name = ".".join(parts[0:-1]), parts[-1]
                try:
                    motor_object = eval(object_name)
                except Exception as x:
                    logging.error(f"{object_name}: {x}\n{format_exc()}")
                    motor_object = self.Dummy_motor()
        ref = reference(motor_object, attribute_name)
        return ref

    def inputs_choices(self):
        return [self.choices_reference]

    def calculate_choices(self, choices):  # noqa: Method 'calculate_choices' may be 'static'
        try:
            choices = list(choices)
        except (TypeError, ValueError):
            choices = []
        return choices

    choices = monitored_property(
        inputs=inputs_choices,
        calculate=calculate_choices,
    )

    @monitored_property
    def choices_reference(self, position_reference):
        motor_object = position_reference.object
        basename = position_reference.attribute_name
        property_names = [basename + "_choices", basename + "s", ]
        for property_name in property_names:
            if hasattr(type(motor_object), property_name):
                ref = reference(motor_object, property_name)
                break
        else:
            ref = reference(self, "default_choices")
        return ref

    default_choices = monitored_value_property(default_value=[])

    command_position = value_property("command_position_reference")

    @monitored_property
    def command_position_reference(self, position_reference):
        if hasattr(type(position_reference.object), "command_value"):
            ref = reference(position_reference.object, "command_value")
        else:
            ref = position_reference
        return ref

    @monitored_property
    def nominal_position(self, formatted_nominal_position, format_string):
        return value_from_formatted_value(formatted_nominal_position, format_string)

    @monitored_property
    def formatted_nominal_position(self, formatted_command_row_values):
        try:
            formatted_nominal_position = formatted_command_row_values[self.index]
        except IndexError:
            formatted_nominal_position = ""
        return formatted_nominal_position

    formatted_command_row_values = alias_property("configuration.formatted_command_row_values")

    @property
    def default_position(self):
        from numpy import nan
        if self.is_numeric:
            default_position = nan
        else:
            default_position = ""
        return default_position

    @monitored_property
    def in_position(self, nominal_position, current_position):
        return self.position_matches(nominal_position, current_position)

    def position_matches(self, nominal_position, current_position):
        """
        nominal_pos: position of motor number *motor_number*
        actual_pos: current position of motor number *motor_number*
            (optional, given to speed up calculation)
        return value: True of False
        """
        if self.is_numeric:
            matches = self.numerical_position_matches(nominal_position, current_position)
        else:  # string-valued
            matches = self.string_matches(nominal_position, current_position)
        return matches

    def numerical_position_matches(self, nominal_position, current_position):
        """
        nominal_pos: position of motor number *motor_number*
        actual_pos: current position of motor number *motor_number*
            (optional, given to speed up calculation)
        return value: True of False
        """
        from numpy import isnan
        if isnan(nominal_position):
            matches = True
        else:
            matches = abs(nominal_position - current_position) <= self.tolerance
        return matches

    @monitored_method
    def string_matches(self, nominal_position, current_position):
        """
        nominal_pos: position of motor number *motor_number*
        actual_pos: current position of motor number *motor_number*
            (optional, given to speed up calculation)
        return value: True of False
        """
        if nominal_position != "":
            matches = nominal_position == current_position
        else:
            matches = True
        # debug("matches(%r,%r): %r" % (nominal_pos,actual_pos,matches))
        return matches

    @monitored_property
    def default_value(self, is_numeric):
        from numpy import nan
        return nan if is_numeric else ""

    @monitored_property
    def is_numeric(self, format_string):
        """If the motor position a number?"""
        # "%s" -> False, "%.3f" -> True
        is_numeric = False if "s" in format_string else True
        return is_numeric

    @monitored_property
    def configuration_name(self, is_configuration, motor_object):
        """If this is a linked configuration, what is its name?"""
        if is_configuration:
            name = getattr(motor_object, "name", "")
            # BioCARS.configuration_table.timing_modes -> BioCARS.timing_modes
            name = name.replace(".configuration_table", "")
        else:
            name = ""
        return name

    @monitored_property
    def is_configuration(self, motor_object):
        """If this is a linked configuration?"""
        type_name = type(motor_object).__name__
        is_configuration = "configuration" in type_name.lower()
        return is_configuration

    @monitored_property
    def motor_object(self, position_reference):
        return position_reference.object

    @monitored_property
    def object_name(self, motor_name):
        name = motor_name
        if not name.startswith("self.domain."):
            name = "self.domain." + name
        return name

    class Dummy_motor:
        from numpy import nan
        value = nan

    @property
    def domain(self):
        from domain import domain
        return domain(self.configuration.domain_name)


def formatted_value_from_value(current_position, format_string):
    try:
        from numpy import isnan, isinf
        if isnan(current_position):
            text = ""
        elif isinf(current_position) and current_position > 0:
            text = "inf"
        elif isinf(current_position) and current_position < 0:
            text = "-inf"
        elif "time" in format_string:
            precision = format_string.split(".")[-1][0]
            try:
                precision = int(precision)
            except ValueError:
                precision = 3
            from time_string import time_string
            text = time_string(current_position, precision)
        else:
            text = format_string % current_position
    except TypeError:
        text = str(current_position)
    return text


def value_from_formatted_value(formatted_value, format_string):
    from time_string import seconds
    from numpy import nan
    if "time" in format_string:
        value = seconds(formatted_value)
    elif "%s" in format_string:
        value = formatted_value  # "%s" -> keep as string
    else:
        if formatted_value == "":
            value = nan
        else:
            try:
                value = eval(formatted_value)
            except Exception as x:
                logging.error(f"eval({formatted_value!r}): {x}")
                value = nan
            try:
                value = float(value)
            except (ValueError, TypeError) as x:
                logging.error(f"float({value!r}): {x}")
                value = nan
    return value


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    # base_name = "beamline_configuration"
    # base_name = "Julich_chopper_modes"
    # base_name = "heat_load_chopper_modes"
    # base_name = "timing_modes"
    # base_name = "sequence_modes"
    # base_name = "delay_configuration"
    # base_name = "temperature_configuration"
    # base_name = "power_configuration"
    # base_name = "scan_configuration"
    # base_name = "diagnostics_configuration"
    # base_name = "detector_configuration"
    base_name = "method"
    # base_name = "laser_optics_modes"
    # base_name = "alio_diffractometer_saved"

    from configuration_table_driver import configuration_table_driver

    configuration = configuration_table_driver(f"{domain_name}.{base_name}")
    self = configuration_table_motor_driver(configuration, 0)

    @handler
    def report(event): logging.info(f"{event}")


    print('reference(self, "current_position").monitors.add(report)')
    reference(self, "current_position").monitors.add(report)
