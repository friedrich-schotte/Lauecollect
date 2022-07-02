#!/usr/bin/env python
"""Log file
Author: Friedrich Schotte,
Date created: 2019-03-02
Date last modified: 2022-03-23
Python Version: 2.7 and 3.7
Revision comment: Simplified
"""
__version__ = "2.0"

from logging import warning
from traceback import format_exc


class LogFile(object):
    name = "logfile"
    columns = ["date time", "value"]

    def __init__(self, filename):
        """filename: where to save
        columns: list of strings"""
        self.filename = filename
        from threading import Lock
        self.lock = Lock()

    def log(self, *args, **kwargs):
        """Append to logfile
        time: time in seconds since 1970-01-01 00:00:00 UTC
        """
        from time import time
        from time_string import date_time
        from normpath import normpath
        from os.path import exists, dirname
        from os import makedirs

        values = args
        if "time" in kwargs:
            timestamp = kwargs["time"]
        else:
            timestamp = time()

        with self.lock:  # Allow only one thread at a time inside this function.
            filename = normpath(self.filename)
            if not exists(filename):
                header = "#" + "\t".join(self.columns) + "\n"
            else:
                header = ""
            fields = [date_time(timestamp)] + [str(v) for v in values]
            line = "\t".join(fields) + "\n"
            directory = dirname(filename)
            if not exists(directory):
                try:
                    makedirs(directory)
                except OSError as x:
                    if not exists(directory):
                        warning(f"{directory}: {x}")
            if exists(directory):
                try:
                    open(filename, "ab").write((header + line).encode("UTF-8"))
                except OSError as x:
                    warning(f"{filename}: {x}")

    def history(self, *args, **kwargs):
        """time_range: t_min,t_max: time in seconds since 1970-01-01 00:00:00 UTC
        range: i_min,i_max: all values from i_min to i_max, including imax
        (Negative integers count from the end, -1 = last.)
        count: last N
        *args: column names"""
        if "count" in kwargs:
            count = kwargs["count"]
            lines = self.lines(*self.last_lines_range(count))
        elif "time_range" in kwargs:
            time_range = kwargs["time_range"]
            lines = self.lines(*self.timestamp_range(*time_range))
        else:
            lines = []
        column_names = args
        column_indices = [self.columns.index(name) for name in column_names]
        values = []
        for i in range(0, len(lines)):
            if len(lines[i]) == len(column_names):
                # noinspection PyBroadException
                try:
                    row_values = [convert(lines[i][j], name) for (j, name)
                                  in zip(column_indices, column_names)]
                    values += [row_values]
                except Exception:
                    warning("logfile: line %d/%d %r: %s" % (i + 1, len(lines), lines[i], format_exc()))
        values = list(zip(*values))  # organize data in rows
        if not values:
            values = [[]] * len(column_names)
        return values

    def lines(self, start, end):
        """Part of the file.
        start: byte offset (self.contents[start] is the first character included)
        end: byte offset (self.contents[end] will not be included)
        Return value: list of lists of strings, each list representing a line
        """
        lines = self.content[start:end].split(b"\n")
        # Get rid of empty lines.
        if lines[:1] == ['']:
            lines = lines[1:]
        if lines[-1:] == ['']:
            lines = lines[:-1]
        # Get rid of comment lines.
        while len(lines) > 0 and lines[0].startswith(b"#"):
            lines = lines[1:]
        lines = [line.split(b"\t") for line in lines]
        return lines

    def last_lines_range(self, count):
        """Where are the last n lines from the end of the file?
        Return value: tuple of byte offsets: begin,end
        """
        content = self.content
        j = len(content)
        if content[j - 1:j] == "\n":
            j -= 1
        i = j
        for n in range(0, count):
            i2 = content.rfind("\n", 0, i)
            if i2 < 0:
                break
            i = i2
        i += 1
        return i, j

    def timestamp_range(self, t1, t2):
        """Start and end byte offsets of a time range
        t1: seconds since 1970-01-01T00:00:00+00
        t2: seconds since 1970-01-01T00:00:00+00
        """
        return [self.timestamp_location(t) for t in (t1, t2)]

    def timestamp_location(self, timestamp):
        """First line with a time stamp later to the given time stamp.
        Return value: byte offset from the beginning of the file.
        Length of file if all timestamp in the file are earlier
        timestamp: seconds since 1970-01-01T00:00:00+00"""
        from numpy import isnan, clip
        text = self.content
        offset = len(text) // 2
        step = len(text) // 4
        while step > 0:
            # debug("offset %r, step %r" % (offset,step))
            t = self.next_timestamp(text, offset)
            if isnan(t):
                offset = len(text)
                break
            if t <= timestamp:
                offset += step
            else:
                offset -= step
            offset = clip(offset, 0, len(text))
            step = (step + 1) // 2 if step > 1 else 0
        return offset

    @staticmethod
    def next_timestamp(text, offset):
        from numpy import nan
        i = text.find(b"\n", offset) + 1
        if i < 0:
            t = nan
        else:
            j = text.find(b"\t", i)
            if j < 0:
                t = nan
            else:
                t = timestamp(text[i:j])
        return t

    @property
    def content(self):
        from normpath import normpath
        filename = normpath(self.filename)
        from mmap import mmap, ACCESS_READ
        try:
            f = open(filename)
            content = mmap(f.fileno(), 0, access=ACCESS_READ)
        except IOError:
            content = b""
        return content

    @property
    def content_new(self):
        from os.path import exists, getsize
        from normpath import normpath
        filename = normpath(self.filename)
        if exists(filename):
            size_change = getsize(filename) - len(self.cached_content)
            if size_change > 0:
                # debug("Logfile: Reading %d bytes" % size_change)
                f = open(filename)
                f.seek(len(self.cached_content))
                self.cached_content += f.read()
            elif size_change < 0:
                # debug("Logfile: Reading %d bytes" % getsize(filename))
                self.cached_content = open(filename, "rb").read()
        else:
            self.cached_content = b""
        return self.cached_content

    def get_cached_content(self):
        if self.filename in self.file_cache:
            content = self.file_cache[self.filename]
        else:
            content = b""
        return content

    def set_cached_content(self, content):
        self.file_cache[self.filename] = content

    cached_content = property(get_cached_content, set_cached_content)

    file_cache = {}

    @property
    def start_time(self):
        from time import time
        lines = self.lines(0, 80)
        # noinspection PyBroadException
        try:
            t = timestamp(lines[0][0])
        except Exception:
            t = time()
        return t

    def __len__(self):
        return self.content[:].count(b"\n") - 1


