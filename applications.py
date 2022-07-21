"""
Author: Friedrich Schotte
Date created: 2022-05-09
Date last modified: 2022-06-13
Revision comment:
"""
__version__ = "1.0"

import logging


class applications:
    domain_name = "BioCARS"

    def __init__(self, domain_name=None):
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        return f"{self.class_name}({self.domain_name!r})"

    @property
    def class_name(self): return type(self).__name__

    @property
    def applications(self):
        from application import application
        return [
            application(f"{self.domain_name}.Servers_Panel.Servers_Panel('{self.domain_name}')"),
            application(f"{self.domain_name}.Timing_Panel.Timing_Panel('{self.domain_name}')"),
            application(f"{self.domain_name}.Acquisition_Panel.Acquisition_Panel('{self.domain_name}')"),
            application(f"{self.domain_name}.Camera_Viewer.Camera_Viewer('{self.domain_name}.MicroscopeCamera')"),
            application(f"{self.domain_name}.Camera_Viewer.Camera_Viewer('{self.domain_name}.WideFieldCamera')"),
            application(f"{self.domain_name}.SAXS_WAXS_Control_Panel.SAXS_WAXS_Control_Panel('{self.domain_name}')"),
            application(f"{self.domain_name}.Environment_Configurations_Panel.Environment_Configurations_Panel('{self.domain_name}')"),
            application(f"{self.domain_name}.Configuration_Tables_Panel.Configuration_Tables_Panel('{self.domain_name}')"),
            application(f"{self.domain_name}.Configuration_Table_Panel.Configuration_Table_Panel('{self.domain_name}')"),
            application(f"{self.domain_name}.Scope_Panel.Scope_Panel('{self.domain_name}.xray_scope')"),
            application(f"{self.domain_name}.Scope_Panel.Scope_Panel('{self.domain_name}.laser_scope')"),
            application(f"{self.domain_name}.Scope_Panel.Scope_Panel('{self.domain_name}.timing_scope')"),
            application(f"{self.domain_name}.Rayonix_Detector_Panel.Rayonix_Detector_Panel('{self.domain_name}')"),
            application(f"{self.domain_name}.ADXV_Live_Image_Panel.ADXV_Live_Image_Panel('{self.domain_name}')"),
            application(f"{self.domain_name}.Configuration_Table_Panel.Configuration_Table_Panel('{self.domain_name}.heat_load_chopper_modes')"),
        ]


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    domain_name = "BioCARS"
    self = applications(domain_name)

    print("self.applications")
