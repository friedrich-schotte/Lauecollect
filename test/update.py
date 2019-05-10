#!/usr/bin/python
"""
Friedrich Schotte, NIH, 6 Sep 2007
"""

def update(module): 
  """This allows you to reload a module previously loaded with 
  "from ... import *". This is useful if you have edited the module source
  file using an external editor and want to try out the new version without
  leaving the Python interpreter."""
  exec "import "+module
  exec "reload("+module+")"
  exec "from "+module+" import *"
