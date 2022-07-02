"""
Author: Friedrich Schotte
Date created: 2022-06-20
Date last modified: 2022-06-22
Revision comment: Issue: in close:
    mmap.close(): AttributeError: 'File_Memory_Map' has no attribute 'mmap'
"""
__version__ = "1.0.1"

import logging


class File_Memory_Map:
    def __init__(self, filename, size, writable=True):
        self.filename = filename
        self.size = size
        self.writable = writable
        from mmap import mmap, ACCESS_WRITE, ACCESS_READ
        if self.writable:
            file = open(self.filename, "rb+")
            self.mmap = mmap(file.fileno(), offset=0, length=self.size, prot=ACCESS_WRITE)
        else:
            file = open(self.filename, "rb")
            self.mmap = mmap(file.fileno(), offset=0, length=self.size, prot=ACCESS_READ)

    def __repr__(self):
        return f"{self.class_name}({self.filename!r}, size={self.size}, writable={self.writable})"

    @property
    def class_name(self):
        return type(self).__name__

    def __len__(self):
        return self.mmap.__len__()

    def __getitem__(self, index):
        return self.mmap.__getitem__(index)

    def __setitem__(self, index, value):
        return self.mmap.__setitem__(index, value)

    def __del__(self):
        # logging.debug(f"Closing {self}.")
        self.close()

    def close(self):
        try:
            self.mmap.close()
        except AttributeError:
            pass


if __name__ == '__main__':
    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s, line %(lineno)d: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    # filename = "/net/femto-data2/C/Data/2021.07/WAXS/RNA-Poly-U12_Tramp_B-1/xray_images/RNA-Poly-U12_Tramp_B-1_0001_-16.000C_01.mccd"
    # filename = "/net/femto-data2/C/Data/2022.02/WAXS/Ca-CaM/Ca-CaM_PumpProbe_PC0-1/xray_images/Ca-CaM_PumpProbe_PC0-1_0001_-20us_01_-16.000C_01.mccd"
    # filename = "/net/femto-data2/C/Data/2022.03/WAXS/GB3/GB3_PumpProbe_PC0-1/xray_images/GB3_PumpProbe_PC0-1_0001_-10us_01_74.040C_01.mccd"
    filename = "/mx340hs/data/anfinrud_2203/Data/WAXS/RNA-Dumbbell-8BP/RNA-Dumbell-8BP_PumpProbe_PC0-2/xray_images/RNA-Dumbell-8BP_PumpProbe_PC0-2_0001_-10us_01_95.040C_01.mccd"
    # print("self.save('/tmp/test.rx')")
    self = File_Memory_Map(filename, size=4096)
