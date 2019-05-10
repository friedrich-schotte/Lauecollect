"""
Support module for LaueCrystallographyControlPanel.py
Serial Laue crystallography application level (AL) module
Author: Friedrich Schotte
Date created: Sep 28, 2017
Date last modified: Oct 17, 2017
"""
__version__ = "1.0.4" # X-ray detector

class Laue_Crystallography(object):
    """Serial Laue crystallography"""
    from persistent_property import persistent_property
    from action_property import action_property
    # instumentation
    from image_scan import image_scan
    from cavro_centris_syringe_pump_IOC import volume,port # volume[0],...,volume[3]
    mother_liquor = volume[0]
    mother_liquor_dV = persistent_property("mother_liquor_dV",10)
    crystal_liquor = volume[2]
    crystal_liquor_dV = persistent_property("crystal_liquor_dV",10)
    from cavro_centris_syringe_pump import PumpController
    pump = p = PumpController()
    from cavro_centris_syringe_pump import S_flow,S_load,S_flowIM
    from CA import PV
    upstream_pressure   = PV("NIH:DI245.56671FE403.CH1.pressure")
    downstream_pressure = PV("NIH:DI245.56671FE403.CH3.pressure")
    from instrumentation import microscope_camera as camera

    from instrumentation import DetZ
    det_inserted_pos = 185.8
    det_retracted_pos = 485.8

    def get_det_inserted(self):
        from numpy import isnan,nan
        value = abs(self.DetZ.value-self.det_inserted_pos) < 0.001\
            if not isnan(self.DetZ.value) else nan
        return value
    def set_det_inserted(self,value):
        if value: self.DetZ.command_value = self.det_inserted_pos
        else: self.DetZ.moving = False
    det_inserted = property(get_det_inserted,set_det_inserted)

    def get_det_retracted(self):
        from numpy import isnan,nan
        value = abs(self.DetZ.value-self.det_retracted_pos) < 0.001\
            if not isnan(self.DetZ.value) else nan
        return value
    def set_det_retracted(self,value):
        if value: self.DetZ.command_value = self.det_retracted_pos
        else: self.DetZ.moving = False
    det_retracted = property(get_det_retracted,set_det_retracted)

    def get_stage_enabled(self):
        from instrumentation import SampleX,SampleY,SampleZ
        return SampleX.enabled * SampleY.enabled * SampleZ.enabled
    def set_stage_enabled(self,value):
        from instrumentation import SampleX,SampleY,SampleZ
        SampleX.enabled,SampleY.enabled,SampleZ.enabled = True,True,True
    stage_enabled = property(get_stage_enabled,get_stage_enabled)

    @property
    def stage_online(self):
        from instrumentation import ensemble
        return ensemble.connected

    def get_centered(self):
        return self.image_scan.position == self.image_scan.center
    def set_centered(self,value):
        if value: self.image_scan.position = self.image_scan.center
    centered = property(get_centered,set_centered)

    def define_center(self):
        self.image_scan.center = self.image_scan.position

    inserted = centered

    @property
    def retracted_position(self):
        x,y,z = self.image_scan.center
        return x,y+11,z
    
    def get_retracted(self):
        return self.image_scan.position == self.retracted_position
    def set_retracted(self,value):
        if value: self.image_scan.position = self.retracted_position
    retracted = property(get_retracted,set_retracted)

    scanning = action_property("self.image_scan.acquire()",
        stop="self.image_scan.cancelled = True")

    @property
    def crystal_coordinates(self):
        """X,Y,Z in mm as formatted text"""
        XYZ = self.image_scan.crystal_XYZ
        lines = "\n".join(["%+.3f,%+.3f,%+.3f" % tuple(xyz) for xyz in XYZ.T])
        return lines

    @property
    def pump_online(self):
        from numpy import isnan
        return not isnan(self.volume[0].value)

    def init(self):
        """Home all motors"""
        self.p.init()

    def get_flowing(self):
        return self.mother_liquor.moving and \
            self.mother_liquor.speed == self.S_flow
    def set_flowing(self,value):
        if value: self.p.flow()
        else: self.p.abort()
    flowing = property(get_flowing,set_flowing)

    def inject(self):
        """Load crystals"""
        self.inject_count += 1
        self.p.inject()

    inject_count = persistent_property("inject_count",0)

    def get_injecting(self):
        return self.mother_liquor.moving \
            and self.mother_liquor.speed == self.S_flowIM
    def set_injecting(self,value):
        if value:
            self.inject_count += 1
            self.p.inject()
        else: self.p.abort()
    injecting = property(get_injecting,set_injecting)

    def get_mother_liquor_refilling(self):
        return self.mother_liquor.moving \
            and self.mother_liquor.speed == self.S_load
    def set_mother_liquor_refilling(self,value):
        if value: self.p.refill_1()
        else: self.p.abort()
    mother_liquor_refilling = property(get_mother_liquor_refilling,
        set_mother_liquor_refilling)

    def get_crystal_liquor_refilling(self):
        return self.crystal_liquor.moving \
            and self.crystal_liquor.speed == self.S_load
    def set_crystal_liquor_refilling(self,value):
        if value:
            self.inject_count = 0
            self.p.refill_3()
        else: self.p.abort()
    crystal_liquor_refilling = property(get_crystal_liquor_refilling,
        set_crystal_liquor_refilling)

    image_rootname = persistent_property("image_rootname","")

    def save_image(self):
        """Record photo"""
        from os.path import dirname
        directory = dirname(self.image_scan.directory)
        filename = "%s/%s.jpg" % (directory,self.image_rootname)
        self.camera.save_image(filename)


Laue_crystallography = Laue_Crystallography()
control = Laue_crystallography

if __name__ == "__main__": # for debugging
    from pdb import pm
    self = Laue_crystallography # for debugging
    import logging
    logging.basicConfig(level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s")
    ##print('control.scanning = True')
    ##print('control.scanning = False')
