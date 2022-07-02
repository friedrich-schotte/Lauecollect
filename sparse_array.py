"""Author: Friedrich Schotte
Date created: 2015-09-25
Date last modified: 2020-09-02
Revision comment: Fixed: Issue: line 107, in set_elements
    for key in self.content.keys():
    RuntimeError: dictionary changed size during iteration
"""
from logging import debug

__version__ = "1.3.3"

class sparse_array(object):
    """"""
    default_value = 0
    
    def __init__(self,size_or_array,default_value=0):
        """size_or_array: if integer, the length of the array
        """
        self.default_value = default_value
        self.content = {0: self.default_value}
        if hasattr(size_or_array,"__len__"):
            array = size_or_array
            if type(array) == sparse_array:
                self.content.update(array.content)
                self.size = array.size
            else:
                self.size = len(size_or_array)
                self[:] = size_or_array
        else:
            size = size_or_array
            self.size = size

    def __len__(self):
        return self.size

    def __setitem__(self,index,value):
        """Element assignment: e.g. x[2] = 1"""
        ##debug("sparse_array.__setitem__(%r)" % index)
        if type(index) == slice:
            start,stop,step = index.start,index.stop,index.step
            if start is None: start = 0
            if stop is None: stop = len(self)
            if step is None: step = 1
            self.set_elements(start,stop,step,value)
        elif hasattr(index,"__len__") and not hasattr(value,"__len__"):
            ##debug("sparse_array[%d indices] = %r..." % (len(index),value))
            for i in index: self.set_element(i,value)
            ##debug("sparse_array[%d indices] = %r done." % (len(index),value))
        elif hasattr(index,"__len__") and hasattr(value,"__len__"):
            for i in range(0,len(index)):
                self.set_element(index[i],value[i])
        else: self.set_element(index,value)
        self.optimize()

    def __getitem__(self,index):
        """Index: x[2]"""
        from numpy import arange
        i = arange(0,len(self))[index]
        if not hasattr(i,"__len__"): return self.element(i)
        else:
            ##debug("sparse_array[%d indices]..." % len(index))
            values = sparse_array([self.element(j) for j in i])
            ##debug("sparse_array[%d indices] done." % len(index))
            return values

    def element(self,index):
        """"""
        if len(self.content) == 0: return self.default_value
        if index in self.content: return self.content[index]
        n = self.starts
        i = 0
        while i+1 < len(n) and n[i+1] < index: i += 1
        return self.content[n[i]]

    def set_element(self,index,value):
        ##debug("sparse_array.set_element(%r,%r)" % (index,value))
        if index<0 or index>len(self)-1: return
        if index+1 < len(self): next_value = self[index+1]
        if self[index] != value:
            self.content[index] = value
            if index+1 < len(self): self.content[index+1] = next_value

    def optimize(self):
        """Delete unneccessary repeating entries."""
        n = sorted(self.content.keys())
        i,j=0,1
        while i<len(n):
            while j<len(n) and self.content[n[i]]==self.content[n[j]]:
                del self.content[n[j]]
                j += 1
            else:
                i = j
                j = i+1 
                            

    def set_elements(self,start,stop,step,value):
        """start: first element to change, 0-based index
        end: element after last element to change 0-based index
        value: array or scalar"""
        ##debug("sparse_array.set_elements(%r,%r,%r,%r)" % (start,stop,step,value))
        j = 0
        if hasattr(value,"__getitem__"):
            for i in range(start,stop,step):
                self[i] = value[j]
                j += 1
        elif start < stop and step == 1:
            if stop < len(self): next_value = self[stop]
            if self[start] != value: self.content[start] = value
            for key in list(self.content.keys()):
                if start < key < stop: del self.content[key]
            if stop < len(self): self.content[stop] = next_value
        else:
            for i in range(start,stop,step): self[i] = value

    @property
    def starts(self):
        """Indicis of the element where the value changes"""
        return sorted(self.content.keys())

    def __mul__(self,n):
        """Conatenation. Called for array*n
        n: integer
        Result: an n times longer array repeating the content n times."""
        ##debug("sparse_array.__mul__(%r,%r)" % (self,n))
        result = sparse_array(len(self)*n)
        last_value = result[0]
        for i in range(0,n):
            for j in self.starts:
                if self[j] != last_value:
                    result.content[i*len(self)+j] = self[j]
                    last_value = self[j]
        return result

    def __add__(self,value):
        """Numeric addition. Called for array+value
        value: scalar"""
        ##debug("sparse_array.__add__(%r,%r)" % (self,value))
        for i in self.content: self.content[i] += value
        return self

    def __sub__(self,value):
        """Numeric subtraction. Called for array+value
        value: scalar"""
        ##debug("sparse_array.__add__(%r,%r)" % (self,value))
        for i in self.content: self.content[i] -= value
        return self

    def __eq__(self,other):
        """Are two array the same?"""
        equal = False
        if hasattr(other,"content"): equal = self.content == other.content
        elif hasattr(other,"__len__") and len(self) == len(other):
            equal = all([self[i] == other[i] for i in range(0,len(self))])
        return equal

    def __repr__(self):
        """"""
        s = ""
        n = self.starts
        for i in range(0,len(n)-1):
            nrep = n[i+1]-n[i]
            if nrep == 1: s += "[%r]+" % self[n[i]]
            else: s += "[%r]*%d+" % (self[n[i]],nrep)
        if len(self) > 0:
            i = len(n)-1
            nrep = len(self)-n[i]
            if nrep == 1: s += "[%r]" % self[n[i]]
            else: s += "[%r]*%d" % (self[n[i]],nrep)
        if len(self) == 0: s = "[]"
        return s

    def cumsum(self,*args,**kwargs):
        """Cumulative sum"""
        ##debug("sparse_array.cumsum...")
        result = sparse_array(len(self))
        sum = 0
        indices = sorted(self.content.keys())
        ranges = list(zip(indices,indices[1:]+[len(self)]))
        for i,j in ranges:
            inc = self[i]
            ##if inc == 0: result.content[j-1] = sum
            if inc != 0:
                for k in range(i,j):
                    sum += inc
                    result.content[k] = sum
        ##debug("sparse_array.cumsum done.")
        return result

    def clip(self,min,max,*args,**kwargs):
        """Limit range"""
        ##debug("sparse_array.clip...")
        def clip(x,min,max):
            if x < min: x = min
            if x > max: x = max
            return x
        clipped = sparse_array(len(self))
        for i,v in zip(self.content.keys(),self.content.values()):
            clipped.content[i] = clip(v,min,max)
        clipped.optimize()
        ##debug("sparse_array.clip done.")
        return clipped

def starts(array):
    """Indices of the elements where the value changes"""
    if type(array) == sparse_array: return array.starts
    else: return sparse_array(array).starts

if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging; logging.basicConfig(level=logging.INFO)
    from numpy import cumsum,clip,array,asarray
    from time import time
    n = 5500 #55200
    i = range(2,n,50)
    j = range(4,n,50)
    self = sparse_array(n)
    self[i] += 1
    self[j] -= 1
    print('clip(cumsum(asarray(self)),0,1)')
    print('clip(cumsum(self),0,1)')
    print('all(asarray(sparse_array(clip(cumsum(self),0,1))) == asarray(sparse_array(clip(cumsum(asarray(self)),0,1))))')
    print('t=time(); x=sparse_array(clip(cumsum(self),0,1)); time()-t')
    print('t=time(); x=sparse_array(clip(cumsum(asarray(self)),0,1)); time()-t')
