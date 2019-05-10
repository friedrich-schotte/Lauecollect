"""Retractable white reflector that can be inserted behind the sample
to improve its visibility. Needs to be retract during X-ray data collection
because it cast a shadow on the X-ray detector.

F. Schotte, 26 Jun 2013 - 26 Jun 2013
"""
__version__ = "1.0"

class IlluminatorOn(object):
    """Retractable white reflector that can be inserted behind the sample
    to improve its visibility. Needs to be retract during X-ray data collection
    because it cast a shadow on the X-ray detector."""
    time_changed = 0.0
    def get_value(self):
        """Is the illuminator currently in the X-ray beam?"""
        from CA import caget
        inserted = (caget("14IDB:Dliepcr1:Out1Mbbi") == 1)
        if self.moving: return not inserted
        return inserted
    def set_value(self,insert):
        from CA import caput
        if insert != self.value: self.time_changed = time()
        if insert: caput("14IDB:BacklightInsert.PROC",1)
        else: caput("14IDB:BacklightRetract.PROC",1)
        # Turn on the fiber light, if inserted.
        if insert: caput("14IDB:B1Bo7",0)
        # Turn off the fiber light, if not inserted.
        if not insert: caput("14IDB:B1Bo7",1)
    value = property(get_value,set_value)

    def get_moving(self):
        """Is illuminator currently moving?"""
        from time import time
        return (time() - self.time_changed < 1.0)
    moving = property(get_moving)

illuminator_on = IlluminatorOn()

illuminator_inserted = illuminator_on # for backward compatibility

if __name__ == '__main__': # test program
    print "illuminator_on.value"
    print "illuminator_on.value = True"
    print "illuminator_on.value = False"
