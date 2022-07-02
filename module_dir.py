"""
Author: Friedrich Schotte
Date created : 2014-11-14
Date last modified: 2020-12-25
Revision comment: Cleanup
"""
__version__ = "1.0.3"

from logging import error


def module_dir(obj):
    """directory of the current module"""
    from os.path import dirname
    module_dir = dirname(module_path(obj))
    # module_dir = module_dir.replace("\\","/")
    if module_dir == "":
        module_dir = "."
    return module_dir


MODULE_PATH = ""


def module_path(obj):
    """full pathname of the current module"""
    from normpath import normpath
    global MODULE_PATH
    if not MODULE_PATH:
        from inspect import getfile
        # 'getfile' retrieves the source file name name compiled into the .pyc file.
        try:
            pathname = getfile(obj)
        except TypeError:
            pathname = getfile(lambda x: x)
        # debug("module_path: pathname: %r" % pathname)
        from os.path import isabs, join
        from os import getcwd
        if not isabs(pathname):
            pathname = join(getcwd(), pathname)
        # debug("module_path: pathname: %r" % pathname)
        from os.path import exists
        if not exists(pathname):
            # The module might have been compiled on a different machine or in a
            # different directory.
            pathname = pathname.replace("\\", "/")
            from os.path import basename
            filename = basename(pathname)
            # debug("module_path: filename: %r" % filename)
            from sys import path
            from os import getcwd
            dirs = [d for d in [getcwd()] + path if exists(d + "/" + filename)]
            if len(dirs) == 0:
                error("pathname of file %r not found" % filename)
            directory = dirs[0] if len(dirs) > 0 else "."
            pathname = directory + "/" + filename
            # debug("module_path: pathname: %r" % pathname)
        pathname = normpath(pathname)
        # debug("module_path: pathname: %r" % pathname)
        MODULE_PATH = pathname
    return MODULE_PATH


if __name__ == "__main__":
    print("module_path(module_dir)")
    print("module_dir(module_dir)")
    from timeit import timeit
    print(timeit('module_dir(module_dir)', number=1, globals=globals()))
