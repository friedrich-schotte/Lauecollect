"""
Authors: Philip Anfinrud, Friedrich Schotte
Date created: 2021-21-02
Revision Comment: Added header.close() before utime
"""
__version__ = "1.0.1"


def mccd_ntp_write(path_name, ntp_start, ntp_stop):
    """Writes 'ntp_start' and 'ntp_stop' to header of path_name;
    preserves 'getmtime' file time stamp."""
    from os import utime
    from os.path import getmtime
    import mmap
    ntp_start_bytes = bytes(str("{}".format(ntp_start)), 'utf-8')
    ntp_stop_bytes = bytes(str("{}".format(ntp_stop)), 'utf-8')
    creation_time = getmtime(path_name)
    with open(path_name, "r+") as f:
        header = mmap.mmap(f.fileno(), 4096, access=mmap.ACCESS_WRITE)
        header[3104:3104 + len(ntp_start_bytes)] = ntp_start_bytes
        header[3136:3136 + len(ntp_stop_bytes)] = ntp_stop_bytes
        header.close() # Added 2021-12-02 Friedrich
    utime(path_name, (creation_time, creation_time))


def test(filename):
    from time_string import timestamp
    from date_time import date_time
    from os.path import getmtime
    ntp_stop = timestamp("2021-11-30 01:01:06.105282-0500")
    ntp_start = ntp_stop - 1.1
    print(f"{date_time(getmtime(filename))}")
    mccd_ntp_write(filename, ntp_start, ntp_stop)
    print(f"{date_time(getmtime(filename))}")


if __name__ == "__main__":
    filenames = [
        "/net/mx340hs.cars.aps.anl.gov/data/anfinrud_2112/Test/WAXS/Test/Test_Tramp-1_B/xray_images/Test_Tramp-1_B_0002_-16.000C_01.mccd",
        "/net/femto-data2.niddk.nih.gov/C/Data/2021.11/Test/WAXS/Reference/Reference-1_A/xray_images/Reference-1_A_0002_02.mccd",
    ]
    print("for filename in filenames: test(filename)")
    # Output:
    # 2021-11-30 01:01:07.319278-0500
    # 2021-11-30 01:01:07.319278-0500
    # 2021-11-23 16:11:04.292251-0500
    # 2021-11-23 16:11:04.292251-0500
