"""
Shorthand notation for timing sequences
Author: Friedrich Schotte
Date created: 2018-10-02
Date last modified: 2010-01-29
"""
__version__ = "1.1.4" # last point of arange(-2,2,0.05)

from logging import debug,info,warn,error

from Ensemble_SAXS_pp import Sequence,Sequences,sequence,seq,sequences

def expand_sequence(s,report=None):
    if report: report(format_report("Original",s))
    operations = [
        quote_binary_numbers,
        quote_strings,
        expand_SI_units,
        add_toplevel_dictionary,
        add_dictionaries,
        fix_repeat_syntax,
        expand_generators,
        add_constructors,
        add_expanders,
        expand_generators,
    ]
    for operation in operations:
        new = operation(s)
        if new != s:
            s = new
            if report: report(format_report(name(operation),s))
    return s

def delay_sequences(s,report=None):
    if report: report(format_report("Original",s))
    operations = [
        quote_binary_numbers,
        quote_strings,
        expand_SI_units,
        add_toplevel_dictionary,
        add_dictionaries,
        fix_repeat_syntax,
        expand_generators,
        delays_to_sequences,
    ]
    for operation in operations:
        new = operation(s)
        if new != s:
            s = new
            if report: report(format_report(name(operation),s))
    return s

def expand(s,report=None):
    if report: report(format_report("Original",s))
    operations = [
        quote_binary_numbers,
        quote_strings,
        expand_SI_units,
        add_toplevel_dictionary,
        add_dictionaries,
        fix_repeat_syntax,
        expand_generators,
    ]
    for operation in operations:
        new = operation(s)
        if new != s:
            s = new
            if report: report(format_report(name(operation),s))
    return s

def name(operation): return operation.__name__.replace("_"," ").capitalize()

def format_report(name,s):
    return name+"\n"+",\n".join(split_list(s))+"\n"

def delays_to_sequences(s,report=None):
    ## "{'delays': [0.001, 0.00178, 0.00316, 0.00562, 0.01, 0.0178, 0.0316, 0.0562]}"
    dictionary = eval(s)
    parameters = dictionary["delays"]
    sequences = []
    for parameter in parameters:
        if type(parameter) == dict: sequences += [Sequence(**parameter)]
        else: sequences += [Sequence(parameter)]
    s = repr(sequences)
    return s

def quote_binary_numbers(s):
    """ S=001 -> S='101' """
    from re import sub
    # S=001 -> S='101'
    s = sub(r"(^|[=:\[\({])([01]{3,5})([ ,=:*\]\)}]|$)",r"\1'\2'\3",s)
    # (...)(...)(...) defining three groups: pre-match, substitute, post-match
    # ^|[ ,=\[\(]) = begin of string of any of the characters space, comma, [, or (
    # [01]{3,5} = 0 or 1, repeated 3 to 5 times
    # [ ,=\]\)]|$ = any of the characters space, comma, ], ), or end of string
    # \1 \2 \3, matching groups defined by grouping parentheses (...)(...)(...)
    return s

def quote_strings(s):
    """ PP=Flythru-4 -> PP='Flythru-4' """
    from re import sub
    # seq=NIH:i5c1 -> seq="NIH:i5c1"
    s = sub(r"(NIH:[A-Za-z0-9_-]*)",r"'\1'",s)
    # PP=Flythru-4 -> PP='Flythru-4', but not 'pairs(-10us,...'
    s = sub(r"=([A-Za-z][A-Za-z0-9_-]*)([^A-Za-z0-9_\(])",r"='\1'\2",s)
    # {enable:'111'} {'enable':'111'}
    s = sub(r"([^A-Za-z0-9_'])([A-Za-z][A-Za-z0-9_-]*):",r"\1'\2':",s)
    return s

def expand_SI_units(s):
    from re import sub
    SI_prefixes = {"p":"e-12","n":"e-9","u":"e-6","m":"e-3"}
    for p in SI_prefixes: s = sub("([0-9])"+p,r"\1"+SI_prefixes[p],s)
    s = sub("([0-9])s",r"\1",s)
    return s

def add_toplevel_dictionary(s):
    from re import sub
    keyword = r"[a-zA-Z_]+"
    s = sub("^("+keyword+"=.*)",r"dict(\1)",s)
    return s    

