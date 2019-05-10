"""
"""

from serial import Serial

port = Serial("COM5")

s = ""

for i in range(0,255):
    port.write(chr(i))
    s += port.read(1)
