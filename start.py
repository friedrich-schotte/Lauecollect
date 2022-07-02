"""
Run a Python command as in an independent sub-process
Author: Friedrich Schotte
Date created: 2018-12-05
Date last modified: 2022-06-28
Revision comment: Updated Example
"""
__version__ = "1.3.6"

from logging import warning


def start(module, command):
    """
    module: e.g. "Configuration_Table_Panel"
    command: e.g. "Configuration_Tables_Panel()"
    Configuration_Table_Panel(name="methods")
    Configuration_Tables_Panel()
    """
    from sys import platform
    if platform == 'darwin':
        from start_macos import start
        start(module, command)
    else:
        start_other(module, command)


def start_other(module, command):
    """
    module: e.g. "Configuration_Table_Panel"
    command: e.g. "Configuration_Tables_Panel()"
    Configuration_Table_Panel(name="methods")
    Configuration_Tables_Panel()
    """
    from module_dir import module_dir
    directory = module_dir(start)
    from os import chdir
    try:
        chdir(directory)
    except Exception as msg:
        warning("%s: %s" % (directory, msg))
    from subprocess import Popen
    Popen(command_line(module, command), stdin=None, stdout=None, stderr=None,
          close_fds=True)


def command_line(module, command):
    """
    module: e.g. "Configuration_Table_Panel"
    command: e.g. "Configuration_Tables_Panel()"
    """
    from sys import executable as python
    command = ("from start import run; run(%r,%r)" % (module, command))
    command_line = [python, "-c", command]
    return command_line


def run(module, command, level=None):
    """
    module: e.g. "Configuration_Table_Panel"
    command: e.g. "Configuration_Tables_Panel()"
    """
    from redirect import redirect
    redirect(module, level=level)
    exec("from %s import *" % module)
    # import autoreload
    import wx
    app = wx.GetApp() if wx.GetApp() else wx.App()
    import locale
    locale.setlocale(locale.LC_ALL, "")  # wxPython 4.1.0 sets it to "en-US"
    exec(command)
    app.MainLoop()


if __name__ == '__main__':
    # from pdb import pm  # for debugging
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    # name = "BioCARS.beamline_configuration"
    # name = "BioCARS.Julich_chopper_modes"
    # name = "BioCARS.heat_load_chopper_modes"
    # name = "BioCARS.timing_modes"
    # name = "BioCARS.sequence_modes"
    # name = "BioCARS.delay_configuration"
    # name = "BioCARS.temperature_configuration"
    # name = "BioCARS.power_configuration"
    # name = "BioCARS.scan_configuration"
    # name = "BioCARS.detector_configuration"
    # name = "BioCARS.diagnostics_configuration"
    name = "BioCARS.method"
    # name = "BioCARS.laser_optics_modes"
    # name = "BioCARS.alio_diffractometer_saved"

    # name = "LaserLab.timing_modes"
    # name = "LaserLab.sequence_modes"
    # name = "LaserLab.delay_configuration"
    # name = "LaserLab.temperature_configuration"
    # name = "LaserLab.power_configuration"
    # name = "LaserLab.scan_configuration"
    # name = "LaserLab.detector_configuration"
    # name = "LaserLab.diagnostics_configuration"
    # name = "LaserLab.method"

    domain_name = name.split(".")[0]

    module, command = "Configuration_Table_Panel", "Configuration_Table_Panel(name=%r)" % name
    print('start("BioCARS_Panel","BioCARS_Panel()")')
    print('start("Configuration_Table_Panel","Configuration_Table_Panel(%r)")' % name)
    print('start("Configuration_Tables_Panel","Configuration_Tables_Panel(%r)")' % domain_name)
    print('start("Configuration_Setup_Panel","Configuration_Setup_Panel(%r)")' % name)
