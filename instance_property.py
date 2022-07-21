#!/usr/bin/env python
"""
Date created: 2022-07-10
Date last modified: 2022-07-10
Revision comment:
"""
__version__ = "1.0"

import logging


class instance_property(property):
    def __init__(self, data_type, *args, **kwargs):
        self.data_type = data_type
        self.args = args
        self.kwargs = kwargs
        super().__init__(fget=self.get_data_object)

    def get_data_object(self, instance):
        from reference_info import reference_info
        return reference_info(self.reference(instance), self.data_type, instance, *self.args, **self.kwargs)

    def reference(self, instance):
        from reference import reference
        return reference(instance, self.get_name(instance))

    def get_name(self, instance):
        if not self.__property_name__:
            class_object = type(instance)
            for name in dir(class_object):
                if getattr(class_object, name) == self:
                    break
            else:
                logging.warning(f"Could not find {self} in {class_object}")
                name = "unknown"
            self.__property_name__ = name
        return self.__property_name__

    __property_name__ = ""


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    class Test_Object:
        @instance_property
        class child:
            def __init__(self, parent):
                self.parent = parent

    self = Test_Object()
