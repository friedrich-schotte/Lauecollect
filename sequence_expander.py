"""
Shorthand notation for timing sequences
Author: Friedrich Schotte
Date created: 2018-10-02
Date last modified: 2022-05-05
Revision comment: Moved: split_list
"""
__version__ = "2.1.6"

from logging import debug
from cached_function import cached_function


@cached_function()
def sequence_expander(domain_name):
    return Sequence_Expander(domain_name)


class Sequence_Expander(object):
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__.lower(), self.domain_name)

    @property
    def domain(self):
        from domain import domain
        return domain(self.domain_name)

    def Sequence(self, delay=None, acquiring=True, **kwargs):
        return self.domain.timing_system.composer.Sequence(delay=delay, acquiring=acquiring, **kwargs)

    def Sequences(self, delay=None, acquiring=True, **kwargs):
        return self.domain.timing_system.composer.Sequences(delay=delay, acquiring=acquiring, **kwargs)

    def expand_sequence(self, s, report=None):
        if report:
            report(format_report("Original", s))
        operations = [
            self.quote_binary_numbers,
            self.quote_strings,
            self.replace_off,
            self.expand_SI_units,
            self.add_toplevel_dictionary,
            self.add_dictionaries,
            self.fix_repeat_syntax,
            self.expand_generators,
            self.add_constructors,
            self.add_expanders,
            self.expand_generators,
        ]
        for operation in operations:
            new = operation(s)
            if new != s:
                s = new
                if report:
                    report(format_report(name(operation), s))
        return s

    def delay_sequences(self, s, report=None):
        if report:
            report(format_report("Original", s))
        operations = [
            self.quote_binary_numbers,
            self.quote_strings,
            self.replace_off,
            self.expand_SI_units,
            self.add_toplevel_dictionary,
            self.add_dictionaries,
            self.fix_repeat_syntax,
            self.expand_generators,
            self.delays_to_sequences,
        ]
        for operation in operations:
            new = operation(s)
            if new != s:
                s = new
                if report:
                    report(format_report(name(operation), s))
        return s

    def expand(self, s, report=None):
        if report:
            report(format_report("Original", s))
        operations = [
            self.quote_binary_numbers,
            self.quote_strings,
            self.replace_off,
            self.expand_SI_units,
            self.add_toplevel_dictionary,
            self.add_dictionaries,
            self.fix_repeat_syntax,
            self.expand_generators,
        ]
        for operation in operations:
            new = operation(s)
            if new != s:
                s = new
                if report:
                    report(format_report(name(operation), s))
        return s

    def delays_to_sequences(self, s):
        # "{'delays': [0.001, 0.00178, 0.00316, 0.00562, 0.01, 0.0178, 0.0316, 0.0562]}"
        from numpy import nan  # noqa - for eval
        dictionary = eval(s)
        parameters = dictionary["delays"]
        sequences = []
        for parameter in parameters:
            if type(parameter) == dict:
                sequences += [self.Sequence(**parameter)]
            else:
                sequences += [self.Sequence(parameter)]
        s = repr(sequences)
        return s

    @staticmethod
    def quote_binary_numbers(s):
        """ S=001 -> S='101' """
        from re import sub
        # S=001 -> S='101'
        s = sub(r"(^|[=:\[({])([01X]{3,5})([ ,=:*\])}]|$)", r"\1'\2'\3", s)
        # (...)(...)(...) defining three groups: pre-match, substitute, post-match
        # ^|[=:\[({]) = begin of string or any of the characters =, :, [, (, or {
        # [01]{3,5} = 0 or 1, repeated 3 to 5 times
        # [ ,=:*\})]|$ = any of the characters space, comma, ], ), }, or end of string
        # \1 \2 \3, matching groups defined by grouping parentheses (...)(...)(...)
        return s

    @staticmethod
    def quote_strings(s):
        """ PP=Flythru-4 -> PP='Flythru-4' """
        from re import sub
        # seq=NIH:i5c1 -> seq="NIH:i5c1"
        s = sub(r"(NIH:[A-Za-z0-9_-]*)", r"'\1'", s)
        # PP=Flythru-4 -> PP='Flythru-4', but not 'pairs(-10us,...'
        s = sub(r"=([A-Za-z][A-Za-z0-9_-]*)([^A-Za-z0-9_(])", r"='\1'\2", s)
        # {enable:'111'} {'enable':'111'}
        s = sub(r"([^A-Za-z0-9_'])([A-Za-z][A-Za-z0-9_-]*):", r"\1'\2':", s)
        return s

    @staticmethod
    def replace_off(s):
        s = s.replace("off", "nan")
        return s

    @staticmethod
    def expand_SI_units(s):
        from re import sub
        SI_prefixes = {"p": "e-12", "n": "e-9", "u": "e-6", "m": "e-3"}
        for p in SI_prefixes:
            s = sub("([0-9])" + p, r"\1" + SI_prefixes[p], s)
        s = sub("([0-9])s", r"\1", s)
        return s

    @staticmethod
    def add_toplevel_dictionary(s):
        from re import sub
        keyword = r"[a-zA-Z_]+"
        s = sub("^(" + keyword + "=.*)", r"dict(\1)", s)
        return s

    @staticmethod
    def add_dictionaries(s):
        from re import sub
        key = r"[a-zA-Z_]+"
        value = r"[0-9A-Za-z-'+*]+"
        pair = key + "=" + value
        argument_list = '(' + pair + ', *)*' + pair
        argument_list_in_parentheses = r'\(' + argument_list + r'\)'
        lookbehind = r'(?<=[^A-Za-z_])'
        pattern = lookbehind + '(' + argument_list_in_parentheses + ')'
        s = sub(pattern, r"dict\1", s)

        pattern = '^(' + argument_list_in_parentheses + ')'  # ^=begin of string
        s = sub(pattern, r"dict\1", s)

        incomplete_argument_list = value + ', *' + argument_list
        incomplete_argument_list_in_parentheses = r'\(' + incomplete_argument_list + r'\)'
        pattern = lookbehind + '(' + incomplete_argument_list_in_parentheses + ')'
        s = sub(pattern, r"dict(delay=\1)", s)

        return s

    @staticmethod
    def add_constructors(s):
        from re import sub
        s = sub("{", "Sequences(**{", s)
        s = sub("}", "})", s)
        return s

    @staticmethod
    def fix_repeat_syntax(s):
        """Sequences(nan,SEQ='100')*32 -> [Sequences(nan,SEQ='100')]*32"""
        from split_list import split_list
        from re import sub
        T = split_list(s)
        for i in range(0, len(T)):
            t = T[i]
            t = sub(r"^(.*\(.*\))\*([0-9]+)$", r"[\1]*\2", t)
            T[i] = t
        s = ", ".join(T)
        return s

    @staticmethod
    def expand_generators(s):
        from flatten import flatten
        from numpy import nan  # noqa - for eval
        t = eval("[" + s + "]")
        t = flatten(t)
        s = repr(t).strip("[]")
        return s

    @staticmethod
    def add_expanders(s):
        from split_list import split_list
        T = split_list(s)
        for i in range(0, len(T)):
            t = T[i]
            if t.startswith("Sequences("):
                t += "[:]"
            T[i] = t
        s = ", ".join(T)
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


