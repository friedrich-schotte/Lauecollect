"""Are two Python objects considered the same?

Author: Friedrich Schotte
Date created: 2019-01-39
"""
__version__ = "1.0.1" # allclose too relaxed

def same(x,y):
    """Are two Python objects considered the same?"""
    try:
        if x == y: return True
    except: pass
    try:
        from numpy import isnan
        if isnan(x) and isnan(y): return True
    except: pass
##    try:
##        from numpy import allclose
##        if allclose(x,y): return True
##    except: pass    
    return False
