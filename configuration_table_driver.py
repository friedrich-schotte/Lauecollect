"""
Author: Friedrich Schotte
Date created: 2022-06-16
Date last modified: 2022-07-11
Revision comment: Updated example
"""
__version__ = "1.0.7"

import logging

from alias_property import alias_property
from thread_property_2 import thread_property, cancelled
from attribute_property import attribute_property
from cached_function import cached_function
from db_property import db_property
from function_property import function_property
from monitored_property import monitored_property
from file import file
from monitored_value_property import monitored_value_property
from configuration_all_motors_property import all_motors_property


@cached_function()
def configuration_table_driver(name):
    return Configuration_Table_Driver(name)


class Configuration_Table_Driver(object):
    """Database save and recall motor positions"""

    def __init__(self, name):
        """name: "domain_name.basename" e.g. "BioCARS.method" """
        self.name = name

        self.applying_row = None
        self.applying = False  # To suppress "Instance attribute applying defined outside __init__"

    def __repr__(self):
        return f"{self.class_name}({self.name!r})"

    @monitored_property
    def value(self, in_position, selected_description):
        if in_position:
            value = selected_description
        else:
            value = f"{selected_description}?"
        return value

    @value.setter
    def value(self, value):
        self.command_value = value

    @monitored_property
    def command_value(self, selected_description):
        return selected_description

    @command_value.setter
    def command_value(self, value):
        self.applied_row = self.row_of_description(value)

    @monitored_property
    def applied_row(self, command_row):
        return command_row

    @applied_row.setter
    def applied_row(self, row):
        row = int(row)  # TypeError: list indices must be integers or slices, not str
        self.command_row = row
        self.applying_row = row
        self.applying = True

    @thread_property
    def applying(self):
        if self.applying_row is not None:
            row = self.applying_row
            self.applying_row = None
        else:
            row = self.command_row
        self.apply_row(row)

    def apply_row(self, row):
        motor_rows = self.motor_rows
        try:
            formatted_values = motor_rows[row]
        except IndexError:
            formatted_values = [""] * self.n_motors
        self.apply_formatted_values(formatted_values)

    def apply_formatted_values(self, formatted_values):
        for i in range(0, self.n_motors):
            self.motor[i].formatted_position = formatted_values[i]
            if cancelled():
                break

    def apply(self):
        self.applying = True

    motors_in_position = all_motors_property("in_position")

    @monitored_property
    def in_position(self, motors_in_position):
        # logging.debug(f"motors_in_position = {motors_in_position}")
        return all(motors_in_position)

    @property
    def motor(self):
        from configuration_table_motors_driver import motors
        return motors(self)

    @monitored_property
    def formatted_command_row_values(self, command_row, motor_rows, n_motors):
        if command_row >= 0:
            formatted_command_values = motor_rows[command_row]
        else:
            formatted_command_values = [""] * n_motors
        return formatted_command_values

    @monitored_property
    def command_row(self, command_row_saved, n_rows):
        row = command_row_saved
        if row >= n_rows:
            row = -1
        return row

    @command_row.setter
    def command_row(self, row):
        row = int(row)
        if row >= self.n_rows:
            row = -1
        self.command_row_saved = row

    command_row_saved = db_property("command_row", 0, local=True)

    @monitored_property
    def n_rows(self, rows):
        return len(rows)

    @monitored_property
    def selected_description(self, descriptions, command_row):
        try:
            selected_description = descriptions[command_row]
        except IndexError:
            selected_description = ""
        return selected_description

    @selected_description.setter
    def selected_description(self, description):
        row = self.row_of_description(description)
        self.command_row = row

    def row_of_description(self, description):
        if description in self.descriptions:
            row = self.descriptions.index(description)
        else:
            row = -1
        return row

    @monitored_property
    def descriptions(self, columns):
        try:
            descriptions = columns[1]
        except IndexError:
            descriptions = []
        return descriptions

    @monitored_property
    def n_motors(self, header_row):
        return max(len(header_row) - 3, 0)

    @monitored_property
    def motor_rows(self, motor_columns):
        return transpose(motor_columns)

    @monitored_property
    def motor_columns(self, columns):
        return columns[3:]

    @monitored_property
    def columns(self, rows):
        return transpose(rows)

    @monitored_property
    def header_row(self, rows_with_header):
        try:
            header_row = rows_with_header[1]
        except IndexError:
            header_row = []
        return header_row

    @monitored_property
    def rows(self, rows_with_header):
        return rows_with_header[1:]

    @monitored_property
    def rows_with_header(self, file_content):
        rows = [line.split("\t") for line in file_content.rstrip("\n").split("\n")]
        rows = regular_2D_string_list(rows)
        return rows

    file_content = attribute_property("file", "content")
    file = function_property(file, "filename")

    @monitored_property
    def filename(self, domain_name, base_name):
        return f"{self.settings_dir}/domains/{domain_name}/table/{base_name}.txt"

    @property
    def settings_dir(self):
        from DB import db_global_settings_dir
        return db_global_settings_dir()

    @monitored_property
    def domain_name(self, name):
        return name.split(".")[0]

    @monitored_property
    def base_name(self, name):
        return name.split(".", 1)[-1]

    name = monitored_value_property("")

    @property
    def db_name(self):
        return "configuration/%s/%s" % (self.domain_name, self.base_name)

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @monitored_property
    def title(self, saved_title):
        if saved_title:
            title = saved_title
        else:
            title = self.base_name.replace("_", " ").title()
        return title

    @title.setter
    def title(self, title):
        self.saved_title = title

    saved_title = db_property("title", "")

    values = alias_property("descriptions")   # needed by acquisition_control
    names = all_motors_property("name")  # needed by configuration_client: __getattr__, state
    show_in_list = db_property("show_in_list", True)  # needed by Configuration_Tables_Panel


def transpose(a):
    return [list(x) for x in zip(*a)]


def regular_2D_string_list(a):
    n_col = max([len(row) for row in a])
    return [row + [""] * (n_col - len(row)) for row in a]


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
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

    from handler import handler as _handler

    from IOC import ioc as _ioc
    ioc = _ioc(f'{domain_name}.configuration.{base_name}')
    self = ioc.driver
    # from IOC_3 import ioc as _ioc
    # self = configuration_table_driver(f'{domain_name}.{base_name}')
    # ioc = _ioc(driver=self)

    @_handler
    def report(event=None): logging.info(f"{event}")

    # from reference import reference as _reference
    # _reference(self, "command_row_saved").monitors.add(report)
    # _reference(self, "command_row").monitors.add(report)
    print("ioc.start()")
