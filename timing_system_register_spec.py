#!/usr/bin/env python
"""
FPGA Timing System

Author: Friedrich Schotte
Date created: 2021-05-03
Date last modified: 2022-03-38
Revision comment: Renamed: timing_system_register_spec
"""
__version__ = "1.2"


class timing_system_register_spec:
    from sparse_array import sparse_array
    from timing_system_register import Register

    def __init__(
            self,
            register: Register,
            counts: sparse_array,
            op: str,
    ):
        self.register = register
        self.counts = counts
        self.op = op

    def __repr__(self):
        return f"{type(self).__name__}({self.register!r}, {self.counts!r}, {self.op!r})"
