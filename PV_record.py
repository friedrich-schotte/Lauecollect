"""
Author: Friedrich Schotte
Date created: 2021-05-01
Date last modified: 2022-06-27
Revision comment: Compatibility with acquisition_control
"""
__version__ = "1.5.1"


class PV_record(object):
    def __init__(self, domain_name=None, base_name=None, prefix=None, name=None):
        self.defaults = self.Defaults()
        if domain_name is not None:
            self.domain_name = domain_name
        if base_name is not None:
            self.base_name = base_name
        if prefix is not None:
            self.prefix = prefix
        if name is not None:
            self.name = name

    def __repr__(self):
        parameters = []
        for attr in "domain_name", "base_name", "prefix":
            value = getattr(self.defaults, attr)
            if value is not None:
                parameters.append(f"{attr}={value!r}")
        parameter_list = ", ".join(parameters)
        return f"{self.class_name}({parameter_list})"

    class Defaults:
        domain_name = None
        base_name = None
        prefix = None

    @property
    def domain_name(self):
        if self.defaults.domain_name is None:
            domain_name = "BioCARS"
        else:
            domain_name = self.defaults.domain_name
        return domain_name

    @domain_name.setter
    def domain_name(self, domain_name):
        self.defaults.domain_name = domain_name

    @property
    def prefix(self):
        if self.defaults.prefix is None:
            prefix = f'{self.domain_name}:{self.base_name}'
            prefix = prefix.replace("_client", "")
            prefix = prefix.replace("_control", "")
            prefix = prefix.upper()
        else:
            prefix = self.defaults.prefix
        return prefix

    @prefix.setter
    def prefix(self, prefix):
        self.defaults.prefix = prefix

    @property
    def base_name(self):
        if self.defaults.base_name is None:
            name = self.class_name
        else:
            name = self.defaults.base_name
        return name

    @base_name.setter
    def base_name(self, base_name):
        self.defaults.base_name = base_name

    @property
    def name(self):
        return self.domain_name + "." + self.base_name

    @name.setter
    def name(self, value):
        if "." in value:
            self.domain_name, self.base_name = value.split(".", 1)
        else:
            self.base_name = value

    @property
    def class_name(self):
        return type(self).__name__.lower()
