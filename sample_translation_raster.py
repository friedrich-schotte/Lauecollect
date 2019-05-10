"""
2D scan of the sample on a regular periodic grid.
For the photocrystallography chip.

Friedrich Schotte, Nov 13, 2013 - Dec 6, 2013
"""
from numpy import *
__version__ = "1.0.3"

from DB import dbput,dbget
from linear_fit import linear_fit_coeff
from logging import debug

class Grid(object):
    """Periodic structure"""
    def get_n(self):
        """Size of the grid"""
        try: value = asarray(eval(dbget("sample_translation_grid.n")))
        except: value = array([8,8,10,10])
        return value
    def set_n(self,value):
        dbput("sample_translation_grid.n",asstring(asarray(value).tolist()))
    n = property(get_n,set_n)

    def get_origin(self):
        """XYZ coordinates of the grid point (0,0,..0).
        3D vector"""
        try: value = asarray(eval(dbget("sample_translation_grid.origin")))
        except: value = array([-4.000,-4.000,0.0])
        return value
    def set_origin(self,value):
        dbput("sample_translation_grid.origin",
            asstring(asarray(value).tolist()))
    origin = property(get_origin,set_origin)

    def get_base_vectors(self):
        """m x (N+1) matrix (m: number of support points, N: number of
        dimensions)"""
        try: value = asarray(eval(dbget("sample_translation_grid.base_vectors")))
        except: value = array([[1.000,0,0],[0,1.000,0],[0.050,0,0],[0,0.05,0]])
        return value
    def set_base_vectors(self,value):
        dbput("sample_translation_grid.base_vectors",
            asstring(asarray(value).tolist()))
    base_vectors = property(get_base_vectors,set_base_vectors)

    def get_support_indices(self):
        """N x 3 matrix (m: number of support points)"""
        s = dbget("sample_translation_grid.support_indices")
        try: value = atleast_2d(eval(s))
        except Exception,details:
            debug("sample_translation_grid.support_indices: %s: %s" % (s,details))
            value = zeros((0,0),dtype=int)
        ndim = len(self.n)
        if value.shape[1] != ndim: value = zeros((0,ndim),dtype=int)
        return value
    def set_support_indices(self,value):
        dbput("sample_translation_grid.support_indices",
            asstring(asarray(value).tolist()))
    support_indices = property(get_support_indices,set_support_indices)

    def get_support_xyz(self):
        """m x 3 matrix (N: number of dimensions)"""
        s = dbget("sample_translation_grid.support_xyz")
        try: value = atleast_2d(eval(s))
        except Exception,details:
            debug("sample_translation_grid.support_xyz: %s: %s" % (s,details))
            value = zeros((0,3))
        if value.shape[1] != 3: value = zeros((0,3))
        return value
    def set_support_xyz(self,value):
        dbput("sample_translation_grid.support_xyz",
            asstring(asarray(value).tolist()))
    support_xyz = property(get_support_xyz,set_support_xyz)

    def add_support_point(self,indices,xyz):
        """indices: array of n 0-based integers (e.g. n=4)
        xyz: array of three floating point values"""
        self.remove_support_indices(indices)
        self.remove_support_xyz(xyz)
        self.support_indices = concatenate((self.support_indices,[indices]))
        self.support_xyz     = concatenate((self.support_xyz,[xyz]))
        self.fit()

    def remove_support_indices(self,indices):
        """indices: array of n 0-based integers (e.g. n=4)"""
        keep = ~all(self.support_indices == indices,axis=1)
        self.support_indices = self.support_indices[keep]
        self.support_xyz = self.support_xyz[keep]
        self.fit()

    def has_support_indices(self,indices):
        """indices: array of n 0-based integers (e.g. n=4)"""
        return any(all(indices == self.support_indices,axis=1))

    def remove_support_xyz(self,xyz):
        """xyz: array of three floating point values"""
        keep = ~all(self.support_xyz == xyz,axis=1)
        self.support_indices = self.support_indices[keep]
        self.support_xyz[keep]

    def clear_support_points(self):
        ndim = len(self.n)
        self.support_indices = zeros((0,ndim))
        self.support_xyz = zeros((0,3))

    def get_Ip(self):
        """Matrix of support point indices (I) with all ones as the first column.
        Ip and Bp are related by the equation: Ip.Bp = support_xyz
        m x (N+1) matrix (m: number of support points, N: number of dimensions)"""
        I = self.support_indices
        n = len(self.support_indices)
        Ip = column_stack((ones(n),I))
        return Ip
    Ip = property(get_Ip)

    def get_Bp(self):
        """Origin (o) and base vectors (B) as a single matrix.
        The origin is in the first row.
        Ip and Bp are related by the equation: Ip.Bp = support_xyz
        (N+1) x 3 matrix (N: number of dimensions)"""
        b = self.base_vectors
        o = self.origin
        Bp = row_stack((o,b))
        return Bp
    def set_Bp(self,Bp):
        self.origin = Bp[0]
        self.base_vectors = Bp[1:]
    Bp = property(get_Bp,set_Bp)

    @property
    def fit_Bp(self):
        """Calculate the grid parameters from the support points"""
        Ip = self.Ip
        R = self.support_xyz
        Bp = linear_fit_coeff(R.T,Ip.T).T
        return Bp

    @property
    def has_sufficient_support_points(self):
        """Are there sufficient support points to calculate the grid
        parameters?"""
        return not any(isnan(self.fit_Bp))

    def fit(self):
        """Calculate the grid parameters from the support points"""
        Bp = self.fit_Bp
        if not any(isnan(Bp)): self.Bp = Bp

    @property
    def indices(self):
        """0-based integer coordinates all grid points
        (n[0]*n[1]*...*n[N-1]) x N array of 0-based integers"""
        return index_list(self.n)

    @property
    def xyz(self):
        """Positions of all grid points"""
        return self.xyz_of_indices(self.indices)

    def xyz_of_indices(self,indices):
        """XYZ coordinates of all grid points
        indices: ? x N array of 0-based integers"""
        o = self.origin
        B = self.base_vectors
        i = asarray(indices)
        R = o + dot(B.T,i.T).T
        return R

    @property
    def npoints(self):
        """total number of grid points"""
        return product(self.n)

    def point(self,i):
        """i: 0-based index"""
        return self.xyz[i%self.npoints,:]
        
    
