"""Make a class property that return s a list by modifiable item by item.
Author: Friedrich Schotte
Date created: 2019-07-24
Date last modified: 2019-07-24
"""

__version__ = "1.0"

def list_wrapper(property_object):
    class ListWrapper(object):
        def __init__(self,object,property_object):
            self.object = object
            self.property_object = property_object

        def get_value(self): return self.property_object.fget(self.object)
        def set_value(self,value): self.property_object.fset(self.object,value)
        value = property(get_value,set_value)
        
        def __getitem__(self,i): return self.value[i]
        def __setitem__(self,i,value):
            current_value = self.value
            current_value[i] = value
            self.value = current_value
        def __len__(self): return len(self.value)
        def __iter__(self):
            for i in range(0,len(self)):
                if i < len(self): yield self[i]
        def __repr__(self):
            return "%s(%s,%r)" % (type(self).__name__,self.object,self.property_object)
            
    def get(self): return ListWrapper(self,property_object)
    def set(self,value): get(self)[:] = value
    return property(get,set)

if __name__ == "__main__":
    class Test(object):
        from persistent_property import persistent_property
        value = persistent_property("value",[0,0,0])
        value = list_wrapper(value)
    test = Test()

    print("test.value = [0,0,0]")
    print("test.value[1] = 1")
    print("test.value[:]")
