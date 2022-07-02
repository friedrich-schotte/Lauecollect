"""
What is the name of a variable or instance?

Authors: Friedrich Schotte, Hyun Sun Cho
Date created: 2019-09-26
Date last modified: 2019-09-26
Python Version: 2.7 and 3.7
"""
__version__ = "1.0"

def variable_name(x):
    """Name of a variable"""
    variable_name = ""
    import inspect
    for frame_info in inspect.stack()[1:]:
        frame = frame_info[0]
        variable_dict = frame.f_globals
        for name in variable_dict:
            if id(variable_dict[name]) == id(x): variable_name = name
    return variable_name


if __name__ == "__main__":
    from pdb import pm
    class A(object): pass
    a = A()
    def f(x): return x
    print("variable_name(a)")
    print("variable_name(f(a))")
