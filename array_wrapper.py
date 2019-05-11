"""
Numpy array like interface
Friedrich Schotte, 27 Jun 2014 - 9 Feb 2016
"""
__version__ = "1.2.1" # repr,str

from numpy import ndarray
from logging import debug,info,warn,error

class ArrayWrapper(ndarray):
    """Numpy array interface"""
    def __init__(self,object,name,method="single",**keyword_arguments):
        """object must have the following methods
        get_<name>(i): returns value of i-th array element
        set_<name>(i,value): changes i-th array element
        <name>_count(): return number of elements, highest allowed i minus 1
        method: "single":   get_<name>,set_<name> accept single value
                "multiple": get_<name>,set_<name> accept arrays of values
        """
        ##debug("ArrayWrapper.__init__(%r,%r)" % (object,name))
        self.object = object
        self.name = name
        self.method = method

    def __new__(subclass,*args,**keyword_arguments):
        ##debug("ArrayWrapper.__new__(%r,%r,%r)" % (subclass,args,keyword_arguments))
        # Called by Python before __init__ when creating a new array object of
        # this type.
        # The remaining arguments after 'subclass' are used only by '__init__'.
        ##debug("table.__new__(subclass=%r,%r" % (subclass,keyword_arguments))
        dtype = keyword_arguments["dtype"] if "dtype" in keyword_arguments else float 
        self = ndarray(0,dtype=dtype)
        # To get an ndarray subclass that owns its own data, copy() must be
        # called. Otherwise, "resize" will fail. ("cannot resize this array:
        # it does not own its data")
        return self.view(subclass).copy()

    def __array_finalize__(self,source):
        """Called after on object of this class has been copied.
        Passes non-array attributes from the original to the new object."""
        ##debug("__array_finalize__(id%r%r,id%r%r)" % (id(self),type(self),id(source),type(source)))
        if hasattr(source,"object"): self.object = source.object
        if hasattr(source,"name"  ): self.name   = source.name
        if hasattr(source,"method"): self.method = source.method

    def get(self,index):
        """index: 0-based integer count"""
        get = getattr(self.object,"get_"+self.name)
        return get(index)

    def set(self,index,value):
        """index: 0-based integer count
        value: new value to assigne to the i-th element, with i = index
        """
        set = getattr(self.object,"set_"+self.name)
        set(index,value)

    def get_values(self,indices):
        """indices: list of 0-based integers"""
        ##debug("array_wrapper: get_values(%r)" % (indices,))
        from numpy import asarray
        get = getattr(self.object,"get_"+self.name)
        if self.method == "multiple": values = get(self.tolist(indices))
        if self.method == "single": values = [get(i) for i in self.tolist(indices)]
        if self.method == "all": values = asarray(get())[indices]
        values = asarray(values)
        if not hasattr(indices,"__len__") and type(indices) != slice:
            ##debug("array_wrapper: get_values(%d): converting %r to scalar" % (indices,values))
            if hasattr(values,"shape") and values.shape == (): # 0-dim numpy array
                if "float" in str(values.dtype): values = float(values)
                elif "int" in str(values.dtype): values = int(values)
            else:
                if hasattr(values,"__len__") and len(values) == 1: values = values[0]
        return values

    def set_values(self,indices,values):
        """index: 0-based integer count
        value: new value to assign to the i-th element, with i = index
        """
        ##debug("array_wrapper: set_values(%r)" % (indices,))
        from numpy import asarray
        set = getattr(self.object,"set_"+self.name)
        if not hasattr(indices,"__len__") and type(indices) != slice:
            index = indices
            if self.method == "multiple":
                # Index might be negative, meaning counting from the end.
                index = range(0,len(self))[index] 
                set([index],values)
            if self.method == "single":
                # Index might be negative, meaning counting from the end.
                index = range(0,len(self))[index] 
                set(index,values)
            if self.method == "all":
                get = getattr(self.object,"get_"+self.name)
                all_values = asarray(get())
                all_values[index] = values
                set(all_values)
        else:
            if self.method == "multiple": set(self.tolist(indices),values)
            elif self.method == "single":
                for i,value in zip(self.tolist(indices),values): set(i,value)
            elif self.method == "all":
                get = getattr(self.object,"get_"+self.name)
                all_values = asarray(get())
                all_values[indices] = values
                set(all_values)
        
    def tolist(self,index):
        """Convert index (which may be a slice) to a list"""
        from numpy import atleast_1d,arange
        index_list = atleast_1d(arange(0,len(self))[index])
        ##debug("tolist: converted %r to %r" % (index,index_list))
        return index_list

    def count(self):
        """Number of elements in the array"""
        if hasattr(self.object,self.name+"_count"):
            count = getattr(self.object,self.name+"_count")
            if hasattr(count,"__call__"): count = count()
        elif hasattr(self.object,"get_"+self.name+"_count"):
            count = getattr(self.object,"get_"+self.name+"_count")()
        elif self.method == "all":
            obj = getattr(self.object,"get_"+self.name)()
            count = len(obj)
        else: count = 0
        return count

    def __getitem__(self,index):
        """Called when [0] is used.
        index: integer or list/array of intergers or array of booleans"""
        ##debug("ArrayWrapper.__getitem__(%r)" % (index,))
        return self.get_values(index)

    def __setitem__(self,index,value):
        """Called when [0]= is used.
        index: single index, slice or list of indices
        value: single value or array of values"""
        ##debug("ArrayWrapper.__setitem__(%r,%r)" % (index,value))
        self.set_values(index,value)

    def __getslice__(self,i,j):
        """Called when [i:j] is used."""
        ##debug("%r.__getslice__(%r,%r)" % (type(self),i,j))
        # Handle the case x[0:].
        if j >= 2**31-1: j = len(self)
        return self.get_values(slice(i,j))

    def __setslice__(self,i,j,values):
        """Called when [i:j] is used."""
        ##debug("%r.__setslice__(%r,%r,%r)" % (type(self),i,j,values))
        if j >= 2**31-1: j = len(self) # if j omitted [0:]
        from numpy import asarray,arange,zeros
        # Handle the case case x[0:6] = 0.
        values = asarray(values)
        all_values = zeros(self.count(),dtype=values.dtype)
        all_values[slice(i,j)] = values
        values = all_values[slice(i,j)]
        self.set_values(range(i,j),values)

    def __len__(self): return self.count()

##    def __getattr__(self,name):
##        """Called when '.' is used."""
##        debug("ArrayWrapper.__getattr__(%r)" % name)
##        return ndarray.__getattribute__(self,name)

    def get_size(self): return len(self)
    size = property(get_size)

    def get_shape(self):
        if self.method == "all":
            obj = getattr(self.object,"get_"+self.name)()
            return obj.shape
        return (len(self),)
    shape = property(get_shape)

    def __repr__(self):
        return repr(self[:])

    def _str__(self):
        return str(self[:])

# turn off debugging
##def debug(message): pass

    
if __name__ == "__main__":
    from pdb import pm
    from logging import debug
    import logging; logging.basicConfig(level=logging.DEBUG)
    from Ensemble_registers import Ensemble_registers
    from Ensemble import Ensemble,ensemble_driver
    ensemble = Ensemble()
    positions = ArrayWrapper(ensemble,"position")
    command_dial_values = ArrayWrapper(ensemble,"command_dial_values",
        method="multiple")
    floating_point_variables =\
        ArrayWrapper(ensemble,"floating_point_variables",method="multiple")

