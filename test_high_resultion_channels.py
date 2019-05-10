from timing_system import timing_system
from time import sleep

delays = (
    timing_system.ch1.delay,
    timing_system.ch14.delay,
    timing_system.ch16.delay,
    timing_system.ch18.delay,
)

def shift(dt=1.4e-9):
    for d in delays: d.dial += dt

def inc(count=1):
    for d in delays: d.count += count

def test(count=10,delay=0):
    sleep(delay)
    for i in range(count):
        inc()
        sleep(1)

print('inc(-10)')
print('test(count=10,delay=0)')
    
