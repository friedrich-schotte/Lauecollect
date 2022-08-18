#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-06-18
Date last modified: 2021-06-20
Revision comment: Added: __dir__
"""
__version__ = "1.2"


class Domains(object):
    def __init__(self, globals=None, locals=None):
        self.globals = globals
        self.locals = locals

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("%s has not attribute %r" % (self, name))
        return self.domain(name)

    def __call__(self, name): return self.domain(name)

    from cached_function import cached_function

    @cached_function()
    def domain(self, name):
        return Domain(name, self.globals, self.locals)


domain = Domains()


class Domain:
    def __init__(self, domain_name, globals=None, locals=None):
        self.domain_name = domain_name
        if globals is not None: self.globals = globals
        if locals is not None: self.locals = locals

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.domain_name)

    def __getattr__(self, name):
        if name.startswith("__") and name.endswith("__"):
            raise AttributeError("%s has not attribute %r" % (self, name))
        obj = eval(name, self.globals, self.locals)
        try:
            obj = obj(self.domain_name)
        except TypeError:
            pass
        return obj

    def get_globals(self):
        if not hasattr(self, "__globals__") or self.__globals__ is None:
            exec("from instrumentation import *")  # -> globals()
            self.__globals__ = globals()
        return self.__globals__

    def set_globals(self, value):
        self.__globals__ = value

    globals = property(get_globals, set_globals)

    def get_locals(self):
        if not hasattr(self, "__locals__") or self.__locals__ is None:
            exec("from instrumentation import *")  # -> locals()
            self.__locals__ = locals()
        return self.__locals__

    def set_locals(self, value):
        self.__locals__ = value

    locals = property(get_locals, set_locals)

    def __dir__(self):
        return sorted(set(self.names + list(super().__dir__()) + list(self.__dict__.keys())))

    @property
    def names(self):
        return list(self.locals.keys())


if __name__ == "__main__":
    BioCARS = domain("BioCARS")
    LaserLab = domain("LaserLab")

    print("domain.BioCARS")
    print("BioCARS.timing_system")
    print("BioCARS.acquisition")
    print("BioCARS.camera_controls.MicroscopeCamera")
