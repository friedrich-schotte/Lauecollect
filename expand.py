"""
Author: Friedrich Schotte
Date created: 2022-05-04
Date last modified: 2022-05-05
Revision comment:
"""
__version__ = "1.0"

import logging


def expand(s, report=None):
    if report:
        report(format_report("Original", s))
    operations = [
        quote_binary_numbers,
        quote_strings,
        replace_off,
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
            if report:
                report(format_report(name(operation), s))
    return s


def name(operation): return operation.__name__.replace("_", " ").capitalize()


def format_report(name, s):
    from split_list import split_list
    return name + "\n" + ",\n".join(split_list(s)) + "\n"


def expand_SI_units(s):
    from re import sub
    SI_prefixes = {"p": "e-12", "n": "e-9", "u": "e-6", "m": "e-3"}
    for p in SI_prefixes:
        s = sub("([0-9])" + p, r"\1" + SI_prefixes[p], s)
    s = sub("([0-9])s", r"\1", s)
    return s


def add_toplevel_dictionary(s):
    from re import sub
    keyword = r"[a-zA-Z_]+"
    s = sub("^(" + keyword + "=.*)", r"dict(\1)", s)
    return s


def quote_binary_numbers(s):
    """ S=001 -> S='101' """
    from re import sub
    # S=001 -> S='101'
    s = sub(r"(^|[=:\[({])([01X]{3,5})([ ,=:*\])}]|$)", r"\1'\2'\3", s)
    # (...)(...)(...) defining three groups: pre-match, substitute, post-match
    # ^|[=\[({]) = begin of string or any of the characters =, colon, [, (, or {
    # [01]{3,5} = 0 or 1, repeated 3 to 5 times
    # [ ,=:*\])}]|$ = any of the characters space, comma, colon, ], ), }, or end of string
    # \1 \2 \3, matching groups defined by grouping parentheses (...)(...)(...)
    return s


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


def replace_off(s):
    s = s.replace("off", "nan")
    return s


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


def fix_repeat_syntax(s):
    """Sequences(nan,SEQ='100')*32 -> [Sequences(nan,SEQ='100')]*32"""
    from re import sub
    from split_list import split_list
    T = split_list(s)
    for i in range(0, len(T)):
        t = T[i]
        t = sub(r"^(.*\(.*\))\*([0-9]+)$", r"[\1]*\2", t)
        T[i] = t
    s = ", ".join(T)
    return s


def expand_generators(s):
    from flatten import flatten
    t = eval("[" + s + "]")
    t = flatten(t)
    s = repr(t).strip("[]")
    return s


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    print('expand("enable=1X1")')
    print('expand("enable=[011]*2+[111], circulate=[1]")')
