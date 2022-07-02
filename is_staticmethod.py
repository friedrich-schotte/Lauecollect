"""
Check if method is static
https://stackoverflow.com/questions/8727059/python-check-if-method-is-static

Author: Friedrich Schotte
Date created: 2022-03-28
Date last modified: 2022-03-28
Revision comment:
"""
__version__ = "1.0"


def is_staticmethod(f):
    import types
    return isinstance(f, types.FunctionType)


if __name__ == '__main__':  # for testing
    class A:
        def f(self):
            return 'this is f'

        @staticmethod
        def g():
            return 'this is g'

        global G
        G = g

    a = A()

    print(f"is_staticmethod({a.f}): {is_staticmethod(a.f)}")
    print(f"is_staticmethod({a.g}): {is_staticmethod(a.g)}")
    print(f"is_staticmethod({G}): {is_staticmethod(G)}")
    print(f"is_staticmethod({G.__func__}): {is_staticmethod(G.__func__)}")
