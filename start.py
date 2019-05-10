"""
Run a Python command as in an independent sub-process
Author: Friedrich Schotte
Date created: 2018-12-05
Date last modified: 2019-01-30
"""
__version__ = "1.1" # using "redirect" to log error messages, including tracebacks

def start(module,command):
    """
    module: e.g. "SavedPositionsPanel_2"
    command: e.g. "ConfigurationsPanel()"
    SavedPositionsPanel(name="methods",globals=globals(),locals=locals())
    ConfigurationPanel(name="methods",globals=globals(),locals=locals())
    ConfigurationsPanel()
    """
    from module_dir import module_dir
    directory = module_dir(start)
    from os import chdir
    try: chdir(directory)
    except Exception,msg: warn("%s: %s" % (directory,msg))
    from subprocess import Popen
    Popen(command_line(module,command),stdin=None,stdout=None,stderr=None,
        close_fds=True)

def command_line(module,command):
    """
    module: e.g. "SavedPositionsPanel_2"
    command: e.g. "ConfigurationsPanel()"
    """
    from sys import executable as python
    command = ("from start import run; run(%r,%r)" % (module,command))
    command_line = [python,"-c",command]
    return command_line

def run(module,command):
    """
    module: e.g. "SavedPositionsPanel_2"
    command: e.g. "ConfigurationsPanel()"
    """
    from redirect import redirect
    redirect(module)
    import autoreload
    import wx
    if not hasattr(wx,"app"): wx.app = wx.App(redirect=False) 
    exec("from instrumentation import *") # -> locals()
    exec("from %s import *" % module) 
    exec(command)
    wx.app.MainLoop()    

def modulename(object):
    from inspect import getmodulename,getfile
    return getmodulename(getfile(object))


if __name__ == '__main__':
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )
    name = "detector_configuration"
    print('start("SavedPositionsPanel_2","ConfigurationsPanel()")')
    print('''start("SavedPositionsPanel_2","SavedPositionsPanel(name=%r,globals=globals(),locals=locals())")''' % name)
    print('''start("SavedPositionsPanel_2","ConfigurationPanel(name=%r,globals=globals(),locals=locals())")''' % name)
    print('''run("SavedPositionsPanel_2","SavedPositionsPanel(name=%r,globals=globals(),locals=locals())")''' % name)

