"""
Dynamically refresh Python code

Author: Friedrich Schotte
Date created: 07/08/2017
Date last modified: 12/07/2017
"""
__version__ = "1.2.2" # daemon thread
from logging import debug,info,warn,error

#-----------------------------------------------------------------------------
# This code is from the IPython extension "autoreload" by Pauli Virtanen,
# based on the autoreload code by Thomas Heller.
# Copyright (C) 2000 Thomas Heller
#-----------------------------------------------------------------------------
import os
import sys
import traceback
import types
import weakref
PY3 = sys.version_info[0] == 3

if PY3:
    func_attrs = ['__code__', '__defaults__', '__doc__',
                  '__closure__', '__globals__', '__dict__']
else:
    func_attrs = ['func_code', 'func_defaults', 'func_doc',
                  'func_closure', 'func_globals', 'func_dict']

def update_function(old, new):
    """Upgrade the code object of a function"""
    for name in func_attrs:
        try:
            setattr(old, name, getattr(new, name))
        except (AttributeError, TypeError):
            pass


def update_class(old, new):
    """Replace stuff in the __dict__ of a class, and upgrade
    method code objects"""
    for key in list(old.__dict__.keys()):
        old_obj = getattr(old, key)

        try:
            new_obj = getattr(new, key)
        except AttributeError:
            # obsolete attribute: remove it
            try:
                delattr(old, key)
            except (AttributeError, TypeError):
                pass
            continue

        if update_generic(old_obj, new_obj): continue

        try:
            setattr(old, key, getattr(new, key))
        except (AttributeError, TypeError):
            pass # skip non-writable attributes


def update_property(old, new):
    """Replace get/set/del functions of a property"""
    update_generic(old.fdel, new.fdel)
    update_generic(old.fget, new.fget)
    update_generic(old.fset, new.fset)


def isinstance2(a, b, typ):
    return isinstance(a, typ) and isinstance(b, typ)


UPDATE_RULES = [
    (lambda a, b: isinstance2(a, b, type),
     update_class),
    (lambda a, b: isinstance2(a, b, types.FunctionType),
     update_function),
    (lambda a, b: isinstance2(a, b, property),
     update_property),
]


if PY3:
    UPDATE_RULES.extend([(lambda a, b: isinstance2(a, b, types.MethodType),
                          lambda a, b: update_function(a.__func__, b.__func__)),
                        ])
else:
    UPDATE_RULES.extend([(lambda a, b: isinstance2(a, b, types.ClassType),
                          update_class),
                         (lambda a, b: isinstance2(a, b, types.MethodType),
                          lambda a, b: update_function(a.__func__, b.__func__)),
                        ])


def update_generic(a, b):
    for type_check, update in UPDATE_RULES:
        if type_check(a, b):
            update(a, b)
            return True
    return False


class StrongRef(object):
    def __init__(self, obj):
        self.obj = obj
    def __call__(self):
        return self.obj


def superreload(module, reload=reload, old_objects={}):
    """Enhanced version of the builtin reload function.

    superreload remembers objects previously in the module, and

    - upgrades the class dictionary of every old class in the module
    - upgrades the code object of every old function and method
    - clears the module's namespace before reloading

    """

    # collect old objects in the module
    for name, obj in list(module.__dict__.items()):
        if not hasattr(obj, '__module__') or obj.__module__ != module.__name__:
            continue
        key = (module.__name__, name)
        try:
            old_objects.setdefault(key, []).append(weakref.ref(obj))
        except TypeError:
            # weakref doesn't work for all types;
            # create strong references for 'important' cases
            if not PY3 and isinstance(obj, types.ClassType):
                old_objects.setdefault(key, []).append(StrongRef(obj))

    # reload module
    try:
        # clear namespace first from old cruft
        old_dict = module.__dict__.copy()
        old_name = module.__name__
        module.__dict__.clear()
        module.__dict__['__name__'] = old_name
        module.__dict__['__loader__'] = old_dict['__loader__']
    except (TypeError, AttributeError, KeyError):
        pass

    try:
        module = reload(module)
    except:
        # restore module dictionary on failed reload
        module.__dict__.update(old_dict)
        raise

    # iterate over all objects and update functions & classes
    for name, new_obj in list(module.__dict__.items()):
        key = (module.__name__, name)
        if key not in old_objects: continue

        new_refs = []
        for old_ref in old_objects[key]:
            old_obj = old_ref()
            if old_obj is None: continue
            new_refs.append(old_ref)
            update_generic(old_obj, new_obj)

        if new_refs:
            old_objects[key] = new_refs
        else:
            del old_objects[key]

    return module


def keep_user_modules_updated():
    global task
    if not task or not task.isAlive():
        import threading
        task = threading.Thread(target=keep_user_modules_updated_task,
            name="keep_user_modules_updated_task")
        task.daemon = True
        task.start()

task = None

def keep_user_modules_updated_task():
    from time import sleep
    while True:
        try: update_user_modules()
        except Exception,msg: error("%s\n%s" % (msg,traceback.format_exc()))
        sleep(1)

def update_user_modules():
    import sys
    from os.path import getmtime,basename
    from time import time
    import traceback

    modules = user_modules()
    for module in modules:
        filename = module.__file__.replace(".pyc",".py")
        if not filename in module_file_timestamps:
            module_file_timestamps[filename] = getmtime(filename)
        if module_file_timestamps[filename] != getmtime(filename):
            module_file_timestamps[filename] = getmtime(filename)
            name = module.__name__
            if name == "__main__":
                module_name = basename(filename).replace(".py","")
                debug("module %r is %r" % (name,module_name))
                module = __import__(module_name)
            module_load_timestamps[filename] = t0 = time()
            try: superreload(module)
            except Exception,msg: error("%s\n%s" % (msg,traceback.format_exc()))
            t = time() - t0
            info("reloaded module %r (%.3f s)" % (name,t))

module_file_timestamps = {}
module_load_timestamps = {}

def user_modules():
    """List of non-builtin modules"""
    import sys
    path = sys.path[1:] # exclude current directory
    modules = []
    system_modules = {}; system_modules.update(sys.modules)
    for name in system_modules:
        module = system_modules[name]
        module_file = module.__file__ if hasattr(module,"__file__") else ""
        if module_file and not any([module_file.startswith(d) for d in path]):
            modules.append(module)
    return modules

keep_user_modules_updated()


if __name__ == "__main__":
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")
    ##from timing_system_simulator import timing_system_simulator
    ##object = timing_system_simulator # for debugging
    ##import lauecollect
    ##print('outdated(getmodule(object))')
    ##print('object = update(object,always=True)')
    ##print('object = update(object)')
    ##print('user_modules()')
    print('update_user_modules()')
    print('keep_user_modules_updated()')
    
