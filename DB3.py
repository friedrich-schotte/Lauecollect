"""Simple data base
Author: Friedrich Schotte 10 Dec 2010 - Sep 30, 2017
"""
from logging import debug
import sys

__version__ = "1.5" # multi-line
if sys.version_info[0] ==3:
    from _thread import allocate_lock
else:
    from thread import allocate_lock
lock = allocate_lock()

def dbset(name,value):
    """Store a value in the data base
    value: any python built-in data type"""
    dbput(name,repr(value))

def db(name,default_value=""):
    """Retrieve a value from the data base
    Return value: any built-in Python data type"""
    value = dbget(name)
    dtype = type(default_value)
    from numpy import nan,inf,array # for "eval"
    from collections import OrderedDict # for "eval"
    try: value = dtype(eval(value))
    except: value = default_value
    return value

def dbput(name,value):
    """Store a value in the data base
    value: string"""
    with lock: # Allow only one thread at a time in this critical section.
        basename = name.split(".")[0]
        resname = name[len(basename)+1:]
        dbread(basename)
        values = DB[basename]
        if resname in values and values[resname] == value: return
        DB[basename][resname] = value
        dbsave(basename)

def dbget(name):
    """Retrieve a value from the data base
    Return value: string, if not found: empty string"""
    with lock: # Allow only one thread at a time in this critical section.
        basename = name.split(".")[0]
        resname = name[len(basename)+1:]
        dbread(basename)
        values = DB[basename]
        if resname in values: return values[resname]
        else: return ""

def dbdir(name):
    """List of entries names starting with 'name'"""
    with lock: # Allow only one thread at a time in this critical section.
        from os.path import isdir
        keys = []
        basename = name.split(".")[0]
        pathname = normpath(settings_dir()+"/"+basename)
        files = listdir(pathname) if isdir(pathname) else []
        keys += [file.replace("_settings.py","") for file in files]
        resname = name[len(basename)+1:]
        dbread(basename)
        keys += list(set([key.split(".")[0] for key in DB[basename].keys()]))
        return keys

def listdir(pathname):
    """Directory content, minus "hidden" files"""
    from os import listdir
    filenames = listdir(pathname)
    # Exclude "hidden" files.
    filenames = [f for f in filenames if not f.startswith(".")]
    return filenames

def dbread(basename):
    from os.path import exists,getmtime
    from time import time
    from collections import OrderedDict
    
    if not basename in DB: DB[basename] = OrderedDict()
    settings_file = normpath(settings_dir()+"/"+basename+"_settings.py")
    # Check only every N seconds to avoid excessive system load.
    if settings_file in last_checked and \
       time()-last_checked[settings_file] < 1.0: return
    last_checked[settings_file] = time()
    
    if not exists(settings_file):
        ##debug("Settings file %r not found" % settings_file)
        return
    if settings_file in timestamps and \
        getmtime(settings_file) == timestamps[settings_file]: return
    try:
        file = open(settings_file,'r')
        settings = file.read()
    except IOError: settings = ""
    settings = settings.replace("\r","") # Convert DOS to UNIX

    DB[basename] = OrderedDict()
    values =  DB[basename]
    lines = settings.split("\n")
    if len(lines) > 0 and lines[-1] == "": lines = lines[0:-1]

    def process(entry):
        if "=" in entry:
            i = entry.index("=")
            resname = entry[:i].strip(" ")
            values[resname] = entry[i+1:].strip(" ")

    entry = ""
    for line in lines:
        # Continuation of previous entry?
        if entry == "": entry = entry = line
        elif entry.endswith("\\"): entry += "\n"+line
        elif line.startswith(" "): entry += "\n"+line
        elif line.startswith("\t"): entry += "\n"+line
        elif "=" not in line: entry += "\n"+line
        else: process(entry); entry = line
    process(entry)
        
    timestamps[settings_file] = getmtime(settings_file)

def dbsave(basename):
    from os.path import exists,getmtime,dirname,basename as file_basename
    from os import makedirs,umask,remove,rename
    from tempfile import NamedTemporaryFile
    from time import time
    if basename in DB: 
        values = DB[basename]
        lines = [key+" = "+values[key] for key in values]
        ##lines.sort()
        text = "\n".join(lines)
        umask(0) # make sure the file is writable to all users.
        settings_file = normpath(settings_dir()+"/"+basename+"_settings.py")
        if not exists(dirname(settings_file)): makedirs(dirname(settings_file))
        # Make sure that is a non-writeable file alreadt exists, is will be
        # replaced by a writeable file.
        tempfile = NamedTemporaryFile(delete=False,dir=dirname(settings_file),
            prefix=file_basename(settings_file))
        tempfile.write(text)
        tempfile.close()
        if exists(settings_file): remove(settings_file)
        rename(tempfile.name,settings_file)
        timestamps[settings_file] = getmtime(settings_file)
        last_checked[settings_file] = time()

def normpath(pathname):
    """Make sure no illegal characters are contained in the file name."""
    # Colon (:) may in the path after the drive letter.
    pathname = pathname[0:2]+pathname[2:].replace(":","")
    illegal_chars = "?*"
    for c in illegal_chars: pathname = pathname.replace(c,"")
    return pathname

# Needed by "dbread" and "dbsave"
DB = {}
timestamps = {}
last_checked = {}
    
def settings_dir():
    """Pathname of the file used to store persistent parameters"""
    if sys.version_info[0] ==3:
        from module_dir3 import module_dir
    else:
        from module_dir import module_dir
    path = module_dir(settings_dir)+"/settings"
    return path

if __name__ == '__main__': # for testing
    from pdb import pm
    import logging
    logging.basicConfig(level=logging.DEBUG,format="%(asctime)s: %(message)s")
    from time import time
    print('print(dbget("LaueCrystallographyControl.GotoSaved.action"))')
    print('dbset("LaueCrystallographyControl.time",time())')

