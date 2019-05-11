"""
Friedrich Schotte, APS 27 Oct 2007
The is to scan the Gigabaudics PADL3-10-11 delay line
control bit 3 has got a very high attenuation, making te Lock-to-Clock loose
synchtonization.
This is to perform a full range scan avioding the defective delay.
(50 % of the full range).
"""

from timing_system import *

class broken_delayline (object):
  def __init__(self,bit=3):
    object.__init__(self)
    self.name = "allowed count"
    self.bit = bit # broken bit

  def get_value(self):
    """reads current value and removes broken bit"""
    count = psd1.count
    count = int(round(count))
    low_mask = (1<<self.bit)-1
    high_mask = ~((1<<(self.bit+1))-1)
    allowed_count = ((count & high_mask)>>1) | (count & low_mask)
    return allowed_count
    
  def set_value(self,value):
    value = int(round(value))
    """insert bit 3 = before writing count to hardware"""
    low_mask = (1<<self.bit)-1
    high_mask = ~((1<<self.bit)-1)
    count = ((value & high_mask)<<1) | (value & low_mask)
    psd1.count = count

  value = property(get_value,set_value,doc="allowed count")

allowed_count = broken_delayline(bit=3)
