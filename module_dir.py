"""Friedrich Schotte, 14 Nov 2014 - 14 Nov 2014"""
__version__ = "1.0"

def module_dir(object):
    """directory of the current module"""
    from os.path import dirname
    module_dir = dirname(module_path(object))
    ##module_dir = module_dir.replace("\\","/")
    if module_dir == "": module_dir = "."
    return module_dir

def module_path(object):
    """full pathname of the current module"""
    from normpath import normpath
    global MODULE_PATH
    if "MODULE_PATH" in globals(): return MODULE_PATH
    from sys import path
    from os import getcwd
    from os.path import basename,exists
    from inspect import getmodulename,getfile
    # 'getfile' retreives the source file name name compiled into the .pyc file.
    try: pathname = getfile(object)
    except: pathname = getfile(lambda x:x)
    ##print("module_path: pathname: %r" % pathname)
    if not exists(pathname): 
        # The module might have been compiled on a different machine or in a
        # different directory.
        pathname = pathname.replace("\\","/")
        filename = basename(pathname)
        ##print("module_path: filename: %r" % filename)
        dirs = [dir for dir in [getcwd()]+path if exists(dir+"/"+filename)]
        if len(dirs) == 0: print "pathname of file %r not found" % filename
        dir = dirs[0] if len(dirs) > 0 else "."
        pathname = dir+"/"+filename
        ##print("module_path: pathname: %r" % pathname)
    pathname = normpath(pathname)
    MODULE_PATH = pathname
    return pathname

if __name__ == "__main__":
    print "module_path(module_dir)"
    print "module_dir(module_dir)"
