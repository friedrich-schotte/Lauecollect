#!/usr/bin/env python
"""High-speed X-ray Chopper operation modes.
Save and restore motor positions.
Author: Friedrich Schotte
Date created: 10/16/2009
Date last modified: 11/06/2017
"""
__version__ = "1.1" # No hard-coded defaults

from configuration import configuration
from instrumentation import ChopX,ChopY,timing_system # passed in globals()

high_speed_chopper_modes = configuration(
    name="high_speed_chopper_modes_2",
    globals=globals(),
)

if __name__ == '__main__': # for testing
    from pdb import pm # for debugging
    self = high_speed_chopper_modes # for debugging
    print('high_speed_chopper_mode.position("S-1")')
