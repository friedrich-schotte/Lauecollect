"""
Table-like interface
Author: Friedrich Schotte
Date created: 2021-07-28
Date last modified: 2022-07-06
Revision comment: Cell: updated __repr__
"""
__version__ = "1.4.1"

import logging

from cached_function import cached_function
from run_async import run_async
from function_property import function_property
from attribute_property import attribute_property
from file import file as file_object
from monitored_property import monitored_property
from monitored_value_property import monitored_value_property


@cached_function()
def spreadsheet_control(name):
    return Spreadsheet_Control(name)


class Spreadsheet_Control:
    def __init__(self, name):
        self.name = name
        self.cells_monitors = set()
        self.cells_text_formatted = self.file_content
        self.initialize()

    @run_async
    def initialize(self):
        # logging.debug(f"Initializing Spreadsheet Control...")
        self.file_content = self.cells_text_formatted
        self.monitoring_cells = True
        self.monitoring_file = True

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

    @monitored_property
    def n_rows(self, my_n_rows):
        return my_n_rows

    @n_rows.setter
    def n_rows(self, new_n_rows):
        self.update_shape((self.n_rows, self.n_columns), (new_n_rows, self.n_columns))
        self.my_n_rows = new_n_rows

    @monitored_property
    def n_columns(self, my_n_columns):
        return my_n_columns

    @n_columns.setter
    def n_columns(self, new_n_columns):
        self.update_shape((self.n_rows, self.n_columns), (self.n_rows, new_n_columns))
        self.my_n_columns = new_n_columns

    def cells_monitors_add(self, handler):
        self.cells_monitors.add(handler)
        for cell_reference in self.cell_references:
            cell_reference.monitors.add(handler)

    def cells_monitors_remove(self, handler):
        self.cells_monitors.remove(handler)
        for cell_reference in self.cell_references:
            try:
                cell_reference.monitors.remove(handler)
            except KeyError:
                pass

    my_n_rows = monitored_value_property(1)
    my_n_columns = monitored_value_property(1)

    def update_shape(self, old_shape, new_shape):
        from reference import reference

        cells_removed = self.cells_removed(old_shape, new_shape)
        cells_added = self.cells_added(old_shape, new_shape)

        for cell in cells_removed:
            cell.text = ""

        for cell in cells_removed:
            monitors = reference(cell, "text").monitors
            for handler in list(monitors):
                try:
                    monitors.remove(handler)
                except KeyError:
                    pass

        for cell in cells_added:
            monitors = reference(cell, "text").monitors
            for handler in list(self.cells_monitors):
                monitors.add(handler)

        for cell in cells_added:
            cell.text = ""

    def cells_removed(self, old_shape, new_shape):
        cells = []
        old_n_rows, old_n_columns = old_shape
        new_n_rows, new_n_columns = new_shape
        for row in range(0, old_n_rows):
            for column in range(0, old_n_columns):
                if row >= new_n_rows or column >= new_n_columns:
                    cells.append(self.cell(row, column))
        return cells

    def cells_added(self, old_shape, new_shape):
        cells = []
        old_n_rows, old_n_columns = old_shape
        new_n_rows, new_n_columns = new_shape
        for row in range(0, new_n_rows):
            for column in range(0, new_n_columns):
                if row >= old_n_rows or column >= old_n_columns:
                    cells.append(self.cell(row, column))
        return cells

    @property
    def monitoring_cells(self):
        return self.cells_update_handler in self.cells_monitors

    @monitoring_cells.setter
    def monitoring_cells(self, monitoring):
        if monitoring:
            self.cells_monitors_add(self.cells_update_handler)
        else:
            self.cells_monitors_remove(self.cells_update_handler)

    @property
    def monitoring_file(self):
        return self.file_update_handler in self.file_reference.monitors

    @monitoring_file.setter
    def monitoring_file(self, monitoring):
        if monitoring:
            self.file_reference.monitors.add(self.file_update_handler)
        else:
            self.file_reference.monitors.remove(self.file_update_handler)

    def handle_cells_update(self):
        logging.debug(f"{self}: Cells updated: Updating file...")
        self.update_file()

    def handle_file_update(self):
        logging.debug(f"{self}: File updated")
        self.update_cells()

    def update_cells(self):
        file_content = self.file_content
        if self.cells_text_formatted != file_content:
            logging.debug(f"{self}: Updating cells")
            self.monitoring_cells = False
            self.cells_text_formatted = file_content
            self.monitoring_cells = True

    def update_file(self):
        cells_text_formatted = self.cells_text_formatted
        if self.file_content != cells_text_formatted:
            logging.debug(f"{self}: Updating file")
            self.monitoring_file = False
            self.file_content = cells_text_formatted
            self.monitoring_file = True

    @monitored_property
    def cell_references(self, cells):
        from reference import reference
        references = [reference(cell, "text") for cell in cells]
        references += [reference(self, "n_rows")]
        references += [reference(self, "n_columns")]
        return references

    @property
    def shape_references(self):
        from reference import reference
        return [reference(self, "n_rows"), reference(self, "n_columns")]

    @property
    def cells_update_handler(self):
        from handler import handler
        return handler(self.handle_cells_update, delay=1.0)

    @property
    def file_reference(self):
        from reference import reference
        return reference(self, "file_content")

    @property
    def file_update_handler(self):
        from handler import handler
        return handler(self.handle_file_update, delay=0.2)

    @monitored_property
    def cells(self, n_rows, n_columns):
        cells = []
        for row in range(0, n_rows):
            for column in range(0, n_columns):
                cells.append(self.cell(row, column))
        return cells

    name = monitored_value_property("")

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

    @monitored_property
    def filename(self, domain_name, base_name):
        return f"{self.settings_dir}/domains/{domain_name}/table/{base_name}.txt"

    file = function_property(file_object, "filename")
    file_content = attribute_property("file", "content")

    @property
    def settings_dir(self):
        from DB import db_global_settings_dir
        return db_global_settings_dir()

    @cached_function()
    def cell(self, row, column):
        return self.Cell(self, row, column)

    class Cell(object):
        def __init__(self, table, row, column):
            self.table = table
            self.row = row
            self.column = column

        def __repr__(self):
            return f"{self.table}.cell({self.row}, {self.column})"

        @property
        def class_name(self):
            return type(self).__name__.lower()

        text = monitored_value_property("")
        choices = monitored_value_property([])
        background_color = monitored_value_property([255, 255, 255])

    def row_menu_items(self, row):  # noqa
        return []

    def column_menu_items(self, row):  # noqa
        return []

    @monitored_property
    def domain_name(self, name):
        if "." not in name:
            name = "default." + name
        domain_name = name.split(".", 1)[0]
        return domain_name

    @monitored_property
    def base_name(self, name):
        return name.split(".", 1)[-1]


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
    # logging.getLogger("file_monitor").level = logging.DEBUG

    from handler import handler as _handler
    from reference import reference as _reference
    from time import sleep

    # name = "BioCARS.beamline_configuration"
    # name = "BioCARS.Julich_chopper_modes"
    # name = "BioCARS.heat_load_chopper_modes"
    # name = "BioCARS.timing_modes"
    # name = "BioCARS.sequence_modes"
    # name = "BioCARS.delay_configuration"
    # name = "BioCARS.temperature_configuration"
    name = "BioCARS.power_configuration"
    # name = "BioCARS.scan_configuration"
    # name = "BioCARS.detector_configuration"
    # name = "BioCARS.diagnostics_configuration"
    # name = "BioCARS.method"
    # name = "BioCARS.laser_optics_modes"
    # name = "BioCARS.alio_diffractometer_saved"

    self = spreadsheet_control(name)

    print('self = %r' % self)
    print('')


    @_handler
    def report(event=None):
        logging.info(f"event={event}")

    sleep(1.0)
    _reference(self.cell(1, 1), "text").monitors.add(report)

    print("self.cell(1, 1).text")
