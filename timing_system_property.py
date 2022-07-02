"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-05
Revision comment:
"""
__version__ = "2.0"

from EPICS_CA.reference import reference

from monitored_property import monitored_property


class Property(monitored_property):
    name = ""

    def __init__(self, name=None):
        super().__init__(
            calculate=self.calculate,
            fset=self.set_value,
            inputs=self.inputs,
        )
        if name is not None:
            self.name = name

    def __repr__(self):
        name = type(self).__name__
        return "%s(%r)" % (name, self.name)

    def calculate(self, instance, value):
        return value

    def set_value(self, instance, value):
        self.PV(instance).value = value

    def inputs(self, instance):
        return [reference(self.PV(instance), "value")]

    def PV(self, instance):
        name = self.property_name(instance)
        return self.timing_system(instance).property_PV(name)

    def property_name(self, instance):
        return self.name

    @staticmethod
    def timing_system(instance):
        return getattr(instance, "timing_system", instance)