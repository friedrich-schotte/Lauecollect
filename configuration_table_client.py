"""
Author: Friedrich Schotte
Date created: 2022-06-25
Date last modified: 2022-06-25
Revision comment:
"""
__version__ = "1.0"

import logging

from monitored_property import monitored_property
from PV_array_property import PV_array_property
from PV_connected_property import PV_connected_property
from PV_record import PV_record
from array_PV_property import array_PV_property
from cached_function import cached_function
from PV_record_property import PV_record_property
from PV_property import PV_property


@cached_function()
def configuration_table_client(domain_name): return Configuration_Table_Client(domain_name)


class Configuration_Table_Client(PV_record):
    def __init__(self, name):
        domain_name, suffix = name.split(".", 1)
        name = f"{domain_name}.configuration.{suffix}"
        super().__init__(name=name)

    online = PV_connected_property("value")

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
    show_in_list = PV_property("show_in_list", True)

    n_motors = PV_property(default_value=0)
    n_rows = PV_property(default_value=0)
    motor_names = array_PV_property("motor_names", "")
    names = array_PV_property("names", "")
    motor_labels = array_PV_property("motor_labels", "")
    formats = array_PV_property("formats", "%s")
    tolerance = array_PV_property("tolerance", 0)
    motors_in_position = array_PV_property("motors_in_position", 0)
    current_position = PV_array_property("motor{i+1}.current_position", count="n_motors", default_value="")
    positions = PV_array_property("motor{i+1}.positions", count="n_motors", default_value=())
    choices = PV_array_property("motor{i+1}.choices", count="n_motors", default_value=())
    _motors_in_position = PV_array_property("motor{i+1}.in_position", count="n_motors", default_value=False)
    formatted_position = PV_array_property("motor{i+1}.formatted_position", count="n_motors", default_value="")

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

    self = configuration_table_client(name)
