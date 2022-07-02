"""
Author: Friedrich Schotte
Date created: 2022-04-05
Date last modified: 2022-04-05
Revision comment:
"""
__version__ = "1.0"

from EPICS_CA.reference import reference

from monitored_property import monitored_property


class Parameter(monitored_property):
    name = ""
    default_value = 0.0

    def __init__(self, name=None, default_value=None):
        super().__init__(
            calculate=self.calculate,
            fset=self.set_parameter,
            inputs=self.inputs,
        )
        if name is not None:
            self.name = name
        if default_value is not None:
            self.default_value = default_value

    def __repr__(self):
        return "%s(%r,default_value=%r)" % (
            type(self).__name__,
            self.name,
            self.default_value,
        )

    def calculate(self, instance, value):
        from timing_system import parameter_value
        value = parameter_value(value, self.default_value,
                                report_name=self.PV(instance).name)
        return value

    def set_parameter(self, instance, value):
        from timing_system import parameter_PV_value
        str_value = parameter_PV_value(value, self.default_value)
        self.PV(instance).value = str_value

    def inputs(self, instance):
        return [reference(self.PV(instance), "value")]

    def PV(self, instance):
        return self.timing_system(instance).parameter_PV(
            self.parameter_name(instance)
        )

    def parameter_name(self, instance):
        from timing_system import Timing_System
        if type(instance) == Timing_System:
            name = self.name
        else:
            name = self.instance_name(instance) + "." + self.name
        return name

    @staticmethod
    def instance_name(instance):
        return getattr(instance, "name", instance.__class__.__name__)

    @staticmethod
    def timing_system(instance):
        return getattr(instance, "timing_system", instance)