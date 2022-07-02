__version__ = "1.0"
import logging
level = logging.DEBUG
msg_format = "%(asctime)s: %(levelname)s %(module)s.%(funcName)s: %(message)s"
logging.basicConfig(level=level, format=msg_format)
logging.getLogger("EPICS_CA").level = level

PV_names = "TEST:TEST.VAL", "TEST:TEST.STRVAL"
values = [0,1], ["",""]
new_values = [1,2], ["ABC","DEF"]

from CAServer import casput, casget
for PV_name, value in zip(PV_names, values):
    casput(PV_name, value)

from CA import caput, caget
print("caget(PV_name)")
print("caput(PV_name, new_value)")
print("casget(PV_name)")
print("caget(PV_name)")



