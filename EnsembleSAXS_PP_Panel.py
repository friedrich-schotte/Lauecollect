#!/usr/bin/env python
from Timing_Panel import *

if __name__ == '__main__':
    import Timing_Panel as module
    from inspect import getfile
    file = getfile(module).replace(".pyc",".py")
    execfile(file)
