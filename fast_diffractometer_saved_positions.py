#!/usr/bin/env python
"""High-speed diffractometer
Control panel to save and motor positions.
Friedrich Schotte 31 Oct 2013 - 1 Nov 2013"""
__version__ = "1.0"
from saved_positions import SavedPositions
from id14 import SampleX,SampleY,SampleZ,SamplePhi

saved_positions = SavedPositions(
    name="goniometer_saved",
    motors=[SampleX,SampleY,SampleZ,SamplePhi],
    motor_names=["SampleX","SampleY","SampleZ","SamplePhi"],
    nrows=13)
