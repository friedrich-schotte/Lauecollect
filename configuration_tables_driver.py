#!/usr/bin/env python
"""
Database to save and recall motor positions
Author: Friedrich Schotte
Date created: 2013-11-29
Date last modified: 2022-06-28
Revision comment: Renamed: configuration_tables_driver
"""
__version__ = "7.6"

import logging
import numpy

from cached_function import cached_function

numpy.warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
numpy.warnings.filterwarnings('ignore', r'Mean of empty slice')
numpy.seterr(invalid="ignore")  # invalid value encountered in double_scalars


@cached_function()
def configuration_tables_driver(domain_name):
    return Configuration_Tables_Driver(domain_name)


class Configuration_Tables_Driver(object):
    """Name space containing all defined configuration tables"""
    from alias_property import alias_property

    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        # return "configuration_tables.%s" % self.domain_name
        return f"configuration_tables({self.domain_name!r})"

    @property
    def db_name(self):
        return "configuration/" + self.domain_name

    from db_property import db_property
    names = db_property("names", [])
    configuration_names = alias_property("names")  # for backward compatibility

    def __getattr__(self, name):
        if name == "__members__":
            return self.names
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("%s" % name)
        return self.configuration(name)

    def __getitem__(self, index):
        if type(index) == slice:
            value = [x for x in self]
        else:
            value = self.configuration(self.names[index])
        return value

    def __dir__(self):
        return sorted(set(self.names + super().__dir__() + list(self.__dict__.keys())))

    def __len__(self):
        return len(self.names)

    def __iter__(self):
        for i in range(0, len(self)):
            if i < len(self):
                yield self[i]

    def __call__(self, name):
        return self.configuration(name)

    def configuration(self, name):
        from configuration_driver import configuration_driver
        return configuration_driver(self.domain_name + "." + name)


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from reference import reference
    from handler import handler as _handler

    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    self = Configuration_Tables_Driver(domain_name)

    @_handler
    def report(event=None): logging.info(f"{event}")

    print('reference(self, "names").monitors.add(report)')
    reference(self, "configuration_names").monitors.add(report)
