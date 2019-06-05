#!/usr/bin/env python
"""This is to rename images files that have been given wrong  during
data collection. This script also updates Lauecollect logfiles.
Author: Friedrich Schotte
Date created: 2011-07-27
Date last modified: 2019-06-02
"""
__version__ = "1.4.1" # Issues: repeat in old name, empty replacement string

from logging import debug,info,warn,error

def rename_files(directories,replacements,test_run=False):
    """directories: list of folders to search
    replacements: list of [old,new] pairs
    test_run: True to generate a list of filenames affects."""
    from find import find
    from os import utime
    from os.path import exists,getmtime
    try: from scandir import walk
    except ImportError: from os import walk
    import re

    update_extensions = [".log",".par","_timing.txt"]
    exclude = ["*/.*","*/trash*","*/backup*"]
    exclude = [re.compile(glob_to_regex(pattern)) for pattern in exclude]

    for topdir in directories:
        for (directory,subdirs,files) in walk(topdir):
            old_directory = directory
            directory = renamed_filename(directory)
            for basename in subdirs+files:
                old = directory+"/"+basename
                match = not any([pattern.match(old) for pattern in exclude])
                if not match: continue
                new = replace_all(old,replacements)
                if new != old: 
                    if exists(new):
                        info("Keeping   %s" % old)
                        info("Exists!   %s" % new)
                        continue
                    rename(old,new,test_run)
                # Update file contents
                filename = new if not test_run else old_directory+"/"+basename 
                if any([new.endswith(ext) for ext in update_extensions]):
                    old_content = file(filename).read()
                    new_content = replace_all(old_content,replacements)
                    if new_content != old_content:
                        backup_file = new+".old"
                        i = 2
                        while exists(backup_file):
                            backup_file = new+(".old%d" % i)
                            i += 1
                        rename(new,backup_file,test_run)
                        info("Rewriting %s" % new)
                        if not test_run: 
                            file(new,"wb").write(new_content)
                            # Set the file timestamp to be the same as of the original file.
                            utime(new,(-1,getmtime(backup_file)))
            if not test_run:
                subdirs[:] = [replace_all(s,replacements) for s in subdirs]

renamed = {}

def renamed_filename(filename):
    old_filename = filename
    while True:
        for old in renamed:
            if filename.startswith(old):
                filename = filename.replace(old,renamed[old],1)
        if filename == old_filename: break
        old_filename = filename
    return filename

def replace_all(s,replacements):
    """replacements: list of pairs [old,new]"""
    for name,replacement in replacements:
        s = replace(s,name,replacement)
    return s

def glob_to_regex(pattern):
    """Convert a 'glob' pattern for file name matching to a regular
    expression. E.g. "foo.? bar*" -> "foo\.. \bar.*" """
    return "^"+pattern.replace(".","\.").replace("*",".*").replace("?",".")+"$"

def rename(old,new,test_run):
    """Move or rename a file"""
    from os import makedirs,rename
    from os.path import dirname,exists

    renamed[old] = new
    info("Renaming  %s" % old)
    info("->        %s" % new)
    if not test_run:
        if not exists(dirname(new)): makedirs(dirname(new))
        rename(old,new)

def replace(string,old,new):
    """Substitute occurences of "old" in string by "new"
    Return value: string with replacements made."""
    occurances = set(findall(string,old))
    # Make sure that if "old" is a substring of "new", occurrances of
    # "new" will not be modified.
    if old in new: occurances -= set(findall(string,new))
    return replace_at(string,old,new,occurances)
    
def findall(string,sub):
    """Starting indices of all occuenreces of a substring within a string.
    E.g. findall("Allowed Hello Hollow","ll") -> [1,10,16]"""
    indices = []
    if len(sub) > 0:
        index = 0 - len(sub)
        while True:
            index = string.find(sub,index+len(sub))
            if index == -1: break
            indices += [index]
    return indices

def replace_at(string,old,new,indices):
    """Replace the substring "old" by "new" in a string at specific locations
    only.
    indices: starting indices of the occurences of "old" where to perform the
    replacement
    return value: string with replacements done"""
    if len(indices) == 0: return string
    indices = sorted(indices)
    s = string[0:indices[0]]
    for i in range(0,len(indices)-1):
        s += string[indices[i]:indices[i+1]].replace(old,new,1)
    s += string[indices[-1]:].replace(old,new,1)
    return s


if __name__ == "__main__":
    from pdb import pm # for debugging
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    directories = [
        "/net/mx340hs/data/anfinrud_1906/Data/WAXS/RNA-Hairpin/RNA-Hairpin-4BP/RNA-Hairpin-4BP-CG-Stem-End/RNA-Hairpin-4BP-CG-Stem-End-1",
    ]
    replacements = [
        ["RNA-Hairpin-4BP-CG-Stem-End-1RNA-Hairpin-4BP-CG-Stem-End-1",
         "RNA-Hairpin-4BP-CG-Stem-End-1"],
    ]
    rename_files(directories,replacements,test_run=True)
