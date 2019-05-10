"""
Control of Prosilica gigE camera via Python Remote Objects (Pyron) interface
by Zhong Ren.

Usage example:

from Pyro.core import *
cam = getProxyForURI("PYRONAME://Prosilica@192_168_2_27")
cam.init("192.168.2.27") # only needed if first client
cam.connect(1)
frame=cam.frameRGB()
len(frame)
4177920
cam.disconnect()

Methods:
connect([bin_factor]) - increment the connection counter. bin_factor has
no effect unless for the first client.
connections() - read connection counter for statistics, 'connect' increments,
'disconnect' decrements. If the connection counter drops the zero the server
disconnects fro mthe camera.
getBin() - tell current bin factor
frameSize() - number of pixels (not bytes) per frame

"""
