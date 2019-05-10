"""Suspend data collection when the X-ray beam is down
Usage:
from checklist import beam_ok

def wait_for_beam():
    while not beam_ok() and not cancelled: sleep(1)
    
Friedrich Schotte, Feb 24, 2017 - Mar 2, 2017
"""
__version__ = "1.3" # reorder


class Checklist(object):
    name = "checklist"
    from persistent_property import persistent_property
    N = persistent_property("N",1) # How may test are there?

    defaults = {
        "Frontend Shutter":
            {"value":'caget("PA:14ID:STA_A_FES_OPEN_PL.VAL")',
             "format":'{0:"CLOSED",1:"OPEN"}[value]',
             "test":'value == 1'},
        "Heatload chopper phased":
            {"value":'timing_system.hlcled.count',
             "format":'str(value)',
             "test":'value == 1'},
        "Heatload chopper phase":
            {"value":'timing_system.hlcad.value',
             "format":'"%+.3f us" % (value/1e-6)',
             "test":'-8e-6 < value < 8e-6'},
        "Heatload chopper controller":
            {"value":'caget("14IDA:LA2000_ENABLE.TINP")',
             "format":'value',
             "test":'value == "ENABLED"'},
    }

    class Test(object):
        from persistent_property import persistent_property
        label = persistent_property("label","New item")
        value_code = persistent_property("value",'True')
        format = persistent_property("format",'"OK" if value else "not OK"')
        test_code = persistent_property("code",'value == True')
        enabled = persistent_property("enabled",False)

        def __init__(self,parent,n):
            self.parent = parent
            self.name = "checklist.%s" % (n+1)

        @property
        def test_code_OK(self):
            """Is the code for this test executable?"""
            exec("from instrumentation import *")
            value = self.value
            try: eval(self.test_code); OK = True
            except: OK = False
            return OK

        @property
        def value(self):
            """Current value of diagnostic"""
            exec("from instrumentation import *")
            try: value = eval(self.value_code)
            except: value = ""
            return value

        @property
        def formatted_value(self):
            """Current value of diagnostic as string"""
            value = self.value
            try: text = eval(self.format)
            except: text = str(value)
            return text

        @property
        def OK(self):
            """Did this test pass OK?"""
            exec("from instrumentation import *")
            value = self.value
            try: passed = eval(self.test_code)
            except: passed = True
            return passed

        def get_parameters(self):
            """Representation as a dictionary"""
            parameters = {
                "label": self.label,
                "value_code": self.value_code,
                "format": self.format,
                "test_code": self.test_code,
                "enabled": self.enabled,
            }
            return parameters
        def set_parameters(self,value):
            for key in value: setattr(self,key,value[key])
        parameters = property(get_parameters,set_parameters)

        def __repr__(self): return self.name

    def test(self,n): return self.Test(self,n)
    
    @property
    def OK(self):
        """Is there an X-ray beam available right now?"""
        OK = all(self.tests_passed)
        return OK

    @property
    def tests_passed(self):
        """Is there an X-ray beam available right now?"""
        tests_passed = [not self.test(i).enabled or self.test(i).OK
            for i in range(self.N)]
        return tests_passed

    @property
    def test_failed(self):
        """Name of first test that failed"""
        tests_passed = self.tests_passed
        if not all(tests_passed):
            i = tests_passed.index(False)
            label = "%s (%s)" % (self.test(i).label,
                self.test(i).formatted_value)
        else: label = ""
        return label

    def reorder(self,order):
        """Change order of tests
        order: list of 0-based integers"""
        parameters = [self.test(i).parameters for i in order]
        for i in range(0,len(parameters)):
            self.test(i).parameters = parameters[i]

checklist = Checklist()

def beam_ok():
    """Is there an X-ray beam available right now?"""
    return checklist.OK

if __name__ == "__main__":
    from pdb import pm # for debugging
    self = checklist # for debugging
    order = [1,0,2,3,4,5,6,7,8]
    print('beam_ok()')
    print('checklist.reorder(order)')
    print('[checklist.test(i).label for i in range(0,checklist.N)]')
