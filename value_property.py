"""
Author: Friedrich Schotte
Date created: 2020-12-10
Date last modified: 2020-12-10
Revision comment:
"""
__version__ = "1.0"

from logging import error
from traceback import format_exc

from monitored_property import monitored_property


class value_property(monitored_property):
    def __init__(self, reference_name):
        self.reference_name = reference_name
        monitored_property.__init__(
            self,
            inputs=self.inputs_reference_property,
            calculate=self.calculate_reference_property,
            fset=self.set_reference_property,
        )

    def inputs_reference_property(self, instance):
        return [self.value_reference(instance)]

    def calculate_reference_property(self, instance, value):
        return value

    def set_reference_property(self, instance, value):
        try:
            self.value_reference(instance).value = value
        except Exception:
            error(f"{self.value_reference(instance)}.value = {value}: {format_exc()}")

    def value_reference(self, instance):
        return getattr(instance, self.reference_name)

