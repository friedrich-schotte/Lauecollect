"""
Author: Friedrich Schotte
Date created: 2022-05-29
Date last modified: 2022-06-16
Revision comment:
"""
__version__ = "1.0"

import logging

from alias_property import alias_property
from cached_function import cached_function
from monitored_property import monitored_property
from spreadsheet_control import Spreadsheet_Control
from numpy import isnan


@cached_function()
def configuration_table_control(name):
    return Configuration_Table_Control(name)


class Configuration_Table_Control(Spreadsheet_Control):
    @cached_function()
    def cell(self, row, column):
        if column >= 3:
            cell = self.Motor_Cell(self, row, column)
        else:
            cell = self.Cell(self, row, column)
        return cell

    class Cell(Spreadsheet_Control.Cell):
        @monitored_property
        def background_color(self, is_selected, in_position):
            from color import white, green, orange
            color = white
            if is_selected:
                if in_position:
                    color = green
                else:
                    color = orange
            return color

        @monitored_property
        def is_selected(self, command_row):
            return command_row == self.configuration_row

        @property
        def configuration_row(self):
            return self.table.configuration_row(self.row)

        command_row = alias_property("configuration.command_row")
        in_position = alias_property("configuration.in_position")
        configuration = alias_property("table.configuration")

    class Motor_Cell(Cell):
        @monitored_property
        def choices(self, motor_choices):
            choices = list(motor_choices)
            if choices:
                choices.insert(0, "")
            return choices

        @monitored_property
        def background_color(self, is_selected, in_position):
            from color import white, green, red
            color = white
            if is_selected:
                if in_position is not None and not isnan(in_position):
                    if in_position:
                        color = green
                    else:
                        color = red
            return color

        motor_choices = alias_property("motor.choices")
        in_position = alias_property("motor.in_position")

        @property
        def motor(self):
            return self.configuration.motor[self.motor_num]

        @property
        def motor_num(self):
            return self.table.motor_num(self.column)

    def row_menu_items(self, row):
        from handler import handler
        from menu_item import Menu_Item
        items = [
            Menu_Item(
                label="Go To Row",
                handler=handler(self.apply_row, row),
                enabled=True
            ),
        ]
        return items

    def apply_row(self, row): self.applied_row = self.configuration_row(row)

    def column_menu_items(self, column):
        from handler import handler
        from menu_item import Menu_Item
        items = []

        action = self.show_table_action(column)
        if action:
            menu_item = Menu_Item(label="Show Table...", handler=handler(action.start))
            items.append(menu_item)

        action = self.configure_column_action(column)
        if action:
            menu_item = Menu_Item(label="Configure Column...", handler=handler(action.start))
            items.append(menu_item)

        return items

    def show_table_action(self, column):
        name = self.configuration_name(column)
        if name:
            from application import application
            app = application(
                domain_name=self.domain_name,
                module_name="Configuration_Table_Panel",
                command=f"Configuration_Table_Panel({name !r})",
            )
        else:
            app = None
        return app

    def configure_column_action(self, column):
        motor_num = self.motor_num(column)
        if motor_num >= 0:
            name = f"{self.name}.motor{motor_num + 1}"
            from application import application
            app = application(
                domain_name=self.domain_name,
                module_name="Configuration_Motor_Setup_Panel",
                command=f"Configuration_Motor_Setup_Panel({name!r})",
            )
        else:
            app = None
        return app

    def configuration_name(self, column):
        name = ""
        motor_num = self.motor_num(column)
        if motor_num >= 0:
            # logging.debug(f"motor_num: {motor_num}")
            # logging.debug(f"self.configuration: {self.configuration}")
            name = self.configuration.motor[motor_num].configuration_name
        # logging.debug(f"name: {name}")
        return name

    @staticmethod
    def motor(motor_num): return self.configuration.motor[motor_num]

    @staticmethod
    def motor_num(column): return column - 3

    @staticmethod
    def configuration_row(row): return row - 1

    applied_row = alias_property("configuration.applied_row")

    @property
    def configuration(self):
        from configuration import configuration
        return configuration(self.name)


if __name__ == '__main__':
    from handler import handler as _handler
    from reference import reference as _reference

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

    self = configuration_table_control(name)

    @_handler
    def report(event=None):
        logging.info(f"event={event}")

    _reference(self.cell(25, 1), "in_position").monitors.add(report)
    _reference(self.cell(25, 1), "background_color").monitors.add(report)
    _reference(self.cell(25, 3), "in_position").monitors.add(report)
    _reference(self.cell(25, 3), "background_color").monitors.add(report)
