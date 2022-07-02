#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-12-22
Date last modified: 2022-06-16
Revision comment: Cleanup
"""
__version__ = "1.0.2"

from monitored_property import monitored_property


class all_motors_property(monitored_property):
    def __init__(self, attribute_name):
        self.attribute_name = attribute_name
        super().__init__(
            inputs=self.inputs_values,
            calculate=self.calculate_values,
            fset=self.set_values,
        )

    def inputs_values(self, instance):
        from reference import reference
        return [reference(motor, self.attribute_name) for motor in instance.motor]

    @staticmethod
    def calculate_values(_instance, *values):
        return values

    def set_values(self, instance, values):
        for motor, value in zip(instance.motor, values):
            # debug(f"{motor}.{self.attribute_name} = {value}")
            setattr(motor, self.attribute_name, value)
