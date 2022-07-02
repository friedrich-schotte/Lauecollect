"""
Author: Friedrich Schotte
Date created: 2021-10-07
Date last modified: 2021-10-07
Revision comment:
"""
__version__ = "1.0"

from numpy import nan


def array2d_from_list2d(ragged_list2d, default_value=nan):
    # VisibleDeprecationWarning: Creating an ndarray from ragged nested sequences (which is a list-or-tuple of lists-or-tuples-or ndarrays with different
    # lengths or shapes) is deprecated. If you meant to do this, you must specify 'dtype=object' when creating the ndarray.
    # https://stackoverflow.com/questions/10346336/list-of-lists-into-numpy-array
    from numpy import array
    width = max(map(len, ragged_list2d))
    regular_list2d = [row + [default_value] * (width - len(row)) for row in ragged_list2d]
    array2d = array(regular_list2d)
    return array2d