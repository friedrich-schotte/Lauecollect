#!/usr/bin/env python
"""
Author: Friedrich Schotte
Date created: 2020-03-04
Date last modified: 2022-07-07
Revision comment: Issue: Diff option missing:
cp -p ../Lauecollect/monitored_property_2_1_1.py ../backup/Lauecollect/monitored_property-2.1.1.py (New)? (Yes/No)
"""
__version__ = "1.16.14"

from logging import warning


def auto_backup(confirm=True, preview=False, file_type="*.py"):
    try:
        if not preview:
            auto_backup(preview=True, file_type=file_type)
        for file in files(file_type=file_type):
            for backup_file in backup_files(file):
                if copied(file, backup_file, confirm, preview):
                    break
    except KeyboardInterrupt:
        pass


def backup_files(file):
    from os.path import exists
    version = file_version(file)
    backup_files = []
    if version:
        backup_file = backup_filename(file, version)
        if files_differ(file, backup_file):
            backup_files.append(backup_file)
        if exists(backup_file) and files_differ(file, backup_file):
            timestamp = file_timestamp(file)
            # backup_file = backup_filename(file, version + "-" + timestamp)
            ext = file_extension(backup_file)
            backup_file = backup_file.replace(ext, f"-{timestamp}{ext}")
            if files_differ(file, backup_file):
                if version.endswith(".0"):
                    backup_files.append(backup_file)
                else:
                    backup_files.insert(0, backup_file)
            else:
                backup_files = []
    else:
        last_backup_file = last_backup_filename(file)
        if files_differ(file, last_backup_file):
            timestamp = file_timestamp(file)
            backup_file = backup_filename(file, timestamp)
            if files_differ(file, backup_file):
                backup_files.append(backup_file)
    return backup_files


def copied(file, backup_file, confirm, preview):
    copied = False
    if copy_confirmed(file, backup_file, confirm, preview):
        copy(file, backup_file)
        copied = True
    return copied


def copy(file, backup_file):
    from os.path import exists, dirname
    from os import makedirs
    directory = dirname(backup_file)
    if directory and not exists(directory):
        makedirs(directory)
    from shutil import copy2
    copy2(file, backup_file)


def copy_confirmed(file, backup_file, confirm, preview):
    from os.path import exists
    option = "i" if exists(backup_file) else ""
    message = "cp -p%s %s %s" % (option, file, backup_file)
    if not exists(backup_file):
        message += " (New)"
    else:
        message += " (Overwrite)"

    if preview:
        print(message)
        confirmed = False
    elif confirm:
        last_backup_file = last_backup_filename(file)
        choices = ["Yes", "No"]
        if exists(backup_file) or exists(last_backup_file):
            choices = ["Yes", "Diff", "No"]
        default_choice = choices[0]
        choice = ""
        while choice not in ["Yes", "No"]:
            reply = input(message + "? (%s) " % "/".join(choices))
            if not reply:
                choice = default_choice
            else:
                for c in choices:
                    if c.upper().startswith(reply.upper()):
                        choice = c
                        break
                else:
                    choice = ""
            if choice == "Diff":
                if exists(backup_file):
                    ref_file = backup_file
                elif exists(last_backup_file):
                    ref_file = last_backup_file
                else:
                    ref_file = ""
                if ref_file:
                    print(diff(file, ref_file))
        confirmed = choice in ["Yes"]
    else:
        confirmed = True

    return confirmed


def diff(file, backup_file):
    import difflib

    text = f"diff {file} {backup_file}\n"

    lines1 = normalize(file_content(file).splitlines())
    lines2 = normalize(file_content(backup_file).splitlines())

    lines = difflib.ndiff(lines2, lines1)
    lines = (line for line in lines if not line.startswith(' '))
    text += ''.join(lines)
    return text


def normalize(lines):
    lines = [line.rstrip() + "\n\r" for line in lines]
    return lines


def backup_filename(file, version):
    extension = file_extension(file)
    backup_file = file.replace("../", "../backup/")

    partial_version = version
    while partial_version:
        ending = "_" + partial_version.replace(".", "_") + extension
        if backup_file.endswith(ending):
            backup_file = backup_file.replace(ending, "-" + version + extension)
            break
        partial_version = ".".join(partial_version.split(".")[0:-1])
    else:
        new_ending = "-" + version + extension
        if not backup_file.endswith(new_ending):
            backup_file = backup_file.replace(extension, new_ending)
    return backup_file


def last_backup_filename(file):
    version = file_version(file)
    filename = versioned_last_backup_filename(file, version)
    version = ".".join(version.split(".")[0:-1])
    while not filename and version:
        filename = versioned_last_backup_filename(file, version)
        version = ".".join(version.split(".")[0:-1])
    return filename


