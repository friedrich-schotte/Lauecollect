"""
Rename files in a traceble, reversible, and tranparent way, using symbolic links

Example:
>>> test_setup()

(base) friedrich@dk0502145857 ~ % ls -lR /tmp/save_rename_test
total 24
-rw-r--r--  1 friedrich  wheel  2 Sep  9 21:39 1
-rw-r--r--  1 friedrich  wheel  2 Sep  9 21:39 2
-rw-r--r--  1 friedrich  wheel  2 Sep  9 21:39 3

>>> source_filenames
['/tmp/save_rename_test/1', '/tmp/save_rename_test/2', '/tmp/save_rename_test/3']
>>> destination_filenames
['/tmp/save_rename_test/2', '/tmp/save_rename_test/3', '/tmp/save_rename_test/1']
>>> save_rename_files(source_filenames, destination_filenames)

(base) friedrich@dk0502145857 ~ % ls -lR /tmp/save_rename_test
total 0
lrwxr-xr-x  1 friedrich  wheel   10 Sep  9 21:36 1 -> original/3
lrwxr-xr-x  1 friedrich  wheel   10 Sep  9 21:36 2 -> original/1
lrwxr-xr-x  1 friedrich  wheel   10 Sep  9 21:36 3 -> original/2
drwxr-xr-x  5 friedrich  wheel  160 Sep  9 21:36 original

/tmp/save_rename_test/original:
total 24
-rw-r--r--  1 friedrich  wheel  2 Sep  9 21:36 1
-rw-r--r--  1 friedrich  wheel  2 Sep  9 21:36 2
-rw-r--r--  1 friedrich  wheel  2 Sep  9 21:36 3

Author: Friedrich Schotte
Date created: 2021-09-09
Date last modified: 2021-09-21
Revision comment: Added: Checking length of source_filenames, destination_filenames
"""
__version__ = "1.0.4"

import logging
from os import makedirs, rename, symlink, readlink, unlink, listdir, rmdir
from os.path import exists, islink, dirname, isdir, basename, relpath, normpath, isabs, isfile

logger = logging.getLogger(__name__)
if not logger.level:
    logger.level = logging.INFO


def save_rename_files(source_filenames, destination_filenames, dry_run=False):
    assert len(source_filenames) == len(destination_filenames)

    delete_filenames = filenames_to_delete(source_filenames, destination_filenames)
    source_filenames, destination_filenames = filenames_to_rename(source_filenames, destination_filenames)

    if delete_filenames:
        logger.info(f"Deleting {len(delete_filenames)} files:")
    for filename in delete_filenames:
        logger.info(f"Deleting {filename!r}")

    if source_filenames:
        logger.info(f"Renaming {len(source_filenames)} files:")
    for source_filename, destination_filename in zip(source_filenames, destination_filenames):
        logger.info(f"Renaming {source_filename!r} to {destination_filename!r}")

    if not dry_run:
        filenames = set(delete_filenames + source_filenames + destination_filenames)
        for filename in filenames:
            create_backup(filename)
        original_filename = {}
        for filename in filenames:
            original_filename[filename] = symlink_target_abs_path(filename)

        for filename in filenames:
            if filename not in destination_filenames:
                remove_symlink(filename)

        for filename in delete_filenames:
            remove_symlink(filename)

        for source_filename, destination_filename in zip(source_filenames, destination_filenames):
            destination_directory = dirname(destination_filename)
            if not exists(destination_directory):
                makedirs(destination_directory)
            target = original_filename[source_filename]
            target_relative_path = relpath(target, dirname(destination_filename))
            create_symlink(target_relative_path, destination_filename)

        for destination_filename in destination_filenames:
            simplify(destination_filename)


def rollback_directory(toplevel_directory, dry_run=False):
    try:
        from scandir import walk
    except ImportError:
        from os import walk

    for (directory, subdirs, files) in walk(toplevel_directory):
        rollback_single_directory(directory, dry_run)


def rollback_single_directory(directory, dry_run=False):
    for filename in listdir(directory):
        filename = directory + "/" + filename
        symlink_target = symlink_content(filename)
        if symlink_target.startswith("original/"):
            logger.info(f"Removing link {filename!r} -> {symlink_target!r}")
            if not dry_run:
                remove_symlink(filename)
    backup_directory = directory + "/" + "original"
    if isdir(backup_directory):
        for filename in listdir(backup_directory):
            filename = backup_directory + "/" + filename
            original_filename = directory + "/" + basename(filename)
            logger.info(f"Moving {filename!r} to {original_filename!r}")
            if not dry_run:
                move_without_overwriting(filename, original_filename)
        logger.info(f"Removing {backup_directory!r} (if emtpy)")
        if not dry_run:
            remove_directory_if_empty(backup_directory)