def add_dictionaries_1(s):
    from re import sub
    key = r"[a-zA-Z_]+"
    interger = r"[0-9]+"
    floating_point_number = r"([0-9]+[.]*[0-9]*e[0-9]+)"
    number = "("+interger+'|'+floating_point_number+")"
    string = r"('[^']*')"
    value = "("+number+"|"+string+")"
    list = "([("+value+" *,)*"+value+"])"
    expr = "("+value+"|"+list+")" 
    expr = value 
    key_value_pair = "("+key+"="+expr+")"
    argument_list = '('+key_value_pair+', *)*'+key_value_pair
    incomplete_argument_list = value+', *'+argument_list

    pattern = '('+argument_list+')'
    s = sub(pattern,r"dict(\1)",s)
    return s

def add_dictionaries(s):
    from re import sub
    key = r"[a-zA-Z_]+"
    value = r"[0-9A-Za-z-'+*]+"
    pair = key+"="+value
    argument_list = '('+pair+', *)*'+pair
    argument_list_in_parenteses = r'\('+argument_list+r'\)'
    lookbehind = r'(?<=[^A-Za-z_])'
    pattern = lookbehind+'('+argument_list_in_parenteses+')'
    s = sub(pattern,r"dict\1",s)

    pattern = '^('+argument_list_in_parenteses+')' # ^=begin of string
    s = sub(pattern,r"dict\1",s)

    incomplete_argument_list = value+', *'+argument_list
    incomplete_argument_list_in_parenteses = r'\('+incomplete_argument_list+r'\)'
    pattern = lookbehind+'('+incomplete_argument_list_in_parenteses+')'
    s = sub(pattern,r"dict(delay=\1)",s)

    return s

def add_constructors(s):
    from re import sub
    s = sub("{","Sequences(**{",s)
    s = sub("}","})",s)
    return s

def fix_repeat_syntax(s):
    """Sequences(nan,SEQ='100')*32 -> [Sequences(nan,SEQ='100')]*32"""
    from re import sub
    T = split_list(s)
    for i in range(0,len(T)):
        t = T[i]
        t = sub(r"^(.*\(.*\))\*([0-9]+)$",r"[\1]*\2",t)
        T[i] = t
    s = ", ".join(T)
    return s


def expand_generators(s):
    from flatten import flatten
    from numpy import nan # for eval
    t = eval("["+s+"]")
    t = flatten(t)
    s = repr(t).strip("[]")
    return s

def add_expanders(s):
    T = split_list(s)
    for i in range(0,len(T)):
        t = T[i]
        if t.startswith("Sequences("): t += "[:]"
        T[i] = t
    s = ", ".join(T)
    return s

def lin_series(start,end,step,interleave=None):
    """Linear series"""
    from numpy import arange,finfo
    eps = finfo(float).eps
    t = arange(start,end+eps,step)
    t = [round_exp(x,3) for x in t]
    t = list(t)
    if interleave is not None: t = interleave_value(t,interleave)
    return t

def log_series(start,end,steps_per_decade=4,interleave=None):
    """Geometric series"""
    from numpy import log10,arange,finfo
    eps = finfo(float).eps
    t = 10**arange(log10(start),log10(end+eps)+1e-3,1./steps_per_decade)
    t = [round_exp(x,3) for x in t]
    # Make sure end point is included.
    if end <= t[-1]*1.01: t[-1] = end 
    else: t += [end] 
    t = list(t)
    if interleave is not None: t = interleave_value(interleave,t)
    return t

def interleave_value(t0,series,begin=False,end=False):
    """Add t0 between every element of *series*"""
    T = []
    if begin: T += [t0]
    if len(series) > 0: T += [series[0]]
    for t in series[1:]: T += [t0,t]
    if end: T += [t0]
    return T
interleave = interleave_value

def pairs(t0,series):
    """preceed every elelemt of *series* with t0"""
    T = []
    for t in series: T += [t0,t]
    return T
pair = pairs

def arange(start,end,step=1.0):
    """list of value from *start* to *end*, inclusive *end*"""
    from numpy import arange,finfo,sign
    eps = finfo(float).eps
    s = sign(end-start)
    step = s*abs(step)
    values = arange(start,end*(1+s*2*eps),step)
    values = list(values)
    return values