def ramp(low=20.0, high=24.0, step=1.0, hold=1, hold_low=None, hold_high=None, repeat=1):
    """List of values from *low* to *high* and back to *low* again"""
    from numpy import sign
    if hold_low is None:
        hold_low = hold
    if hold_high is None:
        hold_high = hold
    s = sign(high - low)
    step = s * abs(step)
    values = (
            [low] * hold_low +
            arange(low, high - step, step) +
            [high] * hold_high +
            arange(high, low - step, step)
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


def name(operation):
    return operation.__name__.replace("_", " ").capitalize()


def format_report(name, s):
    from split_list import split_list
    return name + "\n" + ",\n".join(split_list(s)) + "\n"


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)-5s] %(module)s.%(funcName)s: %(message)s")

    # from instrumentation import *

    domain_name = "BioCARS"
    # domain_name = "LaserLab"

    self = sequence_expander(domain_name)
    print("self.domain_name = %r" % self.domain_name)

    # s = "delays=[-10us,interleave(-10us,lin_series(-100ps,75ps,25ps)+log_series(100ps,1us,steps_per_decade=4)),-10us]"
    s = 'delays=[-10us,interleave(-10us,log_series(10ms,178ms,steps_per_decade=4)),-10us]'
    # s = 'delays=[(-10us,PP=Flythru-48),interleave(-10us,log_series(10ms,178ms,steps_per_decade=4)),-10us]'
    # s = "delays=[(144, S=[110]*5+[101]), (1440, S=[100]*8+[101]), (14400, S=[100]*89+[101])]"

    # s = "delays=[(nan, PLP=Period-48, SEQ=010)*5, (nan, PLP=Period-144, SEQ=100), (264+1*144, SEQ=101), (nan, SEQ=100)*2, (264+4*144, SEQ=101), "\
    #    "(nan, SEQ=100)*4, (264+9*144, SEQ=101), (nan, SEQ=100)*8, (264+18*144, SEQ=101), (nan, SEQ=100)*16, (264+35*144, SEQ=101), (nan, SEQ=100)*32, "\
    #    "(264+68*144, SEQ=101)"
    # s = "delays=[(-10us, PLP=Flythru-4), -10us, (264, SEQ=1010), 528, 792, 1056, (-10us, SEQ=1111), -10us"
    # s = 'delays=[[enable=011]*4+[enable=111]'
    # s = "delays=[[(pp=Period-48, enable=010)]*5, (image=0, pp=Period-144, enable=100), (264+1*144, enable=101), [(image=0, enable=100)]*2, "\
    #    "(264+4*144, enable=101), (image=0, enable=100)*4, (264+9*144, enable=101), (image=0, enable=100)*8, (264+18*144, enable=101), "\
    #    "(image=0, enable=100)*16, (264+35*144, enable=101), (image=0, enable=100)*32, (264+68*144, enable=101)]"
    # s = 'delays=[(enable=111)]'
    # s = 'delays=[off,100ps,off,1ns]'
    report = debug

    # print('add_dictionaries("hsc=\'H-56\',pp=\'Flythru-4\',seq=\'NIH:i1\',delays=[]")')
    # print('add_toplevel_dictionary("hsc=\'H-56\',pp=\'Flythru-4\',seq=\'NIH:i1\'")')

    # print("x=expand_sequence(sequence_modes.acquisition.value,report=debug)")
    # print("x=expand_sequence(scan_configuration.points.value,report=debug)")
    # print("x=expand_sequence(temperature_configuration.list.value,report=debug)")
    # print("x=expand_sequence(power_configuration.list.value,report=debug)")
    # print("x=delay_sequences(delay_configuration.delay_configuration.value,report=debug)")
    # print('max(arange(-2,2,0.05))')
    print('self.delay_sequences(%r,report=debug)' % s)
