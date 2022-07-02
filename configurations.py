"""
Manage settings for different locations / instruments
Author: Friedrich Schotte
Date created: 2015-06-12
Date last modified: 2021-11-29
Revision comment: Updated IOC & Servers Machine names
"""
__version__ = "2.5"

from cached_function import cached_function

parameters = {
    "BioCARS": r"""
        #descriptions                              names                                                               default_values                         choices
        "Wide-Field Camera IP Address"             GigE_camera.WideFieldCamera.camera.IP_addr                          \"id14b-prosilica2.cars.aps.anl.gov\"  \"pico3.niddk.nih.gov\"
        "Wide-Field Camera Pixel Size [mm]"        domains/BioCARS/cameras/WideFieldCamera.NominalPixelSize            0.00465                                0.002445
        "Wide-Field Camera Orientation [deg]"      domains/BioCARS/cameras/WideFieldCamera.Orientation                 0                                      90,180,-90
        "Wide-Field Camera Mirror"                 domains/BioCARS/cameras/WideFieldCamera.Mirror                      False                                  True
        "Wide-Field Camera Crosshair"              domains/BioCARS/cameras/WideFieldCamera.ImageWindow.Center          (680,512)
        "Wide-Field Camera X Scale Factor"         domains/BioCARS/cameras/WideFieldCamera.x_scale                     1.0                                    -1.0
        "Wide-Field Camera Y Scale Factor"         domains/BioCARS/cameras/WideFieldCamera.y_scale                     1.0                                    -1.0 
        "Wide-Field Camera Z Scale Factor"         domains/BioCARS/cameras/WideFieldCamera.z_scale                     1.0                                    -1.0
        "Microscope Camera IP Address"             GigE_camera.MicroscopeCamera.camera.IP_addr                         \"id14b-prosilica1.cars.aps.anl.gov\"  \"pico22.niddk.nih.gov\"
        "Microscope Camera Pixel Size [mm]"        domains/BioCARS/cameras/MicroscopeCamera.NominalPixelSize           0.000526                               0.000517
        "Microscope Camera Orientation [deg]"      domains/BioCARS/cameras/MicroscopeCamera.Orientation                0                                      90,180,-90
        "Microscope Camera Mirror"                 domains/BioCARS/cameras/MicroscopeCamera.Mirror                     False                                  True
        "Microscope Camera Crosshair"              domains/BioCARS/cameras/MicroscopeCamera.ImageWindow.Center         (680,512)
        "Microscope Camera X Scale Factor"         domains/BioCARS/cameras/MicroscopeCamera.x_scale                    1.0                                    -1.0
        "Microscope Camera Y Scale Factor"         domains/BioCARS/cameras/MicroscopeCamera.y_scale                    1.0                                    -1.0
        "Microscope Camera Z Scale Factor"         domains/BioCARS/cameras/MicroscopeCamera.z_scale                    1.0                                    -1.0
        "SAXS/WAXS Inserted X [mm]"                SAXS_WAXS_control.x                                                 0.084                                  0.699
        "SAXS/WAXS Inserted Y [mm]"                SAXS_WAXS_control.y                                                 0.539                                  -0.386
        "Ensemble Server IP Address"               Ensemble.ip_address                                                 \"nih-instrumentation.aps.anl.gov:2000\" \"pico20.niddk.nih.gov:2000\",\"172.21.46.206:2000\"
        "Timing System EPICS Record"               timing_system/BioCARS.prefix                                        \"NIH:TIMING.\"                        \"NIH:TIMING3.\"
        "Rayonix Detector IP Address"              BioCARS/rayonix_detector_driver.ip_address                          \"mx340hs.cars.aps.anl.gov:2222\"      \"localhost:2222\",\"pico7.niddk.nih.gov:2222\",\"pico1.niddk.nih.gov:2222\",\"pico5.niddk.nih.gov:2222\"
        "Rayonix Detector Scratch Directory"       BioCARS/rayonix_detector_driver.scratch_directory                   \"//mx340hs/data/tmp\"                 \"//femto-data/C/Data/tmp\",\"//femto-data/C/Data/tmp\"
        "Default Logfile Directory"                logging.directory                                                   \"\"                                   \"/net/mx340hs/data/anfinrud_2011/Logfiles\",\"/net/femto-data/C/Data/2020.11/Test/Logfiles\"
        "BioCARS Logfile Directory"                BioCARS/logging.directory                                           \"\"                                   \"/net/mx340hs/data/anfinrud_2011/Logfiles\",\"/net/femto-data/C/Data/2020.11/Test/Logfiles\"
        "Channel Archiver Directory"               channel_archiver/BioCARS.directory                                  \"/net/mx340hs/data/anfinrud_2011/Archive\" \"/net/femto/C/All\ Projects/APS/Experiments/2020.11/Test/Archive\"
        "14-ID Simulator"                          servers/BioCARS/servers/1.machine_name                              \"NIH-INSTRUMENTATION\"                \"NIH-INSTRUMENTATION\"
        "Timing System Simulator"                  servers/BioCARS/servers/2.machine_name                              \"NIH-INSTRUMENTATION\"                \"NIH-INSTRUMENTATION\"
        "Configuration Server Machine Name"        servers/BioCARS/servers/3.machine_name                              \"NIH-INSTRUMENTATION\"                \"NIH-INSTRUMENTATION\"
        "PP Acquire Server Machine Name"           servers/BioCARS/servers/4.machine_name                              \"NIH-INSTRUMENTATION\"                \"NIH-INSTRUMENTATION\"
        "Channel Archiver Machine Name"            servers/BioCARS/servers/5.machine_name                              \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Timing Sequencer Server Machine Name"     servers/BioCARS/servers/6.machine_name                              \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Ensemble Server Machine Name"             servers/BioCARS/servers/7.machine_name                              \"NIH-INSTRUMENTATION\"                \"NIH-INSTRUMENTATION\"
        "WideField Camera Server Machine Name"     servers/BioCARS/servers/8.machine_name                              \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "WideField Camera Simulator Machine Name"  servers/BioCARS/servers/9.machine_name                              \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Microscope Camera Server Machine Name"    servers/BioCARS/servers/10.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Microscope Camera Simulator Machine Name" servers/BioCARS/servers/11.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Lightwave TEC Server Machine Name"        servers/BioCARS/servers/12.machine_name                             \"NIH-INSTRUMENTATION\"                \"ID14B4\"
        "Thermocouple IOC Machine Name"            servers/BioCARS/servers/13.machine_name                             \"NIH-INSTRUMENTATION\"                \"ID14B4\"
        "Oasis Chiller Machine Name"               servers/BioCARS/servers/14.machine_name                             \"NIH-INSTRUMENTATION\"                \"ID14B4\"
        "DI-245 Server Machine Name"               servers/BioCARS/servers/13.machine_name                             \"NIH-INSTRUMENTATION\"                \"ID14B4\"
        "Temperature System Machine Name"          servers/BioCARS/servers/16.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Temperature SL (Valentyn) Machine Name"   servers/BioCARS/servers/17.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Rayonix Detector Simulator Machine Name"  servers/BioCARS/servers/20.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "X-Ray Scope Server Machine Name"          servers/BioCARS/servers/24.machine_name                             \"ID14B-XSCOPE\"                       \"FEMTO10\"
        "Laser Scope Server Machine Name"          servers/BioCARS/servers/25.machine_name                             \"ID14L-SCOPE\"                        \"PICO21\"
        "Diagnostics Scope Server Machine Name"    servers/BioCARS/servers/26.machine_name                             \"ID14B-WAVESURFER\"                   \"PICO21\"
        "Timing Scope Server Machine Name"         servers/BioCARS/servers/27.machine_name                             \"ID14B-TSCOPE\"                       \"PICO21\"
        "Lightwave TEC Simulator Machine Name"     servers/BioCARS/servers/28.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Oasis Chiller Simulator Machine Name"     servers/BioCARS/servers/29.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Rayonix Detector IOC Machine Name"        servers/BioCARS/servers/30.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "X-Ray Scope Simulator Machine Name"       servers/BioCARS/servers/31.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Laser Scope Simulator Machine Name"       servers/BioCARS/servers/32.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Beamline Configurations Machine Name"     servers/BioCARS/servers/33.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "High-Speed Chopper Modes Configuration Machine Name" servers/BioCARS/servers/34.machine_name                  \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Heat-Load Chopper Modes Configuration Machine Name"  servers/BioCARS/servers/35.machine_name                  \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "PP Modes Configuration Machine Name"      servers/BioCARS/servers/36.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Sequence Configuration Machine Name"      servers/BioCARS/servers/37.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Delay Configuration Machine Name"         servers/BioCARS/servers/38.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Temperature Configuration Machine Name"   servers/BioCARS/servers/39.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Power Configuration Machine Name"         servers/BioCARS/servers/40.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Scan Configuration Machine Name"          servers/BioCARS/servers/41.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Laser Optics Configuration Machine Name"  servers/BioCARS/servers/42.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Alio Diffractometer Configuration Machine Name" servers/BioCARS/servers/43.machine_name                       \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Detector Configuration Machine Name"      servers/BioCARS/servers/44.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Diagnostics Configuration Machine Name"   servers/BioCARS/servers/45.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Methods Configuration Machine Name"       servers/BioCARS/servers/46.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
        "Temperature Scan IOC Machine Name"        servers/BioCARS/servers/47.machine_name                             \"ID14B4\"                             \"NIH-INSTRUMENTATION\"
    """,
    "LaserLab": r"""
        #descriptions                              names                                                               default_values                         choices
        "Default Logfile Directory"                logging.directory                                                   \"\"                                   \"//femto-data2/C/covid19Data/Logfiles\",\"//femto-data2/C/Data/2021.01/Logfiles\"
        "LaserLab Logfile Directory"               LaserLab/logging.directory                                          \"\"                                   \"//femto-data2/C/covid19Data/Logfiles\",\"//femto-data2/C/Data/2021.01/Logfiles\"
    """,
    "TestBench": r"""
        #descriptions                              names                                                               default_values                         choices
        "Default Logfile Directory"                logging.directory                                                   \"\"                                   \"//femto-data2/C/covid19Data/Logfiles\",\"//femto-data2/C/Data/2021.01/Logfiles\"
        "TestBench Logfile Directory"              TestBench/logging.directory                                         \"\"                                   \"//femto-data2/C/covid19Data/Logfiles\",\"//femto-data2/C/Data/2021.01/Logfiles\"
    """,
}