def versioned_last_backup_filename(file, version):
    file_template = file.replace("../", "../backup/")
    from re import sub
    if version:
        file_template = sub("_([0-9_]+)[.]py", ".py", file_template)
        file_template = sub(r"([^*]).py", rf"\1-{version}.*.py", file_template)
    else:
        file_template = file_template.replace(".py", "-20??????_??????Z.py")
    from glob import glob
    file_candidates = glob(file_template)
    if len(file_candidates) > 0:
        times = [getmtime(file) for file in file_candidates]
        oldest = times.index(max(times))
        filename = file_candidates[oldest]
    else:
        filename = ""
    return filename


def file_major_version(file):
    return file_version(file).split(".")[0]


def files(file_type="*.py"):
    from find import find
    files = []
    for directory in directories():
        files += find(directory, file_type, exclude="*/.AppleDouble/*")
    files = [file for file in files if do_backup(file)]
    files = sorted(files)
    files = [f for f in files if "/settings/" not in f] + [f for f in files if "/settings/" in f]
    return files


def do_backup(pathname):
    do_backup = True
    if "/." in pathname:
        do_backup = False
    if "_new.py" in pathname:
        do_backup = False
    if "_old.py" in pathname:
        do_backup = False
    if pathname.endswith(".txt") and "/settings/" not in pathname:
        do_backup = False
    return do_backup


def directories():
    directories = ["../Lauecollect", "../EPICS_CA/EPICS_CA"]
    return directories


def auto_backup_preview():
    auto_backup(preview=True)


def files_differ(file, backup_file):
    dt = getmtime(file) - getmtime(backup_file)
    ds = getsize(file) - getsize(backup_file)
    metadata_differ = not (abs(dt) < 1 and ds == 0)
    if not metadata_differ:
        files_differ = False
    else:
        files_differ = file_content(file) != file_content(backup_file)
    return files_differ


def getmtime(file):
    t = 0
    from os.path import getmtime
    try:
        t = getmtime(file)
    except OSError:
        pass
    return t


def getsize(file):
    size = 0
    from os.path import getsize
    try:
        size = getsize(file)
    except OSError:
        pass
    return size


def file_content(file):
    content = ""
    from os.path import exists
    if exists(file):
        try:
            content = open(file).read()
        except UnicodeDecodeError:
            content = open(file, encoding="latin-1").read()
    return content


def file_version_or_timestamp(file):
    version = ""
    if version == "":
        version = file_version(file)
    if version == "":
        version = file_timestamp(file)
    return version


def file_version(file):
    version = ""
    if version == "":
        version = file_python_version(file)
    if version == "":
        version = file_rcs_version(file)
    return version


def file_python_version(file):
    version = get_tag(file, "__version__")
    if type(version) != str:
        warning("%s: __version__ = %r: Should be string" % (file, version))
        version = str(version)
    if version.endswith("."):
        warning("%s: __version__ = %r: Unexpected ending ." % (file, version))
        version = version.rstrip(".")
    return version


def file_rcs_version(file):
    version = ""
    rcsid = get_tag(file, "_rcsid")
    words = rcsid.split(" ")
    if len(words) >= 2:
        version = words[1]
    return version


def get_tag(file, name):
    # __version__ = "1.0"
    # _rcsid="example.py,v 1.6 2003/05/30 13:29:23 author Release-20050805"
    value = ""
    content = file_content(file)
    keyword = name
    begin = content.find(keyword)
    if begin != -1:
        length = content[begin:].find('\n')
        if length == -1:
            length = len(content[begin:])
        end = begin + length
        line = content[begin:end]
        # noinspection PyBroadException
        try:
            exec(line)
        except Exception:
            pass
        if name in locals():
            value = locals()[name]
    return value


def file_extension(file):
    from os.path import splitext
    return splitext(file)[1]


def file_timestamp(file):
    from os.path import getmtime
    t = getmtime(file)
    from datetime import datetime
    d = datetime.utcfromtimestamp(t)
    timestamp = d.strftime("%Y%m%d_%H%M%SZ")
    return timestamp


try:
    # Needed for compatibility with PyCharm's Python Console
    from console_thrift import KeyboardInterruptException as KeyboardInterrupt  # noqa
except ImportError:
    pass

if __name__ == "__main__":
    import logging

    for handler in list(logging.root.handlers):
        logging.root.removeHandler(handler)
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")

    auto_backup()
    # auto_backup(file_type="*_settings.txt", confirm=True)
    # auto_backup(file_type="*/table/*.txt", confirm=True)
    # auto_backup(file_type="*/configuration/*_settings.txt", confirm=True)
    # auto_backup(file_type="*/servers/*_settings.txt", confirm=True)
