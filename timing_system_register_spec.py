#!/usr/bin/env python
"""
FPGA Timing System

Author: Friedrich Schotte
Date created: 2021-05-03
Date last modified: 2022-08-12
Revision comment: Fixed: imports
"""
__version__ = "1.2.1"


class timing_system_register_spec:
    from sparse_array import sparse_array
    from timing_system_register_driver_2 import Timing_System_Register_Driver

    def __init__(
            self,
            register: Timing_System_Register_Driver,
            counts: sparse_array,
            op: str,
    ):
        self.register = register
        self.counts = counts
        self.op = op

    def __repr__(self):
        return f"{type(self).__name__}({self.register!r}, {self.counts!r}, {self.op!r})"
