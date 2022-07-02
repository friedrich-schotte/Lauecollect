from glob import glob
files = sorted(glob("*.py"))
for file in files:
    content = open(file).read()
    new_content = content.replace('#!/bin/env\n','#!/usr/bin/env\n')
    if new_content != content:
        print("%r"%file)
        ##open(file,"w").write(new_content)
