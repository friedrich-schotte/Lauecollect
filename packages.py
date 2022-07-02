#!/usr/bin/env python
"""Check whether the necessary modules are installed to run the Python code
in the directory
Authors: Friedrich Schotte, Valentyn Stadnytskyi
Date created: 2011-02-11
Date last modified: 2022-07-01
Revision comment: Using importlib metadata
"""
__version__ = "2.12"

from logging import info

module_names = {
    "all": [
        "wx",
        "numpy",
        "scipy",
        "matplotlib",
        "PIL",
        "pyaudio",
        "serial",
        "psutil",
        "watchdog",
        "h5py",
        "msgpack",
        "msgpack_numpy",
        "pytz",
        "tzlocal",
        "EPICS_CA",
        "scandir",
    ],
    "python3": [
        "caproto",
        "ubcs_auxiliary",
        "circular_buffer_numpy",
        "syringe_pump",
        "dataq_di_245",
        "usb",
        "epics",
    ],
    "win32": [
        "win32file",
        "win32con",
        "win32event",
    ],
    "darwin": [
    ],
    "posix": [
    ],
    "anaconda": [
        "conda",
    ]
}


def check_module(module_name):
    if module_installed(module_name):
        version = module_version(module_name)
        comment = ""
        if has_local_repository(module_name) and not is_local_module(module_name):
            comment = "try:\n"
            comment += "%s\n" % command_string(uninstall_pypi_module_command(module_name))
            comment += "%s\n" % command_string(install_local_module_command(module_name))
        elif is_local_module(module_name):
            comment = "editable"
        comment = " (%s)" % comment if comment else ""
        print("%s %s%s" % (module_name, version, comment))
    else:
        print("%s not installed (try: %s)" %
              (module_name, command_string(install_module_command(module_name))))
        if special_installation(module_name):
            print("%s\n" % special_installation(module_name))


def special_installation(module_name):
    instruction = ""
    if module_name == "pyaudio":
        from sys import platform
        if platform == "win32":
            instruction = "try: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio\n"
            instruction += "pip3 install PyAudio-0.2.11-cp38-cp38-win_amd64.whl"
        if platform == "darwin":
            instruction = "try: brew install portaudio"
        if platform == "posix":
            instruction = "try: sudo apt install portaudio\n"
            instruction += "sudo apt install portaudio19-dev"
    return instruction


def module_installed(module_name):
    installed = False
    # noinspection PyBroadException
    try:
        exec("import %s" % module_name)
        installed = True
    except ImportError:
        pass
    except Exception:
        installed = True
    return installed


def module_properly_installed(module_name):
    if not module_installed(module_name):
        return False
    if has_local_repository(module_name) and not is_local_module(module_name):
        return False
    return True


def install_module(module_name):
    command_line = install_module_command(module_name)
    info("Running %r..." % command_string(command_line))
    from subprocess import call
    status = call(command_line)
    if status != 0 and special_installation(module_name):
        info(special_installation(module_name))


def uninstall_module(module_name):
    command_line = uninstall_module_command(module_name)
    info("Running %r..." % command_string(command_line))
    from subprocess import call
    call(command_line)


def install_module_command(module_name):
    if has_local_repository(module_name):
        command = install_local_module_command(module_name)
    else:
        command = install_pypi_module_command(module_name)
    return command


def uninstall_module_command(module_name):
    if has_local_repository(module_name):
        command = uninstall_local_module_command(module_name)
    else:
        command = uninstall_pypi_module_command(module_name)
    return command


def install_pypi_module_command(module_name):
    name = package_name(module_name)
    inst = installer(module_name)
    from sys import executable as python
    command = [python, "-m", inst]
    if inst == "conda":
        command = ["conda"]
    options = []
    if inst == "conda":
        options = ["--yes"]
    command_line = command + ["install"] + options + [name]
    return command_line


def uninstall_pypi_module_command(module_name):
    name = package_name(module_name)
    inst = installer(module_name)
    from sys import executable as python
    command = [python, "-m", inst]
    if inst == "conda":
        command = ["conda"]
    command_line = command + ["uninstall", "--yes", name]
    return command_line


def install_local_module_command(module_name):
    pathname = local_repository_dir(module_name)
    from sys import executable as python
    command = [python, "-m", "pip"]
    command_line = command + ["install", "-e", pathname]
    return command_line


def uninstall_local_module_command(module_name):
    pathname = local_repository_dir(module_name)
    from sys import executable as python
    command = [python, "-m", "pip"]
    command_line = command + ["uninstall", "-e", pathname]
    return command_line


def command_string(command_line):
    """Command line: list of strings"""
    command_line = [('"' + w + '"' if " " in w else w) for w in command_line]
    string = " ".join(command_line)
    return string


def has_local_repository(module_name):
    from os.path import exists
    return exists(local_repository_dir(module_name))


