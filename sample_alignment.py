"""
Interface to visual sample alignment using the camera image.
Friedrich Schotte, 6 Oct 2010 - 31 Jan 2016
"""
from diffractometer import diffractometer

__version__ = "1.7"

class Sample(object):
    """Subsystem for sample alignment"""
    def __init__(self):
        # settings
        self.settings = Settings()

    @property
    def spot_zs(self):
        """Diffracometer Z positions at which support points were entered"""
        Zs = []
        for s in self.samples:
            Zs += [diffractometer.z_of_sample(s["start"][2])]
            Zs += [diffractometer.z_of_sample(s["end"][2])]
        return Zs

    zs = spot_zs

    @property
    def mark_zs(self):
        """Diffracometer Z positions at which support points where entered"""
        from numpy import array,unique,isnan
        if len(self.support_points) == 0: # MarKk sample start and end
            Z = []
            sx1,sy1,sz1 = self.sample_start
            sx2,sy2,sz2 = self.sample_end
            z1,z2 = self.calibration_z + sz1,self.calibration_z + sz2            
            if not isnan(z1): Z += [z1]
            if not isnan(z2): Z += [z2]
        else: # Define edge
            PHI,X,Y,Z,OFFSET = array(self.support_points).T
        Z = unique(Z)
        return Z

    def get_spot_phis(self):
        """Diffracometer Z positions at which support points where entered"""
        from numpy import array,unique
        support_points = self.support_points
        if len(support_points) == 0:
            return array([0.0])
        else:
            PHI,X,Y,Z,OFFSET = array(support_points).T
            return unique(PHI)
    spot_phis = property(get_spot_phis)
                              
    def visual_center_offset(self,phi,z):
        """The returned offset is with respect to the center of the sample
        as defined by visual click centering."""
        offset1 = self.visual_edge_offset(phi,z)
        offset2 = self.visual_edge_offset(phi+180,z)
        return (offset1-offset2)/2

    def xray_scan_start_offset(self,phi,z):
        """The X-ray alignment scan starts outside the sample, in sufficient
        distance not to hit the sample.
        The returned offset is with respect to the center of the sample
        as defined by visual click centering."""
        return self.visual_edge_offset(phi,z)+self.xray_scan_clearance

    def visual_edge_offset(self,phi,z):
        """Interpolated offset as function of phi and z, using measured
        support points.
        The returned offset is with respect to the center of the sample
        as defined by visual click centering."""
        from numpy import nan,array,concatenate
        if len(self.support_points) == 0: # Mark Sample
            sx1,sy1,sz1 = self.sample_start
            sx2,sy2,sz2 = self.sample_end
            z1,z2 = self.calibration_z + sz1,self.calibration_z + sz2
            cx,cy = self.click_center_x,self.click_center_y
            sdx1,sdy1 = sx1-cx,sy1-cy
            sdx2,sdy2 = sx2-cx,sy2-cy
            dx1,dy1 = self.diffractometer_dxdy(sdx1,sdy1,phi)
            dx2,dy2 = self.diffractometer_dxdy(sdx2,sdy2,phi)
            dy = interpolate([[z1,dy1],[z2,dy2]],z)
            offset = dy + self.sample_r
            return -offset
        else: # Define Edge
            PHI,X,Y,Z,OFFSET = array(self.support_points).T
            PHI = concatenate((PHI-360,PHI,PHI+360))
            Z = concatenate((Z,Z,Z))
            OFFSET = concatenate((OFFSET,OFFSET,OFFSET))
            phi = phi % 360
            offset = interpolate_2D(PHI,Z,OFFSET,phi,z)
            return -offset

    def diffractometer_dxdy(self,sx,sy,phi):
        """Sample position with respect to the intersection of laser and X-ray
        beam.
        sx,sy: point on sample the with respect to the rotation axis at phi=0
        phi: spidle angle
        Return value: (dx,dy,dz)
        dx: horizontal along x-ray beam
        dy: vertical
        """
        from numpy import sin,cos,radians,degrees,arctan2,sqrt
        r = sqrt(sx**2+sy**2)
        phi0 = degrees(arctan2(-sy,sx)) % 360
        phi1 = phi0 + phi
        dx = -r*cos(radians(phi1))
        dy =  r*sin(radians(phi1))
        return dx,dy

    def get_support_points(self):
        """List if (phi,x,y,z,offset) tuples"""
        self.settings.read()
        return self.settings.support_points
    def set_support_points(self,value):
        self.settings.support_points = value
        self.settings.save()
    support_points = property(get_support_points,set_support_points)

    def get_samples(self):
        """Starting and ending points of the center lines for each sample
        marked on the camera image"""
        self.settings.read()
        return self.settings.samples
    def set_samples(self,value):
        self.settings.samples = value
        self.settings.save()
    samples = property(get_samples,set_samples)    

    def get_sample_r(self):
        """Sample radius as marked on the camera"""
        self.settings.read()
        return self.settings.sample_r
    def set_sample_r(self,value):
        self.settings.sample_r = value
        self.settings.save()
    sample_r = property(get_sample_r,set_sample_r)    

    def get_sample_start(self):
        """Start of crystal center line, defined by mouse click.
        (x,y,z) relative coordonates
        x,y relative to rotation center at phi=0
        z relatize to "calibraion_z"
        """
        self.settings.read()
        return self.settings.sample_start
    def set_sample_start(self,value):
        self.settings.sample_start = value
        self.settings.save()
    sample_start = property(get_sample_start,set_sample_start)

    def get_sample_end(self):
        """End of crystal center line, defined by mouse click.
        (x,y,z) relative coordonates in mm
        x,y relative to rotation center at phi=0
        z relatize to "calibraion_z"
        """
        self.settings.read()
        return self.settings.sample_end
    def set_sample_end(self,value):
        self.settings.sample_end = value
        self.settings.save()
    sample_end = property(get_sample_end,set_sample_end)

    def get_sample_r(self):
        """Radius for the outline of the sample defined by mouse click,
        in mm"""
        self.settings.read()
        return self.settings.sample_r
    def set_sample_r(self,value):
        self.settings.sample_r = value
        self.settings.save()
    sample_r = property(get_sample_r,set_sample_r)

    def get_calibration_z(self):
        """List of (phi,x,y,z,offset) tuples"""
        self.settings.read()
        return self.settings.calibration_z
    def set_calibration_z(self,value):
        self.settings.calibration_z = value
        self.settings.save()
    calibration_z = property(get_calibration_z,set_calibration_z)

    def get_center(self):
        """Click centering X,Y,Z"""
        self.settings.read()
        x,y,z = 0,0,self.settings.click_center_z
        return x,y,z
    def set_center(self,(x,y,z)):
        self.settings.click_center_z = z
        self.settings.save()
    center = property(get_center,set_center)

    def get_click_center_x(self):
        """Offset of the sample (as marked by a mouse click) from the
        rotation axis in x direction at phi = 0."""
        self.settings.read()
        value = self.settings.click_center_x
        return value
    def set_click_center_x(self,value):
        self.settings.click_center_x = value
        self.settings.save()
    click_center_x = property(get_click_center_x,set_click_center_x)

    def get_click_center_y(self):
        """Offset of the sample (as marked by a mouse click) from the
        rotation axis in y direction at phi = 0."""
        self.settings.read()
        value = self.settings.click_center_y
        return value
    def set_click_center_y(self,value):
        self.settings.click_center_y = value
        self.settings.save()
    click_center_y = property(get_click_center_y,set_click_center_y)

    def get_click_center_z(self):
        """Offset of the sample (as marked by a mouse click) from the
        rotation axis in y direction at phi = 0."""
        self.settings.read()
        value = self.settings.click_center_z
        return value
    def set_click_center_z(self,value):
        self.settings.click_center_z = value
        self.settings.save()
    click_center_z = property(get_click_center_z,set_click_center_z)

    def get_grid_spacing(self):
        """Horizontal spacing on Diffracometer Z direction used on camera image, in mm"""
        self.settings.read()
        return self.settings.GridSpacing
    def set_grid_spacing(self,value):
        self.settings.GridSpacing = value
        self.settings.save()
    grid_spacing = property(get_grid_spacing,set_grid_spacing)

    def get_xray_scan_clearance(self):
        """Horizontal spacing on Diffracometer Z direction used on camera image, in mm"""
        self.settings.read()
        return self.settings.xray_scan_clearance
    def set_xray_scan_clearance(self,value):
        self.settings.xray_scan_clearance = value
        self.settings.save()
    xray_scan_clearance = property(get_xray_scan_clearance,set_xray_scan_clearance)

    def get_zmin(self):
        """Diffracometer Z translation range for data collection.
        Defined as range over which support points have been entered"""
        if len(self.mark_zs) == 0: return diffractometer.Z.command_value
        return min(self.mark_zs)
    zmin = property(get_zmin)

    def get_zmax(self):
        """Diffracometer Z translation range for data collection.
        Defined as range over which support points have been entered"""
        if len(self.mark_zs) == 0: return diffractometer.Z.command_value
        return max(self.mark_zs)
    zmax = property(get_zmax)

    z_step = grid_spacing

    def closest_support_points(self,phi,z):
        """Phi values and z values of the four closest click point
        to (phi,z) which have been defined visually,
        as numpy array"""
        from numpy import concatenate,argmin,nan,isnan,array,any
        phi = phi % 360
        PHI,Z = self.spot_phis,self.mark_zs
        PHI = concatenate((PHI-360,PHI,PHI+360))

        PHI1,PHI2 = PHI[PHI<=phi],PHI[PHI>=phi]
        PHI1,PHI2 = PHI[PHI<=phi],PHI[PHI>=phi]
        phi1 = PHI1[argmin(abs(PHI1-phi))] if len(PHI1)>0 else nan
        phi2 = PHI2[argmin(abs(PHI2-phi))] if len(PHI2)>0 else nan
        phi1 = phi1 % 360
        phi2 = phi2 % 360
        if phi1 == phi2: phi2 = nan
        Z1,Z2 = Z[Z<=z],Z[Z>=z]
        z1 = Z1[argmin(abs(Z1-z))] if len(Z1)>0 else nan
        z2 = Z2[argmin(abs(Z2-z))] if len(Z2)>0 else nan
        if z1 == z2: z2 = nan
        points = array([[phi1,z1],[phi1,z2],[phi2,z1],[phi2,z2]])
        points = points[~any(isnan(points),axis=1)]
        return points.T

    def closest_support_phis(self,phi):
        """Phi values of the two closest click point
        to 'phi' which have been defined visually,
        as numpy array"""
        from numpy import concatenate,argmin,nan,isnan,array,any
        phi = phi % 360
        PHI = self.spot_phis
        PHI = concatenate((PHI-360,PHI,PHI+360))

        PHI1,PHI2 = PHI[PHI<=phi],PHI[PHI>=phi]
        PHI1,PHI2 = PHI[PHI<=phi],PHI[PHI>=phi]
        phi1 = PHI1[argmin(abs(PHI1-phi))] if len(PHI1)>0 else nan
        phi2 = PHI2[argmin(abs(PHI2-phi))] if len(PHI2)>0 else nan
        phi1 = phi1 % 360
        phi2 = phi2 % 360
        if phi1 == phi2: phi2 = nan
        phis = array([phi1,phi2])
        phis = phis[~any(isnan(phis))]
        if not hasattr(phis,"len"): phis = array([phis]) 
        return phis

    def closest_support_zs(self,z):
        """z values of the two closest click point
        to 'z' which have been defined visually,
        as numpy array"""
        from numpy import argmin,nan,isnan,array,any
        Z = self.mark_zs
        Z1,Z2 = Z[Z<=z],Z[Z>=z]
        z1 = Z1[argmin(abs(Z1-z))] if len(Z1)>0 else nan
        z2 = Z2[argmin(abs(Z2-z))] if len(Z2)>0 else nan
        if z1 == z2: z2 = nan
        zs = array([z1,z2])
        zs = zs[~any(isnan(zs))]
        if not hasattr(zs,"len"): zs = array([zs]) 
        return zs
       

