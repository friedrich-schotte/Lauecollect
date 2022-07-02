"""Aerotech  Motion Controller
Communication via Aeroch's C library interface using a proprietary
protocol by Aerotech.
Author: Friedrich Schotte
Date created: 2019-08-15
Date lst modified: 2019-08-15
"""
__version__ = "1.0" 
from logging import debug,info,warn,error

class Ensemble_Library(object):
    library = None
    library_load_failed = False
    
    library_path = r'C:\Program Files (x86)\Aerotech\Ensemble\CLibrary\Bin'
    library_name = "EnsembleC.dll"
    
    def load_library(self):
        if self.library is None and not self.library_load_failed:
            from os import environ
            if not self.library_path in environ["PATH"]:
                environ["PATH"] = self.library_path+";"+environ["PATH"]
            import ctypes
            try: self.library = ctypes.windll.LoadLibrary(self.library_name)
            except Exception as details:
                error('ctypes.windll.LoadLibrary(%r): %s' % (self.library_name,details))
                error("This module needs to be running on operating system Windows.")
                self.library_load_failed = True
                info("Entering simulation mode")
                from Ensemble_library_simulator import ensemble_library
                self.library = ensemble_library

    def __getattr__(self,name):
        if name.startswith("__") and name.endswith("__"):
            value = object.__getattribute__(self,name)
        else:
            self.load_library()
            if self.library is None:
                raise RuntimeError("Library %r not loaded" % self.library_name) 
            value = getattr(self.library,name)
        return value


ensemble_library = Ensemble_Library()

if __name__ == "__main__":
    from pdb import pm
    import logging
    format="%(asctime)s: %(levelname)s %(message)s"
    logging.basicConfig(level=logging.DEBUG,format=format)

    self = ensemble_library
    print("self.EnsembleConnect")
