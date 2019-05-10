from timing_system import timing_system

registers = \
    (timing_system.image_number,timing_system.image_number_inc),\
    (timing_system.pass_number,timing_system.pass_number_inc),\
    (timing_system.pulses,timing_system.pulses_inc)

for (acc,inc) in registers:
    acc.count = 0
    count = 100
    for i in range(0,count):
       inc.count=1
       inc.count=0
    print "%r: expecting %r, got %r" % (acc,count,acc.count)
    acc.count = 0
