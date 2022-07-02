#!/usr/bin/env python
"""
Remove a file or directory
Author: Friedrich Schotte
Date created: 2020-06-19
Date last modified: 2020-06-19
Revision comment:
"""
__version__ = "1.0"

def remove(pathname):
    from os.path import isdir
    if not isdir(pathname):
        from os import remove
        remove(pathname)
    else:
        from shutil import rmtree
        rmtree(pathname)

if __name__ == "__main__":
    pathname = "/tmp/test"
    print("open(pathname,'w').write('test\\n')")
    from os import makedirs
    print("makedirs(pathname)")
    print("open(pathname+'/test','w').write('test\\n')")
    print("remove(pathname)")
    from os.path import exists
    print("exists(pathname)")
