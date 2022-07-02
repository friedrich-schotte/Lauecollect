#!/usr/bin/env python
"""Author: Friedrich Schotte
Date created: 2019-11-15
Date last modified: 2019-11-15
"""

def disk_space(directory):
    from numpy import nan
    bytes_available = nan
    try: from os import statvfs
    except ImportError: warn("os.statvfs not supported in this platform")
    else:
        try: s = statvfs(directory)
        except Exception,x: warn("statvfs: %s: %s" % (directory,x))
        else: bytes_available = s.f_bavail*s.f_frsize
    return bytes_available 

if __name__ == "__main__":
    print("disk_space(%r)")