def is_local_module(module_name):
    """Was this package installed with 'pip install -e ...'?"""
    return is_subdir(installation_dir(module_name), local_repository_top_dir())


def is_subdir(directory, top_dir):
    directory = normpath(directory)
    top_dir = normpath(top_dir)
    is_subdir = directory.startswith(top_dir)
    return is_subdir


def normpath(path):
    from os.path import normpath
    path = normpath(path)
    from sys import platform
    if platform == "win32":
        path = path.lower()
    return path


def installation_dir(module_name):
    # noinspection PyBroadException
    try:
        exec("import %s" % module_name)
    except Exception:
        module = None
    else:
        module = eval(module_name)
    from inspect import getfile
    from os.path import dirname
    # noinspection PyBroadException
    try:
        path = dirname(getfile(module))
    except Exception:
        path = ""
    return path


def local_repository_dir(module_name):
    """For our own in-house developed packages
    'EPICS_CA', 'ubcs_auxiliary'"""
    return local_repository_top_dir() + "/" + package_name(module_name)


def local_repository_top_dir():
    """For our own in-house developed packages
    'EPICS_CA', 'ubcs_auxiliary', ..."""
    from os.path import dirname
    pathname = dirname(module_dir())
    return pathname


def installer(module_name):
    """'pip' or 'conda'"""
    installer = default_installer()
    if package_name(module_name) in pip_only_packages:
        installer = "pip"
    return installer


pip_only_packages = [
    "msgpack",
    "msgpack_numpy",
    "pyusb",
    "ubcs_auxiliary",
    "circular_buffer_numpy",
    "syringe_pump",
    "dataq_di_245",
]


def default_installer():
    """'pip' or 'conda'"""
    installer = "pip"
    if anaconda_detected():
        installer = "conda"
    return installer


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


def package_name(module_name):
    """Which name needs to be passed to pip to install a Python module
    Normally, the PyPI package has the same, but there are a few exceptions"""
    package_name = module_name
    if module_name == "wx":
        package_name = "wxPython"
    if module_name == "PIL":
        package_name = "Pillow"
    if module_name == "serial":
        package_name = "pyserial"
    if module_name == "usb":
        package_name = "pyusb"
    if module_name == "win32file":
        package_name = "pywin32"
    if module_name == "win32event":
        package_name = "pywin32"
    if module_name == "win32con":
        package_name = "pywin32"
    if module_name == "epics":
        package_name = "pyepics"
    if module_name == "psutil":
        # psutil 3.4.2 is the latest version which supports Windows 2000,
        # XP and 2003 server
        if windows_version() == "5.1":
            package_name += "==3.4.2"
    return package_name


def module_version(module_name):
    version = pip_version(module_name)
    if not version:
        version = module_internal_version(module_name)
    return version


def pip_version(module_name):
    from importlib import metadata
    version = ""
    project_name = package_name(module_name)
    for dist in metadata.distributions():
        name = dist.metadata["Name"]
        if package_name_matches(name, project_name):
            version = dist.version
    return version


def module_internal_version(module_name):
    version = ""
    try:
        module = __import__(module_name)
    except ImportError:
        module = None
    if hasattr(module, "__version__"):
        version = module.__version__
    return version


def package_name_matches(p1, p2):
    return p1.replace("-", "_").lower() == p2.replace("-", "_").lower()


def list_packages():
    from importlib import metadata
    package_list = []
    for dist in metadata.distributions():
        name = dist.metadata["Name"]
        version = dist.version
        package_list.append(f"{name} {version}")
    package_list.sort()
    package_list = "\n".join(package_list)
    print(package_list)


def check_packages():
    for platform_version in module_names:
        if required(platform_version):
            for module_name in module_names[platform_version]:
                check_module(module_name)


def install_packages():
    for platform_version in module_names:
        if required(platform_version):
            for module_name in module_names[platform_version]:
                if not module_properly_installed(module_name):
                    install_module(module_name)


def required(platform_version):
    """Should a package be installed on this machine?"""
    required = False
    if platform_version == "all":
        required = True
    from sys import platform
    if platform_version.startswith(platform):
        required = True
    if platform_version.endswith("python" + python_version()):
        required = True
    if "anaconda" in platform_version and anaconda_detected():
        required = True
    return required


def python_version():
    import sys
    version = str(sys.version_info.major)
    return version


def windows_version():
    version = ""
    try:
        from sys import getwindowsversion
    except ImportError:
        getwindowsversion = None
    if getwindowsversion:
        v = getwindowsversion()
        version = "%s.%s" % (v.major, v.minor)
    return version


def anaconda_detected():
    detected = False
    from sys import executable
    detected = detected or "anaconda" in executable.lower()
    from sys import version
    detected = detected or "anaconda" in version.lower()
    return detected


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    print("check_packages()")
    print("install_packages()")
