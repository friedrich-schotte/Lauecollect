"""
Date: 2019-04-23
"""
from struct import pack,calcsize,Struct

def write_packet(address,bitmask,count):
    type = 1
    version = 1
    length = 16
    data = pack(">BBHIII",type,version,length,address,bitmask,count)
    return data

write_scruct = Struct(">BBHIII")

def write_packet_2(address,bitmask,count):
    type = 1
    version = 1
    length = 16
    data = write_scruct.pack(type,version,length,address,bitmask,count)
    return data

address = 0
bitmask = 0
count = 0

if __name__ == "__main__":
    from timeit import timeit
    setup = "from test_struct import *"
    print('write_packet_2(address,bitmask,count)')
    print('timeit("data = write_packet(address,bitmask,count)",number=1000000,setup=setup)')
    print('timeit("data = write_packet_2(address,bitmask,count)",number=1000000,setup=setup)')
