#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2021-09-15
Date last modified: 2021-09-15
Revision comment:
"""
__version__ = "1.0"

from logging import debug, info, error
from sys import argv

from redirect import redirect
from servers import Local_Startup_Server

domain_name = ""
# domain_name = "BioCARS"
# domain_name = "LaserLab"
# domain_name = "WetLab"
# domain_name = "TestBench"

domain_names = [
    "BioCARS",
    "LaserLab",
    "WetLab",
    "TestBench",
]

if len(argv) > 1:
    domain_name = argv[1]

if domain_name:
    redirect(f"{domain_name}.auto_start_servers")
    startup_server = Local_Startup_Server(domain_name)
    info(f"{startup_server}.machine_name: {startup_server.machine_name}")
    if not startup_server.running:
        info(f"Starting {startup_server}...")
        startup_server.running = True
    else:
        info(f"{startup_server} already started")
else:
    error(f"Usage: {argv[0]} {'|'.join(domain_names)}")
