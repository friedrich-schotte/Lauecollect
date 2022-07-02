"""
Table-like interface
Author: Friedrich Schotte
Date created: 2022-06-09
Date last modified: 2022-06-09
Revision comment:
"""
__version__ = "1.0"

import logging

from cached_function import cached_function
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property


@cached_function()
def spreadsheet_base_control(name):
    return Spreadsheet_Base_Control(name)


class Spreadsheet_Base_Control:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        name = self.class_name
        return f"{name}({self.name!r})"

    @property
    def class_name(self):
        return type(self).__name__.lower()

    @monitored_property
    def shape(self, n_rows, n_columns):
        return n_rows, n_columns

    @shape.setter
    def shape(self, value):
        self.n_rows, self.n_columns = value

    n_rows = monitored_value_property(2)
    n_columns = monitored_value_property(2)

    @monitored_property
    def cells(self, n_rows, n_columns):
        cells = []
        for row in range(0, n_rows):
            for column in range(0, n_columns):
                cells.append(self.cell(row, column))
        return cells

    name = monitored_value_property("")

    @monitored_property
    def domain_name(self, name):
        if "." not in name:
            name = "default." + name
        domain_name = name.split(".", 1)[0]
        return domain_name

    @monitored_property
    def base_name(self, name):
        return name.split(".", 1)[-1]

    @property
    def cells_text_formatted(self):
        lines = []
        for row in self.cells_text:
            row_cells_text = []
            for cell_text in row:
                cell_text = cell_text.replace("\n", " ")
                cell_text = cell_text.replace("\t", " ")
                row_cells_text.append(cell_text)
            line = "\t".join(row_cells_text)
            lines.append(line)
        text = "\n".join(lines)
        return text

    @cells_text_formatted.setter
    def cells_text_formatted(self, text):
        cells_text = [line.split("\t") for line in text.rstrip("\n").split("\n")]
        self.cells_text = cells_text

    @property
    def cells_text(self):
        cells_text = []
        for row in range(0, self.n_rows):
            row_cells_text = []
            for column in range(0, self.n_columns):
                row_cells_text.append(self.cell(row, column).text)
            cells_text.append(row_cells_text)
        return cells_text

    @cells_text.setter
    def cells_text(self, cells_text):
        self.n_rows = len(cells_text)
        self.n_columns = max([0] + [len(row) for row in cells_text])

        for row, row_cells_text in enumerate(cells_text):
            for column, cell_text in enumerate(row_cells_text):
                if row < self.n_rows and column < self.n_columns:
                    self.cell(row, column).text = cell_text

    @cached_function()
    def cell(self, row, column):
        return self.Cell(self, row, column)

    class Cell(object):
        def __init__(self, table, row, column):
            self.table = table
            self.row = row
            self.column = column

        def __repr__(self):
            return f"{self.class_name}({self.table}, {self.row}, {self.column})"

        @property
        def class_name(self):
            return type(self).__name__.lower()

        text = monitored_value_property("")
        choices = monitored_value_property([])
        background_color = monitored_value_property([255, 255, 255])


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

    self = spreadsheet_base_control(name)
