"""
Database to save and recall motor positions
Author: Friedrich Schotte
Date created: 2019-05-24
Date last modified: 2022-06-27
Revision comment: Added: _names (Might be a replacement for "names"?)
"""
__version__ = "1.34.9"

import logging

from cached_function import cached_function
from PV_property import PV_property
from PV_connected_property import PV_connected_property
from PV_record_property import PV_record_property
from array_PV_property import array_PV_property
from PV_array_property import PV_array_property
from monitored_property import monitored_property


@cached_function()
def configuration_client(name):
    return Configuration_Client(name)


class Configuration_Client(object):
    """Database save and recall motor positions"""

    domain_name = "BioCARS"
    base_name = "configuration_test"

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        name = type(self).__name__.lower()
        return f"{name}({self.name!r})"

    @property
    def name(self):
        return self.domain_name + "." + self.base_name

    @name.setter
    def name(self, value):
        if "." in value:
            self.domain_name, self.base_name = value.split(".", 1)
        else:
            self.domain_name, self.base_name = "BioCARS", value

    online = PV_connected_property("title")

    @property
    def prefix(self):
        prefix = f'{self.domain_name}:CONFIGURATION.{self.base_name}'
        prefix = prefix.upper()
        return prefix

    motor = PV_record_property(type_name="configuration_motors_client")

    value = PV_property(dtype=str)
    values = array_PV_property("values", "")
    descriptions = array_PV_property("descriptions", "")
    command_value = PV_property(dtype=str)
    command_row = PV_property(default_value=-1)
    selected_description = PV_property(dtype=str)
    applying = PV_property(default_value=False)
    applied_row = PV_property(default_value=-1)
    in_position = PV_property(default_value=False)
    n_motors = PV_property(default_value=0)
    n_rows = PV_property(default_value=0)
    motor_names = array_PV_property("motor_names", "")
    names = array_PV_property("names", "")
    motor_labels = array_PV_property("motor_labels", "")
    formats = array_PV_property("formats", "%s")
    tolerance = array_PV_property("tolerance", 0)
    show_in_list = PV_property("show_in_list", True)
    motors_in_position = array_PV_property("motors_in_position", 0)

    current_position = PV_array_property("motor{i+1}.current_position", count="n_motors", default_value="")
    positions = PV_array_property("motor{i+1}.positions", count="n_motors", default_value=())
    choices = PV_array_property("motor{i+1}.choices", count="n_motors", default_value=())

    _motors_in_position = PV_array_property("motor{i+1}.in_position", count="n_motors", default_value=False)
    formatted_position = PV_array_property("motor{i+1}.formatted_position", count="n_motors", default_value="")
    _names = PV_array_property("motor{i+1}.name", count="n_motors", default_value="")

    @monitored_property
    def title(self, _title):
        if _title:
            title = _title
        else:
            title = self.default_title
        return title

    _title = PV_property("title", "")

    @property
    def default_title(self):
        from capitalize import capitalize
        title = self.base_name
        title = title.replace("_", " ")
        title = title.replace(".", " ")
        title = capitalize(title)
        return title

    @property
    def state(self):
        """Current state as Python commands that can be executed to
        restore the state"""
        s = ""
        for name, value in zip(self.names, self.current_position):
            s += "%r.%s.current_position = %r\n" % (self, name, value)
        return s

    @state.setter
    def state(self, value):
        for line in value.split("\n"):
            try:
                exec(line)
            except Exception as x:
                logging.error("%s: %s" % (line, x))

    def __getattr__old(self, name):
        if name.startswith("__") and name.endswith("__"):
            return object.__getattribute__(self, name)
        if name.startswith("_"):  # needed for IPython
            return object.__getattribute__(self, name)
        if name in self.names:
            mon_num = self.names.index(name)
            return self.motor[mon_num]
        else:
            raise AttributeError(f"{self} has no attribute {name!r}")


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler as _handler

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

    self = configuration_client(name)

    print(f'self = {self}')

    @_handler
    def report(event=None):
        logging.info(f"event={event}")

    # from reference import reference as _reference
    # _reference(self, "value").monitors.add(report)

    # from item_reference import item_reference as _item_reference
    # _item_reference(self.formatted_position, 0).monitors.add(report)

    # for i in range(self.n_motors):
    #    _reference(self.motor[i], "in_position").monitors.add(report)
