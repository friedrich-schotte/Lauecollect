"""
Authors:Friedrich Schotte
Date created: 2020-02-05
Date last modified: 2021-05-26
Revision comment: Fixed: Issue: Read-only, value changes ignored 
"""
__version__ = "1.0.3"


def imported_property(name):
    """name: e.g. 'acquisition.acquisition.temperatures'
    """
    module_name, object_name, property_name = name.split(".")
    from importlib import import_module
    module = import_module(module_name)
    obj = getattr(module, object_name)

    def fget(_self): return getattr(obj, property_name)

    def fset(_self, value): setattr(obj, property_name, value)

    property_object = Imported_Property(fget, fset)
    property_object.name = name
    return property_object


class Imported_Property(property):
    name = ""


if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)


    class Test(object):
        temperatures = imported_property('acquisition.acquisition.temperatures')


    test = Test()
    print("test.temperatures")
