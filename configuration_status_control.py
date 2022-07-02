"""
Author: Friedrich Schotte
Date created: 2022-06-09
Date last modified: 2022-06-13
Revision comment:
"""
__version__ = "1.0"

import logging

from alias_property import alias_property
from cached_function import cached_function
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property
from spreadsheet_base_control import Spreadsheet_Base_Control


@cached_function()
def configuration_status_control(name):
    return Configuration_Status_Control(name)


class Configuration_Status_Control(Spreadsheet_Base_Control):
    @monitored_property
    def n_rows(self): return 1 + 1

    @n_rows.setter
    def n_rows(self, _): pass

    n_motors = alias_property("configuration.n_motors")

    @property
    def configuration(self):
        from configuration import configuration
        return configuration(self.name)

    @cached_function()
    def cell(self, row, column):
        if row == 1 and column == 1:
            cell = self.Name_Cell(self, row, column)
        elif row == 1 and column >= 3:
            cell = self.Motor_Cell(self, row, column)
        else:
            cell = self.Cell(self, row, column)
        return cell

    class Cell(Spreadsheet_Base_Control.Cell):
        from color import light_gray
        background_color = monitored_value_property(light_gray)
        configuration = alias_property("table.configuration")

    class Name_Cell(Cell):
        text = alias_property("configuration.value")

        @monitored_property
        def choices(self, configuration_values):
            choices = list(configuration_values)
            if choices:
                choices.insert(0, "")
            return choices

        configuration_values = alias_property("configuration.values")

    class Motor_Cell(Cell):
        text = alias_property("motor.formatted_position")

        @monitored_property
        def choices(self, motor_choices):
            choices = list(motor_choices)
            if choices:
                choices.insert(0, "")
            return choices

        motor_choices = alias_property("motor.choices")

        @property
        def motor(self):
            return self.configuration.motor[self.motor_num]

        @property
        def motor_num(self): return self.column - 3


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # name = "BioCARS.beamline_configuration"
    # name = "BioCARS.Julich_chopper_modes"
    # name = "BioCARS.heat_load_chopper_modes"
    # name = "BioCARS.timing_modes"
    # name = "BioCARS.sequence_modes"
    # name = "BioCARS.delay_configuration"
    # name = "BioCARS.temperature_configuration"
    # name = "BioCARS.power_configuration"
    # name = "BioCARS.scan_configuration"
    # name = "BioCARS.detector_configuration"
    # name = "BioCARS.diagnostics_configuration"
    name = "BioCARS.method"
    # name = "BioCARS.laser_optics_modes"
    # name = "BioCARS.alio_diffractometer_saved"

    # name = "LaserLab.timing_modes"
    # name = "LaserLab.sequence_modes"
    # name = "LaserLab.delay_configuration"
    # name = "LaserLab.temperature_configuration"
    # name = "LaserLab.power_configuration"
    # name = "LaserLab.scan_configuration"
    # name = "LaserLab.detector_configuration"
    # name = "LaserLab.diagnostics_configuration"
    # name = "LaserLab.method"

    self = configuration_status_control(name)
