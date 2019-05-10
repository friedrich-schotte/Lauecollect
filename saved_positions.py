"""
Data base save and recall motor positions
F. Schotte, 29 Nov 2013 - 29 Nov 2019
"""
__version__ = "1.0"
from DB import dbput,dbget
from numpy import nan,asarray

class SavedPositions(object):
    """Data base save and recall motor positions"""
    
    def __init__(self,parent=None,
        name = "goniometer_saved",
        motors = [],
        motor_names = [],
        nrows = 8):
        """name: basename of settings file"""
        self.name = name
        self.motors = motors
        self.motor_names = motor_names
        self.nrows = nrows

    def description(self,row):
        """row: zero-based index"""
        return dbget("%s.line%d.description" % (self.name,row))

    def position(self,row):
        """Saved motor positions.
        row: zero-based index or description string"""
        if not isinstance(row,basestring): return self.position_of_row(row)
        else: return self.position_of_description(row)

    def position_of_row(self,row):
        position = []
        for j in range(0,len(self.motors)):
            position += [tofloat(
                dbget("%s.line%d.%s" % (self.name,row,self.motor_names[j])))]
        return asarray(position)
    
    def position_of_description(self,description):
        for row in range(0,self.nrows):
            if self.description(row) == description:
                return self.position_of_row(row)
        return [nan]*len(self.motor_names)

        
def tofloat(s):
    """Convert string to float and return 'not a number' in case of """
    from numpy import nan
    try: return float(s)
    except Exception: return nan


if __name__ == '__main__': # for testing
    from pdb import pm # for debugging
    from id14 import SampleX,SampleY,SampleZ,SamplePhi
    saved_positions = SavedPositions(
        name="goniometer_saved",
        motors=[SampleX,SampleY,SampleZ,SamplePhi],
        motor_names=["SampleX","SampleY","SampleZ","SamplePhi"],
        nrows=13)
    self = saved_positions # for debugging
    print 'saved_positions.position("Chip 0,0,0,0")'
