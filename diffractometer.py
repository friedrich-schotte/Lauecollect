"""
General diffractometer module
Friedrich Schotte, 27 Feb 2013 - 31 Jan 2016
"""

__version__ = "1.1"

from DB import dbget,dbput

class Diffractometer(object):
    """General diffractometer with hardware intedendent degrees of freedom
    x: horizontal translation in X-ray beam direction
    y: vertical translation orthogonal to X-ray beam direction
    z: horizonal translation orthogonal to X-ray beam direction
    phi: rotation around z axis
    """

    def __init__(self):
        self.cache = {}
        # Horizontal translation in X-ray beam direction
        self.X = self.Motor(self,"x")
        # Vertical translation orthogonal to X-ray beam direction
        self.Y = self.Motor(self,"y")
        # Horizonal translation orthogonal to X-ray beam direction
        self.Z = self.Motor(self,"z")
        # Rotation around z axis
        self.Phi = self.Motor(self,"phi")
        # Object-specific offset from the rotation axis
        self.ClickCenterX = self.Motor(self,"click_center_x")
        # Object-specific offset from the rotation axis
        self.ClickCenterY = self.Motor(self,"click_center_y")
        self.ClickCenterZ = self.Motor(self,"click_center_z")

    def get_x_motor_name(self):
        try: return eval(dbget("sample.x_motor_name"))
        except: return "GonX"
    def set_x_motor_name(self,name): dbput("sample.x_motor_name",repr(name))
    x_motor_name = property(get_x_motor_name,set_x_motor_name)

    def get_y_motor_name(self):
        try: return eval(dbget("sample.y_motor_name"))
        except: return "GonY"
    def set_y_motor_name(self,name): dbput("sample.y_motor_name",repr(name))
    y_motor_name = property(get_y_motor_name,set_y_motor_name)

    def get_z_motor_name(self):
        try: return eval(dbget("sample.z_motor_name"))
        except: return "GonZ"
    def set_z_motor_name(self,name): dbput("sample.z_motor_name",repr(name))
    z_motor_name = property(get_z_motor_name,set_z_motor_name)

    def get_phi_motor_name(self):
        try: return eval(dbget("sample.phi_motor_name"))
        except: return "Phi"
    def set_phi_motor_name(self,name):
        dbput("sample.phi_motor_name",repr(name))
    phi_motor_name = property(get_phi_motor_name,set_phi_motor_name)

    def motor(self,name):
        if not name in self.cache: self.cache[name] = motor(name)
        return self.cache[name]
        
    @property
    def x_hardware_motor(self):
        """Translation hardware motor"""
        return self.motor(self.x_motor_name)

    @property
    def y_hardware_motor(self):
        """Translation hardware motor"""
        return self.motor(self.y_motor_name)

    @property
    def z_hardware_motor(self):
        """Translation hardware motor"""
        return self.motor(self.z_motor_name)

    @property
    def phi_hardware_motor(self):
        """Translation hardware motor"""
        return self.motor(self.phi_motor_name)

    @property
    def hardware_motors(self):
        """List of Motor objects"""
        return [self.x_hardware_motor,self.y_hardware_motor,
                self.z_hardware_motor,self.phi_hardware_motor]

    def get_xy_rotating(self):
        """Do the hardware X and Y motors rotate with the PHI rotation stage?"""
        return dbget("sample.xy_rotating") == "True"
    def set_xy_rotating(self,value):
        dbput("sample.xy_rotating",repr(value))
    xy_rotating = property(get_xy_rotating,set_xy_rotating)

    def get_x_scale(self):
        """Scale factor to apply to the hardware X translation motor"""
        try: return float(dbget("sample.x_scale"))
        except ValueError: return 1.0
    def set_x_scale(self,value): dbput("sample.x_scale",repr(float(value)))
    x_scale = property(get_x_scale,set_x_scale)
    
    def get_y_scale(self):
        """Scale factor to apply to the hardware Y translation motor"""
        try: return float(dbget("sample.y_scale"))
        except ValueError: return 1.0
    def set_y_scale(self,value): dbput("sample.y_scale",repr(float(value)))
    y_scale = property(get_y_scale,set_y_scale)
    
    def get_z_scale(self):
        """Scale factor to apply to the hardware Z translation motor"""
        try: return float(dbget("sample.z_scale"))
        except ValueError: return 1.0
    def set_z_scale(self,value): dbput("sample.z_scale",repr(float(value)))
    z_scale = property(get_z_scale,set_z_scale)
    
    def get_phi_scale(self):
        """Scale factor to apply to the hardware Phi rotation motor"""
        try: return float(dbget("sample.phi_scale"))
        except ValueError: return 1.0
    def set_phi_scale(self,value): dbput("sample.phi_scale",repr(float(value)))
    phi_scale = property(get_phi_scale,set_phi_scale)
    
    def get_rotation_center_x(self):
        """To which position do you have to drive the X motor for the rotation
        axis to be in the crosshair of both cameras?"""
        try: x,y = eval(dbget("sample.rotation_center"))
        except: return 0.0
        return x
    def set_rotation_center_x(self,value):
        x,y = self.rotation_center_x,self.rotation_center_y
        x = value
        dbput("sample.rotation_center",repr((x,y)))
    rotation_center_x = property(get_rotation_center_x,set_rotation_center_x)
    
    def get_rotation_center_y(self):
        """To which position do you have to drive the Y motor for the rotation
        axis to be in the crosshair of both cameras?"""
        try: x,y = eval(dbget("sample.rotation_center"))
        except: return 0.0
        return y
    def set_rotation_center_y(self,value):
        x,y = self.rotation_center_x,self.rotation_center_y
        y = value
        dbput("sample.rotation_center",repr((x,y)))
    rotation_center_y = property(get_rotation_center_y,set_rotation_center_y)
        
    def get_click_center_x(self):
        try: return float(dbget("sample.click_center_x"))
        except: return 0.0
    def set_click_center_x(self,value):
        dbput("sample.click_center_x",repr(float(value)))
    click_center_x = property(get_click_center_x,set_click_center_x)
    
    def get_click_center_y(self):
        try: return float(dbget("sample.click_center_y"))
        except: return 0.0
    def set_click_center_y(self,value):
        dbput("sample.click_center_y",repr(float(value)))
    click_center_y = property(get_click_center_y,set_click_center_y)

    def get_click_center_z(self):
        try: return float(dbget("sample.click_center_z"))
        except: return 0.0
    def set_click_center_z(self,value):
        dbput("sample.click_center_z",repr(float(value)))
    click_center_z = property(get_click_center_z,set_click_center_z)

    def get_calibration_z(self):
        try: return float(dbget("sample.calibration_z"))
        except: return 0.0
    def set_calibration_z(self,value):
        dbput("sample.calibration_z",repr(float(value)))
    calibration_z = property(get_calibration_z,set_calibration_z)

    def diffractometer_xy(self,x,y,phi):
        """Transform from hardware motor positions to diffractometer coordinates.
        x,y,phi: hardware motor positions
        Return value: (x,y)"""
        from numpy import sin,cos,radians
        rx,ry = self.rotation_center_x,self.rotation_center_y
        cx,cy = self.click_center_x,self.click_center_y
        sx,sy = self.x_scale,self.y_scale
        phip = self.diffractometer_phi(phi)
        phir = phip if self.xy_rotating else 0
        xp = sx*(x-rx)*cos(radians(phir)) - sy*(y-ry)*sin(radians(phir))
        yp = sx*(x-rx)*sin(radians(phir)) + sy*(y-ry)*cos(radians(phir))
        # Offset of the sample with respect to the rotation axis.
        dx =  cx*cos(radians(phip)) + cy*sin(radians(phip))
        dy = -cx*sin(radians(phip)) + cy*cos(radians(phip))
        xp -= dx
        yp -= dy
        return xp,yp

    def hardware_xy(self,xp,yp,phip):
        """Transform from diffractometer coordinates to hardware motor positions.
        xp,yp: hardware-independent diffractometer coordinates
        phip: hardware-independent diffractometer phi
        Return value: (x,y)"""
        from numpy import sin,cos,radians
        rx,ry = self.rotation_center_x,self.rotation_center_y
        cx,cy = self.click_center_x,self.click_center_y
        sx,sy = self.x_scale,self.y_scale
        # Offset of the sample with respect to the rotation axis.
        dx =  cx*cos(radians(phip)) + cy*sin(radians(phip))
        dy = -cx*sin(radians(phip)) + cy*cos(radians(phip))
        phir = phip if self.xy_rotating else 0
        x = ( (xp+dx)*cos(radians(phir)) + (yp+dy)*sin(radians(phir))) / sx + rx
        y = (-(xp+dx)*sin(radians(phir)) + (yp+dy)*cos(radians(phir))) / sy + ry
        return x,y

    def sample_center_xyz(self,phi):
        """Where does the sample need to be translated such that the current
        center is on the crosshair?
        Return value: SampleX.value,SampleY.value"""
        from numpy import degrees,arctan2,sqrt,sin,cos,radians
        x0,y0 = self.click_center_x,self.click_center_y
        r = sqrt(x0**2+y0**2)
        phi0 = degrees(arctan2(-y0,x0)) % 360
        phi1 = (phi0 + phi) % 360
        dx =   r*cos(radians(phi1))
        dy =  -r*sin(radians(phi1))
        cx,cy = self.rotation_center_x,self.rotation_center_y
        x,y = cx+dx,cy+dy
        z = self.click_center_z + self.calibration_z
        return x,y,z

    def xyz_of_sample(self,(sample_x,sample_y,sample_z),phi):
        """Where does the sample need to be translated such that the current
        center is on the crosshair?
        sample_x,sample_y,sample_z: sample coordinates with respect the
        rotation axis of the phi motor
        Return value: SampleX.value,SampleY.value,SampleZ.value"""
        from numpy import degrees,arctan2,sqrt,sin,cos,radians
        x0,y0 = sample_x,sample_y
        r = sqrt(x0**2+y0**2)
        phi0 = degrees(arctan2(-y0,x0)) % 360
        phi1 = (phi0 + phi) % 360
        dx =   r*cos(radians(phi1))
        dy =  -r*sin(radians(phi1))
        cx,cy = self.rotation_center_x,self.rotation_center_y
        x,y = cx+dx,cy+dy
        z = sample_z + self.calibration_z
        return x,y,z

    def z_of_sample(self,sample_z):
        """Where does the sample need to be translated such that the current
        center is on the crosshair?
        sample_z: 
        Return value: SampleZ.value"""
        z = sample_z + self.calibration_z
        return z

    def diffractometer_z(self,z):
        """Transform from hardware motor positions to diffractometer."""
        return z*self.z_scale
    
    def hardware_z(self,z):
        """Transform from diffractometer to hardware motor positions."""
        return z/self.z_scale
    
    def diffractometer_phi(self,phi):
        """Transform from hardware motor positions to diffractometer."""
        return phi*self.phi_scale
    
    def hardware_phi(self,phi):
        """Transform from diffractometer to hardware motor positions."""
        return phi/self.phi_scale

    def get_xy(self):
        """Horizontal translation in X-ray beam direction and vertical
        translation"""
        x = self.x_hardware_motor.value
        y = self.y_hardware_motor.value
        phi = self.phi_hardware_motor.value
        xp,yp = self.diffractometer_xy(x,y,phi)
        return xp,yp
    def set_xy(self,(xp,yp)):
        phi = self.phi_hardware_motor.command_value
        phip = self.diffractometer_phi(phi)
        x,y = self.hardware_xy(xp,yp,phip)
        self.x_hardware_motor.command_value = x
        self.y_hardware_motor.command_value = y
    xy = property(get_xy,set_xy)

    def get_xyc(self):
        """Target (command) value of horizontal translation in X-ray beam
        direction."""
        x = self.x_hardware_motor.command_value
        y = self.y_hardware_motor.command_value
        phi = self.phi_hardware_motor.command_value
        xp,yp = self.diffractometer_xy(x,y,phi)
        return xp,yp
    xyc = property(get_xyc,set_xy)

    def get_x(self):
        """Horizontal translation in X-ray beam direction."""
        x = self.x_hardware_motor.value
        y = self.y_hardware_motor.value
        phi = self.phi_hardware_motor.value
        xp,yp = self.diffractometer_xy(x,y,phi)
        return xp 
    def set_x(self,value):
        x = self.x_hardware_motor.command_value
        y = self.y_hardware_motor.command_value
        phi = self.phi_hardware_motor.command_value
        xp,yp = self.diffractometer_xy(x,y,phi)
        xp = value
        phip = self.diffractometer_phi(phi)
        x,y = self.hardware_xy(xp,yp,phip)
        self.x_hardware_motor.command_value = x
        self.y_hardware_motor.command_value = y
    x = property(get_x,set_x)

    def get_xc(self):
        """Target (command) value of horizontal translation in X-ray beam
        direction."""
        x = self.x_hardware_motor.command_value
        y = self.y_hardware_motor.command_value
        phi = self.phi_hardware_motor.command_value
        xp,yp = self.diffractometer_xy(x,y,phi)
        return xp
    xc = property(get_xc,set_x)

    def get_y(self):
        """Vertical translation orthogonal to the X-ray beam direction."""
        x = self.x_hardware_motor.value
        y = self.y_hardware_motor.value
        phi = self.phi_hardware_motor.value
        xp,yp = self.diffractometer_xy(x,y,phi)
        return yp 
    def set_y(self,value):
        x = self.x_hardware_motor.command_value
        y = self.y_hardware_motor.command_value
        phi = self.phi_hardware_motor.command_value
        xp,yp = self.diffractometer_xy(x,y,phi)
        yp = value
        phip = self.diffractometer_phi(phi)
        x,y = self.hardware_xy(xp,yp,phip)
        self.x_hardware_motor.command_value = x
        self.y_hardware_motor.command_value = y
    y = property(get_y,set_y)

    def get_yc(self):
        """Target (command) value of vertical translation orthogonal to the
        X-ray beam direction."""
        x = self.x_hardware_motor.command_value
        y = self.y_hardware_motor.command_value
        phi = self.phi_hardware_motor.command_value
        xp,yp = self.diffractometer_xy(x,y,phi)
        return yp
    yc = property(get_yc,set_y)

    def get_z(self):
        """Horizontal translation orthogonal to the X-ray beam direction."""
        return self.diffractometer_z(self.z_hardware_motor.value)
    def set_z(self,value):
        self.z_hardware_motor.command_value = self.hardware_z(value)
    z = property(get_z,set_z)

    def get_zc(self):
        """Target (command) value of horizontal translation orthogonal to the
        X-ray beam direction."""
        return self.diffractometer_z(self.z_hardware_motor.command_value)
    zc = property(get_zc,set_z)

    def get_phi(self):
        """Horizontal translation orthogonal to the X-ray beam direction."""
        return self.diffractometer_phi(self.phi_hardware_motor.value)
    def set_phi(self,value):
        self.phi_hardware_motor.command_value = self.hardware_phi(value)
    phi = property(get_phi,set_phi)

    def get_phic(self):
        """Target (command) value of horizontal translation orthogonal to the
        X-ray beam direction."""
        return self.diffractometer_phi(self.phi_hardware_motor.command_value)
    phic = property(get_phic,set_phi)

    def get_phi_moving(self):
        """Is the motor moving?"""
        return self.phi_hardware_motor.moving
    def set_phi_moving(self,value):
        """value: False = stop motors"""
        self.phi_hardware_motor.moving = value
    phi_moving = property(get_phi_moving,set_phi_moving)

    def get_z_moving(self):
        """Is the motor moving?"""
        return self.z_hardware_motor.moving
    def set_z_moving(self,value):
        """value: False = stop motors"""
        self.z_hardware_motor.moving = value
    z_moving = property(get_z_moving,set_z_moving)

    def get_x_moving(self):
        """Is the motor moving?"""
        return self.x_hardware_motor.moving or self.y_hardware_motor.moving
    def set_x_moving(self,value):
        """value: False = stop motors"""
        self.x_hardware_motor.moving = value
        self.y_hardware_motor.moving = value
    x_moving = property(get_x_moving,set_x_moving)

    def get_y_moving(self):
        """Is the motor moving?"""
        return self.x_hardware_motor.moving or self.y_hardware_motor.moving
    def set_y_moving(self,value):
        """value: False = stop motors"""
        self.x_hardware_motor.moving = value
        self.y_hardware_motor.moving = value
    y_moving = property(get_y_moving,set_y_moving)

    def get_moving(self):
        """Is any of the hardware motors moving?"""
        for m in self.hardware_motors:
            if m.moving: return True
        return False
    def set_moving(self,value):
        """value: False = stop motors"""
        for m in self.hardware_motors: m.moving = value
    moving = property(get_moving,set_moving)

    def stop(self):
        """Abort all active motion of the hardware motors"""
        self.moving = False

    class Motor(object):
        def __init__(self,diffractometer,name):
            self.diffractometer = diffractometer
            self.name = name
        def get_value(self): return getattr(self.diffractometer,self.name) 
        def get_command_value(self):
            if hasattr(self.diffractometer,self.name+"c"):
                return getattr(self.diffractometer,self.name+"c")
            else: return self.value
        def set_value(self,value): setattr(self.diffractometer,self.name,value)
        value = property(get_value,set_value)
        command_value = property(get_value,set_value)
        def get_moving(self):
            if hasattr(self.diffractometer,self.name+"_moving"):
                return getattr(self.diffractometer,self.name+"_moving")
            else: return False
        def set_moving(self,value):
            if hasattr(self.diffractometer,self.name+"_moving"):
                setattr(self.diffractometer,self.name+"_moving",value)
        moving = property(get_moving,set_moving)
        def stop(self): self.moving = False
        def get_unit(self):
            if "phi" in self.name.lower(): return "deg"
            else: return "mm"
        unit = property(get_unit)
        speed = 1.0
        def __repr__(self): return "diffractometer.Motor(\""+self.name+"\")"


def motor(name):
    """name: EPICS PV or Python motor defined in 'id14.py'"""
    if not ":" in name:
        exec("from id14 import *")
        try: return eval(name)
        except: pass
    from EPICS_motor import motor
    return motor(name)
        

diffractometer = Diffractometer()

if __name__ == "__main__": # for testing
    self = diffractometer # for debugging
    print 'diffractometer.sample_center_xyz(diffractometer.phi)'
