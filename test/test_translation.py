from id14 import GonX,GonY,GonZ
from time import time,sleep

x0 = 3.873; y0 = 5.285; z0 = 8.5

GonZ.readback_slop = 0.030

def goto_start():
    GonX.value = x0 ; GonY.value = y0 ; GonZ.value = z0
    while (GonX.moving or GonY.moving or GonZ.moving): sleep(0.1)


def test_xyz():
    dx = 0.002; dy = 0.002; dz = 0.240 # mm

    goto_start()

    for i in range(1,5):
        t0 = time()
        GonX.value = x0+i*dx ; GonY.value = y0+i*dy ; GonZ.value = z0+i*dz
        while (GonX.moving or GonY.moving or GonZ.moving): sleep(0.01)
        t  = time()-t0
        print t


def test_z():
    dz = 0.240 # mm

    goto_start()

    for i in range(1,5):
        t0 = time()
        GonZ.value = z0+i*dz
        while GonZ.moving: sleep(0.01)
        t  = time()-t0
        print t

def measure_speed():
    goto_start()
    dz = 5 # mm
    t0 = time()
    GonZ.value = z0+dz
    sleep (0.05)
    while GonZ.moving: sleep(0.05)
    t  = time()-t0
    v = dz/t
    print "t=%.3f, v=%.3f" % (t,v)

def continuous_test():
    while True: test_xyz()

continuous_test()
