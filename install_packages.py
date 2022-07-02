#!/usr/bin/env python
"""Install necessary modules to run the Python code in the directory
Authors: Friedrich Schotte
Date created: 2019-11-07
Date last modified: 2021-05-12
Revision comment: Cleanup
"""
__version__ = "1.1.1"

from packages import install_packages
import logging
logging.basicConfig(level=logging.INFO,format="%(message)s")
install_packages()
