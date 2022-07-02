"""
Author: Friedrich Schotte
Date created: 2021-07-12
Date last modified: 2022-06-16
Revision comment: Fixed: Issue: Setting shared between "xray_scope" and "laser_scope"
"""
__version__ = "1.1.1"

from cached_function import cached_function


@cached_function()
def lecroy_scope_simulator(name):
    return Lecroy_Scope_Simulator(name)


class Lecroy_Scope_Simulator:
    from db_property import db_property
    from alias_property import alias_property
    from monitored_property import monitored_property

    def __init__(self, name):
        """name: "domain_name.basename" e.g. "BioCARS.xray_scope" """
        self.name = name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__.lower(), self.name)

    @property
    def name(self):
        return self.domain_name + "." + self.base_name

    @name.setter
    def name(self, value):
        if "." in value:
            self.domain_name, self.base_name = value.split(".", 1)
        else:
            self.base_name = value

    domain_name = "BioCARS"
    base_name = "lecroy_scope"

    @property
    def db_name(self):
        return f"domains/{self.domain_name}/lecroy_scope_simulator/{self.base_name}"

    setup = db_property("setup", "")
    
    @monitored_property
    def setup_choices(self, setup_filenames):
        setup_filenames = [file for file in setup_filenames if self.is_setup_filename(file)]
        names = [file.replace(".lss", "") for file in setup_filenames]
        names = sorted(names, key=str.casefold)
        return names

    @setup_choices.setter
    def setup_choices(self, choices):
        self.setup_filenames = [name+".lss" for name in choices]

    @staticmethod
    def is_setup_filename(file):
        return all([
            not file.startswith("."),
            file.endswith(".lss"),
        ])

    setups = setup_choices
    
    setup_filenames = alias_property("setup_directory.files")

    @property
    def setup_directory(self):
        from directory import directory
        return directory(self.setup_directory_name)

    @property
    def setup_directory_name(self):
        from module_dir import module_dir
        return f"{module_dir(self)}/lecroy_scope/{self.domain_name}/{self.base_name}"

    acquiring_waveforms = db_property("acquiring_waveforms", False)

    trace_acquisition_running = db_property("trace_acquisition_running", False)


if __name__ == "__main__":  # for testing
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from handler import handler
    from reference import reference

    name = "BioCARS.xray_scope"
    # name = "BioCARS.laser_scope"
    # name = "BioCARS.diagnostics_scope"
    # name = "LaserLab.laser_scope"

    self = lecroy_scope_simulator(name)

    @handler
    def report(event): logging.info(f"event={event}")

    reference(self, "setup").monitors.add(report)
    reference(self, "setup_choices").monitors.add(report)

    print(f"self = {self!r}")
    print(f"self.setup = {self.setup!r}")
    print(f"self.setup_choices = {self.setup_choices!r}")