class Settings(object):
    """Aligment info stored in settings file"""
    attributes = ["support_points","GridOffset","GridSpacing","click_center_z"]
    
    def __init__(self):
        self.timestamp = 0
        # Default values
        self.support_points = []
        self.GridOffset = 0.0
        self.GridSpacing = 0.100
        self.click_center_z = 0.0
        self.xray_scan_clearance = -0.15 # mm
        self.read()

    def read(self):
        "Monitor the settings file and reloads it if it is updated."
        from os.path import exists
        settings_file = settings_dir()+"/sample_settings.py"

        if exists(settings_file) and getmtime(settings_file) != self.timestamp:
            # (Re)load settings file.
            self.state = file(settings_file).read()
            self.saved_sample_state = self.state
            self.timestamp = getmtime(settings_file)

    def save(self):
        "Monitor the settings file and reloads it if it is updated."
        from os import makedirs,remove,rename
        from os.path import exists
        settings_file = settings_dir()+"/sample_settings.py"

        if not hasattr(self,"saved_state") or self.state != self.saved_state \
            or not exists(settings_file):
            # Update settings file.
            if not exists(settings_dir()): makedirs(settings_dir())
            try:
                file(settings_file+".tmp","wb").write(self.state)
                if exists(settings_file): remove(settings_file)
                rename(settings_file+".tmp",settings_file)
                self.saved_state = self.state
                self.timestamp = getmtime(settings_file)
            except IOError:
                print("Failed to update %r" % settings_file)


    def get_state(self):
        state = ""
        for attr in self.attributes:
            line = attr+" = "+repr(eval("self."+attr))
            state += line+"\n"
        return state
    def set_state(self,state):
        from numpy import nan
        for line in state.split("\n"):
            line = line.strip(" \n\r")
            if line != "":
                try: exec("self."+line)
                except Exception,msg: print("ignoring line %r: %s" % (line,msg))
    state = property(get_state,set_state)


