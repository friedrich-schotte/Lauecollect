"""
based on:
http://stackoverflow.com/questions/5189699/how-to-make-a-class-property
Date created: 2018-10-10
Date last modified: 2018-10-10
Author: Mahmoud Abdelkader (mahmoudimus.com)
"""
from logging import debug,info,warn,error

class ClassPropertyMetaClass(type):
    def __setattr__(self, key, value):
        if key in self.__dict__:
            obj = self.__dict__.get(key)
        if obj and type(obj) is ClassPropertyDescriptor:
            return obj.__set__(self, value)

        return super(ClassPropertyMetaClass, self).__setattr__(key, value)

class ClassPropertyDescriptor(object):

    def __init__(self, fget, fset=None):
        self.fget = fget
        self.fset = fset

    def __get__(self, obj, klass=None):
        if klass is None:
            klass = type(obj)
        return self.fget.__get__(obj, klass)()

    def __set__(self, obj, value):
       if not self.fset:
           raise AttributeError("can't set attribute")
       import inspect
       if inspect.isclass(obj):
           type_ = obj
           obj = None
       else:
           type_ = type(obj)
       return self.fset.__get__(obj, type_)(value)

    def setter(self, func):
        if not isinstance(func, (classmethod, staticmethod)):
            func = classmethod(func)
        self.fset = func
        return self

def classproperty(func):
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)

if __name__ == '__main__': # for testing
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    
    class Bar(object):
    ##class Bar(metaclass=ClassPropertyMetaClass): # Python 3+
        __metaclass__ = ClassPropertyMetaClass # Python 2.7
        _bar = 1
        @classproperty
        def bar(cls):
            return cls._bar
        @bar.setter
        def bar(cls, value):
            debug("%r" % value)
            cls._bar = value
    foo = Bar()
    print("Bar.bar = 2")

