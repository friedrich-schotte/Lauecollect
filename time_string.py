"""For converting '100ps' <-> 1e-10, etc.
Author: Friedrich Schotte
Date created: 2009-08-26
Date last modified: 2018-10-27
"""
from __future__ import division # 1/2 = 0.5

__version__ = "1.5.4" # isnan -> isfinite
from logging import debug,info,warn,error

def vectorize(f):
    """Generalize function f(x) so it returns an array if x is an array"""
    from numpy import array
    def F(X,*args,**kwargs):
        if isscalar(X): return f(X,*args,**kwargs)
        return array([f(x,*args,**kwargs) for x in X])
    F.__doc__ = f.__doc__
    return F

def isscalar(x):
    """Is x a scalar type?"""
    # Workaroud for a bug in numpy's "isscalar" returning false for None.  
    from numpy import isscalar
    return isscalar(x) or x is None

# Problem: 'vectorize' returns a array of strings, not a chararray.
def as_chararray(f):
    """Make sure f returns a numpy array of type 'chararray'"""
    from numpy import chararray
    def F(x,*args,**kwargs):
        if isscalar(x): return f(x,*args,**kwargs)
        return f(x,*args,**kwargs).view(chararray)
    F.__doc__ = f.__doc__
    return F

@vectorize
def seconds(s):
    """Convert time string to number. e.g. '100ps' -> 1e-10"""
    from numpy import nan
    try: return float(s)
    except: pass
    s = s.replace("min","*60")
    s = s.replace("h","*60*60")
    s = s.replace("d","*60*60*24")
    s = s.replace("s","")
    s = s.replace("p","*1e-12")
    s = s.replace("n","*1e-9")
    s = s.replace("u","*1e-6")
    s = s.replace("m","*1e-3")
    try: return float(eval(s))
    except: return nan 

@as_chararray
@vectorize
def time_string(t,precision=3):
    """Convert time given in seconds in more readable format
    such as ps, ns, ms, s.
    precision: number of digits"""
    from numpy import isnan,isinf
    if t is None: return "off"
    if t == "off": return "off"
    try: t=float(t)
    except: return "off"
    if isnan(t): return "off"
    if isinf(t) and t>0: return "inf"
    if isinf(t) and t<0: return "-inf"
    if t == 0: return "0"
    if abs(t) < 0.5e-12: return "0"
    if abs(t) < 999e-12: return "%.*gps" % (precision,t*1e12)
    if abs(t) < 999e-9: return "%.*gns" % (precision,t*1e9)
    if abs(t) < 999e-6: return "%.*gus" % (precision,t*1e6)
    if abs(t) < 999e-3: return "%.*gms" % (precision,t*1e3)
    if abs(t) < 60: return "%.*gs" % (precision,t)
    if abs(t) < 60*60: return "%.*gmin" % (precision,t/60.)
    if abs(t) < 24*60*60: return "%.*gh" % (precision,t/(60.*60))
    return "%.*gd" % (precision,t/(24*60.*60))

def timestamp(date_time,timezone=None):
    """Convert a date string to number of seconds since 1 Jan 1970 00:00 UTC
    date: e.g. "2016-01-27 12:24:06.302724692-08"
    """
    from dateutil.parser import parse
    from numpy import nan

    try:
        t = parse(date_time)
        if t.tzinfo is None:
            if timezone is None:
                from dateutil.tz import tzlocal
                from datetime import datetime
                timezone = datetime.now(tzlocal()).tzname()
            debug("timestamp: %r: Assuming time zone %r" % (date_time,timezone))
            t = parse(date_time+timezone)
        t0 = parse("1970-01-01 00:00:00+0000")
        T = (t-t0).total_seconds()
    except Exception,msg: error("timestamp: %r: %s" % (msg,date_time)); T = nan
    return T

def date_time(seconds,timezone=""):
    """Date and time as formatted ASCII text, precise to 1 ms
    seconds: time elapsed since 1 Jan 1970 00:00:00 UTC
    e.g. '2016-02-01 19:14:31.707016-08:00' """
    from datetime import datetime
    import pytz
    from dateutil.tz import tzlocal
    from numpy import isfinite
    if isfinite(seconds):
        timeUTC = datetime.utcfromtimestamp(seconds)
        timezoneLocal = pytz.timezone(timezone) if timezone else tzlocal()
        utc = pytz.utc
        timeLocal = utc.localize(timeUTC).astimezone(timezoneLocal)
        date_time = str(timeLocal)
        # Time zone should be formatted "-0800" not "-08:00"
        if date_time.endswith(":00"): date_time = date_time[:-3]+"00"
    else: date_time = ""
    return date_time

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s: %(levelname)s %(message)s")

    print('date_time(timestamp("1970-01-01 00:00:00"))')
    print('date_time(timestamp("27 Aug 2018 21:00"))')
    print('date_time(timestamp("27 Aug 2018 21:00 EDT"))')
    print('date_time(timestamp("27 Aug 2018 21:00 EST"))')
    print('date_time(timestamp("2018-08-27 21:00:00-0400"))')
