"""
Shorthand notation for scans
Author: Friedrich Schotte
Date created: 2018-10-02
Date last modified: 2022-05-05
Revision comment: Moved: split_list
"""
__version__ = "1.7.1"

import traceback
import logging


def safe_expand_scan_points(expr):
    values = []
    if expr:
        try:
            expr = expand_scan_points(expr)
        except Exception as msg:
            logging.error("expand_scan_points: %r: %s\n%s" % (expr, msg, traceback.format_exc()))
            expr = ""
    if expr:
        from numpy import nan  # noqa - for eval
        try:
            values = eval(expr)
        except Exception as msg:
            logging.error("%s: %s\n%s" % (expr, msg, traceback.format_exc()))
    from as_list import as_list
    values = as_list(values)
    return values


def expand_scan_points(s, report=None):
    if report:
        report(format_report("Original", s))
    operations = [
        expand_generators,
        unify_types,
    ]
    for operation in operations:
        new = operation(s)
        if new != s:
            s = new
            if report:
                report(format_report(name(operation), s))
    return s


def name(operation): return operation.__name__.replace("_", " ").capitalize()


def format_report(name, s):
    from split_list import split_list
    return name + "\n" + ",\n".join(split_list(s)) + "\n"


def expand_generators(s):
    from flatten import flatten
    t = eval("[" + s + "]")
    t = flatten(t)
    s = repr(t).strip("[]")
    return s


def unify_types(s):
    from numpy import array
    t = eval(s)
    t = array(t).tolist()
    s = repr(t).strip("[]")
    return s


def lin_series(start, end, step, interleave=None):
    """Linear series"""
    from numpy import arange, finfo
    eps = finfo(float).eps
    t = arange(start, end + eps, step)
    t = [round_exp(x, 3) for x in t]
    t = list(t)
    if interleave is not None:
        t = interleave_value(t, interleave)
    return t


def log_series(start, end, steps_per_decade=4, interleave=None):
    """Geometric series"""
    from numpy import log10, arange, finfo
    eps = finfo(float).eps
    t = 10 ** arange(log10(start), log10(end + eps) + 1e-3, 1. / steps_per_decade)
    t = [round_exp(x, 3) for x in t]
    # Make sure end point is included.
    if end <= t[-1] * 1.01:
        t[-1] = end
    else:
        t += [end]
    t = list(t)
    if interleave is not None:
        t = interleave_value(interleave, t)
    return t


def interleave_value(t0, series, begin=False, end=False):
    """Add t0 between every element of *series*"""
    T = []
    if begin:
        T += [t0]
    if len(series) > 0:
        T += [series[0]]
    for t in series[1:]:
        T += [t0, t]
    if end:
        T += [t0]
    return T


interleave = interleave_value


def pairs(t0, series):
    """Precede every element of *series* with t0"""
    T = []
    for t in series:
        T += [t0, t]
    return T


pair = pairs


def arange(start, end, step=1.0):
    """list of value from *start* to *end*, inclusive *end*"""
    from numpy import arange, finfo, sign
    eps = finfo(float).eps
    s = sign(end - start)
    step = s * abs(step)
    values = arange(start, end * (1 + s * 2 * eps), step)
    values = list(values)
    return values


def ramp(low=20.0, high=24.0, step=1.0, hold=1, hold_low=None, hold_high=None,
         hold_low_begin=None, hold_low_end=None, repeat=1):
    """List of values from *low* to *high* and back to *low* again"""
    from numpy import sign

    low = float(low)
    high = float(high)
    step = float(step)

    if hold_low is None:
        hold_low = hold
    if hold_high is None:
        hold_high = hold
    if hold_low_begin is None:
        hold_low_begin = hold_low
    if hold_low_end is None:
        hold_low_end = 0
    s = sign(high - low)
    step = s * abs(step)
    values = (
            [low] * hold_low_begin +
            arange(low, high - step, step) +
            [high] * hold_high +
            arange(high, low - step, step) +
            [low] * hold_low_end
    )
    values = values * repeat
    return values


def power(T0=1.0, N_per_decade=4, N_power=6, reverse=False):
    """Power titration series
    T0: highest transmission level
    reverse=False: falling
    reverse=True: rising
    """
    from numpy import arange
    t = T0 * 10 ** (-arange(0., N_power) / N_per_decade)
    t = [round_exp(x, 3) for x in t]
    t = list(t)
    if reverse:
        t = t[::-1]
    return t


def round_exp(x, n):
    """Round floating point number to *n* decimal digits in the mantissa"""
    return float(("%." + str(n) + "g") % x)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)-5s] %(module)s.%(funcName)s: %(message)s")

    report = logging.debug

    print('safe_expand_scan_points("95.04, 75.04, 62.04, 52.04, 42.04, 30.04, 2.04, -16 ")')
    print('safe_expand_scan_points("ramp(low=-16, high=120, step=1, hold_low_begin=20, hold_high=15, hold_low_end=20)")')
    print('safe_expand_scan_points("arange(9,16,0.01)")')
    print('safe_expand_scan_points("power(T0=1.0, N_per_decade=4, N_power=6, reverse=False)")')