def camera_position(Z,offset):
    """Transform from Z, offset to camera viewing plane 2D
    coordinates, using the current settigs of the diffractomter Z,Y,Z,Phi."""
    x = (diffractometer.Z.value - Z)
    y = offset
    return x,y

def interpolate_2D(X,Y,Z,x,y):
    """
    Z is a scalar function of the variables x and y.
    X,Y: vector of length N, support points
    Z: vector of length N, function values at support points
    x,y: where to evaluate the function Z
    """
    from numpy import array,unique
    X,Y,Z = array(X),array(Y),array(Z)
    UY = unique(Y)
    UZ = [interpolate(zip(X[Y==uy],Z[Y==uy]),x) for uy in UY]
    return interpolate(zip(UY,UZ),y)
    
def interpolate(xy_data,xval):
    "Linear interpolation"
    from numpy import array,argsort
    x = array(xvals(xy_data)); y = array(yvals(xy_data)); n = len(xy_data)
    if n == 0: return nan
    if n == 1: return y[0]
    order = argsort(x)
    x = x[order]; y= y[order]
    
    for i in range (1,n):
        if x[i]>xval: break
    if x[i-1]==x[i]: return (y[i-1]+y[i])/2. 
    yval = y[i-1]+(y[i]-y[i-1])*(xval-x[i-1])/(x[i]-x[i-1])
    return yval

