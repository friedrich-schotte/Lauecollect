import EPICS_CA.CA
from EPICS_CA.ca_protocol import CA_event
import logging

EPICS_CA.CA.logger.level = logging.DEBUG
msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
logging.basicConfig(level=logging.DEBUG, format=msg_format)

self = CA_event(value=["A"*55]*4416)
# self = CA_event(value=['A'*55]*291) # OK
# self = CA_event(value=['A'*55]*292) # not OK

