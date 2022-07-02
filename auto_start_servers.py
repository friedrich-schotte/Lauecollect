#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-07-03
Date last modified: 2021-09-15
Revision comment: Cleanup
"""
__version__ = "1.0.3"

from logging import info, error
from sys import argv

from redirect import redirect
from servers import Servers

domain_name = ""
# domain_name = "BioCARS"
# domain_name = "LaserLab"
# domain_name = "WetLab"
# domain_name = "TestBench"

if len(argv) > 1:
    domain_name = argv[1]

if domain_name:
    redirect(f"{domain_name}.auto_start_servers")
    info("domain_name = %r" % domain_name)
    servers = Servers(domain_name)
    servers.auto_start_local_servers()
else:
    error("Usage: %s domain_name" % argv[0])
