"""
Author: Friedrich Schotte
Date created: 2021-09-20
Date last modified: 2021-09-20
Revision comment:
"""
__version__ = "1.0"

from cached_function import cached_function


@cached_function()
def lecroy_scope_simulator(name):
    return Lecroy_Scope_Simulator(name)


class Lecroy_Scope_Simulator:
    from db_property import db_property
    from CA import PV
    from function_property import function_property
    from attribute_property import attribute_property

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.name)

    @property
    def domain_name(self):
        return self.name.split(".", 1)[0]

    @property
    def base_name(self):
        return self.name.replace(self.domain_name, "", 1).strip(".")

    @property
    def db_name(self):
        return f"domains/{self.domain_name}/lecroy_scope_simulator/{self.base_name}"

    waveform_autosave_wrap = db_property("waveform_autosave_mode", True)

    trigger_level_PV_name = db_property("trigger_PV_name", 'NIH:TIMING.registers.ch1_state.count')

    trigger_level_PV = function_property(PV, "trigger_level_PV_name")
    trigger_level = attribute_property("trigger_level_PV", "value")

    def get_value(self, name):
        value = None
        if name == "SaveRecall.Waveform.AutoSave.Value":
            if not self.waveform_autosave:
                value = "Off"
            elif self.waveform_autosave_wrap:
                value = "Wrap"
            else:
                value = "Fill"
        return value

    @property
    def waveform_autosave(self):
        return False


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=msg_format)

    from reference import reference
    from handler import handler

    name = "BioCARS.xray_scope"
    # name = "BioCARS.laser_scope"
    # name = "BioCARS.diagnostics_scope"
    # name = "LaserLab.laser_scope"

    self = lecroy_scope_simulator(name)

    @handler
    def report(event):
        logging.info(f"{event}")

    print(f"self = {self!r}")

    reference(self, "trigger_level").monitors.add(report)
