#!/usr/bin/env python
from CA import Record,caget,caput,cainfo
from numpy import *
from time import sleep,time
from logging import info
import logging; logging.basicConfig(level=logging.INFO)

array_test = Record("NIH:TEST")
ensemble = Record("NIH:ENSEMBLE")

def assign_element(record,name,index,value):
    t0 = time()
    x = getattr(record,name)
    while x is None: x = getattr(record,name); sleep(0.1)
    x[index] = value
    setattr(record,name,x)
    while not nan_equal(getattr(record,name),x): sleep(0.1)
    info("%s.%s[%d]=%r: %.3f s" % (record,name,index,value,time()-t0))

def nan_equal(a,b):
    """Are two arrays containing nan identical, assuming nan == nan?"""
    from numpy import asarray
    from numpy.testing import assert_equal
    a,b = asarray(a),asarray(b)
    try: assert_equal(a,b)
    except: return False
    return True

print 'array_test.X'
print 'array_test.X = ones(len(test.X))'
print 'assign_element(test,"X",-1,-0.9)'
print 'assign_element(test,"Y",-1,-1)'
print 'assign_element(ensemble,"floating_point_registers",-1,-0.9)'
print 'assign_element(ensemble,"integer_registers",-1,-4)'
