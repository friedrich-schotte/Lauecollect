"""
Documentation:
HS High Speed Series X-ray Detector Manual by Ross A. Doyle and Justin Anderson
File: Rayonix_HS_detector_manual-0.3a.pdf
Chapter 8: Image Format (marccd), p. 50

Authors: Hyun Sun Cho, Friedrich Schotte
Date created: 2015-01-24
Date last modified: 2021-09-07
Revision comment: Cleanup
"""
__version__ = "1.0.7"

from logging import error


def rayonix_image_timestamp(filename, timestamp_type="acquire_timestamp"):
    """read mccd file and decode information
    timestamp_type: "acquire_timestamp", "header_timestamp", or "save_timestamp" """
    from mmap import mmap, ACCESS_READ
    with open(filename, "rb") as f:
        # try to map to reduce any overhead to read file.
        content = mmap(f.fileno(), length=0, prot=ACCESS_READ, offset=2048)
        f.close()

    offset = 2048
    # offset = content.find(b"MarCCD X-ray Image File")

    if timestamp_type == "acquire_timestamp":
        timestamp = content[offset+320:offset+352]
    elif timestamp_type == "header_timestamp":
        timestamp = content[offset+352:offset+384]
    elif timestamp_type == "save_timestamp":
        timestamp = content[offset+384:offset+416]
    else:
        error(f"{timestamp_type!r}: expecting 'acquire_timestamp', 'header_timestamp', or 'save_timestamp'")
        timestamp = content[offset + 320:offset + 352]

    months = int(timestamp[:2])
    days = int(timestamp[2:4])
    hours = int(timestamp[4:6])
    minutes = int(timestamp[6:8])
    year = int(timestamp[8:12])
    seconds = int(timestamp[13:15])
    # Old version rayonix mccd file on before Feb 6 2015 does not have microseconds
    try:
        microseconds = int(timestamp[16:22])
    except ValueError:
        microseconds = 0

    from datetime import datetime
    date_time = datetime(year, months, days, hours, minutes, seconds, microseconds)
    from time import mktime
    ts = mktime(date_time.timetuple()) + date_time.microsecond * 1.e-6
    return ts


if __name__ == "__main__":  # for testing
    filename = "/net/femto-data2/C/Data/2021.07/WAXS/RNA-Poly-U12_Tramp_B-1/xray_images/RNA-Poly-U12_Tramp_B-1_0001_-16.000C_01.mccd"
    print("date_time(rayonix_image_timestamp(filename, 'acquire_timestamp'))")
    print("date_time(rayonix_image_timestamp(filename, 'header_timestamp'))")
    print("date_time(rayonix_image_timestamp(filename, 'save_timestamp'))")
    print("t0=time(); t=rayonix_image_timestamp(filename); print(time()-t0)")
