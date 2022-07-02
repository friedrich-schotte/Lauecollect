"""
Author: Friedrich Schotte
Date created: 2022-04-07
Date last modified: 2022-05-03
Revision comment: Relaxed argument names check
"""
__version__ = "1.1.1"

import logging


class PV_record_property(property):
    from cached_function import cached_function

    def __init__(self, property_type=None, type_name=None):
        if property_type is not None:
            self.property_type = property_type
        if type_name is not None:
            self.type_name = type_name
        property.__init__(self, self.get_property)

    property_type = None
    type_name = None

    @property
    def type(self):
        if self.property_type is not None:
            my_type = self.property_type
        elif self.type_name is not None:
            module_name = self.type_name
            module = __import__(module_name)
            my_type = getattr(module, self.type_name)
        else:
            my_type = type(None)
        return my_type

    def get_property(self, instance):
        from function_argument_names import function_argument_names
        argument_names = function_argument_names(self.type)
        if "prefix" in argument_names:
            base_name = self.get_name(instance)
            prefix = f"{instance.prefix}.{base_name.upper()}"
            obj = self.type(prefix=prefix)
        elif len(argument_names) == 2:
            base_name = self.get_name(instance)
            obj = self.type(instance, base_name)
        else:
            obj = self.type(instance)
        return obj

    @cached_function()
    def get_name(self, instance):
        class_object = type(instance)
        for name in dir(class_object):
            if getattr(class_object, name) == self:
                break
        else:
            logging.warning(f"Could not find {self} in {class_object}")
            name = "unknown"
        return name


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)
