"""
How do I mount a filesystem using Python?
https://stackoverflow.com/questions/1667257/how-do-i-mount-a-filesystem-using-python/26084472
"""

import ctypes
import ctypes.util
import os

libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)

# Linux: int mount(const char *source, const char *target,const char
#                 *filesystemtype, unsigned long mountflags,const void *data);
##libc.mount.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_ulong, ctypes.c_char_p) 
# BSD, MacOS: int mount(const char *type, const char *dir, int flags, void *data);
libc.mount.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p) 

def mount(source,target,fstype='nfs',options=''):
    flags = 0
    ##ret = libc.mount(source,target,fstype,0,options) # Linux
    ret = libc.mount(fstype,target,flags,source) # BSD, MacOS
    if ret < 0:
        errno = ctypes.get_errno()
        raise OSError(errno,"mount({!r},{!r},{!r},{!r}) = {}: {}".
            format(fstype,target,flags,source,ret,os.strerror(errno)))

from sh import mount,umount # pip install sh

if __name__ == "__main__":
   # mount femto.niddk.nih.gov:/C /nfs/femto/C
   print("mount('femto.niddk.nih.gov:/C','/nfs/femto/C')")
   print("umount('/nfs/femto/C')")
   print("mount('-t','afp','afp://femtoland:femtosir@femto.niddk.nih.gov:/C','/afp/femto/C')")
   print("umount('/afp/femto/C')")
