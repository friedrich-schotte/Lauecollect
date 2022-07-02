"""
Author: Friedrich Schotte
Date created: 2011-03-02
Date last modified: 2021-10-22
Revision comment: Sorting files by name
"""
__version__ = "1.2.5"

from typing import Union, Iterable


def find(topdir, name: Union[str, Iterable[str]], exclude: Union[str, Iterable[str]] = None):
    """A list of files on directory 'topdir' matching the patterns given by
    'name', excluding those matching thw patterns ''given by 'exclude'"""
    try:
        from scandir import walk
    except ImportError:
        from os import walk
    import re
    if type(name) == str:
        name = [name]
    if exclude is None:
        exclude = []
    if type(exclude) == str:
        exclude = [exclude]
    name = [re.compile(glob_to_regex(pattern)) for pattern in name]
    exclude = [re.compile(glob_to_regex(pattern)) for pattern in exclude]

    file_list = []
    for (directory, subdirs, files) in walk(topdir):
        directory = normpath(directory)
        for file in sorted(files):
            pathname = directory + "/" + file
            match = any([pattern.match(pathname) for pattern in name]) and \
                not any([pattern.match(pathname) for pattern in exclude])
            if match:
                file_list += [pathname]
    return file_list


def normpath(directory):
    directory = directory.replace("\\", "/")
    return directory


def glob_to_regex(pattern):
    """Convert a 'glob' pattern for file name matching to a regular
    expression. E.g. "foo.? bar*" -> "foo\\.. bar.*" """
    return "^" + pattern.replace(".", "\\.").replace("*", ".*").replace("?", ".") + "$"


if __name__ == "__main__":  # for testing
    topdir = "//Femto/C/All Projects/APS/Experiments/2011.02/Analysis/WAXS/Friedrich/run1"
    files = find(topdir, name="*.log", exclude=["*/laser_beamcheck.log", "*/backup/*"])
    for file in files:
        print(file)
