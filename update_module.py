#!/usr/bin/env python
"""Dynamically reload Python modules as needed.
Friedrich Schotte, 28 Jan 2015 - 29 Jan 2015"""

from logging import debug,warn

def update_module(module_name):
    """Reload a module if its source file has changed"""
    try: exec("import %s as module" % module_name)
    except Exception,msg: warn("Loading module %s failed %s" % (module_name,msg)); return
    from inspect import getfile
    from os.path import getmtime
    file = getfile(module)
    timestamp = getattr(module,"__timestamp__",0)
    source_timestamp = getattr(module,"__source_timestamp__",0)
    current_timestamp = getmtime(file)
    current_source_timestamp = getmtime(file.replace(".pyc",".py"))
    if current_timestamp != timestamp or current_source_timestamp != source_timestamp:
        debug("reloading module %s" % module_name)
        try: module=reload(module)
        except Exception,msg: warn("Reloading module %s failed: %s" % (module_name,msg)); return
        module.__timestamp__ = current_timestamp
        module.__source_timestamp__ = current_source_timestamp


if __name__ == '__main__':
    from pdb import pm
    module_name = "Ensemble_SAXS" # for debugging
    import logging; logging.basicConfig(level=logging.DEBUG)
    print "update_module(module_name)"