grid = Grid()


def asstring(x):
    return repr(x).replace("\n","")

def index_list(dimensions):
    """All indices of all the element of an N x M x ... array
    dimensions: tuple (M,N,...)"""
    return indices(dimensions).reshape(len(dimensions),product(dimensions)).T


def calibrate_grid_from_saved_positions():
    """Use 'saved motor positons' panel to get calirbation points"""
    from fast_diffractometer_saved_positions import saved_positions
    grid.clear_support_points()
    for i in range(0,saved_positions.nrows):
        description = saved_positions.description(i)
        if description.startswith("Chip "):
            indices = eval(description.replace("Chip ",""))
            xyz = saved_positions.position(i)[0:3]
            grid.add_support_point(indices,xyz)
    if not grid.has_sufficient_support_points:
        print("grid: insufficient support points")
    grid.fit()

if __name__ == "__main__":
    """for testing"""
    self = grid # for debugging
    def debug(x): print(x) # for debugging
    def xyz(description): return saved_positions.position(description)[0:3]
    from id14 import SampleX,SampleY,SampleZ
    def current_xyz(): return SampleX.value,SampleY.value,SampleZ.value
    def goto((x,y,z)): SampleX.value,SampleY.value,SampleZ.value = x,y,z

    print 'grid.n = [8,8,6,6]'
    print 'calibrate_grid_from_saved_positions()'
    print 'grid.support_indices'
    print 'grid.support_xyz'
    print 'grid.has_sufficient_support_points'
    print 'grid.origin'
    print 'grid.base_vectors'
    print 'goto(grid.point(0))'
    print 'goto(grid.xyz_of_indices([0,0,0,0]))'
    print 'goto(grid.xyz_of_indices([5,5,5,5]))'
    print """grid.base_vectors = array([
       [0, 2.000, 0    ],
       [0, 0    , 2.000],
       [0, 0.178, 0    ],
       [0, 0    , 0.178]])"""
    print "grid.origin = array([-3.461,-7.170,-6.396])"
