"""Interruptible sleep
F. Schotte 4 Jun 2015 - 4 Jun 2015"""
__version__ = "1.0"

def sleep(seconds):
    """Return after for the specified number of seconds"""
    # After load and initializing the PvAPI Python's built-in 'sleep' function
    # stops working (returns too early). The is a replacement.
    from time import sleep,time
    t = t0 = time()
    while t < t0+seconds: sleep(min(0.2,t0+seconds-t)); t = time()
