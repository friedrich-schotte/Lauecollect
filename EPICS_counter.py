"""
Python interface to EPICS supported counters.
Friedrich Schotte, APS, 7 Nov 2007 - 18 Apr 2010
"""
__version__ = "1.1"

from CA import caget,caput

class counter(object): 
    """EPICS-controlled motor
    Using the following process variables:
    14IDB:sclS1.CNT - set 1 to start couter, reads 0 is counting complete
    14IDB:sclS1_cts1.D - Calc result (counts/s)
    14IDB:sclS1.TP - programmed count time in seconds
    14IDB:sclS1.S1 - actula count time 10-MHz clock cycles
    14IDB:sclS1.S2-16 - actual count
    14IDB:sclS1.NM2-16 - description
    """
    def __init__(self,counter_name):
        "ioc_name = EPICS IOC"
        object.__init__(self)
        self.ioc_name = counter_name.split(".")[0]
        self.channel = counter_name.split(".")[1][1:]
        self.unit = "cts/s"

    def get_count(self): return caget(self.ioc_name+".S"+self.channel)
    count = property(fget=get_count,doc="actual count")

    def get_value(self): return self.count/self.count_time
    value = property(fget=get_value,doc="counts/s")

    def get_name(self): return caget(self.ioc_name+".NM"+self.channel)
    name = property(fget=get_name,doc="description")

    def start(self): caput(self.ioc_name+".CNT",1)
    def stop(self): caput(self.ioc_name+".CNT",0)

    def get_count_time(self): return caget(self.ioc_name+".S1")/1e7
    def set_count_time(self,value): return caput(self.ioc_name+".TP",value)
    count_time = property(fget=get_count_time,fset=set_count_time,doc="integration time in s")

if __name__ == "__main__":
    # 14ID-B Joerger VSC16
    IC_up = counter("14IDB:sclS1.S4")
    IO_detector = counter("14IDB:sclS1.S7")
    Downstream_counter = counter("14IDB:sclS1.S9")

    
