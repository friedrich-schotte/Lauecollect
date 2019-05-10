"""
Automatically load samples for Lauec crystallography data collection
Author: Friedrich Schotte
Date created: Oct 28, 2017
Date last modified: Oct 28, 2017
"""
__version__ = "1.0"

from Laue_crystallography import Laue_crystallography

template = "/net/mx340hs/data/anfinrud_1711/Data/Laue/Lyz/Lyz-%d/alignment"
i = 8

def collect():
    Laue_crystallography.image_scan.directory = template % i
    Laue_crystallography.inject()
    Laue_crystallography.scan()
    i += 1
