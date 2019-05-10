"""
Date created: 2018-10-02
"""
__version__ = "1.0"

from logging import debug,info,warn,error

def flatten(l):
    """Make a simple list out of list of lists"""
    flattened_list = iterate(flatten1,l)
    return flattened_list

def flatten1(l):
    """Make a simple list out of list of lists"""
    flattened_list = []
    for x  in l:
        if type(x) == list: flattened_list += x
        else: flattened_list += [x]
    return flattened_list

def iterate(function,value):
    """Apply a function of a value repeatedly, until the value does not
    change any more."""
    new_value = function(value)
    while new_value != value:
        value = new_value
        ##debug("%s" % str(value).replace(" ",""))
        new_value = function(value)
    return value
