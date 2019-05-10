"""Find the repeat period of an array
Author: Friedrich Schotte
Date created: 2018-05-22
Date last modified: 2018-05-23
"""
__version__ = "1.0"

def period(a):
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
    """Are arrays a and b identical"""
    from numpy import all
    if len(a) != len(b): value = False
    else: value = all(a==b)
    return value

if __name__ == "__main__":
    from numpy import tile
    a = ["a","a","b"]*5
    print("period(a)=%r" % period(a))
    

