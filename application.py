"""
Run a GUI application as in an independent sub-process
Author: Friedrich Schotte
Date created: 2020-11-05
Date last modified: 2022-07-28
Revision comment: Updated example
"""
__version__ = "1.1.3"

from logging import warning


def application(*args, **kwargs):
    return application_type()(*args, **kwargs)


def application_type():
    from sys import platform
    if platform == 'darwin':
        from application_macos import Application_MacOS as application_type
    else:
        application_type = Application
    return application_type


class Application(object):
    domain_name = ""
    module_name = ""
    command = ""

    def __init__(self, name=None, domain_name=None, module_name=None, command=None):
        """
        module_name: e.g. "Configuration_Table_Panel"
        command: e.g. "Configuration_Tables_Panel('BioCARS')",
            "Configuration_Table_Panel('BioCARS.methods')"
        domain_name: e.g. "BioCARS", or "LaserLab"
        """
        if name is not None:
            self.name = name
        if module_name is not None:
            self.module_name = module_name
        if command is not None:
            self.command = command
        if domain_name is not None:
            self.domain_name = domain_name

    def __repr__(self):
        return "application(domain_name=%r, module_name=%r, command=%r)" % \
               (self.domain_name, self.module_name, self.command,)

    def get_name(self):
        return "%s.%s.%s" % (self.domain_name, self.module_name, self.command)

    def set_name(self, name):
        self.domain_name, self.module_name, self.command = name.split(".", 2)

    name = property(get_name, set_name)

    def run(self):
        from redirect import redirect
        redirect(self.logfile_basename)
        exec("from %s import *" % self.module_name)
        # import autoreload
        from wx_init import wx_init
        wx_init()
        import wx
        app = wx.GetApp() if wx.GetApp() else wx.App()
        import locale
        locale.setlocale(locale.LC_ALL, "")  # wxPython 4.1.0 sets it to "en-US"
        exec(self.command)
        app.MainLoop()

    @property
    def logfile_basename(self):
        if not self.domain_name:
            name = self.module_name
        else:
            name = "%s.%s" % (self.domain_name, self.module_name)
        return name

    @property
    def module_dir(self):
        from module_dir import module_dir
        return module_dir(type(self))

    def start(self):
        from os import chdir
        try:
            chdir(self.module_dir)
        except Exception as msg:
            warning("%s: %s" % (self.module_dir, msg))
        from subprocess import Popen
        Popen(self.command_line, stdin=None, stdout=None, stderr=None,
              close_fds=True)

    @property
    def command_line(self):
        from sys import executable as python
        command = "from application import application; %r.run()" % self
        command_line = [python, "-c", command]
        return command_line

    @property
    def title(self):
        module = __import__(self.module_name)
        class_name = self.command.split("(")[0]
        class_object = getattr(module, class_name)
        title = getattr(class_object, "title", None)
        if type(title) != str:
            title = self.default_title
        args = self.arguments.replace("_", " ")
        if args:
            title += " [" + args + "]"
        # Replace characters not allowed in file names.
        title = title.replace("/", "-")
        title = title.replace(":", "-")
        return title

    @property
    def icon_dir(self):
        return self.module_dir + "/icons"

    icon_extensions = [".ico", ".png"]

    def icon_filename_with_extensions(self, extensions):
        icon_name = self.icon_name_with_extensions(extensions)
        if icon_name:
            from os.path import exists
            basename = self.icon_dir + "/" + icon_name
            filenames = [basename + extension for extension in extensions]
            for filename in filenames:
                if exists(filename):
                    icon_filename = filename
                    break
            else:
                icon_filename = ""
                warning(f"No icon file found {filenames}")
        else:
            icon_filename = ""
        return icon_filename

    def icon_name_with_extensions(self, extensions):
        from os.path import exists

        module = __import__(self.module_name)
        class_name = self.command.split("(")[0]
        class_object = getattr(module, class_name)
        icon_names = []
        icon_name = getattr(class_object, "icon", None)
        if type(icon_name) == str:
            icon_names.append(icon_name)
        icon_names.append(self.title)
        icon_names.append(self.module_name)
        icon_names.append("default")
        for icon_name in icon_names:
            basename = self.icon_dir + "/" + icon_name
            filenames = [basename + extension for extension in extensions]
            if any([exists(filename) for filename in filenames]):
                break
        else:
            icon_name = "default"
        return icon_name

    @property
    def icon_filename(self):
        return self.icon_filename_with_extensions(self.icon_extensions)

    @property
    def icon_name(self):
        return self.icon_name_with_extensions(self.icon_extensions)

    @property
    def default_title(self):
        """E.g. "Configuration_Table_Panel('BioCARS.method')" -> "Configuration [BioCARS.method]"
        """
        class_name = self.command.split("(")[0]
        title = class_name
        title = title.replace("Panel", "")
        # title = title.replace("Viewer","")
        title = title.rstrip("_")
        title = title.replace("_", " ")
        return title


if __name__ == '__main__':
    # from pdb import pm  # for debugging
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    conf_name = "method"

    print(f'application("{domain_name}.{domain_name}_Panel.{domain_name}_Panel()").start()')
    print(f'application("{domain_name}.Servers_Panel.Servers_Panel(\'{domain_name}\')").start()')
    print(f'application("{domain_name}.Timing_Panel.Timing_Panel(\'{domain_name}\')").start()')
    print(f'application("{domain_name}.Configuration_Table_Panel.Configuration_Table_Panel(\'{domain_name}.{conf_name}\')").start()')
    print(f'application("{domain_name}.Configuration_Setup_Panel.Configuration_Setup_Panel(\'{domain_name}.{conf_name}\')").start()')
    print(f'application("{domain_name}.Configuration_Tables_Panel.Configuration_Tables_Panel(\'{domain_name}\')").start()')
    print(f'application("{domain_name}.Channel_Archiver_Viewer.Channel_Archiver_Viewer(\'{domain_name}\')").start()')

    print(f'application("{domain_name}.Camera_Viewer.Camera_Viewer(\'LaserLabCamera\')").start()')
    print(f'application("{domain_name}.Camera_Viewer.Camera_Viewer(\'MicroscopeCamera\')").start()')
    print(f'application("{domain_name}.Camera_Viewer.Camera_Viewer(\'WideFieldCamera\')").start()')

    print(f'application("{domain_name}.Scope_Panel.Scope_Panel(\'{domain_name}.laser_scope\')").start()')
    print(f'application("{domain_name}.Scope_Panel.Scope_Panel(\'{domain_name}.xray_scope\')").start()')
