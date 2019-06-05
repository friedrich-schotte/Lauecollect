#!/usr/bin/env python
from Rayonix_Detector_Panel_old import *

if __name__ == '__main__':
    import Rayonix_Detector_Panel_old as module
    from inspect import getfile
    file = getfile(module).replace(".pyc",".py")
    execfile(file)
