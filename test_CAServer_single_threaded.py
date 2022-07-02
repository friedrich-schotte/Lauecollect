__version__ = "1.0"
import logging
level = logging.DEBUG
msg_format = "%(asctime)s: %(levelname)s %(module)s.%(funcName)s: %(message)s"
logging.basicConfig(level=level, format=msg_format)
logging.getLogger("EPICS_CA").level = level

PV_names = "TEST:TEST.VAL", "TEST:TEST.STR_VAL"
values = [0,1], ["ABC","DEF"]
new_values = [1,2], ["abc","def"]

from CAServer_single_threaded import casput, start, casget
for PV_name, value in zip(PV_names, values):
    casput(PV_name, value)
start()

from CA import caput, caget
print("caget(PV_name)")
print("caput(PV_name, new_values[1])")
print("casget(PV_name)")
print("caget(PV_name)")