def ramp(low=20.0,high=24.0,step=1.0,hold=1,hold_low=None,hold_high=None,repeat=1):
    """List of values from *low* to *high* and back to *low* again"""
    from numpy import sign
    if hold_low is None: hold_low = hold
    if hold_high is None: hold_high = hold
    s = sign(high-low)
    step = s*abs(step)
    values = arange(low,high-step,step) + [high]*hold_high + \
             arange(high-step,low-step,step) + [low ]*(hold_low-1)
    values = values*repeat
    return values

def power(T0=1.0,N_per_decade=4,N_power=6,reverse=False):
    """Power titration series
    T0: highest transmission level
    reverse=False: falling
    reverse=True: rising
    """
    from numpy import log10,arange
    t = T0 * 10**(-arange(0.,N_power)/N_per_decade)
    t = [round_exp(x,3) for x in t]
    t = list(t)
    if reverse: t = t[::-1]
    return t

def round_exp(x,n):
    """Round floating point number to *n* decimal digits in the mantissa"""
    return float(("%."+str(n)+"g") % x)

def split_list(s):
    """Split a comma-separated list, with out breaking up list elements
    enclosed in backets or parentheses"""
    start = 0
    level = 0
    elements = []
    for i in range(0,len(s)):
        if s[i] in ["(","[",'{']: level += 1
        if s[i] in [")","]",'}']: level -= 1
        if s[i] == "," and level == 0:
            end = i
            element = s[start:end].strip()
            if element: elements += [element]
            start = i+1
    end = len(s)
    element = s[start:end].strip()
    if element: elements += [element]
    return elements


if __name__ == "__main__":
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,format="[%(levelname)-5s] %(module)s.%(funcName)s: %(message)s")
    from instrumentation import *

    s = "-10us,interleave(-10us,lin_series(-100ps,75ps,25ps)+log_series(100ps,1us,steps_per_decade=4)),-10us"
    s = '-10us,interleave(-10us,log_series(10ms,178ms,steps_per_decade=4)),-10us'
    s = '(-10us,PP=Flythru-48),interleave(-10us,log_series(10ms,178ms,steps_per_decade=4)),-10us'
    s = "(144, S=[110]*5+[101]), (1440, S=[100]*8+[101]), (14400, S=[100]*89+[101])"

    s = "(nan, PLP=Period-48, SEQ=010)*5, (nan, PLP=Period-144, SEQ=100), (264+1*144, SEQ=101), (nan, SEQ=100)*2, (264+4*144, SEQ=101), (nan, SEQ=100)*4, (264+9*144, SEQ=101), (nan, SEQ=100)*8, (264+18*144, SEQ=101), (nan, SEQ=100)*16, (264+35*144, SEQ=101), (nan, SEQ=100)*32, (264+68*144, SEQ=101)"
    ##s = "(-10us, PLP=Flythru-4), -10us, (264, SEQ=1010), 528, 792, 1056, (-10us, SEQ=1111), -10us"
    s = '[enable=011]*4+[enable=111]'
    s = "[(pp=Period-48, enable=010)]*5, (image=0, pp=Period-144, enable=100), (264+1*144, enable=101), [(image=0, enable=100)]*2, (264+4*144, enable=101), (image=0, enable=100)*4, (264+9*144, enable=101), (image=0, enable=100)*8, (264+18*144, enable=101), (image=0, enable=100)*16, (264+35*144, enable=101), (image=0, enable=100)*32, (264+68*144, enable=101)"
    s = '{enable:111}'
    
    ##print('add_dictionaries("hsc=\'H-56\',pp=\'Flythru-4\',seq=\'NIH:i1\',delays=[]")')
    ##print('add_toplevel_dictionary("hsc=\'H-56\',pp=\'Flythru-4\',seq=\'NIH:i1\'")')

    print("x=expand_sequence(sequence_modes.acquisition.value,report=debug)")
    print("x=expand_sequence(scan_configuration.points.value,report=debug)")
    print("x=expand_sequence(temperature_configuration.list.value,report=debug)")
    print("x=expand_sequence(power_configuration.list.value,report=debug)")
    print("x=delay_sequences(delay_configuration.delay_configuration.value,report=debug)")
    print('max(arange(-2,2,0.05))')
