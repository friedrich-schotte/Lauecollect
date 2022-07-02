#!/usr/bin/env python
"""
Start a Python GUI module as an App bundle in macOS
Author: Friedrich Schotte
Date created: 2020-03-04
Date last modified: 2022-07-28
Revision comment: Updated examples
"""
__version__ = "1.1.4"


def start(module_name, command):
    """
    module: e.g. "Configuration_Table_Panel"
    command: e.g. "Configuration_Tables_Panel()"
        "Configuration_Table_Panel('methods')"
        "Configuration_Tables_Panel()"
    """
    make_app_bundle(module_name, command)
    launch(application_dir(module_name, command))


def make_app_bundle(module_name, command):
    # https://stackoverflow.com/questions/7404792/how-to-create-mac-application-bundle-for-python-script-via-python
    app_path = application_dir(module_name, command)

    info = """<?xml version="1.0" encoding="UTF-8"?>
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
      </dict>
    </plist>
    """

    update_file(app_path + "/Contents/Info.plist", info)
    update_file(app_path + "/Contents/PkgInfo", "APPL????")

    from sys import executable as python
    python_code = "from start import run; run(%r,%r)" % (module_name, command)
    command_line = f'{python} -c "%s"' % python_code.replace('"', r'\"')
    script = """#!/bin/zsh -l
    # The -l (login) option makes sure that the environment is the same as for
    # an interactive shell. 
    localdir=`dirname "$0"`
    cd "${localdir}/../../../../../.."
    exec %s >> ~/Library/Logs/Python.log 2>&1
    """ % command_line
    update_file(app_path + "/Contents/MacOS/core.sh", script)

    from os import stat, chmod
    mode = stat(app_path + "/Contents/MacOS/core.sh").st_mode
    chmod(app_path + "/Contents/MacOS/core.sh", mode | 0o111)

    icon = icon_filename(module_name, command)
    if icon:
        icon_data = open(icon, "rb").read()
        update_file(app_path + "/Contents/Resources/core.icns", icon_data)


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


def update_app_bundle(filename):
    """Reset the time stamp of the Application bundle top directory to the
    current time. This is needed for the icon to update in case the icon
    was changed"""
    app_path = app_bundle(filename)
    if app_path:
        update_dir(app_path)


def app_bundle(pathname):
    from os.path import dirname
    while not pathname.endswith(".app") and len(pathname) > 1:
        pathname = dirname(pathname)
    if not pathname.endswith(".app"):
        pathname = ""
    return pathname


def update_dir(directory):
    test_file = directory + "/.test"
    open(test_file, "w").write("test")
    from os import remove
    remove(test_file)


def icon_filename(module_name, command):
    icon_filename = ""
    module = __import__(module_name)
    class_name = command.split("(")[0]
    class_object = getattr(module, class_name)
    icon_names = []
    try:
        icon_names.append(getattr(class_object, "icon") + "")
    except (AttributeError, TypeError):
        pass
    icon_names.append(title(module_name, command))
    icon_names.append(module_name)
    icon_names.append("default")
    from os.path import exists
    for icon_name in icon_names:
        filename = icon_dir() + "/" + icon_name + ".icns"
        if exists(filename):
            icon_filename = filename
            break
    return icon_filename


def title(module_name, command):
    title = default_title(module_name, command)
    module = __import__(module_name)
    class_name = command.split("(")[0]
    class_object = getattr(module, class_name)
    try:
        title = getattr(class_object, "title") + ""
    except (AttributeError, TypeError):
        pass
    args = arguments(module_name, command).replace("_", " ")
    if args:
        title += " [" + args + "]"
    # Replace characters not allowed in file names.
    title = title.replace("/", "-")
    title = title.replace(":", "-")
    return title


def default_title(_module_name, command):
    """E.g. "Configuration_Table_Panel('method')" -> "Configuration [method]"
    """
    class_name = command.split("(")[0]
    title = class_name
    title = title.replace("Panel", "")
    # title = title.replace("Viewer","")
    title = title.rstrip("_")
    title = title.replace("_", " ")
    return title


def arguments(_module_name, command):
    args = ""
    if "(" in command:
        args = command.split("(", 1)[1].rstrip(")")
        # noinspection PyBroadException
        try:
            args = str(eval(args))
        except Exception:
            pass
    return args


def launch(app_path):
    """app_path: e.g. '/System/Applications/TextEdit.app' """
    script = f'''
        tell application "{app_path}"
            reopen
            activate
        end tell
    '''
    import subprocess
    subprocess.call(['/usr/bin/osascript', '-e', script])


def application_dir(module_name, command):
    return application_top_dir() + "/" + title(module_name, command) + ".app"


def application_top_dir():
    return module_dir() + "/launcher/macOS/auto-generated"


def icon_dir():
    return module_dir() + "/icons"


def module_dir():
    """The absolute pathname of this module"""
    from inspect import getfile
    pathname = getfile(module_dir)
    from os.path import dirname
    pathname = dirname(pathname)
    from os.path import isabs, join
    from os import getcwd
    if not isabs(pathname):
        pathname = join(getcwd(), pathname)
    from os.path import realpath
    pathname = realpath(pathname)
    return pathname


if __name__ == "__main__":
    domain_name = "BioCARS"
    config_name = f"{domain_name}.method"
    module_name, command = "Channel_Archiver_Viewer", "Channel_Archiver_Viewer(\'BioCARS\')"
    print('start("BioCARS_Panel","BioCARS_Panel()")')
    print('start("Servers_Panel","Servers_Panel()")')
    print('start("Server_Setup_Panel","Server_Setup_Panel()")')
    print(f'start("Configuration_Table_Panel","Configuration_Table_Panel({config_name!r})")')
    print(f'start("Configuration_Tables_Panel","Configuration_Tables_Panel({domain_name!r})")')
    print(f'start("Configuration_Setup_Panel","Configuration_Setup_Panel({config_name!r})")')
    print('start("Camera_Viewer","Camera_Viewer(\'MicroscopeCamera\')")')
    print('start("Camera_Viewer","Camera_Viewer(\'WideFieldCamera\')")')
    print('start("Scope_Panel","Scope_Panel(\'xray_scope\')")')
    print('start("Scope_Panel","Scope_Panel(\'laser_scope\')")')
    print('start("Servers_Panel","Servers_Panel(\'TestBench\')")')
    print('start("Channel_Archiver_Viewer","Channel_Archiver_Viewer(\'BioCARS\')")')
