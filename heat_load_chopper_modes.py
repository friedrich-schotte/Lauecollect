#!/usr/bin/env python
"""High-speed X-ray Chopper operation modes.
Save and restore motor positions.
Author: Friedrich Schotte
Date created: 10/30/2017
Date last modified: 10/30/2017
"""
__version__ = "1.0"

from configuration import configuration
from instrumentation import HLC,timing_system # passed in globals()

heat_load_chopper_modes = configuration(
    name="heat_load_chopper_modes",
    globals=globals(),
    locals=locals(),
)

if __name__ == '__main__': # for testing
    from pdb import pm # for debugging
    self = heat_load_chopper_modes # for debugging
    print('heat_load_chopper_modes.position("82-1.5")')
