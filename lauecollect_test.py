"""
Author: Friedrich Schotte
Date created: 11/3/2017
Date last modified: 11/3/2017
"""
__version__ = "1.0"

import lauecollect,id14
from logging import debug,info,warn,error

if __name__ == "__main__":
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s: %(message)s")
    ##from IPython.extensions.autoreload import superreload
    from autoreload import superreload
    import autoreload
    print("print autoreload.dependencies(id14)")
    print("superreload(id14)")
    print("superreload(lauecollect)")
