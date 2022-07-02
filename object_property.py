"""
This is to import selected properties from one class object into another,
avoiding the ambiguities and conflicts of multiple inheritance.

Usage:
    
class A(object):
    name = "A"
a = A()

class B(object):
    name = object_property(a, "name")
b = B()

In[1]: b.name
Out[1]: 'A'

Author: Friedrich Schotte
Date created: 2020-03-19
Date last modified: 2020-09-03
Revision comment: Updated example
"""
__version__ = "1.0.1"

def object_property(object,name):
    def get(self): return getattr(object,name)
    def set(self,value): setattr(object,name,value)
    return property(get,set)

if __name__ == "__main__":
    class A(object):
        name = "A"
    a = A()

    class B(object):
        name = object_property(a, "name")
    b = B()

    print("b.name")
