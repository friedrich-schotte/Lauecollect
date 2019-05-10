"""Friedrich Schotte, 9 Dec 2010 - Jan 27, 2016
"""
__version__ = "1.0"

class DummyMotor(object):
    name = "Dummy Motor"
    unit = ""
    value = 0

    def __init__(self,*args,**kwargs):
        if len(args)>0: self.name = args[0]

    def get_moving(self): return False
    def set_moving(self,value): pass
    moving = property(get_moving,set_moving)

    def stop(): pass
    

dummy_motor = DummyMotor()
