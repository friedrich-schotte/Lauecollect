import EPICS_CA.CA
import logging

EPICS_CA.CA.logger.level = logging.DEBUG
msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=msg_format)

PV_name = "BIOCARS:TIMING_SYSTEM.ACQUISITION.FIRST_SCAN_POINT"
value = 11088
# value = EPICS_CA.CA.caget(PV_name)
EPICS_CA.CA.caput(PV_name, value)
