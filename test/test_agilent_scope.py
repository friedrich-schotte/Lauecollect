#!/usr/bin/python
from vxi_11 import *
scope=vxi_11_connection("id14b-scope")
scope.write("*IDN?\n")
print scope.read()
# expecting: (0, 4, 'Agilent Technologies,DSO81204A,MY44000226,05.01.0000\n')
