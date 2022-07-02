"""Save division without rasing an exception using IEEE floating point
rules to signal division by zero.
Author: Friedrich Schotte
Date created: 2019-11-14
Date last modified: 2019-11-14
"""
__version__ = "1.0"

from logging import debug,info,warn,error

def div(nominator,denominator):
    """Save division without rasing an exception using IEEE floating point
    rules to signal division by zero
    """
    if denominator == 0:
        from numpy import nan,inf
        result = nan
        if nominator == 0: result = nan
        if nominator > 0: result = inf
        if nominator < 0: result = -inf
    else: result = nominator / denominator
    return result 

if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging 
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    )
    print("div(0,0)")
    print("div(1,0)")
    print("div(-1,0)")

