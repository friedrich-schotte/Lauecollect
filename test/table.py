"""
Table jacks of optical table in 14ID-B end station
Friedrich Schotte, 10 Nov 2007  
"""

from motor import *

TDSY = motor("14IDB:m17")  # downstream vertical
TOUTY = motor("14IDB:m18") # outward vertical
TINY = motor("14IDB:m19")  # inward vertical
TUSX = motor("14IDB:m20")  # upstream horizontal
TDSX = motor("14IDB:m21")  # downstream horizontal
TDSZ = motor("14IDB:m22")  # downstream along X-ray beam (not used yet)

table_motors = [TUSX,TDSX,TOUTY,TINY,TDSY]

def reset_table():
  """ This is to bring the table in a well defined state after it was moved
  applying al the backlsh corrections"""
  step = 0.1
  for m in table_motors: m -= step; m.wait()
  for m in table_motors: m += step; m.wait()
