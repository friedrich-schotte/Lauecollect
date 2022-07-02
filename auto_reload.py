"""
Dynamically refresh Python code

Author: Friedrich Schotte
Date created: 2017-07-08
Date last modified: 2020-03-14
Revision comment: Tweak: fall back to "reload" if "superreload" unavailable
"""
__version__ = "1.3.1"
from logging import debug,info,warning,error
from traceback import format_exc

try: from IPython.extensions.autoreload import superreload
except: 
    try: from importlib import reload as superreload
    except: superreload = reload
                    
class Auto_Reload(object):
    task_name = "auto_reload.run"
    
    def get_enabled(self): return self.running
    def set_enabled(self,value):
        if bool(value) == True:  self.start()
        if bool(value) == False: self.stop()
    enabled = property(get_enabled,set_enabled)

    def start(self):
        if not self.running:
            import threading
            thread = threading.Thread(target=self.run,
                name=self.task_name)
            thread.daemon = True
            thread.start()

    def stop(self): self.run_cancelled = True

    @property
    def running(self):
        running = False
        import threading
        for thread in threading.enumerate():
            if thread.name == self.task_name: running = True
        return running

    def run(self):
        debug("Auto-reload enabled.")
        self.run_cancelled = False
        while not self.run_cancelled:
            try: update_user_modules()
            except Exception as msg: 
                try: error("%s\n%s" % (msg,format_exc()))
                except: pass
            from time import sleep
            sleep(1)
        debug("Auto-reload disabled.")
        
auto_reload = Auto_Reload()
        

def update_user_modules():
    from time import time

    modules = user_modules()
    for module in modules:
        filename = module_filename(module)
        if filename:
            if not filename in module_file_timestamps:
                module_file_timestamps[filename] = getmtime(filename)
            if abs(module_file_timestamps[filename] - getmtime(filename)) > 0.001:
                module_file_timestamps[filename] = getmtime(filename)
                module = real_module(module)
                t0 = time()
                try: superreload(module)
                except Exception as x: 
                    try: 
                        ##warning("Reloading module %r: %r\n%s" % (module_name(module),x,format_exc()))
                        warning("Reloading module %r: %r" % (module_name(module),x))
                    except: pass
                else:
                    dt = time()-t0
                    info("Reloaded module %r (%.3f s)" % (module_name(module),dt))
                    module_load_timestamps[filename] = time()
                
def user_modules():
    """List of non-builtin modules"""
    import sys
    modules = []
    system_modules = {}; system_modules.update(sys.modules)
    for name in system_modules:
        module = system_modules[name]
        module_file = module_filename(module)
        if module_file and not any([module_file.startswith(sys.prefix)]):
            modules.append(module)
    return modules

def module_filename(module):
    """module: Python module object"""
    filename = ""
    from inspect import getfile
    try: filename = getfile(module)
    except Exception as x: 
        ##debug("%s: getfile: %s" % (module_name(module),x))
        pass
    from sys import path
    from os.path import exists
    for d in path:
        pathname = d+"/"+module_name(module)+".py"
        if exists(pathname): filename = pathname; break
    filename = filename.replace(".pyc",".py")
    return filename
    
def real_module(module):
    if module_name(module) == "__main__":
        from os.path import basename
        name = basename(module_filename(module)).replace(".py","")
        debug("module %r is %r" % (module_name(module),name))
        module = __import__(name)
    return module

def module_name(module):
    return getattr(module,"__name__","")
            
def getmtime(filename):
    from os.path import getmtime
    try: return getmtime(filename)
    except: return 0

module_file_timestamps = {}
module_load_timestamps = {}


if __name__ == "__main__":
    from pdb import pm
    import logging
    logger = logging.getLogger()
    for handler in logger.handlers: logger.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")
    print('update_user_modules()')
    print('auto_reload.enabled = True')
    
