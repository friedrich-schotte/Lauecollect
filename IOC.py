"""
EPICS Input/Output Controller

Usage:
from IOC import *; run('BioCARS.channel_archiver')

Author: Friedrich Schotte
Date created: 2022-03-04
Date last modified: 2022-07-11
Revision comment: Separate class for loading driver
"""
__version__ = "3.0"

import logging

from cached_function import cached_function
import IOC_auto_hierarchical


@cached_function()
def ioc(name=None, driver=None): return IOC(name, driver)


class IOC(IOC_auto_hierarchical.IOC):
    def __init__(self, name=None, driver=None):
        """e.g. BioCARS.channel_archiver"""
        super().__init__()
        if name is not None:
            self.driver = Driver(name).driver
        if driver is not None:
            self.driver = driver

    driver = None

    def __repr__(self):
        return f"{self.class_name}(driver={self.driver})"

    def start(self):
        if hasattr(self.driver, "start"):
            logging.debug(f"{self.driver}.start()")
            self.driver.start()
        if hasattr(self.driver, "running"):
            logging.debug(f"{self.driver}.running = True")
            self.driver.running = True
        super().start()

    def stop(self):
        if hasattr(self.driver, "stop"):
            logging.debug(f"{self.driver}.stop()")
            self.driver.stop()
        if hasattr(self.driver, "running"):
            logging.debug(f"{self.driver}.running = False")
            self.driver.running = False
        super().stop()

    @property
    def class_name(self):
        return type(self).__name__.lower()


class Driver:
    def __init__(self, name):
        """e.g. BioCARS.channel_archiver"""
        self.name = name

    def __repr__(self):
        name = f"{self.class_name}({self.name!r})"
        return name

    @property
    def domain_name(self):
        return self.name.split(".")[0]

    @property
    def driver_class_name(self):
        name = self.name.replace(self.domain_name, "", 1).strip(".")
        name = name.split(".")[0]
        return name

    @property
    def driver_base_name(self):
        name = self.name
        name = name.replace(self.domain_name, "", 1).strip(".")
        name = name.replace(self.driver_class_name, "", 1).strip(".")
        return name

    @property
    def driver(self):
        return self.driver_type(self.driver_name)

    @property
    def driver_type(self):
        return getattr(self.driver_module, self.driver_type_name)

    @property
    def driver_name(self):
        if self.driver_base_name:
            name = f"{self.domain_name}.{self.driver_base_name}"
        else:
            name = self.domain_name
        return name

    @property
    def driver_module(self):
        return __import__(self.driver_module_name)

    @property
    def driver_module_name(self):
        for name in self.driver_module_names:
            try:
                __import__(name)
            except ImportError:
                pass
            else:
                module_name = name
                break
        else:
            module_name = self.driver_module_names[0]
        return module_name

    @property
    def driver_module_names(self):
        module_names = []
        base_name = self.driver_class_name
        if "_driver" not in base_name and "_simulator" not in base_name:
            module_name = base_name + "_driver"
            module_names.append(module_name)
        module_names.append(base_name)
        return module_names

    @property
    def driver_type_name(self):
        name = self.driver_module_name
        if "_driver_" in name:
            name = name[0:name.index("_driver")+len("_driver")]
        if "_simulator_" in name:
            name = name[0:name.index("_simulator")+len("_simulator")]
        return name

    @property
    def class_name(self):
        return type(self).__name__.lower()


def run(name): ioc(name).run()


def start(name): ioc(name).start()


def stop(name): ioc(name).stop()


if __name__ == "__main__":
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    name = "BioCARS.rayonix_detector"
    # name = "BioCARS.timing_system"
    # name = 'BioCARS.configuration_table.method'
    # name = 'BioCARS.alio_simulator'
    # name = 'BioCARS.xray_beam_center'
    # name = 'BioCARS.lecroy_scope_simulator.xray_scope'
    # name = 'BioCARS.channel_archiver'

    self = ioc(name)

    print('start(name)')
    # start(name)
