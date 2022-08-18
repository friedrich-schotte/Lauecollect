"""
Author: Friedrich Schotte
Date created: 2011-03-02
Date last modified: 2022-08-07
Revision comment: Issue:
  File "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/scandir.py", line 676, in _walk
    for entry in walk(new_path, topdown, onerror, followlinks):
  [Previous line repeated 978 more times]
  File "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/scandir.py", line 634, in _walk
    is_dir = entry.is_dir()
  File "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/scandir.py", line 504, in is_dir
    st = self.stat(follow_symlinks=follow_symlinks)
  File "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/scandir.py", line 488, in stat
    if self.is_symlink():
  File "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/scandir.py", line 529, in is_symlink
    st = self.stat(follow_symlinks=False)
  File "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/scandir.py", line 497, in stat
    self._lstat = lstat(self.path)
  File "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/site-packages/scandir.py", line 482, in path
    self._path = join(self._scandir_path, self.name)
  File "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/posixpath.py", line 77, in join
    sep = _get_sep(a)
  File "/Library/Frameworks/Python.framework/Versions/3.9/lib/python3.9/posixpath.py", line 42, in _get_sep
    if isinstance(path, bytes):
  RecursionError: maximum recursion depth exceeded while calling a Python object
"""
__version__ = "1.2.6"

from typing import Union, Iterable


def find(topdir, name: Union[str, Iterable[str]], exclude: Union[str, Iterable[str]] = None):
    """A list of files on directory 'topdir' matching the patterns given by
    'name', excluding those matching thw patterns ''given by 'exclude'"""
    # try:
    #     from scandir import walk
    # except ImportError:
    #     from os import walk
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
    # topdir = "//Femto/C/All Projects/APS/Experiments/2011.02/Analysis/WAXS/Friedrich/run1"
    # name = "*.log"
    # exclude = ["*/laser_beamcheck.log", "*/backup/*"]
    from os import getcwd
    topdir = f"{getcwd()}"
    name = "*"
    exclude = []
    print('files = find(topdir, name=name, exclude=exclude)')
    print('for file in files: print(file)')
