from CA import caput,caget,cainfo

class PV (object):
    """EPICS Process Variable"""
    def __init__(self,name):
        """name: PREFIX:Record.Field"""
        self.name = name

    def get_value(self): return caget(self.name)
    def set_value(self,value): caput(self.name,value)
    value = property(get_value,set_value)

    def get_info(self): return cainfo(self.name,printit=False)
    info = property(get_info)

    def __getattr__(self,name):
        ##print "__getattr__(%r)" % name
        pv = PV(self.name+"."+name)
        object.__setattr__(self,name,pv)
        return pv

    ##def __setattr__(self,name,value):
    ##    print "__setattr__(%r,%r)" % (name,value)
    ##    object.__setattr__(self,name,value)

    def __repr__(self): return "PV(%r)" % self.name

LDT5948 = temperature_controller = PV("14IDB:LDT5948")