def xvals(xy_data):
    "xy_data = list of (x,y)-tuples. Teturns list of x values only."
    xvals = []
    for i in range (0,len(xy_data)): xvals.append(xy_data[i][0])
    return xvals  

def yvals(xy_data):
    "xy_data = list of (x,y)-tuples. Returns list of y values only."
    yvals = []
    for i in range (0,len(xy_data)): yvals.append(xy_data[i][1])
    return yvals  

def getmtime(filename):
    """Modification timestamp of a file"""
    from os.path import getmtime
    try: return getmtime(filename)
    except: return 0

def settings_dir():
    """pathname of the file used to store persistent parameters"""
    from os.path import dirname
    path = module_dir()+"/settings"
    return path

def module_dir():
    """directory of the current module"""
    from os.path import dirname
    module_dir = dirname(module_path())
    if module_dir == "": module_dir = "."
    return module_dir

def module_path():
    "full pathname of the current module"
    from sys import path
    from os import getcwd
    from os.path import basename,exists
    from inspect import getmodulename,getfile
    # 'getfile' retreives the source file name name compiled into the .pyc file.
    pathname = getfile(lambda x: None)
    ##print "module_path: pathname: %r" % pathname
    if exists(pathname): return pathname
    # The module might have been compiled on a different machine or in a
    # different directory.
    pathname = pathname.replace("\\","/")
    filename = basename(pathname)
    ##print "module_path: filename: %r" % filename
    dirs = [dir for dir in [getcwd()]+path if exists(dir+"/"+filename)]
    if len(dirs) == 0: print "pathname of file %r not found" % filename
    dir = dirs[0] if len(dirs) > 0 else "."
    pathname = dir+"/"+filename
    ##print "module_path: pathname: %r" % pathname
    return pathname


sample = Sample()

def test():
    from numpy import array
    print "z range %.3f to %.3f, step %.3f mm" % (sample.zmin,sample.zmax,sample.z_step)

    # Outline the crystal shape.
    Z = arange(sample.zmin,sample.zmax+1e-6,sample.z_step)
    phi = Phi.value
    OFFSET = array([sample.visual_edge_offset(phi,z) for z in Z])
    for z,o in zip(Z,OFFSET): print "%.3f\t%.3f" % (z,o)

if __name__ == "__main__": # for testing
    self = sample # for debugging
    phi,z = diffractometer.phic,diffractometer.zc
    print("sample.zs")
    print("sample.spot_zs")
    print("sample.closest_support_points(phi,z)")
    print("sample.visual_edge_offset(phi,z)")
    print("sample.z_step")
    print("sample.center")
