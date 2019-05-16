#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2019-05-14
Date last modified: 2019-05-14
"""
__version__ = "1.0" 

def linear_ranges(values):
    """Break of list of values into lists where the value changes linearly"""
    def close(x,y): return abs(y-x) < 1e-6

    indices = []; support_values = []
    if len(values) > 0:
        indices += [0]; support_values += [values[0]]
    for i in range(0,len(values)):
        is_non_linear = i-1 >= 0 and i+1 < len(values) and \
            not close(values[i-1]-values[i],values[i]-values[i+1])
        if is_non_linear: indices += [i]; support_values += [values[i]]
    if len(values) > 1:
        indices += [len(values)-1]; support_values += [values[len(values)-1]]
    from numpy import array
    indices,support_values = array(indices),array(support_values)
    return indices,support_values
