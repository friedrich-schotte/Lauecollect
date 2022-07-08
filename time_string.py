"""For converting '100ps' <-> 1e-10, etc.
Author: Friedrich Schotte
Date created: 2009-08-26
Date last modified: 2022-07-03
Revision comment: Cleanup: logging
"""
__version__ = "1.6.6"

import logging


def vectorize(f):
    """Generalize function f(x) so it returns an array if x is an array"""
    from numpy import array

    def F(X, *args, **kwargs):
        if isscalar(X):
            return f(X, *args, **kwargs)
        return array([f(x, *args, **kwargs) for x in X])

    F.__doc__ = f.__doc__
    return F


def isscalar(x):
    """Is x a scalar type?"""
    # Work-around for a bug in "isscalar" of numpy returning false for None.
    from numpy import isscalar
    return isscalar(x) or x is None


# Problem: 'vectorize' returns an array of strings, not a chararray.
def as_chararray(f):
    """Make sure f returns a numpy array of type 'chararray'"""
    from numpy import chararray

    def F(x, *args, **kwargs):
        if isscalar(x):
            return f(x, *args, **kwargs)
        return f(x, *args, **kwargs).view(chararray)

    F.__doc__ = f.__doc__
    return F


@vectorize
def seconds(s):
    """Convert time string to number. e.g. '100ps' -> 1e-10"""
    from numpy import nan, isnan

    # noinspection PyBroadException
    try:
        seconds = float(eval(s))
    except Exception:
        seconds = nan

    if isnan(seconds):
        from re import sub
        integer = r"[0-9]+"
        # floating_point_number = r"([0-9]+[.]*[0-9]*e[0-9]+)"
        # number = "(" + integer + '|' + floating_point_number + ")"

        pattern = "(" + integer + "):(" + integer + ")"
        s = sub(pattern, r"(\1+\2/60.0)", s)

        s = s.replace("min", "*60")
        s = s.replace("h", "*60*60")
        s = s.replace("d", "*60*60*24")
        s = s.replace("s", "")
        s = s.replace("p", "*1e-12")
        s = s.replace("n", "*1e-9")
        s = s.replace("u", "*1e-6")
        s = s.replace("m", "*1e-3")
        # noinspection PyBroadException
        try:
            seconds = float(eval(s))
        except Exception:
            seconds = nan
    return seconds


@as_chararray
@vectorize
def time_string(t, precision=3):
    """Convert time given in seconds in more readable format
    such as ps, ns, ms, s.
    precision: number of digits"""
    from numpy import isnan, isinf, floor, rint
    if t is None:
        return "off"
    if t == "off":
        return "off"
    try:
        t = float(t)
    except (ValueError, TypeError):
        return "off"

    try:
        t = round_to_power_of_10(t)
    except (ValueError, TypeError):
        pass

    if isnan(t):
        return "off"
    if isinf(t) and t > 0:
        return "inf"
    if isinf(t) and t < 0:
        return "-inf"
    if t == 0:
        return "0"
    if abs(t) < 0.5e-12:
        return "0"
    if abs(t) < 999e-12:
        return "%.*gps" % (precision, t * 1e12)
    if abs(t) < 999e-9:
        return "%.*gns" % (precision, t * 1e9)
    if abs(t) < 999e-6:
        return "%.*gus" % (precision, t * 1e6)
    if abs(t) < 999e-3:
        return "%.*gms" % (precision, t * 1e3)
    if abs(t) < 60:
        return "%.*gs" % (precision, t)
    if abs(t) < 60 * 60:
        return "%g:%02gmin" % (floor(t / 60), rint(t % 60))
    if abs(t) < 24 * 60 * 60:
        return "%g:%02gh" % (floor((t / 60) / 60), rint((t / 60) % 60))
    return "%.*gd" % (precision, t / (24 * 60. * 60))


def timestamp(date_time, timezone=None):
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
            logging.debug("timestamp: %r: Assuming time zone %r" % (date_time, timezone))
            t = parse(date_time + timezone)
        t0 = parse("1970-01-01 00:00:00+0000")
        T = (t - t0).total_seconds()
    except Exception as msg:
        logging.error("timestamp: %r: %s" % (msg, date_time))
        T = nan
    return T


def round_to_power_of_10(t):
    from numpy import sign, log10, rint
    s = sign(t)
    val = abs(t)
    if val > 0:
        exponent = log10(val)
        if abs(fractional_part(exponent)) < 0.001:
            exponent = rint(exponent)
            t = s * 10 ** exponent
    return t


def fractional_part(x):
    from numpy import modf
    return modf(x)[0]


def isfinite(x):
    from numpy import isfinite
    try:
        return bool(isfinite(x))
    except (TypeError, ValueError):
        return False


if __name__ == "__main__":
    msg_format = "%(asctime)s: %(levelname)s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
