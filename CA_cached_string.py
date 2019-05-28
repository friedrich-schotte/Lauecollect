"""Caching of Channel Access
Author: Friedrich Schotte
Date created: 2018-10-24
Date last modified: 2019-03-19
"""
__version__ = "1.0.5" # performance optimization

from logging import debug,info,warn,error
from cache import Cache

cache = Cache("CA")

def caget_cached(PV_name):
    """Value of Channel Access (CA) Process Variable (PV)"""
    from CA import caget,camonitor
    camonitor(PV_name,callback=CA_cache_update)
    value = caget(PV_name,timeout=0)
    if value is None:
        if cache.exists(PV_name): value = cache.get(PV_name)
    if value is None: value = caget(PV_name)
    if value is None: warn("Failed to get PV %r" % PV_name)
    return value

def CA_cache_update(PV_name,value,formatted_value):
    """Handle Process Variable (PV) update"""
    value = str(value)
    if not cache.exists(PV_name) or value != cache.get(PV_name):
        ##debug("%s=%s" % (PV_name,value))
        cache.set(PV_name,value)


if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging # for debugging
    from time import time # for timing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    PV_name = "NIH:TIMING.registers.cmcnd.count"
    print('caget_cached(PV_name) # should be 20228')
    from CA import caget
    print('caget(PV_name) # should be 20228')
    print('cache.get(PV_name) # should be 20228')
    print('cache.set(PV_name,"20228")')
