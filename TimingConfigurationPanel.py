#!/usr/bin/env python
from Timing_Channel_Configuration_Panel import *

if __name__ == '__main__':
    import Timing_Channel_Configuration_Panel as module
    from inspect import getfile
    file = getfile(module).replace(".pyc",".py")
    execfile(file)
