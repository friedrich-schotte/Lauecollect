"""For Lauecollect logfile.
Select a subset of a dataset, based on filename and the repeat numbers of
collection variables.

Author: Friedrich Schotte
Date created: 2018-12-12
Date last modified: 2018-12-12
"""
__version__ = "1.1"

def image_numbers(logfile,name="",repeat_count=[]):
    """Select a subset of a dataset based on critria, such a file name and repeat counts
    logfile: table object, must have attributes "file",Temperature","Delay"
    name: part of the image filname, e.g. "_offWT"
    repeat_count: e.g. [["Temperature",1],["Delay",0]]
        meaning second repeat of Temperature, first repeat of Delay
    Return value: 0-based image numbers
    """
    from numpy import where
    i = where(logfile.file.find(name) >= 0)[0]
    for (column,n) in repeat_count:
        repeat = repeat_number(getattr(logfile,column)[i])
        i = i[repeat == n]
    return i

def repeat_number(a):
    """Array of 0-based indices for each element of array a.
    a: numpy array
    """
    from numpy import arange
    repeat_number = arange(0,len(a))/period(a)
    return repeat_number

def period(a):
    """Length of the longest repeating sequence in the array a."""
    N = len(a)
    n = 1
    for n in range(1,N):
        if a[n] != a[0]: n+=1; continue
        for i in range(0,N,n):
            l = min(n,N-i)
            if not identical(a[i:i+l],a[0:l]): break
        if not identical(a[i:i+l],a[0:l]): continue
        break
    return n

def identical(a,b):
    """Are arrays a and b identical?"""
    from numpy import all
    if len(a) != len(b): value = False
    else: value = all(a==b)
    return value


if __name__ == "__main__": # usage example
    ##filename = "/net/femto-data/C/Data/2018.10/WAXS/PYP/PYP-cw-delay-temp-1/PYP-cw-delay-temp-1.log"
    filename = "/net/femto-data/C/Data/2018.10/WAXS/Water/Water-ramp-5/Water-ramp-5.log"
    from table import table
    logfile = table(filename,separator="\t")

    # Which image numbers in the subset containing "_offWT" in the filename,
    # correspond to the first repeat of the time delays in the second repeat
    # of the temperatures?
    i = image_numbers(logfile,name="_offWT",repeat_count=[["Temperature",1],["Delay",0]])
