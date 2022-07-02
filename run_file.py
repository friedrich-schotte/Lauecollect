#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-03-07
"""
__version__ = "1.0"

from Acquisition_Panel import *

def run_file(filename):
    """filename: e.g. Acquisition_Panel.py"""
    module_name = filename.replace(".py","")
    module = __import__(module_name)
    pathname = module.__file__
    pathname = pathname.replace(".pyc",".py")
    command = "from %s import *" % module_name
    exec(command,locals(),globals())
    code = open(pathname).read()
    exec(code,locals(),globals())
    
if __name__ == "__main__":
    filename = 'Acquisition_Panel.py'
    print("run_file(%r)" % filename)
    run_file(filename)
