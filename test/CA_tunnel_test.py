"""
EPICS Channel Access via SSH Tunnel

Setup required:
Edit script "NIH Tunnel.sh":
hosts = "... pico7.niddk.nih.gov ..."
ports="... 5064 5065 5066 ..."

Author: Friedrich Schotte
Date created: 2018-06-12
Date last modified: 2018-06-12
"""
from os import environ
from CA1 import caget,caput

environ["EPICS_CA_ADDR_LIST"] = "pico7.niddk.nih.gov"
print caget("NIH:TEMP.VAL")
