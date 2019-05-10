"""
This is to create an object object wth a "value" property from an object that
does have a property named differently.
Useful for scanning.

Friedrich Schotte, Apr 27, 2016 - Apr 28, 2016
"""

__version__ = "1.0"

class MotorWrapper(object):
    """An object wth a "value" property."""
    def __init__(self,obj,property_name,unit=""):
        """
        obj: needs to have a property given by the parameter "property_name".
        property_name: string. This property will be accessible as "value" in
        the wrapper object.
        """
        self.obj = obj
        self.property_name = property_name
        self.unit = ""
        
    def get_value(self): return getattr(self.obj,self.property_name)
    def set_value(self,value): setattr(self.obj,self.property_name,value)
    value = property(get_value,set_value)

    @property
    def name(self):
        return repr(self.obj)+"."+self.property_name

    def __repr__(self): return self.name

    

motor_wrapper = MotorWrapper

if __name__ == "__main__":
    from LokToClock import LokToClock
    locked = motor_wrapper(LokToClock,"locked")
    self = locked
