"""X-ray attenuator in BioCARS 14ID-B station.
Pneumatically inserted silver foil in XIA filter box.
Friedrich Schotte, 29 Nov 2013 - 9 Jul 2014
"""
__version__ = "1.0.1"

class XRayAttenuator(object):
    time_changed = 0.0
    def get_value(self):
        """Is the filter currently in the X-ray beam?"""
        from CA import caget
        inserted = (caget("14IDB:DAC1_3.VAL") == 0)
        if self.moving: return not inserted
        return int(inserted)
    def set_value(self,insert):
        from CA import caput
        from time import time
        if insert != self.value: self.time_changed = time()
        if insert: caput("14IDB:DAC1_3.VAL",0)
        else: caput("14IDB:DAC1_3.VAL",5)
    value = property(get_value,set_value)

    def get_moving(self):
        """Is it currently moving?"""
        from time import time
        return (time() - self.time_changed < 0.1)
    moving = property(get_moving)
xray_attenuator = XRayAttenuator()

