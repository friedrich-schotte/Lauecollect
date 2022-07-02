#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-11-10
Date last modified: 2020-11-10
Revision comment:
"""
__version__ = "1.0"


def to_SI_format(t, precision=3):
    """Convert number to string using "p" for 1e-12, "n" for 1 e-9, etc..."""

    def do_format(precision, t):
        s = "%.*g" % (precision, t)
        # Add trailing zeros if needed
        if "e" not in s:
            if "." not in s and len(s) < precision:
                s += "." + "0" * (precision - len(s))
            if "." in s and len(s) - 1 < precision:
                s += "0" * (precision - (len(s) - 1))
        return s

    try:
        t = float(t)
    except (ValueError, TypeError):
        return ""
    if t != t:
        return ""  # not a number
    if t == 0:
        return "0"
    if abs(t) < 0.5e-12:
        return "0"
    if abs(t) < 999e-12:
        return do_format(precision, t * 1e+12) + " p"
    if abs(t) < 999e-09:
        return do_format(precision, t * 1e+09) + " n"
    if abs(t) < 999e-06:
        return do_format(precision, t * 1e+06) + " u"
    if abs(t) < 999e-03:
        return do_format(precision, t * 1e+03) + " m"
    if abs(t) < 999e+00:
        return do_format(precision, t * 1e+00) + " "
    if abs(t) < 999e+03:
        return do_format(precision, t * 1e-03) + " k"
    if abs(t) < 999e+06:
        return do_format(precision, t * 1e-06) + " M"
    if abs(t) < 999e+09:
        return do_format(precision, t * 1e-09) + " G"
    return "%.*g" % (precision, t)


def from_SI_format(text):
    """Convert a text string as "1k" to the number 1000.
    SI prefixes accepted are P, E, T, G, M, k, m, u, n, p, f, a."""
    text = text.replace("P", "*1e+18")
    text = text.replace("E", "*1e+15")
    text = text.replace("T", "*1e+12")
    text = text.replace("G", "*1e+09")
    text = text.replace("M", "*1e+06")
    text = text.replace("k", "*1e+03")
    text = text.replace("m", "*1e-03")
    text = text.replace("u", "*1e-06")
    text = text.replace("n", "*1e-09")
    text = text.replace("p", "*1e-12")
    text = text.replace("f", "*1e-15")
    text = text.replace("a", "*1e-18")
    try:
        return float(eval(text))
    except Exception:
        from numpy import nan
        return nan
