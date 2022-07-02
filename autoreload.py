"""
Dynamically refresh Python code

Author: Friedrich Schotte
Date created: 2017-07-08
Date last modified: 2020-03-14
Revision comment: Disabled automatic reload, kept module for compatbility
"""
__version__ = "2.0"
try: from IPython.extensions.autoreload import *
except: pass