@cached_function()
def configurations(domain_name=None):
    return Configurations(domain_name)


class Configurations(object):
    """Manage settings for different locations / instruments"""
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        name = type(self).__name__.lower()
        return "%s(%r)" % (name, self.domain_name)

    @property
    @cached_function()
    def parameters(self):
        from table import table
        return table(text=self.parameters_string)

    @property
    def parameters_string(self):
        if self.domain_name in parameters:
            s = parameters[self.domain_name]
        else:
            s = "#descriptions names default_values choices"
        s = s.strip(" \n")+"\n"
        return s

    def get_values(self, configuration_name):
        """list of Python objects of builtin Python data types"""
        from DB import dbget
        prefix = "configurations/"+configuration_name+"." if configuration_name else ""
        values = []
        for name, default_value in zip(self.parameters.names, self.parameters.default_values):
            s = dbget(prefix+name)
            if s == "":
                s = default_value
            dtype = type(eval(default_value))
            try:
                value = dtype(eval(s))
            except Exception:
                value = eval(default_value)
            values += [value]
        return values

    def set_values(self, configuration_name, values):
        from DB import dbput
        prefix = "configurations/"+configuration_name+"." if configuration_name else ""
        for name, value, default_value, current_value in \
                zip(self.parameters.names, values, self.default_values, self.current_values):
            dbput(prefix + name, to_str(value, default_value, current_value))

    def get_current_values(self): return self.get_values("")
    def set_current_values(self, values): self.set_values("", values)
    current_values = property(get_current_values, set_current_values)

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
        """Which of the currently defined configurations is closest to the current
        settings?"""
        values = self[""]
        names = self.configuration_names
        N = [sum([v1 == v2 for v1, v2 in zip(self[name], values)]) for name in names]
        name = names[N.index(max(N))] if len(N) > 0 else ""
        return name
    current_configuration = property(get_current_configuration)

    def __getitem__(self, configuration_name):
        return self.get_values(configuration_name)

    def __setitem__(self, configuration_name, values):
        return self.set_values(configuration_name, values)

    def get_choices(self):
        """List of lists of Python objects of builtin Python data types"""
        default_values = self.parameters.default_values
        choices = self.parameters.choices
        choices = default_values+","+choices
        choices = [eval(c) for c in choices]
        return choices
    choices = property(get_choices)

    def show(self, configuration_name=""):
        s = "Configuration: "+self.current_configuration+"\n\n"
        s += "Choices:\n"
        for n in self.configuration_names:
            s += "- "+n+"\n"
        s += "\n"
        for n, v in zip(self.parameters.descriptions, self[configuration_name]):
            s += "%-40s: %s\n" % (n, v)
        print(s)


def to_str(value, type_value, default_value):
    """String representation of a value
    type_value: example value, defines data type
    default_value: if conversion fails use this value instead"""
    try:
        value = to_type(value, type_value)
    except Exception:
        value = default_value
    value = repr(value)
    return value


def to_type(value, type_value):
    if type(value) == str and type(type_value) != str:
        value = eval(value)
    dtype = type(type_value)
    value = dtype(value)
    if hasattr(dtype, "__len__") and dtype != str:
        value = dtype([to_type(value[i], type_value[i]) for i in range(0, len(type_value))])
    return value


if __name__ == "__main__":
    self = configurations(domain_name="BioCARS")
    # self = configurations(domain_name="LaserLab")
    print('print(self.parameters)')
    print('self.show()')
