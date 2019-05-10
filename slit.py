"""Combination motor for slit gap and center, based on motor for individual
blades
Friedrich SChotte, 14 Dec 2010
"""

__version__ = "1.0"

class gap(object):
    def __init__(self,blade1,blade2):
        self.blade1 = blade1
        self.blade2 = blade2

    def get_value(self):
        return self.blade1.value-self.blade2.value
    value = property(get_value)
    

class center(object):
    def __init__(self,blade1,blade2):
        self.blade1 = blade1
        self.blade2 = blade2

    def get_value(self):
        return (self.blade1.value+self.blade2.value)/2
    value = property(get_value)

