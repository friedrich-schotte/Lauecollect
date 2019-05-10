"""
Manage settings for different locations / instruments
Author: Friedrich Schotte
Date: Jun 12, 2015
Date: May 21, 2018
"""
__version__ = "1.0.8" # timing_system.prefix

parameters = r"""
#descriptions                         names                                       default_values                         choices
"Wide-Field Camera IP Address"        GigE_camera.WideFieldCamera.camera.IP_addr  \"id14b-prosilica2.cars.aps.anl.gov\"  \"pico3.niddk.nih.gov\"
"Wide-Field Camera Server IP Address" GigE_camera.WideFieldCamera.ip_address      \"nih-instrumentation.cars.aps.anl.gov:2001\"  \"pico20.niddk.nih.gov:2001\" 
"Wide-Field Camera Pixel Size [mm]"   WideFieldCamera.NominalPixelSize            0.00465                                0.002445
"Wide-Field Camera Orientation [deg]" WideFieldCamera.Orientation                 0                                      90,180,-90
"Wide-Field Camera Mirror"            WideFieldCamera.Mirror                      False                                  True
"Wide-Field Camera Crosshair"         WideFieldCamera.ImageWindow.Center          (680,512)
"Wide-Field Camera X Scale Factor"    WideFieldCamera.x_scale                     1.0                                    -1.0                                                            
"Wide-Field Camera Y Scale Factor"    WideFieldCamera.y_scale                     1.0                                    -1.0                                                         
"Wide-Field Camera Z Scale Factor"    WideFieldCamera.z_scale                     1.0                                    -1.0                                                             
"Microscope Camera IP Address"        GigE_camera.MicroscopeCamera.camera.IP_addr \"id14b-prosilica1.cars.aps.anl.gov\"  \"pico22.niddk.nih.gov\" 
"Microscope Camera Server IP Address" GigE_camera.MicroscopeCamera.ip_address     \"nih-instrumentation.cars.aps.anl.gov:2002\"  \"pico20.niddk.nih.gov:2002\" 
"Microscope Camera Pixel Size [mm]"   MicroscopeCamera.NominalPixelSize           0.000526                               0.000517                                     
"Microscope Camera Orientation [deg]" MicroscopeCamera.Orientation                0                                      90,180,-90
"Microscope Camera Mirror"            MicroscopeCamera.Mirror                     False                                  True
"Microscope Camera Crosshair"         MicroscopeCamera.ImageWindow.Center         (680,512)
"Microscope Camera X Scale Factor"    MicroscopeCamera.x_scale                    1.0                                    -1.0                                                            
"Microscope Camera Y Scale Factor"    MicroscopeCamera.y_scale                    1.0                                    -1.0                                                         
"Microscope Camera Z Scale Factor"    MicroscopeCamera.z_scale                    1.0                                    -1.0                                                             
"X Stage"                             sample.x_motor_name                 \"SampleX\"                            \"GonX\"                                                    
"Y Stage"                             sample.y_motor_name                 \"SampleY\"                            \"GonY\"                                                                
"Z Stage"                             sample.z_motor_name                 \"SampleZ\"                            \"GonZ\"                                                                   
"Phi Motor"                           sample.phi_motor_name               \"SamplePhi\"                          \"Phi\"                                                                
"XY Rotating"                         sample.xy_rotating                  True                                   False                                                              
"Rotation Center"                     sample.rotation_center              (0.0,0.0)                                                                
"Ensemble Server IP Address"          Ensemble.ip_address                 \"nih-instrumentation.aps.anl.gov:2000\" \"pico20.niddk.nih.gov:2000\",\"172.21.46.206:2000\"
"Timing System IP Address"            timing_system.ip_address_and_port   \"id14timing2.cars.aps.anl.gov:2000\"  \"pico23.niddk.nih.gov:2000\",\"pico24.niddk.nih.gov:2000\",\"pico25.niddk.nih.gov:2000\"
"Timing System EPICS Record"          timing_system.prefix                \"NIH:TIMING.\"                        \"NIH:TIMING3.\"
"Rayonix Detector IP Address"         rayonix_detector.ip_address         \"mx340hs.cars.aps.anl.gov:2222\"      \"pico19.niddk.nih.gov:2222\"                                                            
"X-Ray Oscilloscope IP Address"       xray_scope.ip_address               \"id14b-xscope.cars.aps.anl.gov:2000\" \"pico21.niddk.nih.gov:2000\",\"femto10.niddk.nih.gov:2000\"                                                         
"Laser Oscilloscope IP Address"       laser_scope.ip_address              \"id14l-scope.cars.aps.anl.gov:2000\"  \"femto10.niddk.nih.gov:2000\",\"pico21.niddk.nih.gov:2000\"                                                         
"""

class Configurations(object):
    """Manage settings for different locations / instruments"""
    from table import table
    parameters = table(text=parameters)
    
    def get_values(self,configuration_name):
        """list of Python objects of builtin Python data types"""
        from DB import dbget
        prefix = "configurations/"+configuration_name+"." if configuration_name else ""
        values = []
        for name,default_value in zip(self.parameters.names,self.parameters.default_values):
            s = dbget(prefix+name)
            if s == "": s = default_value
            dtype = type(eval(default_value))
            try: value = dtype(eval(s))
            except: value = eval(default_value)
            values += [value]
        return values
    def set_values(self,configuration_name,values):
        from DB import dbput
        prefix = "configurations/"+configuration_name+"." if configuration_name else ""
        for name,value,default_value,current_value in \
            zip(self.parameters.names,values,self.default_values,self.current_values):
            dbput(prefix+name,tostr(value,type(default_value),current_value))

    def get_current_values(self): return self.get_values("")
    def set_current_values(self,values): self.set_values("",values)
    current_values = property(get_current_values,set_current_values)

    def get_default_values(self):
        return [eval(v) for v in self.parameters.default_values]
    default_values = property(get_default_values)

    def get_configuration_names(self):
        """List of currently in use configuration names, e.g.
        "BioCARS Diffractometer","NIH Diffractometer","LCLS Diffractometer" """
        from DB import dbdir
        return dbdir("configurations")
    configuration_names = property(get_configuration_names)

    def get_current_configuration(self):
        """Which of the currently define configurations is closest to the current
        settings?"""
        values = self[""]
        names = self.configuration_names
        N = [sum([v1 == v2 for v1,v2 in zip(self[name],values)]) for name in names]
        name = names[N.index(max(N))] if len(N)>0 else ""
        return name
    current_configuration = property(get_current_configuration)

    def __getitem__(self,configuration_name):
        return self.get_values(configuration_name)
    def __setitem__(self,configuration_name,values):
        return self.set_values(configuration_name,values)

    def get_choices(self):
        """List of lists of Python objects of builtin Python data types"""
        default_values = self.parameters.default_values
        choices = self.parameters.choices
        choices = default_values+","+choices
        choices = [eval(c) for c in choices]
        return choices
    choices = property(get_choices)

    def show(self,configuration_name=""):
        s = "Configuration: "+self.current_configuration+"\n\n"
        s += "Choices:\n"
        for n in self.configuration_names: s += "- "+n+"\n"
        s += "\n"
        for n,v in zip(self.parameters.descriptions,self[configuration_name]):
            s += "%-40s: %s\n" % (n,v)
        print s

configurations = Configurations()


def tostr(value,dtype,default_value):
    """String represenation of a value"""
    try: value = dtype(value)
    except: value = default_value
    value = repr(value)
    return value

if __name__ == "__main__":
    self = configurations # for debugging
    print 'print self.parameters'
    print 'self.show()'
