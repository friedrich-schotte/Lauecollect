#!/usr/bin/env python
"""
Start a Python GUI module as an App bundle in macOS
Author: Friedrich Schotte
Date created: 2020-11-05
Date last modified: 2022-08-07
Revision comment: Issue: App not launching on M1 Mac
   Traceback (most recent call last):
   File "<string>", line 1, in <module>
   File site-packages/wx/__init__.py, line 17, in <module>
      from wx.core import *
   File site-packages/wx/core.py, line 12, in <module>
       from ._core import *
   ImportError: dynamic module does not define module export function (PyInit__core)
"""
__version__ = "1.1.1"

from application import Application


class Application_MacOS(Application):
    def start(self):
        self.update_app_bundle()
        super().start()

    @property
    def apple_script(self):
        script = [
            f'tell application "{self.application_dir}" to launch',
            f'tell application "{self.application_dir}" to activate',
        ]
        script = "\n".join(script)
        return script

    @property
    def shell_script(self):
        script = [f"osascript -e '{line}'" for line in self.apple_script.splitlines()]
        script = "; ".join(script)
        return script

    @property
    def command_line(self):
        command_line = ['/bin/zsh', '-c', self.shell_script]
        return command_line

    def update_app_bundle(self):
        # https://stackoverflow.com/questions/7404792/how-to-create-mac-application-bundle-for-python-script-via-python
        app_path = self.application_dir
        update_file(app_path + "/Contents/Info.plist", self.bundle_info)
        update_file(app_path + "/Contents/PkgInfo", "APPL????")

        from sys import executable
        from os.path import basename, dirname
        python = basename(executable)
        python_path = dirname(executable)
        python_code = "from application import application; %r.run()" % self
        command_line = f'{python} -c "%s"' % python_code.replace('"', r'\"')
        script = """#!/bin/zsh -l
        # The -l (login) option makes sure that the environment is the same as for
        # an interactive shell. 
        if uname -v | grep -qi arm64 && [ `arch` != arm64 ] ; then
            echo "Switching from `arch` to arm64."
            exec arch -arm64 "$0"
        fi
        localdir=`dirname "$0"`
        cd "${localdir}/../../../../../.."
        export PATH=%s:$PATH
        exec %s >> ~/Library/Logs/Python.log 2>&1
        """ % (python_path, command_line)
        update_file(app_path + "/Contents/MacOS/core.sh", script)

        from os import stat, chmod
        mode = stat(app_path + "/Contents/MacOS/core.sh").st_mode
        chmod(app_path + "/Contents/MacOS/core.sh", mode | 0o111)

        if self.launcher_icon_filename:
            icon_data = open(self.launcher_icon_filename, "rb").read()
            update_file(app_path + "/Contents/Resources/core.icns", icon_data)

    @property
    def launcher_icon_filename(self):
        return self.icon_filename_with_extensions([".icns"])

    @property
    def bundle_info(self):
        # https://stackoverflow.com/questions/7404792/how-to-create-mac-application-bundle-for-python-script-via-python
        # https://stackoverflow.com/questions/22697006/using-applescript-to-selectively-activate-one-instance-of-an-app-with-two-runnin
        from xml.sax.saxutils import escape
        info = f"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
          <dict>
            <key>CFBundleExecutable</key>
            <string>core.sh</string>
            <key>CFBundleIconFile</key>
            <string>core.icns</string>
            <key>CFBundlePackageType</key>
            <string>APPL</string>
            <key>CFBundleSignature</key>
            <string>????</string>
            <key>CFBundleName</key>
            <string>{escape(self.bundle_name)}</string>
            <key>CFBundleIdentifier</key>
            <string>{escape(self.bundle_identifier)}</string>
            <key>CFBundleDisplayName</key>
            <string>{escape(self.title)}</string>
            <key>CFDisplayName</key>
            <string>{escape(self.title)}</string>
            <key>LSMultipleInstancesProhibited</key>
            <true/>
          </dict>
        </plist>
        """
        return info

    @property
    def bundle_name(self):
        name = self.title
        name = "".join([c for c in name if c.isalnum() or c == " "])
        name = name.replace("  ", " ")
        name = name.replace(" ", "_")
        name = name.lower()
        return name

    @property
    def bundle_identifier(self):
        return f"gov.nih.niddk.lauecollect.{self.domain_name}.{self.bundle_name}".lower()

    @property
    def arguments(self):
        args = ""
        if "(" in self.command:
            args = self.command.split("(", 1)[1].rstrip(")")
            try:
                args = str(eval(args))
            except Exception:
                pass
        return args

    @property
    def application_dir(self):
        return self.application_top_dir + "/" + self.title + ".app"

    @property
    def application_top_dir(self):
        return self.module_dir + "/launcher/macOS/auto-generated"


def app_bundle(pathname):
    from os.path import dirname
    while not pathname.endswith(".app") and len(pathname) > 1:
        pathname = dirname(pathname)
    if not pathname.endswith(".app"):
        pathname = ""
    return pathname


def update_dir(directory):
    from os import utime
    from time import time
    # If the bundle is not at least 5 minutes old, multiple instance are launched
    timestamp = time() - 300
    utime(directory, (-1, timestamp))


def update_app_bundle(filename):
    """Reset the time stamp of the Application bundle top directory to the
    current time. This is needed for the icon to update in case the icon
    was changed"""
    app_path = app_bundle(filename)
    if app_path:
        update_dir(app_path)


def update_file(filename, content):
    if type(content) != bytes:
        content = content.encode("UTF-8")
    from os import makedirs
    from os.path import dirname, exists
    directory = dirname(filename)
    if not exists(directory):
        makedirs(directory)
    if exists(filename):
        old_content = open(filename, "rb").read()
    else:
        old_content = b""
    if content != old_content:
        open(filename, "wb").write(content)
        update_app_bundle(filename)


if __name__ == "__main__":
    # from pdb import pm  # for debugging
    import logging

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s",
    )

    domain_name = "BioCARS"
    # domain_name = "LaserLab"
    conf_name = "method"

    # self = Application_MacOS(f"{domain_name}.{domain_name}_Panel.{domain_name}_Panel()")
    self = Application_MacOS(f"{domain_name}.Timing_Panel.Timing_Panel(\'{domain_name}\')")
    # self = Application_MacOS(f"{domain_name}.Servers_Panel.Servers_Panel(\'{domain_name}\')")