logfile = LogFile


def convert(x, name):
    """Try to convert string to a Python object.
    if not possible return a string
    name: if "date time", force conversion from string to seconds"""
    if name == "date time":
        return timestamp(x)
    try:
        return float(x)
    except ValueError:
        pass
    # noinspection PyBroadException
    try:
        return timestamp(x)
    except Exception:
        pass
    return x


def timestamp_fast(date_time):
    """Convert a date string to number of seconds since 1 Jan 1970 00:00 UTC
    date_time: e.g. "2017-10-04 20:17:34.286479-0500"
    or "2017-10-04 20:17:34-0500"
    """
    from datetime import datetime
    if date_time[-5:-4] and date_time[-5:-4] in b"+-":
        date_time, TZ = date_time[:-5], date_time[-5:]
    else:
        TZ = b"+0000"
    if b"." in date_time:
        date_format = "%Y-%m-%d %H:%M:%S.%f"
    else:
        date_format = "%Y-%m-%d %H:%M:%S"
    try:
        utc_dt = datetime.strptime(date_time.decode("utf-8"), date_format)
    except ValueError:
        # warning("{date_time!r} not matching format {date_format!r}")
        from numpy import nan
        timestamp = nan
    else:
        timestamp = (utc_dt - datetime(1970, 1, 1)).total_seconds()
    TZ_offset = int(TZ[0:3]) * 3600
    timestamp -= TZ_offset
    return timestamp


# from time_string import timestamp
timestamp = timestamp_fast  # might raise "unknown locale: en-US"

if __name__ == "__main__":
    import logging

    msg_format = "%(asctime)s %(levelname)s %(module)s.%(funcName)s: %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=msg_format)

    from instrumentation import BioCARS

    self = BioCARS.channel_archiver.logfile("NIH:TEMP.RBV")
    print('from time import time; t=time(); x=self.history("date time","value",time_range=(time()-10*60,time())); time()-t')
    print('len(self.content)')
    print('from time import time; t=time(); x=self.content; time()-t')
