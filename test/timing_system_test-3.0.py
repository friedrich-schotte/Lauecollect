"""
Friedrich Schotte, Aug 20, 2015 - Aug 20, 2015
"""
__version__ = "3.0"
from instrumentation import timing_system
from sleep import sleep

def test_output_state():
    for name in timing_system.output_names:
        timing_system.register(name+"_enable").count = 0
        timing_system.register(name+"_state").count = 1
        sleep(0.5)
        timing_system.register(name+"_state").count = 0

def test_output_enable():
    for name in timing_system.output_names:
        timing_system.register(name+"_state").count = 0
        timing_system.register(name+"_enable").count = 1
        sleep(0.5)
        timing_system.register(name+"_enable").count = 0

def enable_all():
    for name in timing_system.output_names:
        timing_system.register(name+"_enable").count = 1
        timing_system.register(name+"_state").count = 0

def disable_all():
    for name in timing_system.output_names:
        timing_system.register(name+"_enable").count = 0
        timing_system.register(name+"_state").count = 0

if __name__ == "__main__":
    print('timing_system.ip_address = %r' % timing_system.ip_address)
    print('enable_all()')
    print('disable_all()')
    print('test_output_state()')
    print('test_output_enable()')
