#!/usr/bin/env python3
"""
Created on Sun Aug 23 18:57:48 2020

@author: friedrich
"""
filenames = [
    "/tmp/test.hdf5",
    "/net/femto/C/Test/test.hdf5",
    "/net/femto-data/C/Test/test.hdf5",
    "/net/femto-data2/C/Test/test.hdf5",
    "/net/femto-control/mnt/data/test.hdf5",
]

from os.path import exists, dirname
from os import remove, makedirs

from os import environ
##environ["HDF5_USE_FILE_LOCKING"] = "FALSE"

import h5py

for filename in filenames:
    print(filename)
    if not exists(dirname(filename)): makedirs(dirname(filename))
    if exists(filename): remove(filename)
    
    with h5py.File(filename,driver="stdio",mode='a') as f:
        f.create_dataset('test', data = 0)

    remove(filename)
