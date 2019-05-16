#!/usr/bin/env python
from CAServer import casput,casget
from CA import caput,caget,cainfo

casput("NIH:TEST.ARRAY",[])

print('caget("NIH:TEST.ARRAY")')
print('cainfo("NIH:TEST.ARRAY")')
print('caput("NIH:TEST.ARRAY",[])')
print('casget("NIH:TEST.ARRAY")')