def filenames_to_delete(source_filenames, destination_filenames):
    filenames_to_delete = []
    my_source_filenames = {}
    for source_filename, destination_filename in zip(source_filenames, destination_filenames):
        if destination_filename:
            if destination_filename in my_source_filenames.keys():
                filename_to_delete = my_source_filenames[destination_filename]
                if filename_to_delete not in filenames_to_delete:
                    filenames_to_delete.append(filename_to_delete)
                del my_source_filenames[destination_filename]
            my_source_filenames[destination_filename] = source_filename
    for source_filename, destination_filename in zip(source_filenames, destination_filenames):
        if not destination_filename:
            if source_filename not in my_source_filenames.values():
                filename_to_delete = source_filename
                if filename_to_delete not in filenames_to_delete:
                    filenames_to_delete.append(filename_to_delete)
    return filenames_to_delete


def filenames_to_rename(source_filenames, destination_filenames):
    original_filenames = {}
    for source_filename, destination_filename in zip(source_filenames, destination_filenames):
        if destination_filename:
            original_filenames[destination_filename] = source_filename

    source_filenames_to_rename = []
    destination_filenames_to_rename = []

    for destination_filename in destination_filenames:
        if destination_filename:
            source_filename = original_filenames[destination_filename]
            if source_filename != destination_filename:
                if destination_filename not in destination_filenames_to_rename:
                    source_filenames_to_rename.append(source_filename)
                    destination_filenames_to_rename.append(destination_filename)
    return source_filenames_to_rename, destination_filenames_to_rename


def create_backup(filename):
    if exists(filename) and not islink(filename):
        backup_directory = dirname(filename) + "/" + "original"
        if not isdir(backup_directory):
            makedirs(backup_directory)
        backup_filename = backup_directory + "/" + basename(filename)
        move_without_overwriting(filename, backup_filename)
        backup_file_relative_path = relpath(backup_filename, dirname(filename))
        create_symlink(backup_file_relative_path, filename)


def simplify(filename):
    backup_directory = dirname(filename) + "/" + "original"
    backup_filename = backup_directory + "/" + basename(filename)
    backup_file_relative_path = relpath(backup_filename, dirname(filename))
    if symlink_content(filename) == backup_file_relative_path:
        remove_symlink(filename)
        move_without_overwriting(backup_filename, filename)
        remove_directory_if_empty(backup_directory)


def move_without_overwriting(source_filename, destination_filename):
    if not isfile(destination_filename):
        rename(source_filename, destination_filename)
    else:
        logger.warning(f"Not overwriting file {destination_filename} with {source_filename}")


def create_symlink(target_pathname, symlink_pathname):
    if symlink_content(symlink_pathname) != target_pathname:
        remove_symlink(symlink_pathname)
        symlink(target_pathname, symlink_pathname)


def remove_symlink(filename):
    if exists(filename):
        if islink(filename):
            unlink(filename)
        else:
            logger.warning(f"Not removing {filename!r} because it is not a link.")


def symlink_content(filename):
    if islink(filename):
        content = readlink(filename)
    else:
        content = ""
    return content


def symlink_target_abs_path(filename):
    target = filename
    if islink(filename):
        target = readlink(filename)
        if not isabs(target):
            target = normpath(dirname(filename) + "/" + target)
    return target


def remove_directory_if_empty(backup_directory):
    if not listdir(backup_directory):
        rmdir(backup_directory)


if __name__ == "__main__":
    from numpy import array

    msg_format = "%(asctime)s %(levelname)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    test_dir = "/tmp/save_rename_test"
    test_names = [f"{i + 1}" for i in range(0, 4)]
    test_filenames = [f"{test_dir}/{name}" for name in test_names]
    test_contents = [f"{name}\n" for name in test_names]

    source_filenames = test_filenames
    destination_filenames = array(test_filenames)[[0, 1, 1, 3]].tolist()
    # destination_filenames = [source_filenames[1], source_filenames[2], "", ""]


    def test_setup():
        from shutil import rmtree
        if exists(test_dir):
            rmtree(test_dir)
        makedirs(test_dir)
        for filename, content in zip(test_filenames, test_contents):
            open(filename, "w").write(content)


    def test(dry_run=False):
        save_rename_files(source_filenames, destination_filenames, dry_run)

    def test_rollback(dry_run=False):
        rollback_directory(test_dir, dry_run)

    print("test_setup()")
    print("test()")
    print("test_rollback()")
