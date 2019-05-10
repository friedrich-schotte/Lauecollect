#!/bin/env python
"""Check whether the neccessary modules are installed to run the Python code
in the directory
Authors: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2011-02-11
Date last modified: 2019-02-02
"""
__version__ = "1.1.2" # added "watchdog"

module_names = [
    "wx",
    "numpy",
    "scipy",
    "matplotlib",
    "PIL",
    "pyaudio",
    "serial",
    "psutil",
    "watchdog",
    "h5py",
    "msgpack",
    "msgpack_numpy",
]

def check_module(module_name):
    try: 
        exec("import %s as module" % module_name)
        print("%s %s" % (module_name,version(module),))
    except ImportError:
        print("%s not installed (try: pip install %s)" % (module_name,package_name(module_name)))
    except: print("%s installed, but broken" % module_name)

def package_name(module_name):
    """Which name needs to be passed to pip to install a Python module
    Normally, the PIP package has the same same, but there are a few exceptions"""
    package_name = module_name
    if module_name == "wx": package_name = "wxPython"
    if module_name == "PIL": package_name = "Image"
    return package_name

def version(module):
    if hasattr(module,"__version__"): return str(module.__version__)
    if hasattr(module,"VERSION"): return str(module.VERSION)
    if hasattr(module,"version"): return str(module.version)
    try:
        exec("import %s.version as module" % module.__name__)
        return module.__version__
    except: pass
    return "?"

for module_name in module_names: check_module(module_name)
