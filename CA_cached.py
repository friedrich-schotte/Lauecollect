"""Caching of Channel Access
Author: Friedrich Schotte
Date created: 2018-10-24
Date last modified: 2019-05-26
"""
__version__ = "2.0" # preserve data types

from logging import debug,info,warn,error
from cache import Cache

def caget_cached(PV_name):
    """Value of Channel Access (CA) Process Variable (PV)"""
    from CA import caget,camonitor
    camonitor(PV_name,callback=CA_cache_update)
    value = caget(PV_name,timeout=0)
    if value is None:
        if cache_exists(PV_name): value = cache_get(PV_name)
    if value is None: value = caget(PV_name)
    if value is None: warn("Failed to get PV %r" % PV_name)
    return value

def CA_cache_update(PV_name,value,formatted_value):
    """Handle Process Variable (PV) update"""
    if not cache_exists(PV_name) or value != cache_get(PV_name):
        ##debug("%s=%s" % (PV_name,value))
        cache_set(PV_name,value)

cache = Cache("CA")

def cache_set(PV_name,value):
    cache.set(PV_name+".py",repr(value))

def cache_get(PV_name):
    cache_value = cache.get(PV_name+".py")
    try: value = eval(cache_value)
    except: value = None
    return value

def cache_exists(PV_name):
    return cache.exists(PV_name+".py")


if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging # for debugging
    from time import time # for timing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    PV_name = "NIH:CONF.CONFIGURATION_NAMES"
    from CA import caget
    print('caget(PV_name)')
    print('caget_cached(PV_name)')
    print('cache_get(PV_name)')
