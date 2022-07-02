"""
Caching of Channel Access
Author: Friedrich Schotte
Date created: 2018-10-24
Date last modified: 2020-05-27
Revision comment: Cleanup, Debugging
"""
__version__ = "2.0.3"

from logging import debug, warning

from cache import Cache


def caget_cached(PV_name):
    """Value of Channel Access (CA) Process Variable (PV)"""
    from CA import caget, camonitor
    camonitor(PV_name, callback=CA_cache_update)
    value = caget(PV_name, timeout=0)
    if value is None:
        if cache_exists(PV_name):
            value = cache_get(PV_name)
    if value is None:
        value = caget(PV_name)
    if value is None:
        warning("Failed to get PV %r" % PV_name)
    return value


def CA_cache_update(PV_name, value, _formatted_value):
    """Handle Process Variable (PV) update"""
    # debug("PV_name = %r, value = %r" % (PV_name, value))
    from same import same
    if not cache_exists(PV_name) or not same(value, cache_get(PV_name)):
        cache_set(PV_name, value)


cache = Cache("CA")


def cache_set(PV_name, value):
    # debug("%s = %r" % (PV_name, value))
    cache.set(PV_name + ".py", repr(value).encode("utf-8"))


def cache_get(PV_name):
    cache_value = cache.get(PV_name + ".py")
    # Needed for eval:
    try:
        value = eval(cache_value)
    except Exception:
        value = None
    return value


def cache_exists(PV_name):
    return cache.exists(PV_name + ".py")


if __name__ == "__main__":
    import logging  # for debugging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    PV_name = "NIH:TIMING.registers.pass_number.address"
    print('from CA import caget')
    from CA import caget

    print('caget(PV_name)')
    print('caget_cached(PV_name)')
    print('cache_get(PV_name)')
